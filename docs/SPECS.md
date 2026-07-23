# Spécifications et fonctionnalités — Diabetes Log POC

Ce fichier décrit les spécifications actuelles et sert de guide pour le développement.
Mettre à jour ce fichier à chaque évolution des fonctionnalités.

**Architecture actuelle :** Flutter frontend (PWA + iOS + Android) + Django Ninja backend (API JSON uniquement). Il n'existe plus de vues Django ni de templates HTML — tout le UI est Flutter.

---

## Statut des fonctionnalités

### Authentification et session

| Fonctionnalité | Statut | Notes |
|----------------|--------|-------|
| Firebase Auth (JWT Bearer) | Fait | Flutter → Firebase → `POST /api/v1/auth/firebase` → Django User |
| Création de compte automatique | Fait | `_resolve_user` crée le User Django si firebase_uid inconnu |
| Inscription en libre-service | Hors périmètre | Via Firebase Auth uniquement |
| Réinitialisation de mot de passe | Hors périmètre | Délégué à Firebase Auth |

### Profil patient

| Fonctionnalité | Statut | Notes |
|----------------|--------|-------|
| Onboarding pas à pas (Flutter) | Fait | 7 étapes, une question par écran, auto-avance sur sélection |
| Type de diabète | Fait | Type 1, Type 2, Gestationnel, Prédiabète |
| Traitement dynamique (ADA) | Fait | Filtré selon le type : T1=insuline, T2=tout, prédiabète=oral+régime, gestationnel=insuline+oral |
| Genre | Fait | Homme / Femme |
| Cible glycémique personnalisée | Fait | Défaut ADA : 70–180 mg/dL |
| Unité de mesure (mg/dL, mmol/L) | Fait | Stocké + conversion au save (mmol/L → mg/dL) |
| Date de naissance | Fait | Sélecteur de date Flutter |
| Poids et taille | Fait | Champs optionnels |
| Langue préférée | Fait | fr / ar-MA / ar (3 options) |
| Modifier le profil | Fait | `PATCH /api/v1/profile` |

### Saisie des données (Flutter)

| Fonctionnalité | Statut | Notes |
|----------------|--------|-------|
| Mode express (défaut) | Fait | Glycémie + type repas = 3 taps ; `_expressMode = true` par défaut |
| Mode détaillé | Fait | Toggle expand → insuline, aliments, santé |
| Glycémie — curseur avec gradient | Fait | Rouge → vert → orange → rouge, 30–400 |
| Glycémie — saisie manuelle | Fait | Champ texte, 30–600 |
| OCR glycémie (caméra) | Fait | `image_picker` + `google_mlkit_text_recognition` + `glucose_ocr_shield.dart` |
| Insuline — stepper +/- | Fait | Pas de 0.5, suggestions rapides |
| Aliments — chips sélectables | Fait | Recherche + chips libres |
| Reconnaissance repas par photo | Fait | `POST /api/v1/ai/analyze-meal-image` (Gemini Vision) |
| Type de repas | Fait | À jeun, Petit-déj., Déjeuner, Dîner, Collation |
| Exercice / Sommeil / Stress | Fait | Icônes toggle |
| Fatigue + maladie | Fait | 1er log de la journée uniquement |
| Heure personnalisée | Fait | Toggle « Maintenant » / DateTimePicker Flutter |
| Sauvegarde locale (Drift) | Fait | Offline-first, sync batch vers `/api/v1/logs/batch` |
| Modifier une entrée | Fait | `PATCH /api/v1/logs/{id}` |
| Supprimer une entrée | Fait | Swipe-to-delete + `DELETE /api/v1/logs/{id}` |

### API REST — Django Ninja ✅

Toutes les routes sont sous `/api/v1/`. Authentification : Firebase JWT Bearer (sauf endpoints marqués ❌ Public).

#### Authentification & compte

| Endpoint | Méthode | Auth | Statut | Notes |
|----------|---------|------|--------|-------|
| `/auth/firebase` | POST | ❌ Public | ✅ | Firebase JWT bridge — crée User si nouveau |
| `/profile` | GET | ✅ Bearer | ✅ | Récupère PatientProfile |
| `/profile` | PATCH | ✅ Bearer | ✅ | Met à jour le profil |
| `/account/consent` | GET | ✅ Bearer | ✅ | Statut consentement RGPD |
| `/account/consent` | POST | ✅ Bearer | ✅ | Donne le consentement |
| `/account/consent` | DELETE | ✅ Bearer | ✅ | Retire le consentement |
| `/account` | DELETE | ✅ Bearer | ✅ | Supprime le compte (RGPD) |

