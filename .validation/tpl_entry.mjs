export const meta = {
  name: 'entry-validation-batch',
  description: 'Single-reviewer EAB validation of catalog entries (metadata + behavioral-process tag), escalate on doubt',
  phases: [ { title: 'Review' }, { title: 'Escalate' } ],
}

const CANON = __CANON__
const BATCH = __BATCH__

const FINAL_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['idx','metadata_changed','metadata_fixes','process_action','process_final','proposes_new_label','reviewed','signoffs','needs_human','confidence','notes','equation_in_text','equation_note'],
  properties: {
    idx: { type: 'integer' },
    metadata_changed: { type: 'boolean' },
    metadata_fixes: { type: 'object', additionalProperties: false, properties: {
      authors: { type: 'array', items: { type: 'string' } },
      abstract: { type: 'string' }, url: { type: 'string' },
      year: { type: 'integer' }, journal: { type: 'string' }, title: { type: 'string' },
      note: { type: 'string' } } },
    process_action: { type: 'string', enum: ['validated_unchanged','corrected','normalized','assigned','left_empty','flagged_remove'] },
    process_final: { type: 'array', items: { type: 'string' } },
    proposes_new_label: { type: 'boolean' },
    reviewed: { type: 'boolean' },
    signoffs: { type: 'integer' },
    needs_human: { type: 'boolean' },
    confidence: { type: 'number' },
    notes: { type: 'string' },
    equation_in_text: { type: 'string', enum: ['none','present','unknown'] },
    equation_note: { type: 'string' },
  },
}

const FRAME = `You are an editor in the Experimental Analysis of Behavior (EAB) tradition validating a
behavioral-research catalog entry. Journals: JEAB, JEP:ALC (J. Exp. Psych: Animal Learning/Behavior
Processes), BP (Behavioural Processes). You know the canonical behavioral processes and schedules.`

const TAXNOTE = `BEHAVIORAL-PROCESS TAXONOMY (canonical controlled vocabulary). Prefer EXACT matches from this
list; treat case/format variants as the same concept and normalize to the canonical spelling here.
Only set proposes_new_label=true (and needs_human=true) if the paper's process genuinely is not
covered by any canonical label. Be conservative: if you cannot confidently determine the process from
the available title/abstract, leave process empty and set needs_human=true rather than guessing.
CANONICAL: ${CANON.join(' | ')}`

function reviewPrompt(e) {
  return `${FRAME}

${TAXNOTE}

ENTRY (catalog index ${e.idx}):
  title: ${e.title}
  authors: ${(e.authors||[]).join('; ') || '(MISSING)'}
  year: ${e.year}   journal: ${e.journal}
  url: ${e.url || '(MISSING)'}
  abstract: ${e.abstract || '(MISSING)'}
  current process tags: ${e.process.length ? e.process.join(' | ') : '(NONE)'}

TASKS:
1) METADATA: Check authors/abstract/url/year/journal for obvious errors or gaps. If a field is MISSING
   and you can recover it from the title/url/your knowledge of this paper (you MAY web-fetch the url or
   web-search the title), fill it in metadata_fixes; otherwise leave it. Do NOT fabricate. Set
   metadata_changed=true only if you propose a concrete fix.
2) PROCESS: If tags exist, validate each against the paper and the canonical taxonomy: keep good ones
   (validated_unchanged), fix wrong ones (corrected), normalize case/format variants (normalized), or
   mark clearly-wrong junk for removal (flagged_remove). If NO tags, assign 1-3 canonical processes
   when confident (assigned), else leave_empty + needs_human=true. process_final = the final tag list.
3) EQUATION SWEEP: determine whether the article DISPLAYS a mathematical equation (a numbered or
   set-off display equation stating a model). Fetch the url once to check. Judge only from the source:
   - 'present'  -> the article displays at least one equation. In equation_note, name it briefly
                   (e.g. "Eq. 1, Mazur hyperbolic V = A/(1+kD)") so the equation panel can pick it up.
   - 'none'     -> you read the source and it displays no equations.
   - 'unknown'  -> the source is paywalled, a scan, or otherwise not machine-readable. Do NOT guess
                   from the abstract, and do not burn further calls trying.
   Inline statistics (t, F, p, r-squared), fit diagnostics, and descriptive formulas are NOT equations
   for this purpose. Only models mapping independent variables to behavior count. Do NOT write the
   equation into any other field; flagging it here is the whole task.
4) SIGNOFF: reviewed=true and signoffs=1 only if you are confident in BOTH metadata and process and
   no human check is needed; otherwise reviewed=false, signoffs=0, needs_human=true.
Set needs_human=true if: you propose a new label, you removed/changed an existing human tag, you made a
metadata fix you are unsure of, or confidence < 0.6. Return the structured object only.`
}

function seniorPrompt(e, r1, r2) {
  return `${FRAME}

${TAXNOTE}

Two independent reviewers assessed catalog index ${e.idx}. Reconcile into a single FINAL decision.
ENTRY: title="${e.title}"; authors=${JSON.stringify(e.authors)}; journal=${e.journal}; current process=${JSON.stringify(e.process)}.
REVIEWER 1: ${JSON.stringify(r1)}
REVIEWER 2: ${JSON.stringify(r2)}
Produce the final metadata_fixes, process_final (canonical tags), the equation_in_text verdict
(prefer a reviewer who actually reached the source over one who did not), and an honest signoff. Only
signoffs=1 / reviewed=true if both reviewers substantively agree and no human check is needed; else
needs_human=true. Return the structured object only.`
}

function needEscalate(r) {
  return !r || r.needs_human === true || r.confidence < 0.6 || r.proposes_new_label === true
}

const results = (await pipeline(
  BATCH,
  (e) => agent(reviewPrompt(e), { label: `rev:${e.idx}`, phase: 'Review', schema: FINAL_SCHEMA }),
  (r, e) => {
    if (!needEscalate(r)) return r
    return agent(reviewPrompt(e), { label: `rev2:${e.idx}`, phase: 'Escalate', schema: FINAL_SCHEMA })
      .then(r2 => agent(seniorPrompt(e, r, r2), { label: `snr:${e.idx}`, phase: 'Escalate', schema: FINAL_SCHEMA }))
  },
)).filter(Boolean)

return {
  track: 'entry',
  count: results.length,
  signed_off: results.filter(r => r.signoffs >= 1).length,
  needs_human: results.filter(r => r.needs_human).length,
  metadata_changed: results.filter(r => r.metadata_changed).length,
  process_assigned: results.filter(r => r.process_action === 'assigned').length,
  equations_found: results.filter(r => r.equation_in_text === 'present').length,
  equations_unknown: results.filter(r => r.equation_in_text === 'unknown').length,
  results,
}
