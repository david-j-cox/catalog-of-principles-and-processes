export const meta = {
  name: 'entry-validation-batch',
  description: 'Single-reviewer EAB validation of catalog entries (metadata + behavioral-process tag), escalate on doubt',
  phases: [ { title: 'Review', model: 'sonnet' }, { title: 'Escalate', model: 'opus' } ],
}

const KINDS = __KINDS__
const byKind = (k) => Object.keys(KINDS).filter(x => KINDS[x] === k).sort()
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
    processes:  { type: 'array', items: { type: 'string' } },
    principles: { type: 'array', items: { type: 'string' } },
    other_tags: { type: 'array', items: { type: 'string' } },
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

const TAXNOTE = `THE CATALOG SEPARATES TWO THINGS. Tag both for every article.

PROCESS - the pattern of behaviour-environment interaction the study ARRANGED, which
reliably produces a phenomenon. "What happens when I run this?" Schedules, shaping,
matching-to-sample, extinction.

PRINCIPLE - the fundamental component interacting within that process which predicts the
output. Usually known through its output rather than observed directly, the way gravity
is. Reinforcement, discrimination, stimulus control.

RULES THE VOCABULARY WAS BUILT ON. Apply them; do not work around them.
1. BREADTH. A label naming a paradigm rather than a specific relation is useless even
   when true - "Classical Conditioning" is like tagging a physics paper "Quantum
   Physics". Such labels have been removed. Never reach for the broad parent when a
   specific child fits, and never propose a paradigm-level label.
2. AN INPUT IS A MEASURE, NOT A PRINCIPLE. Anything you set, present, or read off the
   apparatus - a delay, a magnitude, a stimulus, a response requirement - is a measure of
   a known input that drives a principle within a process. The principle is the invisible
   thing doing the work, never the dial.
3. A METHOD IS A PROCESS, NOT A PRINCIPLE. Differential, alternative and noncontingent
   reinforcement are ways of APPLYING reinforcement. The principle is reinforcement.
4. TIME IS A STIMULUS DIMENSION. A timing study is discrimination or generalization with
   time as the input, exactly as another study uses a light or a tone. Tag it
   Discrimination (principle) + Temporal Stimulus (measure) + the procedure (process).
   The same holds for visual, auditory, olfactory, gustatory, tactile, interoceptive and
   spatial stimuli.
5. PREFER THE MEASURED RELATION TO AN INTERPRETATION OF IT. "Delay Discounting" names
   what was measured; "self-control" and "impulsivity" are readings laid over the same
   data, and are not in the vocabulary.
6. A PRINCIPLE EXPLAINS; A PHENOMENON NEEDS EXPLAINING. If many processes produce it and
   it would itself have to be accounted for by something more foundational, it is a
   phenomenon, not a principle. Behavioural momentum and response strength are phenomena
   for exactly this reason: reinforcement rate, magnitude and delay are invoked to
   explain them. Reinforcement and discrimination explain other things and are not
   themselves explained here - those are principles.

Use ONLY labels from the lists below, copied EXACTLY, each in its own field. An empty
field is correct when the article genuinely does not support one - do not pad. If the
article's process or principle is genuinely absent from the vocabulary, set
proposes_new_label=true and needs_human=true rather than forcing a poor fit; a proposal
must pass rule 1 at both ends: not a paradigm, and not a one-off that would fit one paper.

PROCESSES: ${byKind('process').join(' | ')}

PRINCIPLES: ${byKind('principle').join(' | ')}

PHENOMENA (the reliable output a process produces; goes in other_tags):
${byKind('phenomenon').join(' | ')}

MEASURES (inputs you set and outputs you read; goes in other_tags):
${byKind('measure').join(' | ')}

MODELS (formal quantitative accounts; goes in other_tags): ${byKind('model').join(' | ')}`

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
2) PROCESS AND PRINCIPLE. The stored tags are a legacy FLAT list that mixed the two
   together, so treat them as a starting point, not as ground truth. Split what is
   correct into the right field, drop what the rules above disqualify, and add what is
   missing. Name what the study ARRANGED (processes) and what that arrangement ENGAGED
   (principles). Most articles support at least one of each; if you can name only one
   side, say why in notes rather than inventing the other. Put phenomena, measures and
   models in other_tags. process_action describes what you did to the stored tags:
   validated_unchanged, corrected, normalized, assigned, left_empty, or flagged_remove.