#### Logs & sync

| Endpoint | Méthode | Auth | Statut | Notes |
|----------|---------|------|--------|-------|
| `/logs` | GET | ✅ Bearer | ✅ | Paginé (page + page_size) |
| `/logs` | POST | ✅ Bearer | ✅ | Crée un LogEntry |
| `/logs/batch` | POST | ✅ Bearer | ✅ | Sync offline Drift → backend (idempotent via client_uuid) |
| `/logs/{id}` | GET | ✅ Bearer | ✅ | Récupère un log |
| `/logs/{id}` | PATCH | ✅ Bearer | ✅ | Met à jour un log |
| `/logs/{id}` | DELETE | ✅ Bearer | ✅ | Supprime un log |
| `/kpis/` | GET | ✅ Bearer | ✅ | KPIs cliniques SQL (TIR, GMI, CV, GRI, AGP percentiles) — cachés Redis |

#### Documents & import

| Endpoint | Méthode | Auth | Statut | Notes |
|----------|---------|------|--------|-------|
| `/documents/ingest` | POST | ✅ Bearer | ✅ | Upload PDF/image → Gemini OCR → preview (batch_id Redis) |
| `/documents/confirm/{batch_id}` | POST | ✅ Bearer | ✅ | Valide l'import → crée LogEntry + LabReport |
| `/documents/` | GET | ✅ Bearer | ✅ | Liste LabReports du patient |
| `/import/librelink` | POST | ✅ Bearer | ✅ | Import CSV LibreLink → LogEntry en masse |

#### IAmina / AI

| Endpoint | Méthode | Auth | Statut | Notes |
|----------|---------|------|--------|-------|
| `/ai/summary` | POST | ✅ Bearer | ✅ | POST `{days: 21}` → résumé clinique Gemini Flash + patterns |
| `/ai/doctor-brief` | GET | ✅ Bearer | ✅ | Rapport médecin structuré (14 jours) |
| `/ai/chat` | POST | ✅ Bearer | ✅ | POST `{message}` → réponse IAmina + conversation_id |
| `/ai/chat/stream` | GET | ✅ Bearer | ✅ | SSE streaming — `?message=...&context_days=14` |
| `/ai/voice` | POST | ✅ Bearer | ✅ | Audio → transcription → parsing glycémie/contexte |
| `/ai/transcribe` | POST | ✅ Bearer | ✅ | Audio → texte (pas de parsing) |
| `/ai/analyze-meal-image` | POST | ✅ Bearer | ✅ | Photo repas → `{foods: [string]}` (Gemini Vision) |
| `/ai/analyze-glucometer-image` | POST | ✅ Bearer | ✅ | Photo lecteur → glycémie numérique (OCR web) |

#### Démo & ops

| Endpoint | Méthode | Auth | Statut | Notes |
|----------|---------|------|--------|-------|
| `/demo/scenarios` | GET | ❌ Public | ✅ | Scénario A uniquement (B–H manquants — TD-015) |
| `/health` | GET | ❌ Public | ✅ | Statut DB + Redis ; 503 si dégradé |

**Documentation :**
- OpenAPI: `python manage.py export_openapi` (backend/)
- Tests : 764 fonctions de test (3 xfailed), couverture ~70 %

### Tableau de bord Flutter

| Fonctionnalité | Statut | Notes |
|----------------|--------|-------|
| NavigationBar 4 destinations | Fait | GoRouter ShellRoute — Dashboard / Journal / IAmina / Profil |
| Dernière mesure (hero card) | Fait | Code couleur, badge, temps relatif |
| KPIs (TIR, GMI, CV) | Fait | Badges GMI confidence (high/medium/low/null) |
| Graphique AGP | Fait | CustomPainter Flutter — bandes p5/p25/p50/p75/p95 |
| Entrées groupées par jour | Fait | 3 dernières semaines, triées par heure |
| Edit / delete entrée | Fait | Tap to edit, swipe-to-delete |
| Sheet IAmina post-save | Fait | Ouvre automatiquement après sauvegarde d'un log |
| Seed guard (données démo) | Fait | `kDebugMode` uniquement |

### IAmina (moteur IA)

