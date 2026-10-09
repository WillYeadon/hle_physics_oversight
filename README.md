# The Answer Is Not the Argument

Code and derived analysis outputs for a study of how access to a reference answer changes chain-of-thought error monitoring on physics problems.

The paper is on arXiv as [arXiv:2609.00264](https://arxiv.org/abs/2609.00264). There are two accompanying LessWrong posts. [The Answer Is Not the Argument](https://www.lesswrong.com/posts/sqFgvBgCkh6yG3p4f/the-answer-is-not-the-argument) covers the main study, and [Telling a CoT monitor that a wrong answer is correct makes it un-see errors it already found](https://www.lesswrong.com/posts/vhNpprNHZYWj3kpME/telling-a-cot-monitor-that-a-wrong-answer-is-correct-makes) covers the certificate-swap follow-up.

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

A follow-up intervention keeps each trace fixed and changes only the answer presented as certified. In **CMATCH** a wrong-answer trace is certified with its own wrong answer (82 traces, as one wrong-answer trace had no recoverable final answer). In **CCONFLICT** a clean trace is certified with a wrong answer that another generator gave to the same question (50 traces). Seven of the monitors were run on this arm. Kimi K3 is left out because its API fixes the sampling temperature, which makes a single-draw paired comparison less clean.

## Main result

Certification raises mean balanced accuracy from 0.637 to 0.796. The gain is concentrated where the conclusion reveals the flaw: wrong-answer recall rises from 0.653 to 0.951, while critical-trace recall falls from 0.521 to 0.438. The difference-in-differences is positive for all eight monitors (`p = 0.0078`, exact two-sided sign test).

Exact first-error localization rises more modestly, from 0.261 under BLIND to 0.379 under CERT. After a blind commitment, revealing the certified answer adds flags to 93.8% of previously passed wrong-answer traces but only 18.0% of previously passed critical traces. These results suggest that trusted-answer access chiefly improves conclusion-consistency checking rather than independent verification of the supporting reasoning.

The certificate swap tests this directly. On wrong-answer traces, certifying the trace's own wrong answer lowers the flag rate by 0.659 relative to the true certified answer (95% CI 0.602 to 0.711) and by 0.389 relative to BLIND. Of the 177 monitor-trace pairs where BLIND had already located the exact error, 55.4% passed under CMATCH, against 1.1% under truthful CERT. On clean traces, certifying a wrong answer raises the flag rate by 0.580 (95% CI 0.451 to 0.699), and 82.9% of the flags that appear only under the false certificate point to interior steps the reference standard marks as sound. All seven monitors move in the same direction on every comparison.

## Public analysis

`hle_physics_oversight_analysis.ipynb` is the repository-facing analysis notebook. It contains the code used to regenerate condition summaries, the certificate-swap analysis, question-clustered bootstrap intervals, figures, robustness analyses and the LaTeX macros used by the manuscript. It makes no model or API calls.

`export_public_data.py` creates the text-free input files from the author's private analysis directory using an explicit field whitelist. It refuses to write a release if step-count metadata is missing, if any exported value looks like free text or a credential, or if the frozen Gold labels would change. It never copies question, answer, rationale, trace, certificate-answer, prompt, monitor-reason or raw-output fields.

The public notebook is deliberately narrower than the private data-construction pipeline. It excludes the HLE source material, generated trace text, the answers used as certificates, the correction registry, adjudication dossiers, human annotation notes, API credentials and historical batch machinery.

The analysis expects text-free derived files under `data/`:

```text
data/
  ground_truth_gold.jsonl
  certificate_swap_targets.jsonl
  public_manifest.json
  monitor_c0__*.jsonl
  monitor_c1u__*.jsonl
  monitor_c1__*.jsonl
  monitor_c3__*.jsonl
  monitor_c3n__*.jsonl
  monitor_c2__*.jsonl
  monitor_cmatch__*.jsonl
  monitor_cconflict__*.jsonl
```

These records contain identifiers, labels, step numbers, confidence values and other derived fields required by the analysis. The Gold records also contain the number of steps in each trace so that localization chance rates, the trace-length robustness check and the CCONFLICT conclusion-versus-interior audit can be reproduced without releasing trace text. The certificate-swap target file records which traces entered each arm and which sibling response supplied each false certificate, by identifier only.

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

The final cell writes the four figures to `figures/` and the frozen paper outputs beneath the selected data directory, including `paper_stats.json`, `numbers.tex`, summary CSVs, the certificate-swap audits and input hashes.

## Data and code availability

Code, derived labels and analysis outputs are available in this repository. The repository does not redistribute HLE question text, images, reference answers or rationales. It also does not include model-generated trace text, the final answers used as false certificates, or monitor outputs that reproduce that text.

HLE is available separately from its maintainers at
<https://huggingface.co/datasets/cais/hle>.

## Citation

If you use this code or data, please cite the preprint.

```bibtex
@misc{yeadon2026answer,
  title         = {The Answer Is Not the Argument},
  author        = {Yeadon, Will and Ju{\'a}rez, Sergio and Mackay, Paul and Dowling, T. J. and Agra, Elise and Inyang, Oto-obong and Mizouri, Arin and Testrow, Craig P.},
  year          = {2026},
  eprint        = {2609.00264},
  archivePrefix = {arXiv},
  primaryClass  = {cs.AI},
  url           = {https://arxiv.org/abs/2609.00264}
}
```

## Contact

Will Yeadon, Department of Physics, Durham University.
