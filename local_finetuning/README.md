# ResShare local fine-tuning runbook

For the full session history, training results, evidence locations, and remaining work, see [SESSION_HANDOFF.md](SESSION_HANDOFF.md).

Start with [PLAN.md](PLAN.md). This folder prepares **Qwen3.5-9B + Together LoRA + local Mac inference**. The backend now uses local generation and BGE embeddings; deployment cutover and reindexing of existing uploads remain operational steps. Commands below run from the repository root unless stated otherwise.

## Contents and current status

- `prompts.py`: compatibility import of the shared contract in `backend/rag/prompts.py`.
- `prepare_data.py`: downloads revision-pinned public data/tokenizer, rejects overlength examples without truncation, and creates reproducible splits.
- `together_job.py`: uploads files, checks ingestion, previews tokenization, estimates cost, checks jobs, and downloads artifacts. It deliberately has no job-creation command.
- `evaluate.py`: records fixed-context answers from an already running local endpoint; no hosted judge or inference fees.
- `audit_data.py`: verifies quotas, split isolation, hashes, prompt parity, and frozen validation/test files.
- `test_workflow.py`: offline split/normalization/prompt checks.

Local dataset preparation completed on 2026-11-11: 6,000 training, 300 validation, and 50 test records. Structural checks passed for quotas, token limits, split isolation, hashes, and assistant-only loss weights; eight preparation tests and 31 backend tests pass. See ignored `data/reviewed-v1/manifest.json` and `artifacts/reviewed-data-audit.json`. Codex reviewed 60 training samples and rejected four; independent human review remains pending. The reviewed training files are in `data/reviewed-v1/`; their validation/test files match the originals exactly. Use that version for the next steps.

One cloud training job has now been submitted: `ft-e80205d9-8b8a`, quoted at **$4**, latest checked state **completed**. Upload validation passed for train/validation; 50 provider-preview rows match local token IDs and assistant-only loss labels without sampled truncation. All 114 steps and validation completed; validation loss was 0.2018. Final billing-unit verification, artifact download, conversion, and Mac performance checks remain pending. Evidence and configuration are under ignored `artifacts/together/`. Do not submit a duplicate job.

To check this job using the saved credential file:

```bash
source /tmp/resshare-finetuning-venv/bin/activate
python -m local_finetuning.together_job --env-file local_finetuning/.env status ft-e80205d9-8b8a
```

The credential file is read without modification. Offline tests require no provider calls.

## 1. Set up an isolated tools environment

The backend targets Python 3.10. Keep this newer training toolchain separate from its lockfile. With `uv` installed:

```bash
source .venv/bin/activate
uv venv --python 3.12 /tmp/resshare-finetuning-venv
source /tmp/resshare-finetuning-venv/bin/activate
uv pip install -r local_finetuning/requirements.txt
mkdir -p local_finetuning/artifacts
uv pip freeze > local_finetuning/artifacts/tool-versions.txt
```

The version ranges allow current provider/tokenizer support; freeze the resolved versions with every run. On later terminals activate that tools environment before Python commands. Do not modify any local `.env` file. Set the Together key only when making provider calls:

```bash
read -rsp 'Together API key: ' TOGETHER_API_KEY
export TOGETHER_API_KEY
```

Create a Together account, purchase only the desired $5–10 credits, and keep automatic recharge disabled. Never paste credentials into tracked files or screenshots. Check account-specific prices before starting.

## 2. Prepare and inspect data

```bash
python -m local_finetuning.prepare_data
```

The script uses official training splits of:

- [Neural Bridge RAG 12000](https://huggingface.co/datasets/neural-bridge/rag-dataset-12000): Apache-2.0, context/question/answer.
- [SQuAD 2.0](https://huggingface.co/datasets/rajpurkar/squad_v2): CC-BY-SA-4.0, empty answer lists become insufficient-evidence targets. Preserve attribution and applicable dataset terms with derivative datasets.

Generated files under ignored `local_finetuning/data/`:

| File | Purpose |
| --- | --- |
| `train.jsonl` | 6,000 conversations: 3,000 Neural Bridge + 1,500 answerable SQuAD + 1,500 unanswerable SQuAD |
| `valid.jsonl` | 300 conversations for training validation |
| `test.records.jsonl` | 50 frozen public test cases; never upload for training |
| `*.records.jsonl` | Source IDs, groups, contexts, references and local token counts |
| `manifest.json` | Dataset/model revisions, prompt version, quotas, exclusions, tokens and file hashes |

SQuAD article titles and Neural Bridge normalized contexts determine splits. Exact normalized context overlap across sources is also excluded. Near-duplicate documents still need manual review. The filename is always `document.txt`, avoiding a dataset-name shortcut for abstention. The script rejects examples over 4,096 locally tokenized tokens; it never cuts off evidence and leaves an unsupported target behind. If any quota cannot be filled, it fails instead of silently changing the experiment. A rerun requires a new output directory.

The recorded review in `artifacts/sample-review.json` covers 20 training examples per category, including the three longest in each. Four rejected IDs and reasons are tracked in `review_exclusions.json`. The reviewed version preserves validation/test and uses the original revisions:

```bash
# Already generated here; a rerun needs another fresh --output path.
python -m local_finetuning.prepare_data --output local_finetuning/data/reviewed-v1 \
  --revisions-from local_finetuning/data/manifest.json \
  --exclude-ids local_finetuning/review_exclusions.json
python -m local_finetuning.audit_data --input local_finetuning/data/reviewed-v1 \
  --previous local_finetuning/data --output local_finetuning/artifacts/reviewed-data-audit.json
```

Obtain an independent human review before adopting the model. Neural Bridge answers are not guaranteed perfectly grounded; reject flawed samples and regenerate/version the dataset if needed. SQuAD short span answers differ from ResShare prose answers; use validation to check verbosity and over-abstention. These public examples contain supplied evidence, not ResShare retrieval distractors; that transfer gap must be tested separately.

## 3. Implement local RAG and establish the baseline

The local backend implementation is in place. Complete the index migration items in `PLAN.md` before evaluating end-to-end behavior. Use local BGE embeddings and a separate collection before comparing models, so retrieval stays fixed. Keep baseline and tuned generation configurations identical.

On the Mac, install llama.cpp and obtain a Q4_K_M baseline from [Unsloth's Qwen3.5-9B GGUF repository](https://huggingface.co/unsloth/Qwen3.5-9B-GGUF/tree/main). Record the repository revision and artifact hash; about 5.68 GB is weights alone.

```bash
brew install llama.cpp
hf download unsloth/Qwen3.5-9B-GGUF Qwen3.5-9B-Q4_K_M.gguf \
  --local-dir local_finetuning/artifacts/baseline
shasum -a 256 local_finetuning/artifacts/baseline/*.gguf
llama-server --version
```

The following command starts a server intentionally; run it on the Mac only when ready to test. Confirm flags with the installed version's `--help`:

```bash
llama-server -m local_finetuning/artifacts/baseline/Qwen3.5-9B-Q4_K_M.gguf \
  --host 127.0.0.1 --port 8081 --alias resshare-local \
  -c 8192 -ngl 99 --jinja --chat-template-kwargs '{"enable_thinking":false}'
```

Use `data/reviewed-v1/valid.records.jsonl` for development. Freeze prompts/settings before testing `test.records.jsonl`. Start the server in a separate terminal; the evaluator does not start one:

```bash
python -m local_finetuning.evaluate \
  --input local_finetuning/data/reviewed-v1/test.records.jsonl \
  --output local_finetuning/results/baseline.jsonl \
  --model resshare-local --artifact 'baseline-Q4_K_M:REPLACE_WITH_SHA256'
```

Check non-thinking behavior with a few validation samples. The request sends `enable_thinking=false` and the server must actually honor it. A plain text instruction alone is not a chat-template switch.

## 4. Upload only train and validation; get a quote

These commands send the public curated examples to Together. They do not launch training:

```bash
python -m local_finetuning.together_job upload local_finetuning/data/reviewed-v1/train.jsonl
python -m local_finetuning.together_job upload local_finetuning/data/reviewed-v1/valid.jsonl
python -m local_finetuning.together_job file-status TRAIN_FILE_ID
python -m local_finetuning.together_job file-status VALID_FILE_ID
```

Save returned IDs in the ignored artifacts directory. Wait for `processing_status=COMPLETED` and `validation_report.valid=true`; `processed=true` alone can still mean validation is pending. Fix validation errors before proceeding. Use Together's dataset/tokenization preview to verify system/user/assistant boundaries, assistant-only loss, and direct-answer/non-thinking template behavior. Do not launch if these differ from local inference.

```bash
python -m local_finetuning.together_job estimate \
  --training-file TRAIN_FILE_ID --validation-file VALID_FILE_ID \
  > local_finetuning/artifacts/quote.json
```

The estimate is for one LoRA SFT epoch, one validation evaluation, rank 16, alpha 32. Inspect the response rather than assuming its schema or price. Current public pricing checked 2026-11-11 lists $0.34/million processed tokens with a $4 minimum for this model's LoRA SFT; live quote wins. Count prior jobs against the same $10 total ceiling. Validation tokens add cost. A separate paid pilot can incur another minimum charge, so do not automatically launch both pilot and full runs on this budget.

## 5. Submitted job and launch settings

In Together's fine-tuning UI, use the uploaded files and the following settings. Compare the final displayed cost with `quote.json` and remaining prepaid balance before clicking Train. This is the step that spends money. The recorded run was already submitted through the SDK with these settings; do not submit another copy in the UI.

| Setting | Value |
| --- | --- |
| Base model | `Qwen/Qwen3.5-9B` (post-trained model, not Base) |
| Method | SFT, LoRA |
| Epochs | 1 |
| LoRA rank / alpha | 16 / 32 |
| Learning rate | 0.00001 as a conservative starting point |
| Maximum sequence length | 4096; reject unexpected provider truncation in preview |
| Training loss | Assistant only; system/user weights 0, assistant weight 1 |
| Validation evaluations | 1 |
| Saved checkpoints | 1 |
| Output suffix | `resshare-grounded-v1` |

Use provider defaults for other settings and save the entire job configuration. If the UI cannot express these settings, use the linked API reference rather than silently changing the recipe. Record the underlying base revision when exposed; verify it against the tokenizer revision in the manifest. Re-preview on any mismatch. Do not create a dedicated inference endpoint.

After submission, save the job ID. A timeout does not mean submission failed: inspect the dashboard before retrying, since another submission creates another paid job.

```bash
python -m local_finetuning.together_job status JOB_ID
```

Record status, loss curves, actual charge, and failure details. Distinguish provider failures from model quality. If failed or over budget, stop and diagnose; do not auto-retry. Use the dashboard to cancel an unwanted running job; completed training charges are not undone by cancellation.

## 6. Export and quantize

Once the job is completed:

```bash
python -m local_finetuning.together_job download JOB_ID --checkpoint adapter \
  --output local_finetuning/artifacts/adapter.tar.zst
python -m local_finetuning.together_job download JOB_ID --checkpoint merged \
  --output local_finetuning/artifacts/merged.tar.zst
brew install zstd
mkdir -p local_finetuning/artifacts/merged
 tar --zstd -xf local_finetuning/artifacts/merged.tar.zst -C local_finetuning/artifacts/merged
```

If the Mac's `tar` lacks `--zstd`, decompress with `zstd -d`, then `tar -xf`. Inspect the archive structure and locate the directory containing `config.json`, tokenizer files, and weights. Provider exports are Hugging Face checkpoints, not ready-to-use GGUFs.

Convert with a llama.cpp checkout supporting Qwen3.5. Use the same llama.cpp revision for both model runs; record `git rev-parse HEAD` in that checkout. The converter requires its own dependencies; install them in a separate activated environment, not the backend environment:

```bash
# Replace these paths with the actual checkout and extracted model directory.
python /path/to/llama.cpp/convert_hf_to_gguf.py /path/to/extracted-model \
  --outfile local_finetuning/artifacts/resshare-f16.gguf --outtype f16
llama-quantize local_finetuning/artifacts/resshare-f16.gguf \
  local_finetuning/artifacts/resshare-Q4_K_M.gguf Q4_K_M
shasum -a 256 local_finetuning/artifacts/resshare-Q4_K_M.gguf
```

Allow roughly 60–80 GB free disk for archives, extracted weights and conversions. Conversion/merging can require more RAM than quantized inference; downloading merged weights avoids doing the merge on the 24 GB Mac. If conversion exceeds memory, use a temporary CPU machine with enough RAM; account for that cost separately. Verify exported tokenizer/chat template and compare a few fixed-context outputs before accepting the artifact. Do not assume generic Transformers text-only loading examples work for this hybrid multimodal architecture.

## 7. Compare and demonstrate

Stop the baseline server with Ctrl-C. Start the tuned GGUF with the same alias, port and flags from step 3, then:

```bash
python -m local_finetuning.evaluate \
  --input local_finetuning/data/reviewed-v1/test.records.jsonl \
  --output local_finetuning/results/tuned.jsonl \
  --model resshare-local --artifact 'tuned-Q4_K_M:REPLACE_WITH_SHA256'
```

Each output contains case IDs, references, answerability, latency, model/artifact provenance and fields for human review. Errors produce nonzero exit status. `exact_abstention` is a diagnostic string match, not a quality score: semantically correct abstentions can use different words. Compare rows by ID, review blind, and summarize the rubric in `PLAN.md`. Report failed/truncated outputs separately. Inspect actual memory and latency on the Mac.

Finally use the real authenticated UI: upload a new TXT/PDF/DOCX, verify successful indexing, ask an answerable question, ask for a fact absent from that document, inspect source filenames, and verify another user's document cannot be retrieved. This is a separate integration check; the fixed-context script alone cannot certify it. Preserve the unmodified baseline as rollback.

## Offline checks

```bash
source .venv/bin/activate
python -m unittest local_finetuning.test_workflow -v
python -m unittest discover -s backend/tests -p 'test_*.py' -v
python -m compileall -q local_finetuning
```

## References

Verified 2026-11-11; recheck model support, SDK signatures and prices before execution:

- [Together model support](https://docs.together.ai/docs/fine-tuning/supported-models)
- [Together quickstart](https://docs.together.ai/docs/fine-tuning/quickstart)
- [Dataset format and masking](https://docs.together.ai/docs/fine-tuning/data-preparation)
- [Price estimation API](https://docs.together.ai/reference/post-fine-tunes-estimate-price)
- [Create-job API](https://docs.together.ai/reference/post-fine-tunes)
- [Export adapter/merged weights](https://docs.together.ai/docs/fine-tuning/deployment)
- [Together pricing](https://www.together.ai/pricing)
- [Qwen3.5-9B model and non-thinking settings](https://huggingface.co/Qwen/Qwen3.5-9B)
- [llama.cpp conversion/runtime](https://github.com/ggml-org/llama.cpp)