| Fonctionnalité | Statut | Notes |
|----------------|--------|-------|
| Branding « IAmina » | Fait | — |
| Seuil d'activation | Fait | ≥ 5 entrées sur les 7 derniers jours |
| Moteur clinique hybride | Fait | `backend/engine/` — détection Python + reformulation Gemini Flash + fallback template |
| LLM actif | Fait | Gemini 2.5 Flash via `llm/factory.py` (`GuardedGeminiProvider`) |
| Détection de patterns | Fait | 7 patterns : aube, hypo post-effort, stress, sommeil, CV élevé, sensibilité alimentaire, Somogyi |
| KPI cliniques | Fait | GMI (ADA), TIR %, écart-type, CV %, GRI, Battelino |
| Chat contextuel (REST + SSE) | Fait | `/api/v1/ai/chat` (POST) + `/api/v1/ai/chat/stream` (SSE) |
| Pseudonymisation PHI | Fait | `backend/llm/pseudonymizer.py` — tokens UUID avant envoi LLM, unmask au retour |
| Résumé de secours (fallback) | Fait | `QuotaExhaustedProvider` → templates statiques |
| Cache du résumé | Fait | Réutilise si existant < 7 jours |
| Darija (ar-MA) | Fait | Strings Darija sur 8 détecteurs cliniques + réponses d'urgence Darija |
| Triage urgences | Fait | `TriageVitalMiddleware` — gate medical pre-LLM, réponse fixe validée |
| Mémoire persistante | Fait | `IAminaMemorySnapshot` + `IAminaDeepMemorySnapshot` en DB |
| Doctor brief | Fait | `/api/v1/ai/doctor-brief` — rapport structuré 14 jours |
| Résumé en arabe classique | À faire | Backend non implémenté |
| Failover Kimi | Bloqué | `llm/kimi.py` implémenté — en attente de `KIMI_API_KEY` (Phase 5) |

### Administration Django

| Fonctionnalité | Statut | Notes |
|----------------|--------|-------|
| Admin activé | Désactivé par défaut | `ENABLE_DJANGO_ADMIN=True` pour activer (opt-in) |
| Liste patients | Fait | Si activé : logs, profils inline |
| Résumés IA | Fait | Si activé : liste avec aperçu |

---

## Modèle de données

### PatientProfile (app `diabetes`)
```
patient             → User (1:1, CASCADE)
diabetes_type       : type1 | type2 | gestational | prediabetes
treatment_type      : insulin_pump | insulin_injections | oral_meds | diet_exercise
gender              : male | female
target_range_low    : int (défaut 70)
target_range_high   : int (défaut 180)
unit_preference     : mg_dl | mmol_l
date_of_birth       : date
weight              : decimal (nullable)
height              : int (nullable)
preferred_language  : fr | ar-MA | ar (défaut fr)
firebase_uid        : str (unique, nullable, indexed)
premium_valid_until : datetime (nullable)
created_at          : datetime (auto)
updated_at          : datetime (auto)
```
Note : `PatientProfile` étend `HealthPatient` (app `clinical`).

### LogEntry (app `diabetes`)
```
patient           → User (N:1, CASCADE)
created_at        : datetime (auto)
logged_at         : datetime (nullable) — heure personnalisée
meal_type         : fasting | breakfast | lunch | dinner | snack | ''
blood_sugar       : decimal (30–600 mg/dL)
insulin_units     : decimal (0–100, nullable)
meal_description  : text (vide autorisé)
meal_items        : JSON (liste d'aliments — mode détaillé)
exercised         : yes | no
sleep_quality     : good | bad
stressed          : yes | no
fatigue_level     : none | mild | moderate | severe (1er log du jour)
is_sick           : bool (1er log du jour)
source            : manual | voice | cgm | import | demo (défaut manual)
client_uuid       : UUID (unique, nullable, indexed) — idempotence sync Drift
```
Note : `daily_wellness` JSONField supprimé — les colonnes scalaires font foi.

### AISummary (app `diabetes`)
```
patient        → User (N:1, CASCADE)
created_at     : datetime (auto)
language       : fr | ar
summary_text   : text
logs_analyzed  : int
```

### AIChatMessage (app `diabetes`)
```
patient        → User (N:1, CASCADE)
role           : user | assistant
message        : text
created_at     : datetime (auto, indexed)
prompt_hash    : str (dédup)
```

### IAminaMemorySnapshot (app `diabetes`)
```
patient        → User (1:1)
data_json      : JSON
updated_at     : datetime (auto)
```

