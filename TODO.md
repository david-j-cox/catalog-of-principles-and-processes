# TODO — Behavioral Process Catalog

All automated audit items complete. Three full audit passes plus an EAB equation peer-review conducted and resolved.

## Equation peer review (EAB three-editor panel)

The 15 previously-flagged corrupted equations were reconstructed by an EAB-lens panel
(reconstruction editor + two independent reviewers + senior-editor signoff) and the
corrected LaTeX + definitions written to `data.json`. Method: reconstruction from the
quantitative-EAB canon guided by the surviving corrupted fragments, because the source
papers are pre-1990 JEAB scans with no machine-readable equation layer (corroborated by
web search/fetch where born-digital sources exist).

**Panel-validated (signoffs = 1, no further action):** 2175, 2204, 4331.

### Human followup — verify against the physical/scanned paper (signoffs = 0)

These 12 are corrected and canon-consistent, but specific details could only be inferred
(not read), because the originals are scanned images. Each needs a human to check the
named detail against the actual paper, then bump `signoffs` to 1.

- **[2120] Toward a Quantitative Theory of Punishment** (conf 0.76)
  Exchange-constant symbol (reconstructed as \alpha; canonical house style is c); and whether a simple additive form with distinct p_1, p_2 was also displayed.
- **[2121] Choice and Reinforcement Delay** (conf 0.60)
  RHS of the proportion-form matching equation (immediacy proportion vs obtained-rate proportion R(s)/(R(s)+R(l))), whether it is a distinct equation, and the truncated trailing factor (source ended in "\cd").
- **[2131] Undermatching on Concurrent VI Schedules and the Power Law** (conf 0.78)
  Whether the terminal +\log c is a displayed equation or a restated general form (model predicts c=1); and the power-law exponent term completions.
- **[2134] On the Discriminability of Stimulus Discrimination** (conf 0.78)
  The +/- log d and +log c bias terms on the two basic condition equations (inferred by analogy, not read).
- **[2144] Reinforcement and Punishment Effects in Concurrent Schedules** (conf 0.78)
  Core model equations confident; the eight appendix partial-derivative/slope terms cannot be corroborated and need checking.
- **[2150] An Analytic Comparison of Herrnstein's Equations and a Multivariate Rate Equation** (conf 0.62)
  Canonical core verified; the multivariate-rate-equation-specific forms (e.g. the e^{1/R} series steps and a_1/a_2 ratio expressions) need source confirmation.
- **[2171] Feedback Functions for Variable-Interval Reinforcement** (conf 0.72)
  The truncated E(R_1...) expression and the paired-equation system (x+y=c, x*y=c) provenance.
- **[2176] Alternative Reinforcement Effects on Fixed-Interval Performance** (conf 0.60)
  The two fitted sensitivity exponents (a) are lost in the corruption and could not be recovered; operational identity of T and R.
- **[2210] Paired Baseline Performance as a Behavioral Ideal** (conf 0.68)
  The (b-1) log-ratio tail, the exponent b in N_1/N_2, the second Slope denominator, and the role of the constant 60.
- **[2211] How to Maximize Reward Rate on Two Variable-Interval Paradigms** (conf 0.56)
  The a_2^{*} closed form and the \hat{\tau}(\lambda)/S(\lambda) critical-value expressions (lowest panel confidence — review first).
- **[2212] Optimal Choice** (conf 0.60)
  The truncated final equation (cut at "t_A=\frac{", completed by inference) and Bayesian-update notation.
- **[2248] Optimization and the Matching Law as Accounts of Instrumental Behavior** (conf 0.78)
  frag 37 (q_2 = bB/B_0) is conjectural from corrupted "q_2 = b\,Bd/k"; verify, plus the VR-VI square-root result.

## Incomplete — full-corpus equation sweep

The peer-review workflow was also configured to deep-review the other **205** equation-bearing
entries (those not in the flagged 15). That phase was interrupted by a session limit before
completing and produced no adjudicated results. Re-run when ready (the 15 above are cached and
return instantly on resume). Note: the heuristic corruption scan found no defects beyond the 15,
so the 205 are expected to be clean — this sweep is confirmatory.

---

## Closed / Won't Fix

- **~~Migrate data.json to Git LFS~~**
  Investigated: GitHub Pages does not serve LFS-tracked files — it would serve the pointer file instead of the actual JSON, breaking the site. Workaround requires a GitHub Actions deploy workflow, which adds complexity for a no-build-step site. The `.git` size (38MB) is manageable at current scale.
