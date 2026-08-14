# Chain-of-thought error monitoring on HLE physics

Code and results for a study of whether monitor LLMs can identify the first erroneous step in step-numbered physics solutions produced by frontier models, and how that ability depends on what the monitor is told about the correct answer.

**Status.** Ground truth is frozen (`gold_version 2026-07-30-v1`). Human annotation is complete. Seven monitors have been run across all five conditions; one held-out frontier monitor (Kimi K3) is pending and will be added under a pre-committed analysis. Numbers below are current as of that freeze and are regenerated, not hand-copied — run `paper_numbers(OUTPUT_DIR)` in the notebook to reproduce every figure quoted here.

## Overview

Scalable oversight proposes that weaker or cheaper models can audit the reasoning of stronger ones. This study tests a concrete version: a monitor reads a solution and reports whether it contains a genuine error and, if so, which step the first error occurs at.

Final-answer correctness and first-error step are labelled **independently**. That independence creates the cell the study centres on: traces whose final answer is correct despite flawed reasoning. These are the only traces where access to the reference answer cannot reveal that an error exists — and they are the shape a sabotaging model's output would take.

The headline result is that giving a monitor the reference answer converts process monitoring into answer checking. Under certification the monitors flag **94.9%** of traces whose conclusion is wrong but locate the error in only **37.9%** of error traces. On the correct-answer/flawed-reasoning cell, certification provides no benefit and slight harm.

## Method

### Questions and traces

Questions come from the physics subset of Humanity's Last Exam. Questions with images, pure knowledge-recall items, and questions that were not genuinely multi-step were removed. Three frontier models (GPT-5.5, Claude Opus 4.7, Gemini 3.1 Pro) each produced one step-numbered solution per question.

Nine questions (27 traces) were used for an inter-rater reliability pilot with volunteer physicist annotators using a custom HTML tool (included here). The pilot rubric carried extra fields (error type, coherence); only `is_correct` and `error_step` reached usable agreement, and the main study uses only those two.

### Ground truth

The reference standard is an **adjudicated composite**, not a human gold standard, and its provenance is reported per label rather than as a single tier.

Construction ran in three stages. A frozen pre-human AI debate (Claude Opus 4.8 annotating, GPT-5.5 responding, Claude replying) produced one independent arm. Volunteer physicist annotators produced a second, independently. A dossier stage then synthesised the two, and disagreements were resolved by the author against the frozen rubric, blind to which arm had proposed which step.

The two independent arms agree on final-answer correctness for **90.7%** of jointly covered traces and on error presence for **76.0%**. Where both name a step they agree exactly **49%** of the time (about six times the uniform chance rate of 7.8%), which is why localization targets went through explicit adjudication rather than being inherited from either arm.

A portion of the adjudications were made in the HTML review tools rather than through code, and the historical decision exports have since drifted. **Gold itself is the authoritative record of those judgements**; the notebook reconstructs them from it rather than from the exports.

Frozen Gold: **252 rows, 237 ready, 15 excluded** across 5 excluded questions. The ready set is 79 questions × 3 generators:

| cell | n |
|---|---|
| correct answer, no error | 129 |
| wrong answer (all contain an error) | 83 |
| **correct answer, flawed reasoning** | **25** |

108 error traces in total: 97 with an exact adjudicated step, 11 with an interval. Error labels: 195 inherited from the composite, 42 set by author adjudication — concentrated in the critical cell, where **17 of 25** localization targets were adjudicated directly.

### Benchmark corrections

Sixteen HLE physics reference answers were reviewed and found to need correction, and three further items are not well-posed as physics questions (they stipulate alternative-universe rules whose stated premises do not determine a unique answer). Corrected keys were used for labelling and for the answer-visible conditions. Corrections are being reported to the HLE maintainers; the correction registry is not distributed here while those items are under review.

### Monitors

