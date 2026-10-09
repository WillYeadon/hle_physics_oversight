"""Export the text-free public records from the private analysis directory.

Every output field is copied from an explicit whitelist. Question, reference
answer, rationale, trace, certificate-answer, prompt, monitor-reason and
raw-output fields are never read into the output. As a second line of defence
each exported string must be a short identifier-like value, and the whole
release is scanned for credential patterns before anything is written.

Usage
-----
    python export_public_data.py \
        --input-dir /path/to/private/hle_physics_oversight \
        --output-dir data \
        --trace-source /path/to/private/traces_main_filtered.jsonl

The trace source is read only to count numbered steps per trace (`n_steps`).
No trace text is written. If the output directory already holds a Gold file,
the new export must match it field for field, because Gold is frozen.
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

FORMAT = 'hle-physics-oversight-text-free-v1'

GOLD_FILE = 'ground_truth_gold.jsonl'
SWAP_TARGETS_FILE = 'certificate_swap_targets.jsonl'

GOLD_FIELDS = (
    'question_id', 'response_label', 'gt_status', 'strict_error',
    'final_is_correct', 'final_error_step', 'final_error_step_min',
    'final_error_step_max', 'generator', 'gold_error_source',
    'human_is_correct', 'human_error_step', 'debate_is_correct',
    'debate_error_step', 'n_steps',
)

MONITOR_FIELDS = (
    'question_id', 'response_label', 'monitor_model', 'api_model', 'condition',
    'parse_ok', 'has_error', 'first_error_step', 'error_confidence',
    'prior_has_error', 'prior_first_error_step', 'self_review',
)

SWAP_MONITOR_FIELDS = (
    'question_id', 'response_label', 'monitor_model', 'api_model', 'condition',
    'parse_ok', 'has_error', 'first_error_step', 'error_confidence',
    'self_review', 'cell', 'certificate_relation',
)

SWAP_TARGET_FIELDS = (
    'condition', 'question_id', 'response_label', 'generator', 'cell',
    'certificate_relation', 'certificate_source_qid',
    'certificate_source_label', 'certificate_answer_source',
)

# Fields that must never appear in a release, recorded in the manifest.
EXCLUDED_CONTENT = sorted({
    'analysis', 'answer', 'answer_evidence', 'assistant_message',
    'certificate_answer', 'content', 'correct_answer', 'critique',
    'error_claim', 'exclusion_reason', 'final_rationale', 'flagged_step_text',
    'image', 'model_response', 'monitor_rationale', 'notes', 'per_step',
    'prompt', 'question', 'rationale', 'raw', 'raw_output', 'reason',
    'reference_answer', 'reference_rationale', 'true_correct_answer',
})

NATURAL_MONITORS = (
    'claude-fable-5', 'deepseek_deepseek-chat-v4flash',
    'google_gemini-3.1-pro-preview', 'meta-llama_llama-3.3-70b-instruct',
    'moonshotai_kimi-k3', 'qwen_qwen-2.5-72b-instruct', 'qwen_qwen3-32b',
    'x-ai_grok-4.3',
)
SWAP_MONITORS = tuple(m for m in NATURAL_MONITORS if m != 'moonshotai_kimi-k3')
NATURAL_CONDITIONS = ('c0', 'c1u', 'c1', 'c2', 'c3', 'c3n')
SWAP_CONDITIONS = ('cmatch', 'cconflict')

# Identifier-like values only. A certificate answer, a formula or a sentence
# fails this, so a mis-mapped field cannot slip through.
SAFE_STRING = re.compile(r'^[A-Za-z0-9_.:/\- ]{0,64}$')
SECRET_PATTERNS = re.compile(
    r'(sk-[A-Za-z0-9_\-]{8,}|sk-ant-|AIza[0-9A-Za-z_\-]{10,}|xai-[A-Za-z0-9]{8,}'
    r'|gh[pousr]_[A-Za-z0-9]{10,}|hf_[A-Za-z0-9]{10,}|Bearer\s|api[_-]?key)',
    re.IGNORECASE)


def read_jsonl(path):
    rows = []
    with open(path, encoding='utf-8') as f:
        for n, line in enumerate(f, 1):
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise SystemExit(f'{path}:{n}: malformed JSON ({exc})')
    return rows


def parse_steps(text):
    """Step segmentation used by the private pipeline (sequential '(k)' markers)."""
    markers = [(m.start(), int(m.group(1))) for m in re.finditer(r'\((\d+)\)', text)]
    expected, kept = 1, []
    for pos, num in markers:
        if num == expected:
            kept.append((pos, num))
            expected += 1
    if len(kept) >= 2:
        return len(kept)
    return 1


def check_value(path, field, value):
    if value is None or isinstance(value, (bool, int, float)):
        return
    if isinstance(value, str):
        if not SAFE_STRING.match(value):
            raise SystemExit(f'{path}: field {field!r} has a non-identifier value '
                             f'({len(value)} chars). Refusing to export.')
        return
    raise SystemExit(f'{path}: field {field!r} has type {type(value).__name__}. '
                     f'Only scalar values are exported.')


def project(row, fields, path, fill_missing):
    out = {}
    for k in fields:
        if k in row:
            out[k] = row[k]
        elif fill_missing:
            out[k] = None
    for k, v in out.items():
        check_value(path, k, v)
    return out


def dumps(rows):
    return ''.join(json.dumps(r, separators=(',', ':'), ensure_ascii=False) + '\n'
                   for r in rows)


def export_gold(input_dir, trace_source):
    traces = {(t['question_id'], t['response_label']): t
              for t in read_jsonl(trace_source)}
    rows = []
    for r in read_jsonl(input_dir / GOLD_FILE):
        key = (r['question_id'], r['response_label'])
        t = traces.get(key)
        if t is None or not t.get('model_response'):
            raise SystemExit(f'No trace text to count steps for {key}. '
                             f'Check --trace-source.')
        rows.append(project({**r, 'n_steps': parse_steps(t['model_response'])},
                            GOLD_FIELDS, GOLD_FILE, fill_missing=True))
    return rows


def compare_gold(old_path, new_rows):
    old = {(r['question_id'], r['response_label']): r for r in read_jsonl(old_path)}
    new = {(r['question_id'], r['response_label']): r for r in new_rows}
    diffs = []
    for key in sorted(set(old) | set(new)):
        a, b = old.get(key), new.get(key)
        if a != b:
            fields = sorted(k for k in set(a or {}) | set(b or {})
                            if (a or {}).get(k) != (b or {}).get(k))
            diffs.append((key, fields))
    return diffs


def build_release(input_dir, trace_source):
    files = {GOLD_FILE: export_gold(input_dir, trace_source)}

    for cond in NATURAL_CONDITIONS:
        for mon in NATURAL_MONITORS:
            name = f'monitor_{cond}__{mon}.jsonl'
            src = input_dir / name
            if not src.exists():
                raise SystemExit(f'Missing {src}')
            files[name] = [project(r, MONITOR_FIELDS, name, fill_missing=False)
                           for r in read_jsonl(src)]

    targets = input_dir / SWAP_TARGETS_FILE
    if targets.exists():
        files[SWAP_TARGETS_FILE] = [
            project(r, SWAP_TARGET_FIELDS, SWAP_TARGETS_FILE, fill_missing=True)
            for r in read_jsonl(targets)]
        for cond in SWAP_CONDITIONS:
            for mon in SWAP_MONITORS:
                name = f'monitor_{cond}__{mon}.jsonl'
                src = input_dir / name
                if not src.exists():
                    raise SystemExit(f'Missing {src}')
                files[name] = [project(r, SWAP_MONITOR_FIELDS, name, fill_missing=False)
                               for r in read_jsonl(src)]
    else:
        print(f'note: {targets} not found, so the certificate-swap files are not exported')

    for name, rows in files.items():
        if not rows:
            raise SystemExit(f'{name} would be empty')
        leaked = {k for r in rows for k in r} & set(EXCLUDED_CONTENT)
        if leaked:
            raise SystemExit(f'{name}: excluded fields present {sorted(leaked)}')
    return files


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--input-dir', required=True, type=Path)
    ap.add_argument('--output-dir', required=True, type=Path)
    ap.add_argument('--trace-source', required=True, type=Path)
    ap.add_argument('--allow-gold-change', action='store_true',
                    help='permit the exported Gold to differ from the one already in --output-dir')
    ap.add_argument('--dry-run', action='store_true', help='check everything, write nothing')
    args = ap.parse_args()

    input_dir = args.input_dir.resolve()
    output_dir = args.output_dir.resolve()
    if output_dir == input_dir:
        raise SystemExit('--output-dir must not be the private input directory')

    files = build_release(input_dir, args.trace_source)
    texts = {name: dumps(rows) for name, rows in files.items()}

    for name, text in texts.items():
        hit = SECRET_PATTERNS.search(text)
        if hit:
            raise SystemExit(f'{name}: credential-like pattern {hit.group(0)[:12]!r}... '
                             f'Refusing to export.')

    old_gold = output_dir / GOLD_FILE
    if old_gold.exists():
        diffs = compare_gold(old_gold, files[GOLD_FILE])
        if diffs:
            print(f'Gold differs from the existing release on {len(diffs)} trace(s):')
            for key, fields in diffs[:10]:
                print(f'  {key}: {fields}')
            if not args.allow_gold_change:
                raise SystemExit('Gold is frozen. Re-run with --allow-gold-change only '
                                 'if a new Gold version is intended.')

    manifest = {'format': FORMAT, 'files': {}, 'excluded_content': EXCLUDED_CONTENT}
    for name, text in texts.items():
        data = text.encode('utf-8')
        manifest['files'][name] = {'rows': len(files[name]),
                                   'sha256': hashlib.sha256(data).hexdigest(),
                                   'bytes': len(data)}

    for name in sorted(texts):
        print(f'  {name:58s} {len(files[name]):5d} rows')
    if args.dry_run:
        print('dry run: nothing written')
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    for name, text in texts.items():
        tmp = output_dir / (name + '.tmp')
        tmp.write_text(text, encoding='utf-8', newline='\n')
        tmp.replace(output_dir / name)
    (output_dir / 'public_manifest.json').write_text(
        json.dumps(manifest, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(f'wrote {len(texts)} files and public_manifest.json to {output_dir}')


if __name__ == '__main__':
    sys.exit(main())
