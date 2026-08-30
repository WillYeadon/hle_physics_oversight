# The Answer Is Not the Argument

Code and derived analysis outputs for a study of how access to a reference answer changes chain-of-thought error monitoring on physics problems.

## Study

Three frontier models produced 237 step-numbered solutions to 79 physics questions from Humanity's Last Exam (HLE). No errors were inserted. A reference standard independently labels whether the final answer is correct and whether the reasoning contains an error, together with its first false step.

Eight LLM monitors evaluated the same traces under six conditions:

- **BLIND** — complete trace without a reference answer;
- **HINT** — an answer supplied as unverified;
- **CERT** — the same answer supplied as certified;
- **REVISE** — certified answer revealed after a blind commitment;
- **RCTRL** — answer-free reconsideration control; and
- **STEP** — online monitoring as the trace unfolds.

The reference standard contains 130 clean traces, 83 wrong-answer traces and 24 **critical traces** whose final answer is correct despite flawed reasoning.

## Main result

Certification raises mean balanced accuracy from 0.637 to 0.796. The gain is concentrated where the conclusion reveals the flaw: wrong-answer recall rises from 0.653 to 0.951, while critical-trace recall falls from 0.521 to 0.438. The difference-in-differences is positive for all eight monitors (`p = 0.0078`, exact two-sided sign test).

Exact first-error localization rises more modestly, from 0.261 under BLIND to 0.379 under CERT. After a blind commitment, revealing the certified answer adds flags to 93.8% of previously passed wrong-answer traces but only 18.0% of previously passed critical traces. These results suggest that trusted-answer access chiefly improves conclusion-consistency checking rather than independent verification of the supporting reasoning.

## Public analysis

`hle_physics_oversight_analysis.ipynb` is the repository-facing analysis notebook. It contains the code used to regenerate condition summaries, question-clustered bootstrap intervals, figures, robustness analyses and the LaTeX macros used by the manuscript.

`export_public_data.py` creates the text-free input files from the author's private analysis directory using an explicit field whitelist. It refuses to write a release if step-count metadata is missing and never copies question, answer, rationale, trace, prompt or raw-output fields.

The public notebook is deliberately narrower than the private data-construction pipeline. It excludes the HLE source material, generated trace text, correction registry, adjudication dossiers, API credentials and historical batch machinery.

The analysis expects text-free derived files under `data/`:

```text
data/
  ground_truth_gold.jsonl
  monitor_c0__*.jsonl
  monitor_c1u__*.jsonl
  monitor_c1__*.jsonl
  monitor_c3__*.jsonl
  monitor_c3n__*.jsonl
  monitor_c2__*.jsonl
```

These records contain identifiers, labels, step numbers, confidence values and other derived fields required by the analysis. The Gold records also contain the number of steps in each trace so that localization chance rates and the trace-length robustness check can be reproduced without releasing trace text.

To prepare the public records from the private working directory:

```bash
python export_public_data.py \
  --input-dir /path/to/private/hle_physics_oversight \
  --output-dir data \
  --trace-source /path/to/private/traces_main_filtered.jsonl
```

Set a different input directory if required:

```bash
export HLE_OVERSIGHT_DATA_DIR=/path/to/derived/data
jupyter lab hle_physics_oversight_analysis.ipynb
```

The final cell writes figures and frozen paper outputs beneath the selected data directory, including `paper_stats.json`, `numbers.tex`, summary CSVs and input hashes.

## Data and code availability

Code, derived labels and analysis outputs are available in this repository. The repository does not redistribute HLE question text, images, reference answers or rationales. It also does not include model-generated trace text or monitor outputs that reproduce that text.

HLE is available separately from its maintainers at
<https://huggingface.co/datasets/cais/hle>.

## Citation

Citation information will be added when the preprint is posted.

## Contact

Will Yeadon, Department of Physics, Durham University.
