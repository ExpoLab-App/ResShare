# ResShare local fine-tuning: session record and handoff

Work performed November 11, 2026 (Toronto); the cloud run completed November 12, 2026 UTC. This document records the work and its evidence, including what remains unverified. See [PLAN.md](PLAN.md) for the checklist and [README.md](README.md) for the full runbook.

## Outcome

One supervised LoRA fine-tune of `Qwen/Qwen3.5-9B` completed successfully on Together AI. Job **`ft-e80205d9-8b8a`** finished all 114 steps, one epoch, and one validation evaluation. Reported validation loss: **0.2018**. The provider compressed and uploaded the outputs. This proves the training workflow completed; it does not establish an improvement over the original model.

The backend now has local generation and embedding integration. Existing uploaded documents have not been migrated, and no live local generation server or Mac evaluation was run. Baseline-versus-tuned evaluation and deployment are still pending.

## Decisions and scope

- Goal: document-grounded answers, concise responses, and abstention when supplied evidence is insufficient.
- Starting checkpoint: `Qwen/Qwen3.5-9B`, the already post-trained checkpoint. Our additional adaptation is supervised fine-tuning with LoRA, not pretraining or reinforcement learning.
- Training location: Together AI cloud GPUs. Experiment budget: USD $5–10 total.
- Inference target confirmed by the user: **MacBook Pro, Apple M5, 24 GB unified RAM**. The screenshot showed no `llama-server` on PATH.
- Planned deployment: text generation through llama.cpp, Q4_K_M GGUF, initially 8K context and 512 output tokens, thinking disabled. The baseline Q4_K_M artifact was listed at about 5.68 GB; this is weight size, not measured total memory consumption.
- The user deferred Mac runtime setup and requested cloud training first. Preserve the original model and frozen test set for comparison later.
- Local embeddings: `BAAI/bge-small-en-v1.5`, FastEmbed, 384 dimensions, cosine similarity.
- New collection: `resshare_bge_small_en_v15_v1`. Existing Gemini collection `resshare_vectors` must not be reused for local vectors.
- IPFS and ResilientDB remain the storage architecture. No managed inference endpoint was created.

## Initial state and environment

`local_finetuning/` already contained a plan, preparation scripts, provider utilities, evaluation script, and offline tests. It was untracked; the repository also had a pre-existing `.gitignore` modification. Those existing changes were preserved during implementation.

Python commands used an activated environment. The backend uses the project `.venv` and Python 3.10. A separate Python 3.12 environment was created at `/tmp/resshare-finetuning-venv` for current datasets, Transformers, and Together tooling. It is machine-local and temporary: recreate it on another machine using the runbook. Resolved training-tool versions were saved in ignored `artifacts/tool-versions.txt`; backend dependencies are recorded in `pyproject.toml`, `requirements.txt`, and `uv.lock`.

Local `.env` files were not edited. The user supplied the Together key in **`local_finetuning/.env`** (initially called `e.nv` in conversation, then corrected). Git ignores that file. Its contents were never printed or copied into this document. The provider utility supports `--env-file` to read it explicitly.

## Dataset preparation

Only official training splits of these public sources were used:

- `neural-bridge/rag-dataset-12000`: supplied context, question, and prose answer.
- `rajpurkar/squad_v2`: supplied context and question; empty answer lists become the shared insufficient-evidence response.

| Split | Neural Bridge | SQuAD answerable | SQuAD unanswerable | Total |
| --- | ---: | ---: | ---: | ---: |
| Train | 3,000 | 1,500 | 1,500 | 6,000 |
| Validation | 150 | 75 | 75 | 300 |
| Test | 25 | 12 | 13 | 50 |

Pinned revisions:

| Resource | Revision |
| --- | --- |
| Qwen tokenizer/model reference | `c202236235762e1c871ad0ccb60c8ee5ba337b9a` |
| Neural Bridge dataset | `586c0d0ddeb022fccd909c7b415cc2ca8660baa4` |
| SQuAD v2 dataset | `3ffb306f725f7d2ce8394bc1873b24868140c412` |

Seed: 42. Prompt version: `resshare-grounded-v1`. SQuAD article titles and normalized Neural Bridge contexts determine document groups. Selection excludes exact normalized context overlap between splits, removes duplicate context/question pairs, and fails if quotas cannot be met. Near-duplicate semantic overlap has not been exhaustively audited.

Every example uses the neutral filename `document.txt`. Examples exceeding 4,096 locally tokenized tokens are rejected rather than truncated. System/user message weights are 0; assistant weights are 1. The test set has a records file only, not an upload-format training file.

