# Plan: Qwen3.5-9B for local ResShare RAG

Use Together AI for one supervised LoRA pass on `Qwen/Qwen3.5-9B`, then export to a quantized GGUF for a 24 GB Apple Silicon Mac. Budget: USD $5–10 total for training experiments. Preserve the existing upload, user isolation, and source display behavior. Decisions recorded 2026-11-11.

## Scope

- In: grounded document Q&A, insufficient-evidence responses, local pretrained embeddings, a separate rebuilt Qdrant collection, baseline/tuned comparison, and upload-to-answer demonstration.
- Out: advanced citation supervision, preference/RL training, vision training, managed inference hosting, repeated hyperparameter sweeps, and replacing IPFS/ResilientDB.
- Local generation and BGE embedding integration are implemented. Existing-document migration and deployment verification remain pending. Public datasets, the tokenizer, and the small BGE encoder were downloaded; one paid LoRA job has been submitted at a $4 estimate; no live servers were started.

## Action items

- [x] Inspect the existing pipeline and establish model, provider, budget, and export choices.
- [x] Add standalone preparation, provider utility, evaluation, and offline test scripts.
- [x] Prepare 6,000 training examples, 300 validation examples, and 50 frozen test examples; verify quotas, token limits, hashes, and disjoint document groups/contexts.
- [x] Review 60 training samples (20 per category), record four exclusions, review their replacements, and rebuild using pinned revisions.
- [x] Check Together's tokenization preview: 50 rows match local token IDs, assistant-only labels, no sampled truncation.
- [ ] Obtain an independent human quality review before adopting the model.
- [x] Implement the shared local prompt and OpenAI-compatible generation client; test errors, timeouts, missing evidence, and source alignment.
- [x] Replace Gemini embeddings with `BAAI/bge-small-en-v1.5` via FastEmbed; validate a separate 384-dimensional collection and test indexing, retrieval, persistence, deletion, and user isolation.
- [x] Establish fixed-context local baseline results on the exact checksum-verified 50-question test; separately verify real BGE/Qdrant retrieval with a fresh synthetic upload. Further model/prompt development uses validation data.
- [x] Upload and validate train/validation only; obtain a $4 quote and submit one LoRA epoch within the $10 experiment budget.
- [ ] Monitor `ft-e80205d9-8b8a` to completion and record final charge and metrics; do not submit another job while it is queued/running.
- [x] Download both adapter and merged weights from the verified Hugging Face publication, check all manifest/LFS hashes, convert to F16 GGUF and Q4_K_M, verify prompt/template parity, and run non-thinking local generation on the Mac.
- [x] Evaluate baseline and tuned GGUFs on the identical 50 frozen questions; all 100 generations completed without request, truncation, or reasoning errors. Agent review was casewise model-blind. Real retrieval was separately exercised with a new upload.
- [x] Record agent-rated correctness, grounding, abstention, latency, sampled process RSS, and errors. Fresh authenticated upload/index/retrieval/answer/source API checks passed. Fine-tuned model selected as the application default at the user's request: tuned 47/50 versus baseline 41/50, but tuned false abstentions increased to 3/37 (2/36 after excluding flagged references) versus zero.
- [ ] Complete independent human review, interactive browser verification, and a controlled peak unified-memory/performance check; existing system swap made the memory comparison inconclusive.

## Implementation map

| Existing file | Required change |
| --- | --- |
| `backend/services/answer_service.py` | Replace Gemini-specific HTTP format with configurable local chat completions; use the prompt contract in `prompts.py`; bounded context/output and explicit request timeout. |
| `backend/controller/chat_controller.py` | Instantiate local client; display sources from exactly the supplied context chunks. Retrieve up to five, select whole chunks within the input budget, and display only those supplied to generation. |
| `backend/rag/embeddings.py` | Local cached FastEmbed model; document/query-specific embedding methods; validate dimensions/counts and finite vectors. |
| `backend/rag/vector_store.py` | Configurable collection and embedding identity; never reuse Gemini vectors. Validate existing collection dimensions; preserve user filters and deletion behavior. |
| `backend/rag/types.py`, `backend/services/upload_service.py` | Remove hardcoded Gemini model names from configuration and failed-index metadata. |
| `.env.example`, dependency manifests, Compose | Document local endpoint/model, embedding model, and collection configuration. Preserve local `.env`. On Docker Desktop, use `host.docker.internal` for a host model server. |
| `backend/tests/` | Cover local HTTP contract/errors, embeddings, upload/index failures, persistence, deletion and authenticated-user isolation. |

The shared prompt now lives in `backend/rag/prompts.py`; `local_finetuning/prompts.py` imports it. Its text and version are unchanged from dataset preparation. Changing it later requires regenerating data and rerunning the baseline.

## Index migration and rollback