### IAminaDeepMemorySnapshot (app `diabetes`)
```
patient        → User (1:1)
data_json      : JSON
updated_at     : datetime (auto)
```

### LabReport (app `diabetes`)
```
patient                   → User (N:1)
created_at                : datetime (auto)
total_cholesterol_mgdl    : float (nullable)
(+ autres biomarqueurs)
glucose_readings_imported : int (LogEntry créés depuis ce document)
```

### DemoFeedback (app `diabetes`)
```
patient        → User (N:1, nullable)
was_surprised  : bool
comment        : text (vide autorisé)
scenario_id    : str (A..H)
created_at     : datetime (auto)
```

### AuditLog (app `diabetes`)
```
created_at     : datetime (auto, indexed)
actor          → User (SET_NULL, nullable)
action         : login | logout | view | create | update | delete | export
resource_type  : str
resource_id    : str (nullable)
metadata       : JSON (jamais de PHI en clair)
ip_address     : inet (nullable)
user_agent     : str (max 512)
```
Rétention 6 ans (RGPD santé). Jamais modifié à la main.

---

## Règles métier

1. **Profil obligatoire** — un patient sans profil est redirigé vers l'onboarding Flutter
2. **Onboarding pas à pas** — 7 étapes avec logique conditionnelle (traitement filtré par type de diabète selon ADA)
3. **IAmina** — activé après ≥ 5 entrées dans les 7 derniers jours
4. **Cache résumé** — un résumé existant de moins de 7 jours est réutilisé
5. **Fallback LLM** — si Gemini échoue ou quota atteint, `QuotaExhaustedProvider` retourne un template statique
6. **Permissions** — un patient ne peut voir/modifier/supprimer que ses propres entrées
7. **Horodatage** — `effective_time` retourne `logged_at` si défini, sinon `created_at`
8. **Traitement ADA** — Type 1 : pompe + injections ; Type 2 : tout ; Gestationnel : pompe + injections + oral ; Prédiabète : oral + régime
9. **Dashboard** — 3 dernières semaines d'entrées, groupées par jour, triées par heure
10. **Graphique AGP** — CustomPainter Flutter avec bandes p5/p25/p50/p75/p95 (SQL PERCENTILE_CONT / interpolation Python sur SQLite)
11. **Lifestyle conditionnel** — `fatigue_level` et `is_sick` uniquement au premier log de la journée
12. **Fenêtre clinique** — 21 jours analysés pour le résumé IAmina ; TIR segmenté (hypo/basse/cible/élevée/hyper)
13. **Scénarios démo** — scénario A disponible ; B–H à restaurer (TD-015)
14. **Urgences** — `TriageVitalMiddleware` intercept avant tout appel LLM ; réponse fixe validée médicalement
15. **KPIs** — SQL-first, jamais calculés en Python (ADR-0007)
16. **Offline-first** — Drift local → batch sync via `POST /api/v1/logs/batch` (idempotent via `client_uuid`)

---

## Conventions de code

### Backend (Django Ninja)
- **Langue utilisateur** : tout texte visible par le patient est en français (ou Darija/arabe selon `preferred_language`)
- **LLM input** : English Pivot Text uniquement, jamais données brutes patient (ADR-0007)
- **Vues** : aucune — tout passe par `django-ninja` sous `/api/v1/`
- **Services** : tout appel LLM dans `engine/` ou `llm/` — aucun appel SDK dans une view
- **Erreurs LLM** : `except Exception → log → FallbackProvider` (template statique)
- **KPIs** : SQL pur dans `diabetes/api/v1/kpis.py` — voir ADR-0007
- **Sécurité** : `TriageVitalMiddleware` et `UnitGuardMiddleware` non contournables

### Frontend (Flutter)
- **Branding IA** : « IAmina » (pas « IA », « AI », « Amina »)
- **Navigation** : `GoRouter 14` + `ShellRoute` — `NavigationBar` 4 destinations
- **State** : Provider — `context.read` dans les callbacks, `context.watch` dans `build`
- **Offline** : Drift 2.20 avec `MigrationStrategy` (schemaVersion courant : 3)
- **API client** : retry 5xx avec backoff, refresh 401 automatique
- **Touch targets** : ≥ 44px (WCAG)

Références : `TEAM.md` (rôles), `ROADMAP.md` (trajectoire), `docs/adr/` (décisions structurelles), `docs/TECHDEBT.md` (dettes).