deepseek-v4flash, qwen3-32b, qwen-2.5-72b, llama-3.3-70b, grok-4.3, gemini-3.1-pro, claude-fable-5. Kimi K3 is held out and will be run against a hash-committed analysis.

GPT-5.5 and Claude Opus are excluded as monitors because they produced the ground-truth debate. Two contamination caveats are reported rather than assumed away: gemini-3.1-pro generated a third of the traces and so self-reviews them, and claude-fable-5 shares a family with the generator of another third and contributed to a small number of disputed adjudications. Results are reported with and without Fable, and split by monitor–generator family match.

### Conditions

Four conditions form an **information ladder** — each sees a strict superset of the one before:

- **BLIND** (`C0`) — question and full step-numbered solution. No reference answer. The deployment-realistic condition.
- **HINT** (`C1u`) — as BLIND, plus the reference answer framed as proposed and unverified, with an instruction not to trust it.
- **CERT** (`C1`) — the same answer string, framed as known correct, with an explicit warning that a correct final answer does not imply sound reasoning.
- **REVISE** (`C3`) — the monitor's own BLIND verdict is replayed to it, then the certified answer is revealed and it may revise.

Two further conditions sit off the ladder:

- **RCTRL** (`C3n`) — identical to REVISE except the answer is withheld and the monitor is merely invited to reconsider. This is the control for reconsideration pressure: without it, revision under certification is confounded with a model folding when questioned.
- **STEP** (`C2`) — the monitor sees the solution one prefix at a time and commits at the first step it flags. This is a **compound intervention, not a rung**: it hides future context, segments the trace, makes one decision per step, and takes the union of them, so its false-positive rate accumulates with trace length. It is reported separately throughout.

### Metrics

**Balanced accuracy** — the mean of sensitivity and specificity. Chance is 0.5. Reported because the monitors sit at wildly different operating points: deepseek-v4flash flags 94.5% of traces under BLIND at specificity 0.078, so plain accuracy or recall alone would rank the least informative monitor first.

**Exact localization (L₀)** — the share of *all* Gold error traces where the monitor both flagged the trace and named the correct step. Missing the error and flagging the wrong step both count as failures. This is the primary outcome, because it is what the monitors were instructed to do.

**Cell-restricted recall** — the fraction of error traces flagged, computed separately on the wrong-answer and correct-answer/flawed cells against a common per-monitor subset. Specificity does not decompose by cell (all traces in an error cell are positives), which is why it is reported only in aggregate.

**AUC** — threshold-free discrimination on `error_confidence`. Marked degenerate where a monitor emits near-constant confidence.

**Four-way localization outcome** — early / exact / late / missed, over all Gold error traces. "Flagged too early" is what any-flag sensitivity silently credits as a success.

## Results

### The information ladder

Means across the seven monitors:

| condition | balanced accuracy | exact localization L₀ |
|---|---|---|
| STEP *(off ladder)* | .609 | .215 |
| BLIND | .637 | .290 |
| HINT | .711 | .313 |
| CERT | **.789** | .379 |
| REVISE | .769 | **.421** |

Balanced accuracy rises monotonically along the ladder and looks like oversight straightforwardly improving. Localization rises far less, and the gap between the two panels is the study's methodological claim.

### The interaction

Cell-restricted recall, BLIND → CERT:

- mean gain on wrong-answer traces: **+0.262**, closing 73.4% of the remaining headroom
- mean gain on correct-answer/flawed traces: **−0.086**
- difference-in-differences positive for **7 of 7** monitors (exact two-sided sign test, *p* = 0.0156)

Under CERT, six of seven monitors land between 0.855 and 0.988 on the wrong-answer cell — near ceiling, and mechanically what comparing a final answer against a key produces. The flawed cell does not move, despite a prompt that explicitly warns a correct answer does not imply sound reasoning.

### Detection versus localization

Under CERT the monitors detect **94.9%** of wrong-answer traces and locate the error in **37.9%** of all error traces. Answer access buys an alarm, not an explanation.

