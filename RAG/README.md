# HVNH RAG AI

Production-oriented FastAPI and RAG ingestion foundation for the independent AI service
used by HVNH Hub. Retrieval/chat endpoints, crawling, and LangGraph remain out of scope.

## Stack

- Python 3.11 and FastAPI
- PostgreSQL 16 with SQLAlchemy 2 async and Alembic
- Qdrant vector database with Gemini document embeddings
- Redis (provisioned for future cache, queue, or session use)
- Pytest and Docker Compose

## Project layout

```text
app/
  api/             API router and route modules
  core/            settings and logging
  db/              SQLAlchemy base, engine, and async sessions
  models/          Document, Conversation, Message
  schemas/         API schemas
  knowledge/       local loaders, ingestion orchestration, Qdrant indexer
  rag/             deterministic chunking and Gemini embeddings
  agent/           placeholder for a later phase
alembic/           database migrations
tests/             test foundation
```

## Run with Docker

Requirements: Docker Engine/Desktop with Compose.

```powershell
Copy-Item ..\backend\.env.example ..\backend\.env
docker compose --env-file ..\backend\.env up --build
```

The default Compose command keeps the cloud endpoints from `.env`; it does not
override them with Docker service names. To run PostgreSQL, Qdrant, and Redis locally
instead, use the explicit override:

```powershell
docker compose --env-file ..\backend\.env -f compose.yaml -f compose.local.yaml --profile local-infra up --build
```

The API waits for PostgreSQL, Qdrant, and Redis to become healthy, applies
`alembic upgrade head`, then starts Uvicorn.

- API health: http://localhost:8000/api/v1/health
- OpenAPI docs: http://localhost:8000/docs
- Qdrant dashboard: http://localhost:6333/dashboard
- PostgreSQL: localhost:5432
- Redis: localhost:6379

Stop with `docker compose down`. Add `-v` only when you deliberately want to delete
all persisted local volumes.

## Local development

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
Copy-Item ..\backend\.env.example ..\backend\.env
pytest
uvicorn app.main:app --reload
```

Outside Docker, keep service hosts as `localhost`. Compose overrides them with its
internal service names.

## Configuration

Configuration is loaded from environment variables and the shared `../backend/.env` using
`pydantic-settings`. See `../backend/.env.example` for application, PostgreSQL, Qdrant, Redis,
and LLM settings. Never commit `.env` or credentials. `DATABASE_URL`, when supplied,
overrides the individual PostgreSQL fields.

## Database migrations

```powershell
alembic upgrade head
alembic downgrade -1
alembic revision --autogenerate -m "describe change"
alembic check
```

Import new models from `app/models/__init__.py` so Alembic discovers them. Application
startup does not use `create_all`; migrations own schema changes.

The Neon V2 schema is baselined at revision `20260903_0001`. An existing database
created from `base_v2.sql` must be stamped once instead of upgraded:

```powershell
alembic stamp 20260903_0001
```

Do not run that command on an empty database; use `alembic upgrade head` there. To print
a read-only table/enum summary for the configured database, run:

```powershell
python -m scripts.check_schema
```

## Verification

```powershell
pytest
docker compose --env-file ..\backend\.env config
```

`GET /api/v1/health` is a liveness endpoint and deliberately does not depend on
external services. Docker evaluates PostgreSQL, Qdrant, and Redis health separately.

`GET /api/v1/ready` checks PostgreSQL, Qdrant, and Redis and returns HTTP 503 when any
dependency is unavailable. It never returns connection strings or raw exceptions.

To verify the services configured in `.env` from the command line:

```powershell
python -m scripts.check_dependencies
```

To make one safe structured-output Gemini connectivity check:

```powershell
python -m scripts.check_llm
```

To verify Gemini embeddings without printing the source text or vector:

```powershell
python -m scripts.check_embedding
python -m scripts.check_vector_store
```

Transient Gemini failures (timeouts, HTTP 429, and HTTP 5xx) are retried with
exponential backoff. Configure this with `LLM_TIMEOUT_SECONDS`, `LLM_MAX_RETRIES`,
and `LLM_RETRY_BASE_SECONDS`.

### Switching Gemini to DeepSeek

The RAG layer depends only on the shared `LLMProvider` contract. Gemini and DeepSeek
apply the same input guard, structured `LLMAnswer`, citation-ID validation, timeout,
retry, and safe error behavior. When a DeepSeek API key is available, restart the
service after changing only:

```env
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-v4-flash
LLM_API_KEY=replace-with-your-deepseek-api-key
LLM_BASE_URL=https://api.deepseek.com
```

No re-crawling, re-chunking, re-embedding, Qdrant migration, or RAG code change is
required. Model names can change over time, so verify the current model in DeepSeek's
official documentation when purchasing access.

An internal end-to-end provider probe is available at `POST /api/v1/internal/llm/test`.
It is excluded from OpenAPI and disabled unless `INTERNAL_API_KEY` is configured. Call
it with the same value in the `X-Internal-API-Key` header; never expose this key to a
browser or mobile client.

LLM threat boundaries and controls are documented in `SECURITY.md`. The LLM service is intentionally
not exposed through a public chat endpoint until authentication and Redis rate limiting are added.

## Document ingestion

The admin CLI accepts local UTF-8 `.txt`, `.md`, and text-based `.pdf` files up to 25 MiB.
It creates an immutable `PENDING` document version in Neon. Chunking, embedding and Qdrant
indexing intentionally run in a later pipeline, so a failed AI service cannot lose source data.

```powershell
python -m scripts.ingest docs/quy-che-2025-2026.pdf `
  --code QC-2025-2026 `
  --title "Quy chế đào tạo 2025/2026" `
  --type REGULATION `
  --academic-year 2025/2026 `
  --issuer "Học viện Ngân hàng" `
  --source-url "https://hvnh.edu.vn/nguon-chinh-thuc" `
  --published-at "2025-08-01T00:00:00+07:00" `
  --effective-from "2025-09-01T00:00:00+07:00"