Problems found by real execution and fixed:

1. Jinja2 was missing from the tools requirements, preventing chat-template rendering.
2. Some public source fields were null; normalization now rejects invalid fields. Two source rows were rejected.
3. Installed Transformers returned a dictionary by default; `len(...)` would count fields instead of tokens. Preparation now explicitly requests `return_dict=False`.

The original dataset is retained in ignored `data/`. The accepted reviewed version is **`data/reviewed-v1/`**. Use the reviewed version for further work.

## Qualitative sample review and rebuild

Codex reviewed 60 training examples: for each of the three categories, the three longest plus 17 examples selected with seed 42. This was an agent review against supplied evidence, not an independent human review or external fact check.

Four examples were rejected; reasons are tracked in [review_exclusions.json](review_exclusions.json):

| ID | Reason |
| --- | --- |
| `neural:7097` | Incoherent keyword-stuffed source does not establish the question's product premise. |
| `squad:5726d25e5951b619008f7f12` | Question asks for a country, but the target answers “military machinery.” |
| `squad:5733797b4776f41900660b6e` | Question reverses the passage's cause-and-effect relationship. |
| `squad:5a07dcd73fc8740018207024` | Abstention label conflicts with the passage's description of recent imaging developments. |

`prepare_data.py` gained `--exclude-ids` and `--revisions-from` so the reviewed version could be rebuilt reproducibly. The four replacements were also reviewed and retained. Validation and test files are **byte-for-byte unchanged**. No final-test answers were qualitatively inspected during this review.

| Locally counted tokens | Original | Reviewed |
| --- | ---: | ---: |
| Train | 3,697,232 | 3,697,135 |
| Validation | 189,123 | 189,123 |
| Test | 33,601 | 33,601 |

Reviewed token ranges: train 140–1,916; validation 189–1,641; test 174–1,623. Structural auditing checks quotas, unique IDs, disjoint groups/contexts, token totals and limits, SHA256 hashes, excluded IDs, shared prompt/target parity, loss weights, and frozen evaluation files.

Important hashes:

- Reviewed `train.jsonl`: `b3f7b1052c7ca99abc1595e35c9d18663c5785f42128dabc29eea9bbb15335ab`
- `valid.jsonl`: `7ac6514c65dbdbdaf0dc9fb68f1287552a4dee69521445b8963d7b60041cb2c5`
- `test.records.jsonl`: `37cca68d5b56bc59275d6cd1e5a7675d72b4f28a3f89f447db30a4f60d226d53`

The sample review found noisy scraped HTML/comments and some verbose prose targets. SQuAD supplies many short answer spans and false-premise negatives. These are transfer risks to evaluate; neither sample review nor structural checks certify all 6,000 examples.

## Backend changes

| File | Change |
| --- | --- |
| `backend/rag/prompts.py` | Shared grounded-answer prompt and abstention text. Prompt text/version preserved from preparation. |
| `local_finetuning/prompts.py` | Compatibility imports of the backend prompt. |
| `backend/services/answer_service.py` | Replaced Gemini generation with configurable local chat completions, timeout, temperature 0, 512 output tokens, and thinking disabled. Rejects malformed, empty, reasoning-tagged, or incomplete output. |
| `backend/controller/chat_controller.py` | Validates query type, uses authenticated owner, selects whole context chunks, and displays only sources actually supplied. Model/retrieval errors return 502/503. No evidence uses the shared abstention. |
| `backend/rag/embeddings.py` | Cached FastEmbed model, distinct passage/query APIs, shape/count/finite/nonzero-vector validation. |
| `backend/rag/config.py` | BGE identity/dimensions and separate collection defaults; rejects legacy Gemini collection selection. |
| `backend/rag/vector_store.py` | Uses local embeddings, validates dimensions/distance, records embedding identity/collection, preserves owner filters, and reports retrieval failures explicitly. |
| `backend/rag/chunking.py` | Stable chunk IDs now include owner, preventing users with identical document IDs from overwriting each other's points. |
| `backend/models/file.py` | Persists embedding collection and clears it on failed indexing. |
| `backend/controller/helpers.py` | Local statistics can filter by embedding model and collection, excluding stale Gemini metadata. |
| `backend/rag/types.py`, `backend/services/upload_service.py` | Local defaults and collection metadata; removed hardcoded Gemini names from failure metadata. |
| `.env.example`, Compose, dependency manifests | Local endpoint configuration, persistent embedding cache, host access from containers, and pinned FastEmbed dependency. |
| Backend tests | HTTP contracts/failures, source alignment, embedding validation, collection mismatch, metadata, ownership, persistence, deletion, and upload failure handling. |

