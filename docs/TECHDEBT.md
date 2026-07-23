# Tech Debt — Diabetes Log

Registre des dettes techniques identifiées mais non résolues. Une dette est un choix délibéré de court terme, pas une régression à cacher. Chaque entrée doit être résoluble ou explicitement acceptée.

**Convention :** ajouter une entrée au moment où la dette est créée ou découverte. Supprimer l'entrée quand la dette est payée (ne pas archiver, le git log fait foi).

---

## AI / LLM

### TD-002 — Migration vers Kimi 2.5 (Moonshot) comme provider premium

- **Créé :** 2026-04-17
- **Mis à jour :** 2026-06-03 — env var corrigée : `KIMI_API_KEY` (pas `MOONSHOT_API_KEY`). `llm/kimi.py` et `llm/factory.py` implémentés ; factory charge Kimi automatiquement si `KIMI_API_KEY` est défini.
- **Contexte :** Kimi 2.5 (Moonshot AI) est le provider premium cible — meilleur rapport qualité/prix, contexte 200K+ tokens, support natif français et arabe. L'infrastructure est prête (`KimiProvider`, factory), mais aucune clé n'est provisionnée.
- **Impact :** aucun runtime aujourd'hui (Gemini-only en production). Kimi est silencieusement ignoré.
- **Résolution prévue :** provisionner `KIMI_API_KEY` dans l'environnement (Phase 5). Vérifier `llm/kimi.py` avec clé réelle.
- **Owner :** Data/AI Engineer + Product Manager
- **Priorité :** moyenne — bloqué par Phase 5.

### TD-003 — Timeout et circuit breaker par appel LLM absents