```

Use the same `--code` for a replacement version. Re-ingesting identical normalized content
is idempotent. Scanned PDFs without a text layer need OCR before ingestion.

### Controlled web crawling

Sources must be explicitly registered with a HTTPS seed, domain allowlist, optional path
prefixes, depth and page limit. Redis Streams separates scheduling from crawl workers; URL/content
hashes and conditional HTTP headers make recurring crawls incremental.
Large backfills are checkpointed in each `PARTIAL` run (`frontier` plus `visited` URLs). The next
run for the same source resumes that frontier, so a page limit bounds each batch without making
deep sites restart from their home page.

```powershell
python -m scripts.discover_links "https://hvnh.edu.vn/pdt/vn/bgddt"
python -m scripts.crawl add-source --name "PDT - Quy dinh Bo GDDT" --url "https://hvnh.edu.vn/pdt/vn/bgddt" --domains "hvnh.edu.vn" --paths "/pdt/vn/bgddt,/medias/pdt/vi" --type REGULATION --depth 2 --max-pages 120
python -m scripts.crawl add-source --name "Online HVNH - CTDT" --url "https://online.hvnh.edu.vn/News/Type/1017" --domains "online.hvnh.edu.vn" --paths "/News/Type/1017,/News/Detail/" --detail-paths "/News/Detail/" --type GUIDE --depth 2 --max-pages 120
python -m scripts.crawl list
python -m scripts.crawl find-url --url "https://hvnh.edu.vn/example.html"
python -m scripts.crawl set-enabled --source-id <SOURCE_UUID> --enabled false
python -m scripts.crawl enqueue --source-id <SOURCE_UUID>
python -m scripts.crawl enqueue --source-id <SOURCE_UUID> --fresh
python -m scripts.crawl_worker --run-id <RUN_UUID>
python -m scripts.crawl status --run-id <RUN_UUID>
python -m scripts.crawl normalize-source --source-id <SOURCE_UUID>
docker compose --env-file ..\backend\.env --profile crawler up -d --build crawl-scheduler crawl-worker pipeline-worker
```

When RAG is embedded in the main HVNH Hub backend, `uvicorn src.main:app` starts the
scheduler, crawl worker and pipeline worker in the same lifecycle by default. Set
`RAG_CRAWLER_BACKGROUND_ENABLED=false` on API-only replicas if dedicated worker services
are deployed. Overdue sources whose latest terminal run is `PARTIAL` are enqueued as a
`RECOVERY` run and resume the saved frontier instead of restarting at the seed URL.
Terminal `PARTIAL` and `FAILED` runs are retried after
`CRAWLER_RECOVERY_RETRY_MINUTES`, capped by `CRAWLER_RECOVERY_MAX_ATTEMPTS`;
the attempt number and parent run ID are persisted in run metadata for auditing.

The crawler extracts HTML/PDF/DOCX/XLSX into immutable `PENDING` versions only. It does not
run Gemini, Modal embeddings, chunking or Qdrant. Do not expose these administration commands
as public endpoints. `--detail-paths` identifies extensionless HTML article routes; media/file
prefixes must remain explicitly allowlisted. PDF links are discovered from anchors, iframe/object/
embed elements, lazy-load attributes, HVNH viewer query parameters and direct PDF URLs embedded
in JavaScript. Use `--fresh` after changing discovery logic: unlike a normal incremental run, it
ignores an older `PARTIAL` checkpoint and starts again at the seed URL. `crawl status` reports
attachment discovery, saved/unchanged, rejected and pending counts and lists rejected attachment
URLs with reason codes. Scanned PDFs are marked `OCR_REQUIRED` and remain traceable by URL until
the OCR stage processes them; they are never silently treated as indexed text. Deploy after OCR
or embedding code changes, then process one crawl run or source:

```powershell
modal deploy modal_app/hvnh_rag.py
python -m scripts.ocr_documents --run-id <RUN_UUID>
python -m scripts.ocr_documents --source-id <SOURCE_UUID> --include-legacy --limit 20
python -m scripts.process_source --source-id <SOURCE_UUID> --limit 200
```

The OCR command excludes filenames that identify student lists or student debt and marks them
`PII_EXCLUDED`; such records must not be indexed into the public RAG collection.

In deployed operation, `crawl-worker` emits every completed/partial crawl run to a separate Redis
Stream. `pipeline-worker` consumes it and runs OCR followed by the source-scoped chunk/index
pipeline. A non-zero OCR/index exit, provider exception, or stage timeout is retried with
exponential backoff and recorded under `ai_crawl_runs.metadata.pipeline`; one failed attachment
does not stop other pending documents from being processed. Configure this with
`PIPELINE_STAGE_TIMEOUT_SECONDS`, `PIPELINE_MAX_RETRIES`, and
`PIPELINE_RETRY_BASE_SECONDS`. Temporary per-source lock contention is explicitly requeued, so a
Redis Stream entry is not left pending indefinitely.

Document numbers and lifecycle references are extracted before indexing. References are stored in
`ai_document_relations` as `REFERENCES`, `AMENDS`, `SUPERSEDES`, or `REPEALS`; unresolved official
documents remain explicit instead of being guessed. Inspect or rebuild the graph with:

```powershell
python -m scripts.document_references extract --source-id <SOURCE_UUID>
python -m scripts.document_references missing --limit 100
```

For a verified single-document URL found on an approved HVNH domain, register its canonical number
with `crawl add-source --document-code "2450/QĐ-HVNH" ...`. This curated step prevents an external
search result or a guessed URL from becoming trusted knowledge automatically.

The ingestion core is topic-independent: HTML, PDF, scanned PDF, DOCX and XLSX all enter the same
version/policy/chunk/index lifecycle. Source-specific exclusions are configuration, not code:

```powershell
python -m scripts.crawl update-source --source-id <SOURCE_UUID> --url <SEED_URL> `
  --domains "hvnh.edu.vn" --paths "/approved/path,/medias/approved/path" `
  --exclude-url-patterns "danh-sach-ca-nhan,ket-qua-ca-nhan" `
  --exclude-content-patterns "tai-lieu-noi-bo-khong-cong-khai"
```

