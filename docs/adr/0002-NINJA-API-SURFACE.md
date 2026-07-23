# ADR 0002 — Introduction d'une API django-ninja versionnée

- **Statut :** accepté — l'API est désormais le seul point d'entrée ; Flutter la consomme intégralement (TD-010 résolu)
- **Date :** 2026-04-17
- **Mis à jour :** 2026-06-03 — auth migré Firebase JWT, app renommée `diabetes/`, TD-010 fermé
- **Contexte :** branche H-MVP
- **Décideurs :** Software Architect, Enterprise Architect (informé), Security Architect (consulté)

## Contexte

Le POC exposait uniquement des vues Django classiques rendant du HTML. `TEAM.md` (Enterprise Architect) cartographie des intégrations à venir (CGM Libre/Dexcom, FHIR EMR, France Connect) et (Product Manager) évoque une app native mobile post-MVP. Chacune de ces pistes a besoin d'un contrat API structuré, versionné, documenté.

Les options évaluées : Django REST Framework (DRF), django-ninja, et « pas d'API, tout en templates ». DRF est le standard historique mais verbeux. django-ninja offre une API type FastAPI (Pydantic, OpenAPI automatique, typage) avec un coût d'adoption minime sur un monolithe Django.

## Décision

Introduire django-ninja comme surface API sous `diabetes/api/`, strictement versionnée :

- `diabetes/api/main.py` — `NinjaAPI` unique, monté sur `/api/` dans `amina/urls.py`.
- `diabetes/api/v1/` — routers par domaine : logs, profile, kpis, account, auth, demo, documents, imports, health.
- `ai/api/v1/` — routers AI : ai.py (summary, chat, stream, meal/glucometer image), voice.py.
- `diabetes/api/v1/schemas.py` — schémas Pydantic alignés sur les modèles Django.
- OpenAPI exposé sur `/api/docs` (Swagger UI).

**Auth :** Firebase JWT Bearer (`firebase_auth_backend`) **ou** Django session (`django_auth`) — les deux sont acceptés. Endpoints publics : `/auth/firebase`, `/demo/scenarios`, `/health`. Tout autre accès anonyme renvoie `401`.
**Filtrage patient :** chaque endpoint filtre par `patient=request.user`. Isolation garantie au niveau service.
**Pydantic :** versions des schémas sans breaking change ; tout changement incompatible oblige à publier `v2`.

## Conséquences

**Positives**

- Surface structurée prête pour les futurs consommateurs (mobile, intégrations partenaires, tests E2E).
- Documentation OpenAPI générée automatiquement.
- Typage strict sur les entrées et sorties (Pydantic).
- Le versioning explicite (`/v1/`) permet des évolutions sans casser les clients existants.

**Négatives**

- ~~Aujourd'hui l'API n'est consommée par aucun client~~ — **résolu** : Flutter est le seul client depuis Phase 3 (TD-010 fermé).
- Une dépendance supplémentaire (`django-ninja`). Ajoutée à `requirements.txt`.
- ~~Deux manières de lire les données (vues HTML + API)~~ — **résolu** : les vues HTML ont été supprimées en Phase 3.

## Garde-fous

- `django_auth` globalement au niveau `NinjaAPI`, pas par endpoint. Oublier `auth=` ne crée donc pas de fuite.
- Tests automatisés (voir `logs/tests/test_api.py` à partir de Pass 1) :
  - `401` anonyme sur chaque endpoint
  - isolation patient : user A reçoit 404 sur une ressource de user B
  - création d'une entrée via API crée une entrée filtrable dans le dashboard
- Pas de `@csrf_exempt` hors django-ninja (qui ne l'utilise pas par défaut côté session auth).
- `SECURITY.md` ou équivalent doit mentionner la surface API avant toute promotion prod.

## Alternatives rejetées

- **Django REST Framework** : choix le plus conservateur, mais plus verbeux (serializers + viewsets + routers) pour un bénéfice marginal sur notre périmètre. Revisité si une intégration partenaire impose DRF.
- **Pas d'API formelle, continuer à renvoyer du HTML** : bloque la mobile app et les intégrations ; pousse la dette plus loin.
- **FastAPI externe** : rupture complète avec le monolithe Django, charge opérationnelle double. Pas justifié au MVP.

## Suivi

- ~~TD-010~~ : résolu — Flutter consomme intégralement l'API depuis Phase 3.
- ~~TD-005~~ : résolu — `ci.yml` GitHub Actions intègre `pytest` sur l'API.
- Post-MVP : v2 probable quand FHIR sera introduit (Enterprise Architect).
