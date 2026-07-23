# ADR 0006 — Django déplacé dans `backend/`

- **Statut :** accepté
- **Date :** 2026-04-17
- **Mis à jour :** 2026-06-03 — Phase 3 a supprimé `templates/`, `static/`, `tailwind.config.js` ; `logs/` renommé en `diabetes/` ; settings dans `amina/`
- **Décideurs :** Software Architect, DevOps Architect, Product Manager

## Contexte

`AMINA_MVP_PLAN.md` §2 prévoit une arborescence monorepo avec trois couches à la racine : `backend/` (Django + API Ninja), `frontend/` (Flutter PWA + iOS + Android), `infra/` (Docker, Coolify, CI). Jusqu'ici tout le code Django vivait à la racine, ce qui aurait généré une collision directe avec l'arrivée imminente du projet Flutter (`pubspec.yaml`, `lib/`, `web/`, `test/`).

Question §7 #1 : déplacer Django dans `backend/` (propre) ou garder à la racine (moins de casse). Arbitré en faveur de **déplacer**.

## Décision

Déplacer **tout le code Django** et ses artefacts de compilation dans `backend/` :

```
backend/
├── manage.py
├── requirements.txt
├── db.sqlite3             (gitignored)
├── amina/                 (settings.py, urls.py, wsgi.py)
├── diabetes/              (app Django principale — modèles, API, services, tests)
├── ai/                    (app AI — endpoints summary/chat/stream/voice/image)
├── engine/                (app IAmina conscience — state, memory, thinking)
├── llm/                   (package LLM — factory, providers, pseudonymizer)
├── clinical/              (app modèles cliniques de base)
├── core/                  (app utilitaires — AuditLog partagé)
└── ...                    (companion, integrations, observability, safety, evals)
```

> `tailwind.config.js`, `static/`, `templates/` supprimés en Phase 3 (Django HTML Purge — DA-01 Flutter only).
> `logs/` renommé en `diabetes/` lors du refactoring chassis.

Reste à la **racine du monorepo** :

- Tous les `.md` stratégie / documentation (`CLAUDE.md`, `SPECS.md`, `ROADMAP.md`, `AMINA_MVP_PLAN.md`, `techdebt.md`, etc.)
- `docs/`, `scripts/`, `scratch/`, `tasks/`
- `run.sh`, `lancer_ia.bat`, `run_8001.bat` (mis à jour pour `cd backend/`)
- `venv/` (Python virtualenv, gitignored)
- Futurs `frontend/`, `evals/`, `infra/`, `.github/workflows/`

## Conséquences

**Positives**

- Aucune collision possible avec `frontend/` (Flutter) ou `infra/` (Docker Compose, Coolify).
- CI/CD pourra déclencher les pipelines backend et frontend indépendamment via `paths:` filters GitHub Actions.
- Frontière claire pour les futurs contributeurs : "tu travailles sur Django → tu passes ta journée dans `backend/`".
- Git `mv` préserve l'historique de chaque fichier — blame et log restent utilisables.

**Négatives**

- Toutes les commandes `manage.py` se lancent désormais depuis `backend/` (`cd backend && python manage.py ...`). Geste supplémentaire modeste, documenté dans `CLAUDE.md` et absorbé par `run.sh`.
- Les chemins relatifs dans les scripts historiques (`lancer_ia.bat`, `run_8001.bat`) ont dû être mis à jour. Un contributeur avec un clone très ancien peut rencontrer des conflits sur des branches en vol.
- `.env` sera désormais lu depuis `backend/` (CWD au moment de `load_dotenv()`). Les devs doivent créer leur `.env` dans `backend/`, pas à la racine.

## Alternatives rejetées

- **Garder Django à la racine, placer Flutter dans `frontend/`** : aurait conservé la simplicité de setup mais mélangé les responsabilités ; la racine aurait gardé `manage.py` + des dizaines de templates + `pubspec.yaml` côte à côte.
- **Monorepo avec un outil dédié (Nx, Bazel)** : sur-ingénierie au stade MVP. Le simple layout `backend/` + `frontend/` suffit tant que les deux projets ne partagent ni code ni outils de build.

## Suivi

- Mise à jour de `CLAUDE.md`, `run.sh`, `lancer_ia.bat`, `run_8001.bat` : livrée dans le même commit que le déplacement.
- Futurs splits conformes au plan §2 (`requirements/{base,dev,prod}.txt`, `settings/{dev,staging,prod}.py`) quand Phase 4 (infra) sera activée.
- Section 7 du plan mise à jour pour acter la décision.
