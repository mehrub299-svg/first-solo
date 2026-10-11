# First Solo

![CI](https://github.com/mehrub299-svg/first-solo/actions/workflows/ci.yml/badge.svg)

Ask questions about your own documents and see exactly where each answer came from. Upload PDFs, Word files or text, ask in plain language, and get an answer with the source passages highlighted.

## Features

- Upload PDF, DOCX, TXT or Markdown files (up to 10 MB), or paste text
- Answers come only from your documents, with numbered citations and highlighted source passages
- Choose which documents an answer may use
- Saved chats, with follow-up questions that understand the conversation
- Private by design: every search is filtered to the signed-in user, and automated tests check it
- Secure sign-in: Argon2 password hashing, 15-minute access tokens, and rotating refresh tokens in httpOnly cookies with reuse detection
- Rate limits on sign-in, sign-up, questions and uploads

## How it works

```text
Browser (React)
     |
     |  /api/v1/...
     v
FastAPI  ----->  PostgreSQL + pgvector
   |
   +-------->  OpenRouter (embeddings and language model)
```

1. A document is split into overlapping passages (about 1,000 characters). Each passage is embedded as a 1,536-dimension vector and stored with pgvector.
2. A question is embedded the same way. The closest passages, limited to your account and any documents you picked, are retrieved with an exact cosine search.
3. The language model is told to answer using only those passages and to cite them. The interface highlights the sentence in each passage that best matches the answer.
4. For a follow-up, the question is first rewritten as a standalone question using the last few turns, so the search still works.

In production, nginx serves the built frontend and forwards `/api/` to FastAPI, so the browser sees a single origin.

## Tech stack

| Layer | Tools |
|---|---|
| Backend | Python 3.12, FastAPI (async), SQLAlchemy 2 with asyncpg, Alembic |
| Database | PostgreSQL 16 with pgvector |
| AI | OpenRouter (OpenAI-compatible API) for embeddings and chat |
| Frontend | React 19, Vite, Tailwind CSS 4 |
| Infrastructure | Docker Compose, nginx |
| Quality | pytest and pytest-asyncio (68 tests), GitHub Actions |

## Run it locally

Requirements: Docker Desktop and an [OpenRouter](https://openrouter.ai) API key.

1. Copy `.env.example` to `.env` (`copy` on Windows, `cp` elsewhere) and fill in `SECRET_KEY` and `OPENROUTER_API_KEY`.
2. Start everything and apply the database migrations:

```bash
   docker compose up -d --build
   docker compose exec backend alembic upgrade head
```

3. Open <http://127.0.0.1:5173>. The API documentation is at <http://127.0.0.1:8001/docs>.

### Production-like stack

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

Open <http://127.0.0.1:8080>. This stack has its own empty database, runs the backend as a non-root user without auto-reload, and publishes only nginx.

### Tests

```bash
docker compose exec db psql -U rag -d rag_db -c "CREATE DATABASE rag_test;"   # once
docker compose exec backend pytest -q
```

Tests run against the separate `rag_test` database with fake embedding and LLM services, so they cost nothing and never touch your data.

## Configuration

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | Async Postgres URL (`postgresql+asyncpg://...`) |
| `SECRET_KEY` | Signs access tokens. Use a long random value |
| `OPENROUTER_API_KEY` | Key for embeddings and the language model |
| `LLM_MODEL` | Chat model (default `openai/gpt-4o-mini`) |
| `EMBEDDING_MODEL` | Embedding model. **Never change it once documents exist** |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime (default 15) |
| `COOKIE_SECURE` | Set to `true` when served over HTTPS |

All settings and their defaults are in `backend/app/core/config.py`.

## API overview

All routes live under `/api/v1`. Interactive documentation is at `/docs` when running the development stack.

| Method and path | Purpose |
|---|---|
| `POST /auth/register`, `POST /auth/login` | Create an account, sign in |
| `POST /auth/refresh`, `POST /auth/logout` | Rotate the refresh cookie, sign out |
| `GET /auth/me` | Current user |
| `GET /documents`, `POST /documents` | List documents, add pasted text |
| `POST /documents/upload` | Upload a PDF, DOCX, TXT or MD file |
| `DELETE /documents/{id}` | Delete a document and its passages |
| `POST /chat/ask` | Ask a question (optional `chat_id` and `document_ids`) |
| `GET /chats`, `GET /chats/{id}/messages`, `DELETE /chats/{id}` | Chat history |

## Project layout

```text
backend/
  app/
    api/         routers, dependencies, rate limiting, error mapping
    core/        settings, security (JWT, Argon2), API client
    db/          engine, session, base
    models/      SQLAlchemy models
    schemas/     request and response models
    services/    business logic: auth, tokens, chunking, extraction,
                 embedding, llm, ingestion, retrieval, rag, conversation
  alembic/       database migrations
  tests/         pytest suite
frontend/
  src/           React app: api, auth, workspace state, components
  nginx.conf     production web server configuration
docker-compose.yml        development stack
docker-compose.prod.yml   production-like stack on port 8080
```

## Updating dependencies

`requirements.txt`, `requirements-dev.txt` and `frontend/package.json` list the direct dependencies. The `.lock` files and `package-lock.json` pin exact versions, and the Docker builds use them. After changing a list, regenerate the locks and run the tests:

```bash
docker run --rm -v "$PWD/backend:/w" -w /w python:3.12-slim sh -c "pip install -q -r requirements.txt && pip freeze > requirements.lock"
docker run --rm -v "$PWD/backend:/w" -w /w python:3.12-slim sh -c "pip install -q -r requirements-dev.txt && pip freeze > requirements-dev.lock"
```

On PowerShell use `${PWD}` instead of `$PWD`. For the frontend, run `npm install <package>` inside `frontend/`.

## Known limitations

- Broad requests such as "summarize everything" work poorly: an answer is built from the few passages that best match the question.
- Scanned PDFs contain no extractable text and are rejected (there is no OCR).
- Rate limiting is held in memory, so it is exact only with a single server process.
- Search is exact rather than indexed, which is fine up to roughly 10,000 passages.

## License

MIT. See [LICENSE](LICENSE).