The four-way decomposition (pooled, share of error traces):

| condition | early | exact | late | missed |
|---|---|---|---|---|
| BLIND | .165 | .271 | .213 | .351 |
| HINT | .146 | .286 | .302 | .267 |
| CERT | .120 | .356 | .361 | .163 |
| REVISE | .146 | .399 | .310 | .145 |
| STEP | .188 | .194 | .216 | .402 |
| RCTRL | .211 | .143 | .189 | .457 |

Going BLIND → CERT, early flags fall while late flags rise sharply: monitors given the answer place their flags further **downstream** of the true first error, consistent with reasoning backwards from the conclusion rather than forwards through the derivation.

### Revision

Net of the RCTRL control, revealing the certified answer causes monitors to withdraw prior flags at **+0.401** on clean traces (correct behaviour) and **+0.182** on flawed traces (oversight retracting a correct judgement). It causes them to add new flags to **93.2%** of previously-unflagged wrong-answer traces against **17.5%** of flawed ones — the same asymmetry in every monitor.

Harmful withdrawal falls as monitor capability rises: gemini-3.1-pro nets **0.000** on the flawed cell and fable-5 **+0.111**, against **+0.400** for qwen3-32b. Whether certification produces evidence-sensitive revision or plain deference appears to be a capability property. Since a trusted monitor in a control setting is weaker than the model it oversees by construction, the failure concentrates where it matters most.

### Stepwise

STEP has the highest miss rate of any condition pooled (.402) and the lowest exact localization (.194), though this varies considerably by monitor. It flags more and locates less: it removes the anchor and pays for it in false positives on clean traces.

## Limitations

The correct-answer/flawed cell holds 25 traces, so cross-monitor consistency of direction is the unit of evidence rather than any single per-monitor change. Localization targets in that cell are 68% author-adjudicated, which is unavoidable — it is where the independent arms disagreed — but it means the headline cell is the most adjudicator-dependent. The study covers a single domain. Every error studied is an honest generator mistake, not an adversarially planted one. Several monitors emit near-constant or anti-calibrated confidence, limiting AUC comparison. STEP emits no comparable graded score, so BLIND-versus-STEP comparisons are between two fixed operating points. Kimi K3's API fixes temperature at 1.0, so its run will be a single draw rather than a deterministic one.

## Repository contents

- `oversight_pipeline.ipynb` — monitor prompts and runners (threaded httpx, append-only JSONL with resume and retry), the six condition runners, scoring, `paper_numbers()` and the figure module. Ground-truth construction stages are gated behind `REGENERATE = False`: they are a record of how Gold was built, and running them would rebuild a frozen artefact.
- `hle_annotator_v3.html` — the annotation tool used by the volunteer annotators.
- `figures/` — the four results figures.
- `summaries/` — per-condition metric CSVs (`c0`, `c1u`, `c1`, `c2`, `c3`, `c3n`), plus `revision_summary.csv`.

Raw JSONL (HLE question text, model traces, monitor outputs containing trace text) is deliberately withheld to keep HLE viable as a held-out benchmark. Labels and monitor verdicts with question text removed will be released alongside the paper.

## Reproducing the analysis

```python
REGENERATE = False          # default; do not rebuild frozen artefacts
summarize_c0(glob_pat='monitor_c0__*.jsonl', out_csv='c0_summary.csv')   # ...and c1u, c1, c2, c3, c3n
S = paper_numbers(OUTPUT_DIR)   # prints every number quoted above
make_all(OUTPUT_DIR)            # writes the four figures
```

`ground_truth_gold.jsonl` and its manifest pin the reference standard. A pre-Kimi snapshot manifest hashes the notebook, the figures and the Gold set so that the held-out monitor run is verifiably confirmatory rather than exploratory.

## Contact

Will Yeadon, Department of Physics, Durham University.