Generation uses a conservative **6,000 UTF-8-byte prompt budget** and keeps complete chunks. This is not exact model tokenization. The target server context is 8K, leaving room for template and output. Configuration names: `LOCAL_LLM_BASE_URL`, `LOCAL_LLM_MODEL`, `LOCAL_LLM_TIMEOUT`, `RAG_COLLECTION`, `FASTEMBED_CACHE_PATH`.

## Verification performed

- **31 backend tests passed** using `python -m unittest discover -s backend/tests -p 'test_*.py'`.
- **Eight preparation tests passed** using `python -m unittest local_finetuning.test_workflow`.
- Compilation checks and `git diff --check` passed.
- `docker compose config --quiet` passed; this validated configuration without starting containers.
- A real CPU BGE download/encoding test produced the expected 384-dimensional vectors.
- Real BGE embeddings with in-memory Qdrant passed indexing, retrieval, same-document-ID ownership isolation, and owner-scoped deletion.
- HTTP generation tests used mocked responses. No real Qwen inference, live UI demonstration, real Qdrant server migration, or Mac timing/memory measurements occurred.

## Together uploads, preview, and quote

Only reviewed train and validation files were uploaded:

- Train: `file-010c721d-0097-4786-a6c9-8282b24a76fd`
- Validation: `file-928d9386-d9eb-4131-afca-5cfb4f59aea4`

Both completed server validation with the expected 6,000/300 lines, conversational format, message weights present, and no reasoning/image/tool fields. An initial quote returned `train_file_not_validated` while validation was pending. Rechecking the same uploads resolved it. **`processed=true` alone is insufficient**: check `processing_status=COMPLETED` and `validation_report.valid=true`.

The provider quote was **USD $4** with `allowed_to_proceed=true`. Estimated tokens: 4,595,121 train and 235,604 evaluation. These were estimates rather than exact local counts.

A 50-row provider preview matched every local token ID against the pinned tokenizer. No preview row was truncated; the largest sampled row had 1,018 tokens, below our 4,096 training limit. Only assistant responses and their template termination markers contributed to loss. Qwen's empty-thinking wrapper was present; the loss text began with the empty closing-think portion followed by the answer. No reasoning trace was supplied. Local completed-conversation rendering was identical with default settings and `enable_thinking=False`.

This verifies sampled provider preprocessing. It does not prove the future llama.cpp server will apply exactly the same template; check that after export.

## Submitted training configuration

The job was submitted once through the Together SDK after quote and preview verification. The general utility intentionally has no create command. Temporary launch scripts under `/tmp` used a submission marker and checked for an existing matching job to avoid duplicate submission. Those temporary scripts are not a durable interface; the submitted configuration and provider responses are the durable evidence.

| Setting | Submitted value |
| --- | --- |
| Model | `Qwen/Qwen3.5-9B` |
| Method | SFT, LoRA |
| Rank / alpha | 16 / 32 |
| Epochs | 1 |
| Validation evaluations | 1 |
| Checkpoints | 1 |
| Sequence length | 4096 |
| Learning rate | 0.00001 |
| Batch size | 8 |
| Packing | true |
| Seed | 42 |
| Train on inputs | false |
| Train vision | false |
| Suffix | `resshare-grounded-v1` |

The service response reported `all-linear` LoRA targets and cosine LR scheduling. The exact resolved configuration is in `artifacts/together/job.json`; our explicit request is in `job-config.json`. No dedicated inference endpoint or second training job was created.

## Training timeline and result

All times below are UTC on November 12, 2026 (the evening of November 11 in Toronto).

| Time | Event |
| --- | --- |
| 02:51:08 | Job created: `ft-e80205d9-8b8a` |
| 02:52:28 | Job started |
| 02:52:34 | Model download completed |
| 02:59:01 | Prepared tokenized dataset archive uploaded |
| 02:59:32 | Training started |
| 03:03:01 | Validation completed at step 114; loss 0.2018 |
| 03:03:12 | Epoch completed |
| 03:03:28 | Training completed |
| 03:05:09 | Output compression completed |
| 03:05:57 | Output upload completed |
| 03:06:41 | Job completed |

Creation-to-completion took about **15 minutes 33 seconds**. Training-start to training-complete was about **3 minutes 56 seconds**; preparation, compression, and upload account for the remaining time. Early status counters and the first metrics query were empty/zero while setup ran; later events confirmed training progress and completion.