Tuition documents are only an end-to-end verification case. No OCR, relation, versioning,
chunking, security or retrieval component depends on tuition-specific fields or amounts.

After a crawl batch, run the source-scoped post-processing pipeline (normalize metadata,
sync existing Qdrant payloads, chunk pending versions, embed/index, and prune stale points):

```powershell
python -m scripts.process_source --source-id <SOURCE_UUID> --limit 200
```

Suspicious source text is quarantined instead of silently indexed. Review it before approval:

```powershell
python -m scripts.quarantine adopt-failed
python -m scripts.quarantine list
python -m scripts.quarantine approve --version-id <VERSION_UUID>
```

Approval is an explicit trust decision. The approved version returns to `PENDING` and can then
be processed by `scripts.process_source`; never approve content solely to clear an error count.

### Chunking stage

Chunk all pending versions without invoking an embedding model or Qdrant:

```powershell
python -m scripts.chunk run --limit 100
python -m scripts.chunk inspect --version-id <VERSION_UUID> --preview 240
```

The deterministic `structure-v2` chunker preserves Vietnamese Chương/Mục/Điều headings,
overlapping offsets, token estimates, source page ranges and hashes. Successful versions move
from `PENDING` to `PROCESSING`; retrieval-excluded listing pages move to `ARCHIVED`.

