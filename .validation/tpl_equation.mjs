export const meta = {
  name: 'eab-equation-panel-batch',
  description: 'Three-editor EAB peer-review + signoff over a batch of equation-bearing entries',
  phases: [ { title: 'Reconstruct' }, { title: 'Review' }, { title: 'Signoff' } ],
}

const EAB = `You are a senior editor for the quantitative-analysis section of a journal in the
Experimental Analysis of Behavior (EAB) tradition (think JEAB). You know the canonical
quantitative models cold: Herrnstein's matching law R1/(R1+R2)=r1/(r1+r2) and single-operant
hyperbola R=kr/(r+r_e); Baum's generalized matching law log(B1/B2)=a*log(r1/r2)+log c and its
power form; deVilliers' subtractive punishment model R1/(R1+R2)=(r1-c*p1)/((r1-c*p1)+(r2-c*p2));
Davison & Tustin / McCarthy & Davison signal-detection-and-bias models
log(P_w/P_x)=a_r*log(R_w/R_z)+a_s*log(S2/S1)+log c and log d discriminability; concatenated
matching, feedback functions for VI schedules, optimization/maximization accounts, and Bayesian
choice updates. You write equations in clean LaTeX.`

const SCAN_NOTE = `Source-access reality: most pre-1990 JEAB papers on PubMed Central are SCANNED PAGE
IMAGES, so their equations are NOT machine-readable by web fetch. Born-digital papers (roughly 2010+)
and many secondary sources (reviews, textbooks, later papers that restate the model) ARE readable.
So: reconstruct from EAB domain expertise using the surviving corrupted fragments as a guide to WHICH
equations the paper presented; corroborate with web search/fetch when a machine-readable source exists;
and when you cannot confidently confirm a specific equation against the canon, say so plainly rather
than inventing. Never fabricate a citation or claim you read a scan you could not read.`

function meta_block(p) {
  return `PAPER METADATA
  catalog index: ${p.idx}
  title: ${p.title}
  authors: ${(p.authors || []).join('; ')}
  year: ${p.year}   journal: ${p.journal}   vol ${p.volume} iss ${p.issue} pp ${p.pages}
  url: ${p.url}`
}

function fragments_block(p) {
  return `CURRENT (possibly corrupted) FIELDS — semicolon-delimited equation fragments:
  static-equation:
  ${p.static_equation || '(empty)'}
  static-equation-definitions:
  ${p.static_definitions || '(empty)'}
  recursive-equation:
  ${p.recursive_equation || '(empty)'}
  recursive-equation-definitions:
  ${p.recursive_definitions || '(empty)'}`
}

const RECON_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['idx','method','source_machine_readable','corrected_static_equation','corrected_static_definitions','corrected_recursive_equation','corrected_recursive_definitions','equations','confidence','notes'],
  properties: {
    idx: { type: 'integer' },
    method: { type: 'string', enum: ['reconstructed_from_expertise','corrected_partial','verified_unchanged','unresolved'] },
    source_machine_readable: { type: 'boolean' },
    source_url: { type: 'string' },
    equations: { type: 'array', items: { type: 'object', additionalProperties: false,
      required: ['latex','role','confidence'],
      properties: { latex: { type: 'string' }, role: { type: 'string' }, confidence: { type: 'number' } } } },
    corrected_static_equation: { type: 'string' },
    corrected_static_definitions: { type: 'string' },
    corrected_recursive_equation: { type: 'string' },
    corrected_recursive_definitions: { type: 'string' },
    confidence: { type: 'number' },
    notes: { type: 'string' },
  },
}

const REVIEW_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['verdict','eab_consistency','equation_issues','missing_or_extra','confidence','comments'],
  properties: {
    verdict: { type: 'string', enum: ['accept','accept_with_changes','reject'] },
    eab_consistency: { type: 'string' },
    equation_issues: { type: 'array', items: { type: 'object', additionalProperties: false,
      required: ['equation','problem','suggested_fix'],
      properties: { equation: { type: 'string' }, problem: { type: 'string' }, suggested_fix: { type: 'string' } } } },
    missing_or_extra: { type: 'string' },
    confidence: { type: 'number' },
    comments: { type: 'string' },
  },
}

const SIGNOFF_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['idx','changed','final_static_equation','final_static_definitions','final_recursive_equation','final_recursive_definitions','reviewed','signoffs','human_followup_required','followup_reason','panel_confidence','editor_summary'],
  properties: {
    idx: { type: 'integer' },
    changed: { type: 'boolean' },
    final_static_equation: { type: 'string' },
    final_static_definitions: { type: 'string' },
    final_recursive_equation: { type: 'string' },
    final_recursive_definitions: { type: 'string' },
    reviewed: { type: 'boolean' },
    signoffs: { type: 'integer' },
    human_followup_required: { type: 'boolean' },
    followup_reason: { type: 'string' },
    panel_confidence: { type: 'number' },
    editor_summary: { type: 'string' },
  },
}

