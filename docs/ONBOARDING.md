# IAmina — Dev Onboarding

Welcome to IAmina — diabetes companion with AI-powered clinical insights.

---

## 1. Clone & Setup

```bash
git clone <repo>
cd diabetes-poc
./dev.sh
```

`dev.sh` handles everything on first run: creates the Python venv, installs deps, copies `.env.example → .env`, runs migrations, and seeds demo data. Re-running it is safe — all steps are idempotent.

> **Flutter not installed?** Install Flutter 3.41.7 (pinned in `.tool-versions`) before running `dev.sh`:
> - Via mise/asdf: `mise install`
> - Or manually: https://docs.flutter.dev/get-started/install

---

## 2. Get Firebase Credentials

Ask the team lead for `firebase-credentials.json` (service account key).

**CRITICAL:** Place it **OUTSIDE the repo**:

- **Windows:** `C:/Users/YOUR_NAME/.amina-secrets/firebase-credentials.json`
- **Mac/Linux:** `/home/YOUR_NAME/.amina-secrets/firebase-credentials.json`

Update `.env`:
```env
FIREBASE_CREDENTIALS_PATH=/path/to/firebase-credentials.json
SECRET_KEY=<generate-random-64-chars>
GEMINI_API_KEY=<get-from-google-cloud>
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

---

## 3. Backend Setup

### Recommended — Docker (identical on macOS & Windows)

This is the standard dev path (ROADMAP NOW Step 0). It boots backend + Postgres + Redis
reproducibly, so both devs run the same environment.

```bash
docker compose up --build                                   # backend + Postgres + Redis
docker compose run --rm backend python manage.py setup_demo # demo data (first run)
```

✅ API at `http://127.0.0.1:8001/api/v1/` · health `…/api/v1/health` · docs `…/api/docs`
Stop with `docker compose down` (add `-v` to also wipe the DB). Backend reaches Postgres/Redis
over the internal network; only port **8001** is published, so it coexists with other stacks.

> **Firebase auth (to test login):** mount your creds in `docker-compose.override.yml` (snippet in
> the file header) pointing at your own secrets dir. The stack boots without it; only login needs it.

#### 🪟 Windows specifics
- Use **Docker Desktop with the WSL2 backend**, and **clone the repo inside the WSL2 filesystem**
  (e.g. `~/dev/…`), *not* under `C:\` — the source bind-mount that drives hot reload is far faster there.
- Everything else (`docker compose up`, ports, demo seed) is identical to macOS.
- `.gitattributes` enforces LF so container scripts aren't broken by Windows line endings.
- iOS builds are **macOS-only** — on Windows you run the frontend on **Web or Android** (see §4).

### Alternative — manual venv (no Docker)

```bash
# Linux / macOS
source venv/bin/activate && cd backend && python manage.py runserver 8001
# Windows (Git Bash or PowerShell)
source venv/Scripts/activate && cd backend && python manage.py runserver 8001
```

> Note: the manual path uses SQLite and does not start Redis. The legacy `dev.sh`/`dev.ps1`
> launchers are being retired in favour of Docker (ROADMAP SOON).

---

## 4. Frontend Setup

`./dev.sh` handles this automatically (starts both backend + frontend).

✅ App at `http://localhost:3000` — demo login: `dev@iamina.app`

### iOS / Android Setup (Firebase Mobile)

`firebase_options.dart` is gitignored (contains API keys). To enable iOS/Android:

1. **Register apps** in [Firebase Console](https://console.firebase.google.com) → Project Settings → Add app
2. **iOS**: download `GoogleService-Info.plist` → copy to `frontend/ios/Runner/`
3. **Android**: download `google-services.json` → copy to `frontend/android/app/`
4. **Regenerate** `firebase_options.dart`:
   ```bash
   cd frontend
   dart pub global activate flutterfire_cli
   flutterfire configure --project=iamina
   ```
   This auto-fills iOS/Android sections while keeping the existing web config.

---

## 5. Working with Claude Code

**Every session starts with this prompt:**

```markdown
# Session Start — IAmina

Read in order:
1. `CLAUDE.md` (session state + architecture)
2. `docs/MISTAKES.md` (errors to avoid)
3. `docs/ROADMAP.md` (current phase priorities)

Confirm:
- Current branch from CLAUDE.md
- Last action from CLAUDE.md
- Any active blockers

Then ask: "What should I work on?"
```

Then:
1. Claude reads the 3 files automatically
2. You assign a task (or Claude proposes one based on phase)
3. Claude executes + tests
4. Claude updates `CLAUDE.md` session state
5. You commit with phase reference

---

## 6. Architecture Overview

**Monorepo structure:**

```
diabetes-poc/
├── backend/              Django 5.1 + Ninja API + Firebase Auth
│   ├── amina/            Config + middleware (TriageVital, UnitGuard)
│   ├── core/             Audit trail (RGPD compliance)
│   └── tracking/         Health logs + AI services
│
├── frontend/             Flutter/Dart — GoRouter, Drift, Provider
│   ├── lib/features/     Screens (auth, dashboard, journal, profile)
│   ├── lib/data/         Drift ORM (local SQLite) + API DTOs
│   └── lib/services/     Auth, Sync, API client
│
└── docs/                 ADRs, ROADMAP, compliance
```

**Tech stack:**
- **Backend:** Django 5.1, django-ninja, PostgreSQL (prod)
- **Frontend:** Flutter, Dart, GoRouter 14, Drift 2.20
- **Auth:** Firebase JWT + custom Django backend
- **LLM:** Gemini 2.5 Flash (active) → Kimi 2.5 Moonshot (Phase 5, pending API key)
- **State:** Provider + Drift streams (no Bloc/Riverpod)

---

## 7. Critical Components — Never Touch Without Approval

- **`TriageVitalMiddleware`** — Medical emergency detection, never bypass
- **`UnitGuardMiddleware`** — Glucose unit normalization, always upstream
- **`client_uuid` on LogEntry** — Offline sync idempotency
- **`PatientProfile.firebase_uid`** — Firebase Auth ↔ Django User bridge
- **KPI calculations** — SQL-first (ADR-0007), never Python arithmetic

---

## 8. Phase Overview

See **`docs/ROADMAP.md` → "Current Status"** for the live phase grid — it's the single source of
truth and is kept current (Phases 1–26). It also marks the prelaunch blockers (deploy, Firebase)
and what's gated behind the Retention Gate. This file intentionally does not mirror it (the mirror
kept drifting).

---

## 9. Don'ts 🚫

- ❌ **Commit `.env` or `firebase-credentials.json`** — they stay in `.gitignore`
- ❌ **Modify middleware order** — without explicit approval in ADR
- ❌ **Repeat errors from `MISTAKES.md`** — read it at session start
- ❌ **Skip CLAUDE.md session memory** — it's your context
- ❌ **Hardcode credentials** — use `String.fromEnvironment` or `.env`
- ❌ **Compute KPIs in Python** — SQL-first (ADR-0007)
- ❌ **Route medical emergencies to LLM** — use `TriageVitalMiddleware` response
- ❌ **Use bare `except Exception`** — log + fallback (clinical code only)

---

## 10. Useful Commands

```bash
# Dev (everything)
./dev.sh                                        # Setup + start backend + frontend

# Backend only (VM / manual)
source venv/bin/activate && cd backend && python manage.py runserver 8001
source venv/bin/activate
python manage.py check                          # Verify config
python manage.py makemigrations tracking        # Create migrations
python manage.py migrate                        # Run migrations
python manage.py shell                          # Django shell

# Frontend
flutter pub get                                 # Install/sync deps
flutter build web                               # Production build
flutter analyze                                 # Lint check

# Git
git status
git log --oneline -10                           # Recent commits
git diff HEAD~1                                 # Last commit diff
```

---

## 11. Support

- **Questions about architecture?** Check `docs/adr/` (7 ADRs)
- **Previous mistakes?** Read `docs/MISTAKES.md`
- **Roadmap?** Check `docs/ROADMAP.md`
- **Stuck?** Ask Claude Code at session start

---

**Welcome aboard! 🚀 Read CLAUDE.md first, then pick a task.**
