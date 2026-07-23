# ADR 0001 — Passage de `logs/views.py` à un package `logs/views/`

- **Statut :** ~~accepté~~ **supersédé** — Phase 3 (Django HTML Purge) a supprimé l'intégralité du layer views. DA-01 (ROADMAP) : Flutter est le seul frontend ; le backend n'expose que `/api/*`. Ce package n'existe plus.
- **Date :** 2026-04-17
- **Supersédé le :** 2026-05-x (Phase 3 merge)
- **Contexte :** branche H-MVP
- **Décideurs :** Software Architect, Senior SWE

## Contexte

`logs/views.py` dépassait les 1200 lignes et concentrait auth, dashboard, CRUD, IA, démo, API legacy, voice parse. `TEAM.md` (Software Architect, signal d'alerte) pose la règle : `view > 50 lignes → extraire la logique dans un service`. Le fichier unique ne permettait plus de localiser rapidement une vue, ralentissait la revue de code et augmentait les conflits de merge.

La directive Software Architect prévoit également une évolution vers des apps Django séparées (patients, entries, analytics, ai, integrations) sans big-bang. Un fichier monolithique rend cette extraction future beaucoup plus coûteuse.

## Décision

Remplacer `logs/views.py` par un package `logs/views/` organisé par domaine :

- `auth.py` — login, logout, redirection post-login
- `dashboard.py` — tableau de bord patient
- `entries.py` — CRUD `LogEntry` (create, confirmation, edit, delete)
- `profile.py` — configuration profil + onboarding conversationnel
- `summary.py` — vue `ai_summary` (IAmina)
- `demo.py` — `magic_demo_view` + feedback démo
- `api_legacy.py` — endpoints JSON existants (`voice_parse`, `ai_chat_endpoint`)
- `__init__.py` — exporte les noms publics attendus par `diabetes_poc/urls.py`

Toutes les vues restent des function-based views (FBV) conformément à `TEAM.md` (Senior SWE). Les services (`logs/services/ai_chat.py`, `logs/services/clinical/engine.py`) sont déjà extraits en parallèle.

## Conséquences

**Positives**

- Chaque vue trouve sa place par domaine. La règle « 50 lignes » devient mesurable.
- L'extraction future en apps Django séparées consiste à déplacer un sous-module, pas à démêler un fichier.
- La revue de code est localisée : un changement sur la saisie d'entrée touche `entries.py` seulement.
- Les imports dans `urls.py` restent inchangés grâce au re-export dans `__init__.py`.

**Négatives**

- Deux contributeurs qui ajoutent des vues dans le même sous-module peuvent encore créer des conflits (mais plus petits qu'auparavant).
- Pendant la transition, `logs/views.py`, `logs/clinical_engine.py`, `logs/ai_chat_service.py` ont coexisté avec leurs équivalents package/services. Python résout les imports en faveur du package, donc les fichiers .py étaient morts mais encore présents. Nettoyés dans le même cycle H-MVP (voir `git log`).

## Alternatives rejetées

- **Garder `views.py` monolithique + séparer par convention de nommage** : ne résout ni la lisibilité ni la préparation à l'extraction future.
- **Class-based views (CBV) par domaine** : écart trop important avec la directive Senior SWE « FBV par défaut, CBV uniquement pour les cas natifs Django ». Réservé à `CustomLoginView`.
- **Séparer immédiatement en apps Django** : violation du principe « monolithe structuré » de `TEAM.md` ; coûteux avant que les frontières métier soient stabilisées par l'usage.

## Suivi

- Tests à ajouter : un test d'import smoke par sous-module pour détecter toute régression de routing (voir `logs/tests/`).
- Les futurs ajouts de domaines (`analytics`, `integrations`) respectent la même structure.
