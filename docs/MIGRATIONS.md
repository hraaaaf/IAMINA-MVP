# Migrations

---

## 1. SQLite → PostgreSQL

> **Status:** PLANNED — Phase 4
> **Blocker:** None — execute when deploying to staging/production

### Current State

- **DB (dev):** SQLite (`db.sqlite3` — local, git-ignored)
- **Config:** `DATABASE_URL=sqlite:///db.sqlite3` in `.env`
- **Drivers:** `dj-database-url` + `psycopg2-binary` already in `requirements.txt`

### Steps

```bash
# 1. Start local PostgreSQL (install via https://postgresapp.com or brew install postgresql)
# Or use Docker: docker run -e POSTGRES_DB=amina_db -e POSTGRES_USER=amina -e POSTGRES_PASSWORD=amina_dev -p 5432:5432 postgres:16-alpine

# 2. Update .env
DATABASE_URL=postgres://amina:amina_dev@localhost:5432/amina_db

# 3. Run migrations
cd backend && python manage.py migrate

# 4. (Optional) Carry over existing SQLite data
python manage.py dumpdata --natural-foreign --natural-primary \
  -e contenttypes -e auth.Permission --indent 2 > data_backup.json
# Switch DATABASE_URL, then:
python manage.py migrate && python manage.py loaddata data_backup.json

# 5. Verify
python manage.py check --database default
python manage.py shell -c "from django.db import connection; print(connection.vendor)"
# → postgresql
```

### Production (Railway / Render / Fly.io)

All three platforms inject `DATABASE_URL` automatically. No code change needed.

```env
# Platform dashboard only — never commit:
DATABASE_URL=postgres://...
SECRET_KEY=...
DEBUG=False
ALLOWED_HOSTS=api.iamina.app
CORS_ALLOWED_ORIGINS=https://iamina.app
```

### SQLite vs PostgreSQL Differences

| Behaviour | SQLite | PostgreSQL |
|-----------|--------|------------|
| String comparison | Case-insensitive | Case-sensitive |
| Concurrent writes | Locked | Row-level locking |
| JSON field | Text | Native JSONB |
| Migrations | Permissive | Strict column types |

> Review raw SQL in `backend/diabetes/services/clinical/sql_analytics.py` for PostgreSQL dialect compatibility before switching.

### Rollback

```env
DATABASE_URL=sqlite:///db.sqlite3  # revert in .env, restart backend
```

---

## 2. Gemini → Kimi 2.5 (LLM)

> **Status:** PLANNED — Phase 5
> **Blocker:** Kimi API key not yet obtained

### Current State

| Provider | Status | Model |
|----------|--------|-------|
| Gemini 2.5 Flash | ✅ Active | `gemini-2.5-flash-lite` |
| Kimi 2.5 Moonshot | ⏸ Standby | `moonshot-v1-128k` |
| FallbackProvider | 🛡 Always on | static templates |

### Provider Architecture

```
get_llm_provider()  ←  llm/factory.py
        │
        ├── KIMI_API_KEY absent → GeminiProvider (GuardedGeminiProvider + rate guard)
        │
        └── KIMI_API_KEY set   → KimiProvider
                                      │
                                      └── on failure → GeminiProvider → FallbackProvider
```

All providers implement `BaseLLMProvider`. No separate `USE_KIMI` flag — the factory
auto-activates Kimi if `KIMI_API_KEY` is present in the environment.

Medical emergencies always bypass the LLM entirely (`TriageVitalMiddleware`).

### Migration Steps

```bash
# 1. Obtain API key — https://platform.moonshot.cn

# 2. Update .env
KIMI_API_KEY=sk-your-key-here
# No USE_KIMI flag needed — factory detects the key automatically

# 3. Add dependency (not yet in requirements.txt)
# backend/requirements.txt:
openai>=1.0.0   # Kimi uses OpenAI-compatible SDK

pip install openai>=1.0.0

# 4. Restart backend — factory will log: KimiProvider active (model=moonshot-v1-128k)

# 5. Run golden tests
pytest backend/evals/ -v
```

### Gradual Rollout

| Stage | Action | Duration |
|-------|--------|----------|
| Internal | `USE_KIMI=True` on dev/staging | 3 days |
| 10% → 50% | Monitor output consistency | 2 weeks |
| 100% | Deprecate Gemini provider | — |

### Rollback

```env
# Remove or unset KIMI_API_KEY — factory falls back to Gemini on next restart
# KIMI_API_KEY=  # leave empty or remove the line entirely
```

### Why Kimi

- Native French and Moroccan Darija support
- 200K context window — full patient history in prompt
- OpenAI-compatible SDK — no proprietary client
- Better cost/quality ratio than Gemini for clinical text

### Dependencies

```
# Add to requirements.txt when executing:
openai>=1.0.0

# Remove after Gemini fully deprecated:
google-genai==0.3.*
```