### Modal embedding and Qdrant indexing

```powershell
python -m scripts.check_modal_embedding
python -m scripts.index run --limit 100
python -m scripts.index prune
python -m scripts.index prune --apply
python -m scripts.index validate
```

The default provider is Modal `hvnh_rag/BgeM3` with BAAI/bge-m3, 1,024-dimensional
Cosine vectors. A version moves to `INDEXED` only after all points reach Qdrant. Payloads
retain temporal, access-control, source and citation metadata; older versions remain available
with `is_current=false` for historical questions. `prune` first reports, and only deletes with
`--apply`, Qdrant points no longer backed by chunks of a PostgreSQL `INDEXED` version.

### Retrieval smoke tests

Retrieval runs BGE-M3 vector search in Qdrant and an independent PostgreSQL full-text search,
then combines both rankings with Reciprocal Rank Fusion. Temporal, current-version and visibility
filters apply to both branches. This improves exact-name, course-code and numeric queries while
retaining semantic matching, and returns source metadata without calling an LLM:

The default `RETRIEVAL_RERANKER=heuristic` adds deterministic title/entity, content and academic
year signals without another model or GPU. The reranker is injected behind a separate interface,
so a cross-encoder can replace it later without changing the RAG orchestration.

```powershell
python -m scripts.retrieve "Chương trình trao đổi sinh viên năm học 2026/2027 là gì?" --show-content
python -m scripts.retrieve "Thông báo mới nhất dành cho sinh viên là gì?"
python -m scripts.retrieve "Nội quy năm học 2024/2025"
```

### Grounded multi-turn RAG

The internal RAG flow rewrites follow-up questions using bounded conversation memory, retrieves
fresh evidence, requires exact inline citations, and stores message/citation snapshots in Neon.
Conversation history is never treated as a knowledge source.

```powershell
python -m scripts.ask_rag "Chuẩn đầu ra ngoại ngữ VSTEP như thế nào?"
python -m scripts.ask_rag "Còn việc miễn học phần thì sao?" --conversation-id <CONVERSATION_UUID>
python -m scripts.conversation <CONVERSATION_UUID>
```

Only the latest messages are sent for rewriting. Once history exceeds the configured threshold,
older turns are compacted into `ai_conversations.summary`; the original messages remain durable
in Neon. The HTTP equivalent is the key-protected `POST /api/v1/internal/rag/ask` endpoint.

The public `POST /api/v1/rag/chat` endpoint additionally requires a signed Bearer JWT for an
active HVNH user. Configure `AUTH_JWT_SECRET` (at least 32 characters), issuer and audience in
the deployment secret store. Redis applies per-user/per-IP rate limits and a global concurrency
lease. Token issuance/login belongs to the main HVNH authentication service; this backend only
validates access tokens.

The authenticated UI can manage durable chat history without exposing IDs to users:

```text
POST   /api/v1/conversations
GET    /api/v1/conversations?limit=30&offset=0
GET    /api/v1/conversations/{conversation_id}/messages
PATCH  /api/v1/conversations/{conversation_id}
DELETE /api/v1/conversations/{conversation_id}
```

Every lookup includes `user_id` ownership and excludes soft-deleted conversations. Message
history is paginated with `limit` and `before_sequence`.

Run repeatable evaluations with:

```powershell
python -m scripts.evaluate_retrieval
python -m scripts.evaluate_rag
```

The answer-level dataset is deliberately human-gated. Rebuild the evidence candidates and the
40-case draft (35 grounded questions plus 5 correct-refusal cases), then review every case:

```powershell
python -m scripts.export_eval_candidates --limit 400
python -m scripts.build_gold_draft
python -m scripts.review_gold list
python -m scripts.review_gold show --id hvnh-001
python -m scripts.review_gold approve --id hvnh-001 --answer "<verified answer>" --keywords "<key fact>"
```