- **Créé :** 2026-04-17
- **Mis à jour :** 2026-06-03 — couche d'abstraction livrée (`llm/factory.py`, `rate_guard.py`, `kimi.py`, `fallback.py`). Quota journalier Redis en place. Reste : timeout explicite par appel et circuit breaker.
- **Contexte :** `TEAM.md` directive Data/AI : timeout, retry exponentiel, circuit breaker. La factory gère le failover Gemini→Kimi→fallback et le quota journalier, mais aucun timeout per-call n'est configuré côté SDK Gemini, et il n'y a pas de circuit breaker si Gemini répond lentement sans erreur.
- **Impact :** risque de blocage patient si Gemini latence > quelques secondes sans timeout.
- **Résolution prévue :** ajouter `asyncio.wait_for` / `httpx.timeout` dans `GuardedGeminiProvider` ; circuit breaker léger (ex: `tenacity` ou compteur d'échecs/fenêtre glissante).
- **Owner :** Data/AI Engineer
- **Priorité :** moyenne — devient bloquante avant la GA.

---

## Plateforme / Runtime

### TD-023 — CI bandit : chemins d'exclusion obsolètes

- **Créé :** 2026-06-03
- **Contexte :** `.github/workflows/ci.yml` exclut `./tracking/tests,./amina/tests` du scan bandit. Ces répertoires ont été renommés (`tracking` → `diabetes`, `amina` → `engine`) lors du refactoring chassis. Les répertoires exclus n'existent plus ; bandit scanne maintenant les tests par inadvertance.
- **Impact :** bandit peut signaler des faux positifs sur les `assert` de test (B101) malgré le flag `--skip B101` — les deux mécanismes se chevauchent. Plus grave : si un nouveau test introduit du code dangereux, l'exclusion ne le bloque plus.
- **Résolution prévue :** mettre à jour le flag `-x` : `./diabetes/tests,./engine/tests`.
- **Owner :** DevOps Architect
- **Priorité :** haute — correction triviale, risque réel sur la couverture SAST.

---

## Qualité / Tests

### TD-007 — Aucun test de charge ni d'accessibilité

- **Créé :** 2026-04-17
- **Contexte :** `TEAM.md` (QA Lead) demande Locust (50 users simultanés, p95 < 2s), axe-core (WCAG 2.1 AA) et OWASP ZAP baseline. Aucun de ces outils n'est configuré.
- **Impact :** risques non mesurés sur performance, accessibilité patient (40 % de la population cible > 60 ans), conformité RGPD santé.
- **Résolution prévue :** axe-core en CI dès que la CI existe (TD-005). Locust et ZAP en jobs nightly après staging.
- **Owner :** QA Lead
- **Priorité :** moyenne, devient bloquante avant GA.

---

## Produit / UX

### TD-009 — Design candidate `log_form_ghost_elite.html` non intégré ✅ RÉSOLU (2026-06-16)

- **Créé :** 2026-04-17
- **Résolu :** 2026-06-16 — fichier supprimé lors du nettoyage docs. Le frontend est Flutter ;
  le HTML (résidu de l'ère templates Django) ne correspondait à aucune UI active. Les concepts UX
  (slider glycémie coloré, sélecteur repas) restent récupérables via git si besoin.
- **Owner :** UX Designer + PM

---

## Architecture

### TD-011 — ADR rétrospectifs incomplets

- **Créé :** 2026-04-17
- **Mis à jour :** 2026-06-03 — 7 ADR existent (0001–0007). Gap restant : décisions antérieures à H-MVP (migration Bootstrap → Tailwind → Flutter, architecture clinique hybride, pseudonymisation PHI).
- **Contexte :** les ADR 0001–0007 couvrent les choix structurels depuis H-MVP. Les décisions architecturales plus anciennes ne sont pas documentées.
- **Impact :** perte de contexte pour les nouveaux contributeurs sur les choix fondateurs.
- **Résolution prévue :** écrire les ADR manquants à partir du `git log` et du `PROJECT_LOG.md`.
- **Owner :** Software Architect + Technical Writer
- **Priorité :** basse — rétroactif.

---

## Sécurité / Conformité

### TD-012 — MFA non implémenté (admin, professionnels)

- **Créé :** 2026-04-17
- **Contexte :** `TEAM.md` (Security) : « MFA obligatoire pour les comptes admin et professionnels de santé ». Non implémenté. django-otp n'est pas dans `requirements.txt`.
- **Impact :** risque d'accès admin non autorisé à des données de santé. Probabilité faible (pas encore d'admins autres que le fondateur), gravité haute.
- **Résolution prévue :** ajouter django-otp + intégration TOTP, activer sur `is_staff` et futurs rôles « professionnel ». Bloquer avant la GA.
- **Owner :** Security Architect
- **Priorité :** haute avant GA, moyenne pendant le MVP.

### TD-015 — Scénarios de démo B à H manquants

- **Créé :** 2026-04-17
- **Contexte :** `AMINA_MVP_PLAN.md` §5 liste 8 scénarios de démo (A–H). `services/demo_scenarios.py::SCENARIOS` ne contient que le scénario A. Les scénarios B–H existaient dans l'historique git avant un pivot « Simplification pour le POC ».
- **Impact :** catalogue pauvre pour les démos multi-profils ; le séquencement anti-répétition n'est pas effectif.
- **Résolution prévue :** restaurer les 8 scénarios depuis l'historique git, cohérents avec les 7 détecteurs cliniques. Réintroduire le sélecteur anti-répétition (session key). Ajouter un test par scénario.
- **Owner :** Data/AI Engineer + Medical Advisor (validation)
- **Priorité :** moyenne — impact UX démo, pas de risque patient.

### TD-014 — Rate limiting `/login/` absent

- **Créé :** 2026-04-17
- **Contexte :** `TEAM.md` (Security) : django-axes + captcha après 3 échecs. Non installé. Le backend Django ne sert plus de vues HTML mais l'endpoint `/api/v1/auth/` reste exposé au brute-force.
- **Impact :** vulnérable au brute-force. Peu exploitable tant que la base utilisateur est minuscule, critique à > 100 MAU.
- **Résolution prévue :** throttling django-ninja sur les endpoints auth (`AnonRateThrottle`) ou django-axes.
- **Owner :** Security Architect
- **Priorité :** moyenne — durcir avant l'ouverture publique.

### TD-022 — Couverture lexique d'urgence : fautes d'orthographe non couvertes (gap connu, accepté)

- **Créé :** 2026-05-29
- **Contexte :** `triage_vital.py` détecte les urgences par matching exact sur 3 frozensets (FR, Darija Latin, Arabe script). Les variantes orthographiques courantes des termes haute-sévérité (ex : « kanmou » vs « kanmout », « غادي نموت » avec faute de frappe) passent au LLM sans interception.
- **Impact :** un patient en détresse qui fait une faute d'orthographe ne déclenche pas la réponse d'urgence fixe. Le LLM répond — 2-3s de latence et réponse moins déterministe qu'un template validé.
- **Garde-fou existant :** les regex numériques couvrent la majorité des urgences réelles avec un chiffre glycémique.
- **Décision :** Levenshtein rejeté (trop lâche → faux positifs → réponses alarmantes injustifiées). Approche retenue : table de variantes curées pour les termes haute-sévérité uniquement (mort/inconscience/idéation) + corpus de tests négatifs.
- **Priorité :** haute — bloquant avant pilote avec vrais patients.
- **Owner :** Backend / Safety

---

## Qualité / Suivi d'audit

### TD-024 — Suites de l'audit Fable (2026-06-12) — différé post-MVP

- **Créé :** 2026-06-16
- **Source :** `docs/assessments/2026-06-12-fable-assessment.md` (revue ingénierie 7,6/10).
- **Contexte :** items de qualité réels mais **non bloquants pour le MVP**. Regroupés ici pour
  éviter le scope creep sur le chemin critique (deploy → users → D90). À traiter après que le MVP
  mesure de la rétention, ou opportunément dans des PRs dédiées.
  - [ ] Paramétrer les requêtes `retention_sql.py` (`.format()` → params liés) — hygiène SQL (staff-only, input dev-contrôlé, donc non urgent).
  - [ ] `pytest-cov` avec seuil + `manage.py check` en CI ; `pip-audit` (audit dépendances).
  - [ ] i18n complet au-delà des écrans pilote (le minimum pilote est dans ROADMAP NOW).
  - [ ] Découper `add_log_sheet.dart` (~2 558 lignes) ; remplacer les `catch (_)` silencieux par une gestion typée + log.
  - [ ] Labels `Semantics` sur les lectures glycémiques (accessibilité lecteur d'écran).
  - [ ] Politique de rétention des données pour les événements d'observabilité (stockent `patient_id`) — RGPD.
- **Impact :** maintenabilité, couverture mesurée, accessibilité, hygiène. Aucun risque patient immédiat.
- **Priorité :** basse-moyenne — **explicitement après le MVP** (ne pas tirer en avant).
- **Owner :** Backend + Frontend
- **Note :** deux alertes de l'audit étaient des **faux positifs** vérifiés — clés réelles dans `.env`
  (seul `.env.example` est suivi) et « injection SQL » dans `retention_sql` (surévaluée). Ne pas les chasser.

---

## Comment utiliser ce fichier

1. **À la création d'une dette** — ajouter une entrée (ID `TD-NNN`, titre, date, contexte, impact, résolution prévue, owner, priorité).
2. **À la résolution** — supprimer l'entrée. Git log sert d'historique.
3. **En revue mensuelle** — l'équipe passe ce fichier en revue : les priorités changent, les contextes évoluent.
4. **Avant chaque release majeure** — valider que les dettes bloquantes (haute priorité) sont soldées ou re-priorisées explicitement.

Références : `TEAM.md` (rôles et directives), `SPECS.md` (périmètre), `ROADMAP.md` (trajectoire), `docs/adr/` (décisions structurelles).
