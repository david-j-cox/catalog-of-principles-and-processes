#!/usr/bin/env python3
"""Probe which catalog entries have machine-readable full text on PMC.

Writes .validation/fulltext_map.json: {idx: {pmcid, chars, math, status}}.
  status = 'fulltext'  body text present (born-digital HTML)
           'scan'      PMC has only abstract + a scanned PDF
           'nopmc'     no PMC record (Elsevier / APA / unresolved)
           'error'     fetch failed after retries

Uses curl (this environment's Python has no working SSL chain).
Resumable: re-running keeps entries already probed.
"""
import json, os, re, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAP = os.path.join(ROOT, '.validation/fulltext_map.json')
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36'
FULLTEXT_MIN = 15000   # visible chars; scanned PMC pages run ~7k (abstract+refs)
DELAY = 0.4            # be polite to NCBI


def curl(url, timeout=45):
    try:
        r = subprocess.run(['curl', '-sL', '-A', UA, '--max-time', str(timeout), url],
                           capture_output=True, text=True, errors='ignore')
        return r.stdout
    except Exception:
        return ''


def visible_chars(html):
    t = re.sub(r'<script.*?</script>|<style.*?</style>', ' ', html, flags=re.S | re.I)
    t = re.sub(r'<[^>]+>', ' ', t)
    return len(re.sub(r'\s+', ' ', t))


def resolve_dois(dois):
    """Batch DOI -> PMCID via the NCBI ID converter (200 per call)."""
    out = {}
    for i in range(0, len(dois), 180):
        chunk = dois[i:i + 180]
        url = ('https://pmc.ncbi.nlm.nih.gov/tools/idconv/api/v1/articles/'
               '?tool=catalog&email=cox.david.j%40gmail.com&format=json&ids=' + ','.join(chunk))
        try:
            for rec in json.loads(curl(url)).get('records', []):
                if rec.get('pmcid'):
                    out[rec.get('doi')] = rec['pmcid']
        except Exception:
            pass
        print(f'  resolved {len(out)}/{min(i+180, len(dois))}', flush=True)
        time.sleep(DELAY)
    return out


def main():
    data = json.load(open(os.path.join(ROOT, 'data.json')))
    done = json.load(open(MAP)) if os.path.exists(MAP) else {}

    # 1) PMCID straight from the url
    pmcid = {}
    dois = {}
    for i, e in enumerate(data):
        if str(i) in done:
            continue
        u = e.get('url') or ''
        m = re.search(r'(PMC\d+)', u)
        if m:
            pmcid[i] = m.group(1)
            continue
        m = re.search(r'(10\.\d{4,9}/[^\s"<>]+)', u)
        if m:
            d = m.group(1).rstrip('/')
            # only SEAB-era DOIs are in PMC; Elsevier/APA are not
            if d.startswith('10.1901'):
                dois[i] = d

    # 2) resolve the SEAB DOIs
    if dois:
        print(f'resolving {len(dois)} DOIs...', flush=True)
        res = resolve_dois(sorted(set(dois.values())))
        for i, d in dois.items():
            if d in res:
                pmcid[i] = res[d]

    # everything with no PMC route
    for i, e in enumerate(data):
        if str(i) not in done and i not in pmcid:
            done[str(i)] = {'pmcid': None, 'chars': 0, 'math': 0, 'status': 'nopmc'}

    print(f'probing {len(pmcid)} PMC pages...', flush=True)
    n = 0
    for i, pid in sorted(pmcid.items()):
        html = curl(f'https://pmc.ncbi.nlm.nih.gov/articles/{pid}/')
        if not html:
            html = curl(f'https://pmc.ncbi.nlm.nih.gov/articles/{pid}/')  # one retry
        if not html:
            done[str(i)] = {'pmcid': pid, 'chars': 0, 'math': 0, 'status': 'error'}
        else:
            c = visible_chars(html)
            mth = len(re.findall(r'<math|mml:math|MathML', html))
            done[str(i)] = {'pmcid': pid, 'chars': c, 'math': mth,
                            'status': 'fulltext' if c >= FULLTEXT_MIN else 'scan'}
        n += 1
        if n % 50 == 0:
            json.dump(done, open(MAP, 'w'))
            print(f'  {n}/{len(pmcid)}', flush=True)
        time.sleep(DELAY)

    json.dump(done, open(MAP, 'w'))
    counts = {}
    for v in done.values():
        counts[v['status']] = counts.get(v['status'], 0) + 1
    print('done:', json.dumps(counts))


if __name__ == '__main__':
    main()
