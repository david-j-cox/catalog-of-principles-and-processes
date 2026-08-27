#!/usr/bin/env python3
"""Score a local ollama model's process-tagging against the Opus pipeline's output.

Ground truth = entries the full pipeline validated and applied (ai-reviewed, not needs-human).
The local model sees only title + abstract + the canonical vocabulary, which is exactly the
input available for the 7,674 nopmc entries that dominate the remaining corpus.

Usage: python3 .validation/local_bench.py <model> [limit] [out.json]
"""
import json, os, re, sys, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL = sys.argv[1] if len(sys.argv) > 1 else 'qwen2.5:72b'
LIMIT = int(sys.argv[2]) if len(sys.argv) > 2 else 0
OUT = sys.argv[3] if len(sys.argv) > 3 else os.path.join(ROOT, '.validation/local_bench.json')

rows = json.load(open(os.path.join(ROOT, 'data.json')))
prog = json.load(open(os.path.join(ROOT, '.validation/progress.json')))
canon = json.load(open(os.path.join(ROOT, '.validation/taxonomy.json')))['canonical']
canon_lower = {c.lower(): c for c in canon}

gt = [i for i in prog['entry_track']['done']
      if rows[i].get('ai-reviewed') is True and not rows[i].get('needs-human')
      and (rows[i].get('process') or []) and (rows[i].get('abstract') or '').strip()]
if LIMIT:
    gt = gt[:LIMIT]

V2 = os.environ.get('BENCH_PROMPT') in ('v2', 'v3')
# v3: candidate generation. The model does not decide, it narrows 172 labels to K so the
# API reviewer adjudicates a shortlist instead of the whole vocabulary. The metric that
# matters here is recall@K - a true label missing from the shortlist is unrecoverable.
K = int(os.environ.get('BENCH_K') or 0)

SYS = ("You are an editor in the Experimental Analysis of Behavior (EAB) tradition tagging a "
       "behavioral-research catalog entry. Choose 1-3 labels from the controlled vocabulary that "
       "name the behavioral processes this paper studies. Use ONLY labels from the list, copied "
       "exactly. Reply with a JSON array of strings and nothing else.")

SYS_V2 = ("You are an editor in the Experimental Analysis of Behavior (EAB) tradition tagging a "
          "behavioral-research catalog entry. Use ONLY labels from the controlled vocabulary, "
          "copied exactly.\n"
          "THE VOCABULARY CONTAINS BROAD AND SPECIFIC LABELS THAT OVERLAP. Rules:\n"
          "- Always choose the MOST SPECIFIC label the paper supports. Never use a broad parent "
          "when a specific child fits: prefer 'Conditional Discrimination' over 'Discrimination'; "
          "prefer 'Schedule: Concurrent Variable-Interval' over 'Schedule: Concurrent'.\n"
          "- Do NOT tag generic mechanisms every operant study shares. 'Reinforcement', "
          "'Stimulus Control' and 'Response Rate' are almost never right on their own - tag the "
          "specific process or schedule instead.\n"
          "- Name the experimental QUESTION, not just the apparatus: studies comparing allocation "
          "between alternatives are 'Choice'; drug-manipulation studies are "
          "'Behavioral Pharmacology'; sample-comparison procedures are 'Matching to Sample'.\n"
          "- Prefer the 'Schedule: X' spelling over 'Schedules of Reinforcement: X'.\n"
          "- Give 2-4 labels.\n"
          "Reply with a JSON array of strings and nothing else.")


def ask(title, abstract):
    if K:
        tail = (f"List the {K} labels most likely to apply, best first. Favour coverage: it is "
                f"better to include a plausible label than to omit a correct one.\n"
                f"JSON array of exactly {K} exact labels:")
    else:
        tail = "JSON array of exact labels:" if V2 else "JSON array of 1-3 exact labels:"
    prompt = (f"CONTROLLED VOCABULARY (choose only from these):\n{' | '.join(canon)}\n\n"
              f"PAPER\ntitle: {title}\nabstract: {abstract[:2500]}\n\n" + tail)
    body = json.dumps({
        'model': MODEL, 'prompt': prompt, 'system': SYS_V2 if V2 else SYS, 'stream': False,
        'options': {'temperature': 0, 'num_ctx': 8192, 'num_predict': 120 + 30 * K},
    }).encode()
    req = urllib.request.Request('http://localhost:11434/api/generate', body,
                                 {'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(r.read())['response']


def parse(txt):
    m = re.search(r'\[.*?\]', txt, re.S)
    if not m:
        return []
    try:
        vals = json.loads(m.group(0))
    except Exception:
        return []
    out = []
    for v in vals:
        if isinstance(v, str) and v.strip().lower() in canon_lower:
            out.append(canon_lower[v.strip().lower()])   # snap to canonical spelling
    return out


results, t0 = [], time.time()
for n, i in enumerate(gt, 1):
    r = rows[i]
    try:
        raw = ask(r['title'], r.get('abstract') or '')
        pred = parse(raw)
    except Exception as e:
        raw, pred = f'ERROR {e}', []
    truth = [t for t in r['process']]
    ps, ts = set(p.lower() for p in pred), set(t.lower() for t in truth)
    results.append({
        'idx': i, 'title': r['title'][:90], 'pred': pred, 'truth': truth,
        'exact': ps == ts, 'any_overlap': bool(ps & ts),
        'jaccard': len(ps & ts) / len(ps | ts) if (ps | ts) else 0.0,
        'in_vocab': len(pred) > 0, 'raw': raw[:200],
    })
    if n % 10 == 0 or n == len(gt):
        el = time.time() - t0
        print(f'  {n}/{len(gt)}  {el:.0f}s  ({el/n:.1f}s/entry)', flush=True)

N = len(results)
tp = sum(len(set(p.lower() for p in r['pred']) & set(t.lower() for t in r['truth'])) for r in results)
npred = sum(len(r['pred']) for r in results)
ntrue = sum(len(r['truth']) for r in results)
prec = tp / npred if npred else 0.0
rec = tp / ntrue if ntrue else 0.0
summary = {
    'prompt': f'v3(K={K})' if K else ('v2' if V2 else 'v1'),
    'recall_at_k': rec,
    'entries_fully_covered': sum(1 for r in results
        if set(t.lower() for t in r['truth']) <= set(p.lower() for p in r['pred'])) / N,
    'label_precision': prec, 'label_recall': rec,
    'label_f1': 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0,
    'labels_per_entry_pred': npred / N, 'labels_per_entry_truth': ntrue / N,
    'model': MODEL, 'n': N,
    'exact_set_match': sum(r['exact'] for r in results) / N,
    'any_overlap': sum(r['any_overlap'] for r in results) / N,
    'mean_jaccard': sum(r['jaccard'] for r in results) / N,
    'produced_valid_labels': sum(r['in_vocab'] for r in results) / N,
    'seconds_per_entry': (time.time() - t0) / N,
}
json.dump({'summary': summary, 'results': results}, open(OUT, 'w'), indent=2)
print(json.dumps(summary, indent=2))
