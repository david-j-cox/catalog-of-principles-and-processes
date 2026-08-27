#!/usr/bin/env python3
"""Audit already-processed entries for wrong-article reads.

PMC has served a cached page for a different article on first fetch. Any entry
validated off such a fetch would carry tags/metadata describing the wrong paper.

For every processed entry with a PMC route, fetch the page and compare the
citation_title meta tag against the catalog title. Writes
.validation/identity_audit.json: {idx: {pmcid, catalog_title, page_title, match}}.
Resumable.
"""
import json, os, re, subprocess, sys, time
from difflib import SequenceMatcher

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, '.validation/identity_audit.json')
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36'


def norm(s):
    return re.sub(r'[^a-z0-9 ]', '', (s or '').lower()).strip()


def curl(url):
    r = subprocess.run(['curl', '-sL', '-A', UA, '--max-time', '45', url],
                       capture_output=True, text=True, errors='ignore')
    return r.stdout


def meta(html, name):
    m = re.search(r'<meta[^>]+name=["\']%s["\'][^>]+content=["\']([^"\']*)' % name, html, re.I)
    if not m:
        m = re.search(r'<meta[^>]+content=["\']([^"\']*)["\'][^>]+name=["\']%s["\']' % name, html, re.I)
    return m.group(1) if m else ''


def main():
    data = json.load(open(os.path.join(ROOT, 'data.json')))
    prog = json.load(open(os.path.join(ROOT, '.validation/progress.json')))
    fmap = json.load(open(os.path.join(ROOT, '.validation/fulltext_map.json')))
    out = json.load(open(OUT)) if os.path.exists(OUT) else {}

    targets = sorted(set(prog['entry_track']['done']))
    todo = [i for i in targets
            if str(i) not in out and (fmap.get(str(i)) or {}).get('pmcid')]
    print(f'auditing {len(todo)} processed entries with a PMC route', flush=True)

    for n, i in enumerate(todo, 1):
        pid = fmap[str(i)]['pmcid']
        html = curl(f'https://pmc.ncbi.nlm.nih.gov/articles/{pid}/')
        ptitle = meta(html, 'citation_title')
        ppmc = meta(html, 'citation_pmcid') or ''
        ctitle = data[i].get('title') or ''
        ratio = SequenceMatcher(None, norm(ctitle), norm(ptitle)).ratio() if ptitle else 0.0
        out[str(i)] = {'pmcid': pid, 'page_pmcid': ppmc, 'catalog_title': ctitle,
                       'page_title': ptitle, 'ratio': round(ratio, 3),
                       'match': ratio >= 0.75}
        if n % 20 == 0:
            json.dump(out, open(OUT, 'w'), indent=1)
            print(f'  {n}/{len(todo)}', flush=True)
        time.sleep(0.4)

    json.dump(out, open(OUT, 'w'), indent=1)
    bad = [k for k, v in out.items() if not v['match']]
    print(f'done. checked={len(out)} mismatches={len(bad)}')
    for k in bad:
        v = out[k]
        print(f"  idx {k} ({v['pmcid']}) ratio={v['ratio']}")
        print(f"    catalog: {v['catalog_title'][:80]}")
        print(f"    page   : {v['page_title'][:80]}")


if __name__ == '__main__':
    main()
