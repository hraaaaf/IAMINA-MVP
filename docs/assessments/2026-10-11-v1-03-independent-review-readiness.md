# IAMINA V1-03 — Pack de revue indépendante et gates pré-intégration

**Date :** 2026-10-11 | **Statut :** PREPARATION / non approuvé | **Données :** code, tests et fixtures synthétiques exclusivement.
**Périmètre :** #923 OCR, #924 refus IA, #925/#927 SSE/CSRF/ingress, #929 P3 dormant (décision A). Aucun traitement patient, aucun accès à des logs de production, aucun merge ou déploiement.

## 1. Baseline reconstruite en lecture seule

- `main@13b7cce12c86daf60119fb703f22e8c6c192cf8d` (branche de base réelle, sans handover V1-03).
- #932 `15cfe25fcc93fff00a1198d705fb683c7a2eb960` : 16/16 workflows success.
- #933 `6b75ac3e4e88c9337ed480631859fa363f30f8bc` : branche documentaire, **zéro workflow pull_request trouvé sur ce HEAD exact** à la reprise ; anciens 16/16 = autres SHAs.
- #934 `f0b02165b478db6b6bb25d33f534a502ffa542f8` : 19/19 success ; refus IA persistant **par installation**, pas révocation globale.
- #935 `5f2378ee7935bb64b5af850b6bfb2e68a9a49ebe` : 16/16 success ; GET SSE legacy 405 sans Location/provider, OpenAPI POST JSON.
- #936 `62cc18bc0266838a98bbd7fe6b3ad8c794c82938` : 16/16 success ; trace ancienne de timing bootstrap.
- #937 `4d287bb1c8049b416b7e0f2c7ad5aa031c370ca7` : 16/16 success ; CI #38174457859 6/6 jobs success ; base #936, ahead 2 / behind 0, 7 fichiers. Toutes six PR DRAFT, ouvertes, fusionnables, **non fusionnées** lors du contrôle.
- ADR-0009 **ACCEPTED** : `/api/v1/diabetes/*` réservé/dormant pour V1 ; seul l'API canonique est exposée. Les tests #937 vérifient absence OpenAPI/resolver, 404 même avec urgence synthétique, absence d'appel fournisseur et triage du chat canonique.

Ces chiffres attestent des runs GitHub associés aux HEAD ci-dessus, **pas** d'une exécution locale dans cette reprise, ni d'un avis clinique, privacy ou sécurité indépendant. Toute mutation de HEAD invalide le transfert de preuve.

## 2. Vue adversariale A — transport, vie privée, compatibilité

| Risque à démontrer ou exclure | Preuve actuelle | Test / pièce de preuve à obtenir | Verdict |
| --- | --- | --- | --- |
| Ancien GET SSE transporte message dans URL | #935 : GET `?message=<marqueur synthétique>` refuse 405 sans redirect, sans réponse reflétée ni provider | Inventaire des clients **réellement diffusés**, SemVer/build, date de retrait GET ; plan d'upgrade vers POST JSON **sans jamais réactiver GET** | OPEN : clients non inventoriés |
| Proxy/CDN/WAF/APM conserve URL, body ou headers sensibles | `vercel.json` et CI ne décrivent pas les réglages effectivement en place ; inspection Vercel antérieure limitée aux identités de projets | Autorisation accès configs, export minimal des règles de collecte, redaction et rétention, puis requête synthétique à marqueur et contrôle de toutes les destinations ; ne pas ouvrir de log patient | OPEN : preuve infrastructure absente |
| Décision de compatibilité retourne une compatibilité fictive | `backend/core/app_compatibility.py` renvoie `version_unknown / compatible=None / update_required=False` si métadonnées absentes ; `frontend/pubspec.yaml` = `0.1.0+1` | Démontrer qu'un vrai ancien client envoie version/build, que le client actuel consulte la politique, et qu'aucune transition vers GET n'est suggérée | OPEN : distribution inconnue |
| Consentement/refus IA se perd au redémarrage ou sort du périmètre | #934 : tests Flutter/store/route et UI synthétique ; périmètre **installation**, pas cross-device | Matrice vrai iOS, Android, PWA : refus → redémarrage → hors ligne → appel chat/voix/image interdit ; second appareil indépendant ; réacceptation explicite ; changement d'identité et nettoyage local contrôlés | OPEN : appareils réels/non-patient |

**Contrôles négatifs requis en contexte autorisé :** cookie+Bearer falsifié, CSRF absent/invalide, chat urgent, déconnexion ou rupture SSE au milieu d'un flux, scope fournisseur relâché en erreur, et vérification que les journaux ne conservent pas de marqueur synthétique. Respecter le modèle de menace sur redirects et paramètres de requête ; un HTTP 405 **n'efface pas** la query déjà visible à l'ingress.

