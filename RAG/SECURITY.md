# LLM Security Model

Prompt injection cannot be eliminated solely through prompting or keyword filters. HVNH-RAG-AI
uses defense-in-depth and treats both user messages and retrieved documents as untrusted data.

## Stage 1 controls

- The Gemini model has no tools, database access, URL fetching, code execution, or write authority.
- Credentials and internal configuration are never placed in prompts.
- User and context inputs are Unicode-normalized, size-limited, and screened independently.
- Known instruction override, prompt extraction, role hijack, encoded payload, and active markup
  patterns fail closed before an LLM call.
- System instructions explicitly classify the serialized question/context object as data.
- Gemini harm filters block medium-and-above harassment, hate, sexual, and dangerous content.
- Responses must conform to the `LLMAnswer` schema and active markup/prompt leakage is rejected.
- Provider exceptions are translated to generic public errors. Prompts and generated text are not logged.
- Transport loggers run at WARNING to avoid leaking cloud endpoints and query strings.

## Required controls before a public chat endpoint

- Authentication and authorization using the HVNH user identity.
- Redis rate limiting by user and IP, plus a global Gemini concurrency limit.
- Request body limits at the reverse proxy and FastAPI layers.
- CSRF protection where cookie authentication is used and strict CORS allowlists.
- Abuse/audit events that store hashes, decision codes, and metrics—not raw sensitive prompts.
- Plain-text rendering by default; sanitize any Markdown/HTML in Web and Flutter clients.
- A kill switch for LLM traffic and per-user temporary blocking.

## Implemented public RAG controls

- `POST /api/v1/rag/chat` is disabled unless a 32+ character JWT secret is configured.
- JWT validation requires a fixed HS algorithm, signature, issuer, audience, subject, issued-at and expiry.
- Only active, non-deleted database users are accepted; conversation ownership is checked in SQL.
- Redis enforces per-user and per-IP request limits plus a global expiring concurrency lease.
- Visibility filters are derived from authenticated group membership, never from request fields.
- Audit rows contain actor/action/result metadata but never prompts, answers, tokens or credentials.
- Prompt, history, summary, retrieved context, structured output and citation IDs are validated separately.

## Required controls for RAG

- The current ingestion surface is an admin CLI only; no unauthenticated upload route exists.
- Local ingestion accepts only PDF/TXT/Markdown, resolves regular files, and enforces a 25 MiB limit.
- Only allowlisted official domains and approved files may enter ingestion in the future admin API.
- Strip scripts, hidden markup, comments, metadata, and invisible text before chunking.
- Quarantine documents whose chunks trigger the context injection guard.
- Apply access and temporal filters before retrieval; never trust model-generated filters directly.
- The model receives text context only and cannot act on instructions found in documents.
- Citations must be constructed by application code from retrieved chunk IDs, never invented by the model.
- Retrieved context is read-only; it cannot trigger tools or database operations.

## Reporting

Do not commit `.env`. Revoke and rotate a credential immediately if it appears in source control,
logs, screenshots, issues, or chat messages.