`evaluate_rag` runs only `APPROVED` cases by default and matches citations by their exact official
source URL. `--include-pending` is diagnostic only and its report is marked `official_score=false`.
Never use an LLM-generated answer as gold without a domain reviewer checking it against the stored
evidence and linked HVNH source. This reviewed dataset is the prerequisite for later RAGAS scoring.

RAGAS is intentionally isolated from the production environment because its offline evaluation
stack includes large analytics/LangChain dependencies. Create a separate evaluation venv, generate
fresh responses/contexts, export the dataset, then run a bounded judge batch:

```powershell
python -m venv .venv-eval
.\.venv-eval\Scripts\python.exe -m pip install -r requirements-eval.txt
python -m scripts.evaluate_rag
python -m scripts.export_ragas_dataset
.\.venv-eval\Scripts\python.exe -m scripts.evaluate_ragas --limit 10
```

The RAGAS runner uses the 0.4 collections API and reports faithfulness, answer relevancy,
answer correctness, context precision and context recall. Increase `--limit` only after the judge
provider quota and cost are understood.

Every newly crawled stored document also receives a format-neutral extraction quality score and
canonical structure counts. HTML/PDF/DOCX/XLSX/CSV extractors preserve section, page or table
boundaries where available. Low-quality extraction is rejected as `LOW_EXTRACTION_QUALITY` before
chunking and Qdrant indexing; encrypted, scanned or unsupported content continues through the
existing OCR/quarantine path.

Run the read-only knowledge quality gate after every crawl/pipeline batch:

```powershell
python -m scripts.audit_knowledge --report evals/results/knowledge-audit-latest.json
python -m scripts.audit_knowledge --strict
```

`--strict` returns a non-zero status when indexed data is inconsistent, a version failed, or
content awaits security review. Missing year/date counts are reported separately because evergreen
pages such as lecturer profiles legitimately have no academic year.

With the API running, execute a bounded resilience/latency smoke test (the API key is read from
`.env` and is never printed):

```powershell
python -m scripts.load_test_rag --requests 10 --concurrency 2
```

### Grounded RAG and persisted citations

The internal RAG flow combines retrieval with the configured Gemini/DeepSeek provider. It
requires inline markers such as `[1]`, validates them against retrieved context IDs, and stores
both chat messages plus immutable citation snapshots in Neon:

```powershell
python -m scripts.ask_rag "Chuẩn đầu ra ngoại ngữ VSTEP như thế nào?"
```

The hidden endpoint `POST /api/v1/internal/rag/ask` requires `X-Internal-API-Key`. A request
accepts `question` and an optional `conversation_id`; do not expose the internal key in frontend
code. If retrieval has no sufficiently relevant source, the service refuses without calling the LLM.

### Production HTTP boundary

The public UI must call `POST /api/v1/rag/chat` with the main application's bearer JWT. Never put
`INTERNAL_API_KEY`, database, Redis, Qdrant, Modal, or LLM credentials in browser code. In a
production environment startup deliberately fails unless authentication and browser boundaries are
explicitly configured:

```dotenv
ENVIRONMENT=production
DOCS_ENABLED=false
AUTH_JWT_SECRET=<at-least-32-random-characters>
CORS_ALLOWED_ORIGINS=["https://app.hvnh.example"]
TRUSTED_HOSTS=["api.hvnh.example"]
MAX_REQUEST_BODY_BYTES=65536
```

Responses include `X-Request-ID` for tracing plus no-cache, anti-sniffing, frame, referrer, and
browser-permission headers. The API rejects oversized bodies before authentication. Configure the
load balancer to use `/api/v1/health` for liveness and `/api/v1/ready` for traffic readiness. Run
`alembic upgrade head` as one deployment migration job before scaling API replicas; do not let
multiple production replicas race the migration command in the Dockerfile.

## Modal BGE-M3 deployment

The `hvnh_rag` Modal app serves normalized 1024-dimensional BAAI/bge-m3 embeddings
on a T4 GPU. Its web endpoint requires Modal Proxy Auth and therefore rejects public
unauthenticated calls.

```powershell
modal deploy modal_app/hvnh_rag.py --name hvnh_rag
python -m scripts.check_modal_embedding
```

The deployment limits each text to 8,192 characters, accepts at most 64 texts and
100,000 total characters per request, scales to zero, and caps scaling at three GPUs.