## 3. Vue adversariale B — provenance, clinique, UX

| Risque | Observation issue des sources | Gate de preuve |
| --- | --- | --- |
| OCR invente unité/mesure | #932 exige unité explicite, backend et Dart ; aucune preuve optique réelle | Corpus de photos glucomètres synthétiques/autorisées, unité visible, double/aucune unité, valeurs multiples, confusion date/série/mesure, résultat `null` quand non prouvé |
| HI/LO présenté comme concentration exacte | `GlucoseOcrShield` fournit `value=null`, drapeau HI/LO, confidence 1.0 de détection textuelle | Revue clinicien : copie, urgence/triage, refus d'une valeur numérique fabriquée |
| 401–600 mg/dL interprété silencieusement | Regex Dart `([4-9]\\d|[1-3]\\d{2}|400)` ne couvre pas 401–600 malgré commentaire | Arbitrage clinique avant toute correction de plage ; ne pas accepter via simple assouplissement regex |
| Texte reconnu sauvegardé sans confirmation | `needsConfirmation` peut être `false` sur valeur unitaire à confiance forte ; aucun parcours UI connecté prouvé dans l'inventaire ciblé | Si une activation future est approuvée : UI séparée de confirmation, annulation = zéro écriture DB, suivi provenance/unités et journaux sans PHI |
| Module dormant rouvert accidentellement | #937 retire montage dynamique, aligne manifeste/triage | Test HTTP et schéma sur branche intégrée, ne jamais interpréter l'absence de route comme validation CSRF d'une route future |

**Avant activation UI :** feature flag OFF par défaut, BEFORE/target/AFTER mêmes 390×844, 768×1024 et 1280×900, FR/AR/Darija et RTL pertinent, text scaling/accessibilité, tests vrai appareil. Aucun score visuel/clinique ne peut être attribué avant rendu observé et approbation.

## 4. Plan d'intégration sans merge — conflits et preuves

- **Empilement démontré :** #932 → #936 → #937. **Parallèles :** #933 (OCR/doc/ADR/roadmap), #934 (consentement UI), #935 (SSE). Ne pas concaténer les verts individuels comme un run d'intégration.
- Les changements partagés de `frontend/lib/services/api_client.dart` (#934 et composants parent) et des contrats auth/triage nécessitent une **comparaison diff effective sur branche candidate intégrée** ; aucun test d'intégration croisée n'a été lancé ici.
- Une intégration future doit disposer de : décision/autorisation de merge ; ordre de dépendances explicitement revu ; branche d'intégration ou cherry-picks traçables ; tests réels collectés au **nouveau HEAD** (Django SQLite/PostgreSQL, CSRF/egress, Flutter, OCR refus, UI, CI, migrations) ; audits indépendants privacy/sécurité/clinique ; confirmation finale.
- **Ne pas** basculer des bases vers `main` pour les laisser ainsi après CI ; éviter aussi tout merge, Vercel, accès PHI, activation P3 ou patient réel sans human gate.
- Les gates P5-6A/#318 et P5-6B/#320, le gel de release, réglementation/processor et autorisation patient restent distincts.

## 5. Critères de sortie / propriétaire des preuves

1. **Sécurité/privacy (humain qualifié) :** confirmer ingress/processeurs/consentement/CSRF, prouver minimisation et rétention, statuer sur les résidus. Toute détection de PHI non autorisé = BLOCKER.
2. **Clinicien qualifié :** matrice OCR HI/LO/401–600, unité, validation du libellé et de l'absence d'autosave ; aucune règle clinique inventée par test/code.
3. **QA vraie plateforme :** iOS, Android et PWA hors ligne, redémarrage, multi-instance, réacceptation ; résultats identifiés appareil/build/HEAD, sans patient réel.
4. **Certifieur indépendant :** comparer exigences→tests réellement exécutés, skips, HEAD, preuves visuelles, restrictions, décisions/risques ; autorisation de fusion séparée.
5. **Avant patient réel :** gates P5 et décision clinique/privacy/légale/release expressément validés.

**Verdict de cette reprise :** préparation de review pack uniquement ; **aucune nouvelle exécution de tests**, aucune preuve de vrais appareils/infra/clinique ; `NOT_RELEASE_AUTHORIZED`.

**Fichier de reprise :** `docs/handovers/2026-10-11-iamina-v1-03-option-a-p3-dormant-handover.md`. **Roadmap :** `docs/ROADMAP.md`, dans PR DRAFT #933, distinct du `main` en cours.