3) EQUATION SWEEP. Source reachability for this entry was probed in advance:
   source_status=${e.source_status}${e.pmcid ? `, pmcid=${e.pmcid}` : ''}.
   ${e.source_status === 'fulltext'
     ? `RUN THIS TASK. PMC serves the machine-readable HTML body for this article: fetch \
https://pmc.ncbi.nlm.nih.gov/articles/${e.pmcid}/ and read it directly. Display equations appear as \
MathML. This route is known to work; do not settle for 'unknown'.`
     : e.source_status === 'scan'
       ? `RUN THIS TASK. The PMC page carries only the abstract, so go straight to the rendered PDF: \
https://europepmc.org/articles/${e.pmcid}?pdf=render -- it has an OCR text layer. Do not stop at the \
PMC landing page.`
       : `SKIP THIS TASK. No PMC route exists for this article (Elsevier or APA); it needs publisher \
access we do not have here. Return equation_in_text="unknown", equation_note="no PMC route", and \
spend nothing on it.`}
   VERIFY IDENTITY BEFORE READING. PMC has served a cached page for a DIFFERENT article on first
   fetch (observed: a request for PMC1389770 returned PMC1389781's body). After fetching, read the
   page's citation_pmcid / citation_pmid / citation_doi / citation_title meta tags and confirm they
   match THIS entry. If they do not, re-fetch until they do. If you cannot confirm identity, set
   needs_human=true and say so -- never validate an entry against a body you have not confirmed is
   the right article. State the id you matched on in equation_note.
   Determine whether the article DISPLAYS a mathematical equation (a numbered or
   set-off display equation stating a model). Judge only from the source:
   - 'present'  -> the article displays at least one equation. In equation_note, name it briefly
                   (e.g. "Eq. 1, Mazur hyperbolic V = A/(1+kD)") so the equation panel can pick it up.
   - 'none'     -> you read the source and it displays no equations.
   - 'unknown'  -> LAST RESORT ONLY, after every route below has failed. Do NOT guess from the
                   abstract. In equation_note, list which routes you tried and how each failed.
   RESOLUTION ROUTES -- work them in order; a PMC landing page showing only a PDF is NOT a dead end:
     a. Europe PMC full text XML (best): https://www.ebi.ac.uk/europepmc/webservices/rest/PMC<id>/fullTextXML
     b. Europe PMC rendered PDF, which carries a text layer the PMC landing page does not:
        https://europepmc.org/articles/PMC<id>?pdf=render
     c. The PMC article page itself: https://pmc.ncbi.nlm.nih.gov/articles/PMC<id>/
     d. The DOI / publisher page (often HTTP 402; that alone does not justify 'unknown').
   CRITICAL -- scanned JEAB PDFs carry an OCR text layer that SUBSTITUTES DIGITS FOR OPERATORS:
   '=' appears as '5', '+' as '1', '-' as '2'. A real equation therefore looks like
   "PC 5 b0 1 b1S1 1 b2S2" (= "PC = b0 + b1S1 + b2S2"). NEVER conclude 'none' from an absence of
   '=' characters: a body with zero '=' can still be full of equations.
   Decide as follows:
     - Search for explicit references: "Equation <n>", "Eq. <n>", "the following equation". These are
       RELIABLE. Any hit -> 'present'; quote the reference and the equation line in equation_note.
     - The digit-substitution pattern alone is NOT reliable evidence: "r 5 2.31" is the inline
       statistic r = -.31, and "the 5 rats" is just the number five. Use it to READ an equation you
       have already located, not to detect one.
     - 'none' only when you have the full body text AND found no equation references AND no set-off
       display lines. Say in equation_note that you read the full text.
   Report the character count of the text you actually searched, so a zero-effort verdict is visible.
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
ENTRY: title="${e.title}"; authors=${JSON.stringify(e.authors)}; journal=${e.journal}; stored legacy tags=${JSON.stringify(e.process)}.
REVIEWER 1: ${JSON.stringify(r1)}
REVIEWER 2: ${JSON.stringify(r2)}
Produce the final metadata_fixes, processes and principles (canonical labels, each in its own
field), other_tags, the equation_in_text verdict
(prefer a reviewer who actually reached the source over one who did not), and an honest signoff. Only
signoffs=1 / reviewed=true if both reviewers substantively agree and no human check is needed; else
needs_human=true. Return the structured object only.`
}

function needEscalate(r) {
  return !r || r.needs_human === true || r.confidence < 0.6 || r.proposes_new_label === true
}

const results = (await pipeline(
  BATCH,
  (e) => agent(reviewPrompt(e), { label: `rev:${e.idx}`, phase: 'Review', schema: FINAL_SCHEMA, model: 'sonnet' }),
  (r, e) => {
    if (!needEscalate(r)) return r
    return agent(reviewPrompt(e), { label: `rev2:${e.idx}`, phase: 'Escalate', schema: FINAL_SCHEMA, model: 'opus' })
      .then(r2 => agent(seniorPrompt(e, r, r2), { label: `snr:${e.idx}`, phase: 'Escalate', schema: FINAL_SCHEMA, model: 'opus' }))
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
