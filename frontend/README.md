# IAmina — Flutter Frontend

Flutter/Dart web + mobile app for the IAmina diabetes companion.

## Quick Start

From the repo root:

```bash
./dev.sh
```

Opens at `http://localhost:3000`. Demo login: `dev@iamina.app`.

## Stack

- **Flutter 3.41.7** (pinned in `.tool-versions`)
- **GoRouter 14** — navigation
- **Drift 2.20** — offline-first local DB (SQLite)
- **Provider** — state management
- **Firebase Auth** — authentication (web configured, iOS/Android need `flutterfire configure`)

## Structure

```
lib/
├── features/        # Screens — auth, dashboard, journal, chat, profile
├── data/            # Drift DB schema + API DTOs
├── services/        # AuthService, ApiClient, SyncService
├── routes/          # GoRouter config
└── main.dart
```

## Build-time Variables

Required dart-defines (handled automatically by `dev.sh`):

| Variable | Purpose |
|---|---|
| `DEMO_EMAIL` | Demo account email |
| `DEMO_PASSWORD` | Demo account password |
| `API_BASE_URL` | Backend URL (default: `http://127.0.0.1:8001`) |

## Production Build

```bash
flutter build web --dart-define=API_BASE_URL=https://api.iamina.app
```

Output in `build/web/` — serve with nginx.