The completed response reports `token_count=3697231` and `eval_token_count=189123`. Training count differs from the local reviewed count by 96; the cause was not investigated. Do not silently substitute the earlier price-estimator counts for these actual reported fields.

Billing evidence: quote **USD $4**; completed response raw `total_price=4000000000`, `train_price=3805346605`, `eval_price=194653395`. Currency scaling has not been independently verified, so confirm the final dollar charge in Together billing. Do not describe the raw integer as dollars.

Output identifiers from the completed status:

- Model registry name: `devangborkar3-f830/Qwen3.5-9B-resshare-grounded-v1-715072d0`
- Model object: `ml_CgxJ3crN15g8QmCieiHou`
- Model revision: `rv_CgxJ5AarUSgpjLGVMtVSb`
- Adapter registry name: `devangborkar3-f830/Qwen3.5-9B-resshare-grounded-v1-715072d0-adapter`
- Adapter object: `ml_CgxJ38kv6rsbnE4QkHHC4`
- Adapter revision: `rv_CgxJ3XAJG86riuB9xZFED`

The initial response used the output name `devangborkar3_f830/Qwen3.5-9B-resshare-grounded-v1-715072d0`; the completed registry name uses a hyphen in the organization slug. Use job ID for status/download utilities.

## Evidence inventory and portability

All paths in this table are relative to `local_finetuning/`. `data/`, `artifacts/`, and `results/` are intentionally Git-ignored. **Checking out a Git branch on the Mac will not transfer these datasets or artifacts.** Transfer the reviewed data and relevant evidence separately, excluding credentials, or regenerate with the pinned revisions. Never commit the API key.

| Path | Contents |
| --- | --- |
| `data/manifest.json` | Original source revisions, quotas, token counts, hashes |
| `data/reviewed-v1/` | Reviewed train/validation/test files and manifest |
| `review_exclusions.json` | Tracked rejected IDs and review reasons |
| `artifacts/review-samples.jsonl` | 60 selected training examples |
| `artifacts/sample-review.json` | Agent review decisions and four replacement IDs |
| `artifacts/reviewed-data-audit.json` | Structural and frozen-split audit |
| `artifacts/local-rag-smoke.json` | Real encoder/in-memory retrieval test evidence |
| `artifacts/tool-versions.txt` | Resolved training-tool dependencies |
| `artifacts/together/uploads.json` | Upload IDs tied to SHA256 hashes |
| `artifacts/together/*-status.json` | File validation responses |
| `artifacts/together/quote.json` | Provider quote |
| `artifacts/together/train-preview.json` | Full 50-row tokenization preview |
| `artifacts/together/preview-comparison.json` | Local/provider token matching and loss text |
| `artifacts/together/preview-audit.json` | Summary of preview checks |
| `artifacts/together/job-config.json` | Explicit submitted settings |
| `artifacts/together/job.json` | Initial accepted job response |
| `artifacts/together/submission-attempt.json` | Duplicate-submission protection marker |
| `artifacts/together/status-check.json` | Verified completed status and event history |
| `artifacts/together/latest-job-status.json` | Earlier status snapshot; may be stale despite its name |
| `artifacts/together/metrics-check.json` | Early metrics response; empty at that time |

## Resume commands

Run from the repository root. Recreate the tools environment first if its `/tmp` path no longer exists. Credentials should exist only on the machine making provider requests.

```bash
source /tmp/resshare-finetuning-venv/bin/activate
python -m local_finetuning.together_job --env-file local_finetuning/.env status ft-e80205d9-8b8a
```

The next artifact downloads (not yet performed) are:

```bash
source /tmp/resshare-finetuning-venv/bin/activate
python -m local_finetuning.together_job --env-file local_finetuning/.env download ft-e80205d9-8b8a \
  --checkpoint adapter --output local_finetuning/artifacts/adapter.tar.zst
python -m local_finetuning.together_job --env-file local_finetuning/.env download ft-e80205d9-8b8a \
  --checkpoint merged --output local_finetuning/artifacts/merged.tar.zst
```

The script refuses to overwrite existing output paths. Check disk space before downloading/extracting merged weights; the runbook budgets roughly 60–80 GB for archives, extracted weights, and conversions. This disk allowance is a planning estimate, not measured artifact size.

To recheck reviewed data and tests:

```bash
source .venv/bin/activate
python -m local_finetuning.audit_data --input local_finetuning/data/reviewed-v1 \
  --previous local_finetuning/data --output local_finetuning/artifacts/reviewed-data-audit.json
python -m unittest discover -s backend/tests -p 'test_*.py' -v
python -m unittest local_finetuning.test_workflow -v
```

