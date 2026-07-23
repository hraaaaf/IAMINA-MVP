# ADR 0005 — Layout de `diabetes/services/` et packages top-level

- **Statut :** accepté (rétroactif, étendu par la passe Amina et le refactoring chassis)
- **Date :** 2026-04-17
- **Mis à jour :** 2026-06-03 — app renommée `logs` → `diabetes` ; `services/llm/` promu en package top-level `llm/` ; apps `engine/` et `ai/` extraites
- **Décideurs :** Software Architect, Data/AI Engineer, Security Architect

## Contexte

`TEAM.md` (Software Architect) : "models = données et invariants métier ; services = logique applicative (LLM, moteur clinique, pseudonymisation, intégrations) ; views = orchestration HTTP ; forms = validation ; templates = présentation pure". Le POC mélangeait tout dans un seul `views.py` monolithique + une poignée de modules à la racine de `logs/` (`clinical_engine.py`, `ai_chat_service.py`).

## Décision

Structurer les services par domaine métier. Layout actuel (post-refactoring chassis) :

```
backend/
├── diabetes/services/          # Domaine patient / données cliniques
│   ├── clinical/
│   │   ├── engine.py           # 8 détecteurs + reformulation + fallback
│   │   ├── sql_analytics.py    # KPI SQL (TIR, GMI, CV, GRI, AGP)
│   │   ├── semantic_compressor.py
│   │   ├── shield.py
│   │   └── ...
│   ├── documents/              # Document Pulper (PDF/image/CSV)
│   │   └── extractors/
│   ├── iamina/                 # IAmina brain services
│   ├── import_csv/             # LibreLink CSV import
│   ├── demo_scenarios.py
│   ├── session_cache.py
│   └── summary.py
│
├── llm/                        # Package top-level LLM (provider-agnostique)
│   ├── factory.py              # get_llm_provider() → Gemini | Kimi | Fallback
│   ├── rate_guard.py           # Quota journalier Redis
│   ├── fallback.py             # FallbackProvider (templates statiques)
│   ├── kimi.py                 # KimiProvider (OpenAI-compatible SDK)
│   └── pseudonymizer.py        # PHI pseudonymization (voir ADR 0003)
│
├── engine/                     # App IAmina conscience (state, memory, thinking)
└── ai/api/v1/                  # Endpoints AI (summary, chat, stream, voice, image)
```

Règles :

- **Aucun appel ORM lourd dans les services** — les services reçoivent des querysets ou des collections d'entrées déjà filtrées par l'endpoint.
- **Aucune dépendance Django HTTP** (pas de `request`, pas de `JsonResponse`) — les services sont réutilisables depuis un endpoint Ninja, une management command, ou un test.
- **`llm/` top-level** — toute nouvelle intégration provider (Kimi, Claude, etc.) s'ajoute ici, pas dans un sous-package d'app.
- **Futurs services** (`firebase.py`, `payments.py`) landent dans `diabetes/services/` ou leur app dédiée.

## Conséquences

**Positives**

- Vues deviennent minces (< 50 lignes par handler) conformément à la directive Software Architect.
- Double consommation view / API triviale : le handler Ninja appelle le même `services/summary.generate_ai_summary` que la vue HTML.
- Tests unitaires sur les services sans monter Django — vitesse et isolation.

**Négatives**

- Indirection supplémentaire pour un contributeur nouveau venu ; compensée par le fait que chaque fichier a un domaine clair et une docstring.
- Risque de services "fourre-tout" si la discipline baisse — guide : un service ne doit faire qu'une chose, si le fichier dépasse 300 lignes, envisager un sous-package.

## Alternatives rejetées

- **Fonctions utilitaires dans les views** : mauvaise réutilisation, tests forcément HTTP.
- **App Django séparée par domaine dès le MVP** : prématuré, coûte en ergonomie avant d'avoir stabilisé les frontières.

## Suivi

- ADR 0003 pour `pseudonymizer` (maintenant `backend/llm/pseudonymizer.py`).
- ~~TD-001~~ : résolu — `llm/factory.py` est la couche d'abstraction provider.
- TD-003 dans `techdebt.md` — timeout et circuit breaker par appel LLM encore manquants.
- `services/demo_scenarios.py` n'embarque aujourd'hui que le scénario A ; TD-015 suit la restauration des scénarios B à H.
