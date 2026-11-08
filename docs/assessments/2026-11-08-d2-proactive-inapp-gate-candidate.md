# IAMINA — D2 — Politique proactive in-app, candidate isolée

**08/11/2026 | Statut : DRAFT / SYNTHETIC-ONLY / NON MONTÉ / NON CERTIFIÉ.**  
**Décision D2 validée par le propriétaire :** la cloche en haut à droite regroupe les notifications **événementielles + proactives** de l'application. **D3** désigne les rappels affichés en bas de l'accueil, **sans duplication** dans la cloche.

## 1. BEFORE — sources auditées

- Main initial exact : `0a096ac195d79b494e8f2722be95c3b54396cd2d`. `backend/diabetes/services/clinical/proactive_intelligence.py` dispose déjà du budget **1 observation descriptive non urgente / 24 h** et `backend/diabetes/api/v1/proactive.py` sépare lecture GET du POST d'évaluation. **Ces points ne sont ni une notification envoyée ni une preuve de proactivité D2.**
- [PR historique D2 #1135](https://github.com/hraaaaf/IAMINA-MVP/pull/1135) **OPEN/DRAFT** : `frontend/lib/services/d2_notification_policy.dart` est une **autorisation d'aperçu seulement** ; le centre de consentement et la boîte `D2InAppNotice` sont candidats non intégrés. Le « Save governed preview » est une **action du patient**, pas une vraie génération spontanée. Aucune livraison push.
- [PR W01+D2 #1153](https://github.com/hraaaaf/IAMINA-MVP/pull/1153) **OPEN/DRAFT** : intégration trop large pour requalifier D2 seule. [Issue #1161](https://github.com/hraaaaf/IAMINA-MVP/issues/1161) : E2E hébergés et nettoyage applicatif reportés.
- La politique de rétention J+7 dans l'ancien candidat cache les avis expirés ; la **suppression physique programmée n'est pas certifiée**. Ne pas réintroduire le sujet Neon/migration C7 dans ce sous-lot.

## 2. Goal / Success / Proof de ce sous-lot D2

**GOAL :** exprimer et tester de façon déterministe *l'admissibilité théorique* d'un candidat proactive D2, sans ouvrir d'API d'envoi. Cette branche prépare le contrat futur de génération et **n'implémente pas encore la cloche**.

**SUCCESS ciblé :** un appel *pur* rejette les rappels D3, les époques d'identité périmées, le compte différent, l'opt-in absent/retiré, les sources inconnues, les contenus urgents/thérapeutiques ou sensibles, les horodatages invalides, les répétitions et dépassements des plafonds. Il ne produit **aucun** effet de bord.

**PROOF :** `backend/core/d2_proactive_gate_candidate.py` + `backend/core/tests/test_d2_proactive_gate_candidate.py` ; workflow dédié `.github/workflows/d2-proactive-candidate.yml` (Python 3.12, sans DB/secrets/patients). CI exacte SHA à vérifier ; tests Django SQLite/PostgreSQL et autres gates requis par la CI générale, si déclenchés.

## 3. Contrat de contrôle de proactivité — proposition technique, pas licence d'envoi

- Seule surface `in_app_notification`, type `proactive` ; `reminder`, `browser_push` et `companion_conversation` **REFUS**.
- Exiger l'identité patient non vide et cohérente, epoch courant, déverrouillage, **opt-in local et consentement serveur positif**, catégorie activée et absence d'opt-out IA global.
- Accepter seulement deux **types hypothétiques non cliniques** : `weekly_report_ready`, `profile_completion_available`. Un producteur n'existe **pas** dans ce lot ; même `source_verified=true` dans une fixture ne prouve aucun événement réel. Ne jamais générer de notification si les fonctions en question n'existent pas.
- Toute provenance absente, signature absente, contrat inconnu, notification d'urgence, proposition thérapeutique, ou aperçu sensible est refusé. La vraie intégration future devra **revalider côté serveur**, sans se fier à un booléen de l'appelant.
- **Cadence candidate non certifiée :** maximum **2 proactives sur 7 jours glissants** et **1 sur 24 h glissantes**, même événement non répété pendant 7 jours, preuve de moins de 7 jours. Les avis événementiels factuels hors proactivité sont un contrat **séparé**, non soumis à ces plafonds. Aucun travail Cron/scheduler.
- La fonction renvoie `candidate_only_not_delivery` au mieux. Elle ne crée ni enregistrement, ni « notification reçue », ni permission push et ne touche aucune donnée patient.

**Concurrence critique en attente :** en production, les quotas/révocations/idempotence nécessiteraient une transaction atomique **par patient**, des signatures uniques, une séparation stricte des comptes et des preuves de purge. Le prototype pur n'est **pas** un verrou de concurrence ni une source d'autorité.

## 4. FUE futur sur décision D2 complète — NON EXÉCUTÉ

| Scénario Web requis ultérieurement | État |
|---|---|
| Cloche en haut, inbox honnête vide / lue / non lue ; D3 reste en bas de l'accueil | NOT_RUN |
| Événement compte/action réellement constaté, sans notification fictive | NOT_RUN |
| Consentement proactive OFF, ON explicite puis révocation et état persistant | NOT_RUN |
| Limites de cadence, absence de répétition, fraude d'identité et A→B→A | NOT_RUN |
| Décrochage navigateur, offline, vieille session, erreurs et double-clic | NOT_RUN |
| FR/AR RTL, clavier, 390×844 / 768×1024 / 1280×900 et zoom 200 % | NOT_RUN |
| Sécurité/privacy/clinique, rétention et preuve d'absence de livraison externe | NOT_RUN |

Aucune note visuelle sans captures BEFORE/AFTER. Le sous-lot actuel n'a pas de composant visuel modifié : FUE navigateur **non applicable à cette PR seulement**, mais **obligatoire pour clôturer D2**.

## 5. Gates, revue critique et Next

**Safety:** pas de données patients, schéma, Neon, C7, CGM, notifications réelles, traitements, seuils médicaux, Vercel ni merge. La branche ne prouve ni W01/W02 sécurité ni la permission de notifier. Les indicateurs et types d'événements sont encore hypothétiques.

**Revue adversariale :** tester notamment fiabilité de `source_verified` (ne vaut pas attestation), TOCTOU de l'opt-out, quotas concurrents (non traités en dry-run), état hors-ligne/compte différent et sémantique J+7. **NO-GO** pour une implémentation patient tant que ces points, FUE et revues indépendantes ne sont pas clos.

**NEXT exact :** vérifier CI du SHA final, examiner le diff et conserver PR Draft ; puis réaliser un **second** sous-lot D2 pour intégrer des sources non cliniques réellement attestées et leur persistance avec consentement et transaction atomique après résolution des gates d'identité, jamais en recopiant un vieux scheduler.

**Canonique Notion :** [01 — ROADMAP CANONIQUE, D2](https://app.notion.com/p/3df77c66336281f5b308ec17f7f0a63b).