## Remaining work, in order

1. Verify final billing units/charge and retrieve full training metrics if needed.
2. Download adapter and merged checkpoint; inspect the archive, exported tokenizer, configuration, and revision metadata.
3. Convert merged weights to GGUF with a Qwen3.5-capable llama.cpp version, then quantize to Q4_K_M. Record conversion version and file hashes. Conversion has not been validated yet and may need more memory than inference.
4. Install the inference runtime on the M5 Mac and obtain the original baseline GGUF. Verify thinking is disabled and the shared prompt works on validation examples.
5. Reindex existing intended ResShare files into the separate local collection. Preserve owner/document IDs, skipped-file intent, metadata snapshots, and migration reports. Verify full coverage; plan cutover with uploads/deletes paused or reconciled.
6. Freeze settings, then compare original and tuned models on the same 50 held-out questions. Review blind for correctness, grounding, appropriate abstention, and unsupported claims. Record errors separately.
7. Measure actual latency and peak memory on the Mac. Exercise authenticated upload → index → retrieve → answer → displayed sources, including cross-user isolation and missing-evidence cases.
8. Adopt the tuned model only if it meets the plan's quality criteria. Keep baseline weights and rollback evidence. Validation loss alone is insufficient to decide adoption.

No completion claim should be made for artifact conversion, Mac inference, old-document migration, or answer-quality improvement until these checks actually run.

## Combined Mac demo branch

The combined branch is `feat/presentation-demo-qwen-finetuning`. It merges
`origin/presentation-demo` at `1be0993` with the local Qwen/BGE implementation
and this handoff at `cb1c48e`.

The merge preserves the demo's amd64/arm64 container installers, GitHub IPFS
downloads, and corrected IPFS/cluster health checks. The generation client
retains explicit model, URL, and timeout constructor options. Qwen endpoint
defaults (port 8081, model alias `resshare-local`), shared training/inference
prompt, context budget, and HTTP error handling take precedence over the demo's
Ollama defaults and error-as-answer behavior. Embeddings use local BGE.

On the Mac, fetch origin and switch to this branch. Git does not transfer the
ignored `.env`, datasets, training artifacts, or model weights; transfer or
download those separately. Existing Gemini-indexed documents need reindexing.
Container changes were inspected and Compose configuration validated; a full
Apple Silicon image build and live Mac inference still require verification.


## Hugging Face export (2026-11-12)

Both final checkpoints were downloaded from Together job `ft-e80205d9-8b8a`:

| Archive | Bytes | SHA256 |
| --- | ---: | --- |
| Merged | 15,052,416,622 | `9bcdeeb77deea090cd3586e1ea5d96a2322d5cd2f9dc0c198d8691a18ec54b37` |
| Adapter | 164,079,919 | `56dec74438a23fde0a18c6a4618ba278350742d6881ef34d6d52a9ebcb01938d` |

Local exports are under ignored `artifacts/export/`. Safe archive extraction
rejected links and unsafe paths. All four merged safetensors shards were checked
against the weight index: 775 tensors, 19,306,216,416 tensor bytes, 727 BF16 and
48 F32 tensors. Header offsets and file sizes agree. AutoConfig and AutoTokenizer
load locally; non-thinking template rendering passes. Token IDs match the pinned
preparation tokenizer on 10 validation examples. This verifies file structure
and tokenizer behavior, not full model loading or generation quality.

Publication target: `devangb4/Qwen3.5-9B-ResShare`. Root files contain the merged
Hugging Face checkpoint, with the original LoRA export under `adapter/`. The
adapter configuration retains the provider base identifier
`togethercomputer/Qwen3.5-9B`; standalone adapter loading has not been verified.
The model card includes training settings, dataset attribution, upstream license,
shared prompt, and evaluation limitations. No credentials, datasets, or trainer
state are included. `file_manifest.json` records publication file sizes and
SHA256 hashes. Publication completed successfully. Remote file sizes and all LFS SHA256
hashes match the local manifest, and anonymous API access confirms the model
is public. Revision: `0580ebf5de43f19d3b024df9c7355cef090fef4d`.

Public repository: https://huggingface.co/devangb4/Qwen3.5-9B-ResShare

Download on the Mac without a Together key:

```bash
hf download devangb4/Qwen3.5-9B-ResShare \
  --revision 0580ebf5de43f19d3b024df9c7355cef090fef4d \
  --local-dir Qwen3.5-9B-ResShare
```

This is an unquantized Hugging Face checkpoint, not a GGUF or MLX package. Mac
conversion, quantization, and inference testing remain outstanding.