function reconstruct(p) {
  const prompt = `${EAB}

${SCAN_NOTE}

TASK: You are EDITOR 1 (reconstruction). Produce the corrected equation set for this catalog entry.
${meta_block(p)}

${fragments_block(p)}

Instructions:
- The semicolon-delimited fragments are a corrupted extraction. Each fragment is (meant to be) one displayed
  equation from the paper. Identify each intended equation and write it as clean, compilable LaTeX (no surrounding
  $ or \\[ \\]; just the math body, as the catalog stores it).
- Repair corruption artifacts: stray '_' / '*_' tails, injected ']()' or backticks, '\\n\\[' page-break debris,
  and equations cut off mid-token (e.g. "\\frac{r_1 - \\a" -> complete to the canonical form).
- Preserve the paper's own notation and the ORDER of equations. Do not add equations the paper did not present.
- corrected_static_equation = the cleaned equations joined by "; " (matching the catalog's storage format).
- If the entry's current fields look already-correct (common for non-flagged entries), set
  method="verified_unchanged" and echo them back cleaned only of obvious artifacts.
- Set source_machine_readable=true ONLY if you genuinely read a machine-readable source; otherwise false.
Return the structured object. Your output is data, not prose.`
  return agent(prompt, { label: `recon:${p.idx}`, phase: 'Reconstruct', schema: RECON_SCHEMA })
}

function reviewer(p, recon, n) {
  const lens = n === 1
    ? 'Lens A - MODEL CORRECTNESS: verify each equation is the correct canonical form for this paper\'s model, with correct subscripts, parameters, and algebraic structure. Catch wrong signs, swapped numerators/denominators, missing terms.'
    : 'Lens B - NOTATION & COMPLETENESS: verify LaTeX compiles, notation is internally consistent and matches the paper\'s conventions, equation order/count matches the fragments, and nothing canonical is missing or hallucinated.'
  const prompt = `${EAB}

${SCAN_NOTE}

TASK: You are an INDEPENDENT EAB REVIEWER. Adversarially review EDITOR 1's reconstruction. Default to skepticism:
only "accept" if you would stake your name on it. ${lens}
${meta_block(p)}

ORIGINAL (corrupted) fragments:
${p.static_equation || '(empty static)'}
${p.recursive_equation ? 'recursive: ' + p.recursive_equation : ''}

EDITOR 1 RECONSTRUCTION (JSON):
${JSON.stringify(recon)}

Judge whether the reconstruction faithfully and correctly represents the equations this specific paper presented,
consistent with the EAB quantitative canon. List concrete equation_issues with fixes. Return the structured object.`
  return agent(prompt, { label: `review${n}:${p.idx}`, phase: 'Review', schema: REVIEW_SCHEMA })
}

function signoff(p, recon, reviews) {
  const prompt = `${EAB}

${SCAN_NOTE}

TASK: You are the SENIOR EDITOR. Arbitrate Editor 1's reconstruction and the two independent reviews, then issue the
FINAL equation fields and a signoff decision for catalog index ${p.idx}.
${meta_block(p)}

ORIGINAL fields:
  static-equation: ${p.static_equation || '(empty)'}
  static-equation-definitions: ${p.static_definitions || '(empty)'}
  recursive-equation: ${p.recursive_equation || '(empty)'}
  recursive-equation-definitions: ${p.recursive_definitions || '(empty)'}

EDITOR 1 (JSON): ${JSON.stringify(recon)}

REVIEWER 1 (JSON): ${JSON.stringify(reviews[0])}

REVIEWER 2 (JSON): ${JSON.stringify(reviews[1])}

Decide the final fields, applying reviewer fixes you agree with. Rules:
- final_* fields hold the authoritative corrected values (static-equation as "; "-joined canonical LaTeX).
- changed = true iff any final field differs from the ORIGINAL field above.
- signoffs = 1 ONLY if the panel is confident the equations are correct and faithful to the paper; else 0.
- reviewed = true once this panel has adjudicated it (true in essentially all cases).
- human_followup_required = true when correctness depends on details only verifiable against the physical/scanned
  paper, or reviewers materially disagreed.
- followup_reason: empty string if none.
Return the structured object only.`
  return agent(prompt, { label: `signoff:${p.idx}`, phase: 'Signoff', schema: SIGNOFF_SCHEMA })
}

const BATCH = __BATCH__
log(`EAB equation panel: ${BATCH.length} entries`)
const results = (await pipeline(
  BATCH,
  (p) => reconstruct(p),
  (recon, p) => parallel([ () => reviewer(p, recon, 1), () => reviewer(p, recon, 2) ]).then(reviews => ({ recon, reviews })),
  (bundle, p) => signoff(p, bundle.recon, bundle.reviews),
)).filter(Boolean)

return {
  track: 'equation',
  total: results.length,
  signed_off: results.filter(r => r.signoffs >= 1).length,
  human_followup: results.filter(r => r.human_followup_required).length,
  results,
}