1. Use a new collection such as `resshare_bge_small_en_v15_v1`, with cosine distance and 384 dimensions. Do not delete `resshare_vectors`.
2. Enumerate authoritative uploaded files from each user's stored tree, preserving document IDs, paths, CIDs, and ownership. Re-fetch bytes from IPFS and use the existing extraction/chunking pipeline. Respect files intentionally skipped for AI.
3. Write per-document migration successes/failures and chunk counts. Only mark metadata ready after successful indexing. Persist embedding identity and migration collection/version; do not advertise stale Gemini metadata as locally indexed.
4. Verify every intended file, then switch retrieval to the new collection. Pause uploads/deletes during cutover or reconcile all changes before switching; do not leave a silently stale rollback index.
5. Keep prior metadata snapshots and collection available. Rollback generation to baseline GGUF independently. If rolling back embeddings, restore the corresponding metadata and replay mutations, not just the collection name.

## Evaluation contract

- Public test: 25 Neural Bridge answers, 12 answerable SQuAD questions, 13 insufficient-evidence SQuAD questions; no document/article overlaps with training or validation.
- Fixed-context evaluation isolates generation. It does not measure retrieval or prove the upload flow works.
- Separately select ResShare documents/questions outside the training data. Include supported answers, absent answers, unrelated queries, multiple documents, skipped/failed files, and cross-user access checks.
- Use identical GGUF quantization, prompt, non-thinking setting, context limit, retrieval index, top-k, and output limit for baseline/tuned comparisons.
- Blind-review answer correctness, evidence support, appropriate abstention, and unsupported claims. Report raw counts and denominators, answerable and unanswerable subsets separately, and infrastructure errors separately.
- Record end-to-end latency and peak RAM on the actual Mac; do not infer them from file size. Fifty questions are a pilot, not statistical proof of superiority.
- Adoption target: no increase in unsupported answers or false abstentions, at least comparable correctness, and a responsive demo without swapping. If results are tied or worse, ship the baseline and report the fine-tune outcome honestly.

## Remaining operational checks

Execution order updated at the user's request: Mac inference setup is deferred. Cloud training preparation and quoting can proceed first; retain the original model and frozen evaluation files so baseline/tuned comparisons can run later on the Mac. Local runtime/template parity and performance remain unverified until that setup is available.

Local preparation and backend integration completed 2026-11-11. The reviewed dataset is `data/reviewed-v1/`: training has 3,697,135 locally counted tokens, validation 189,123, and test 33,601. The original `data/` files are retained. Two invalid source rows and four reviewed training targets were excluded. Validation/test files are byte-for-byte unchanged. These counts are not a provider price quote.

Verification: 31 backend tests and eight preparation tests pass. A real FastEmbed CPU run with in-memory Qdrant passed indexing, query encoding, same-document-ID ownership isolation, and owner-scoped deletion. Generation HTTP behavior uses mocked responses; actual Qwen answers, server template parity, Mac performance, real Qdrant server deployment, and migration of existing uploads are unverified. Ignored `artifacts/` contains `sample-review.json`, `reviewed-data-audit.json`, `local-rag-smoke.json`, and resolved tool versions.

- Together account/model access and actual quote; export-to-GGUF compatibility must be exercised, not assumed from documentation alone.
- Mac chip, free disk, and installed llama.cpp version; start at 8K context and 512 output tokens.
- Dataset quality/license review and non-thinking chat-template parity in Together's tokenization preview.

## Submitted training run

Submitted 2026-11-12 02:51 UTC (2026-11-11 Toronto). Job: `ft-e80205d9-8b8a`; latest checked state: `completed`. Output: `devangborkar3_f830/Qwen3.5-9B-resshare-grounded-v1-715072d0`.

Reviewed train/validation only were uploaded; both server validation reports are valid with 6,000/300 lines. Provider preview matched the pinned local tokenizer on 50 rows and showed only assistant responses/template termination markers in the loss. Provider estimated 4,595,121 train tokens and 235,604 evaluation tokens; these estimates differ from local counts, while sampled token IDs match exactly. Quoted total: USD $4; final charge is pending. Submitted configuration: SFT LoRA rank 16/alpha 32, one epoch/evaluation/checkpoint, 4,096 sequence length, learning rate 1e-5, batch 8, seed 42, input loss disabled, vision training disabled. Full settings and provider evidence are in ignored `artifacts/together/`.

Credentials are read from ignored `local_finetuning/.env`; the file was not modified. The utility accepts `--env-file local_finetuning/.env` before its subcommand. It still has no create command. If submission status is uncertain, inspect this job/account before any retry.

Completion verified: `ft-e80205d9-8b8a` finished at 2026-11-12 03:06:41 UTC. All 114 steps, one epoch, and one validation evaluation completed; reported validation loss was 0.2018. Output compression/upload completed. The status response reports raw `total_price=4000000000`; billing units have not yet been independently verified (original quote: USD $4). Artifact download, conversion, and baseline/tuned evaluation remain pending.
