# IAMINA B — D24 IA OFF / consentement média — préflight et revue requise (03/11/2026)

## Décision et objectif
- **Décision D24** : une révocation de consentement IA / média doit empêcher tout nouvel appel fournisseur, même après création d'un scope ou lors d'un retour de session A/B/A.
- **Succès préflight technique** : zéro appel provider sans consentement global versionné et grant propriétaire `meal_vision/image`, y compris retrait pendant un scope déjà ouvert ; tests identiques SQLite et PostgreSQL 16.
- **Preuve** : [PR Draft #1244](https://github.com/hraaaaf/IAMINA-MVP/pull/1244), HEAD **2cab1bdc51c03a67faf99319920678d2c5c8129d**, [workflow ciblé #41678663408](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41678663408) **SUCCESS : 32/32 SQLite, 32/32 PostgreSQL 16**. [Migration drift #41678663081](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41678663081) SUCCESS.
- **Statut release : NO-GO**. [CI générale #41678662591](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41678662591) FAILURE : **42 échecs SQLite et 42 PostgreSQL 16** liés aux règles expirées ; les 32 tests de ce scope ne permettent pas de qualifier la production.

## Contrat média vérifié au niveau du code
- `backend/core/ai_egress.py` : contrôle central sur patient, purpose, modality, consentement global et grant média explicite.
- `backend/diabetes/api/v1/profile.py` : API existante `GET /profile/ai-media-consents`, `PUT /profile/ai-media-consents/{purpose}/{modality}`, `DELETE /profile/ai-media-consents/{purpose}/{modality}`. Le couple `meal_vision/image` est dans la matrice ; pas de droit hérité d'un compte à un autre.
- `backend/core/api/v1/account.py` : retrait IA global révoque également tous les grants média ; un nouvel accord global ne restaure pas automatiquement d'anciens grants.
- `backend/core/tests/test_ai_egress.py` + `backend/core/tests/test_media_consent_api.py` : 32 tests dont vérifications D24 spécifiques global OFF, scope déjà ouvert, grant manquant, révocation média, API propriétaire A/B/A et reconsentement. **Les tests synthétiques ne sont pas une autorisation de transfert à un prestataire IA.**

## Gate de revue des trois politiques — aucun auto-renouvellement
Toutes les dates d'échéance observées sont au **02/11/2026** (date actuelle 03/11/2026). Les validateurs exigent une revue courante, et ne doivent pas être neutralisés.

| Politique | Source | Responsable indiqué dans le code | Contenu à revoir avec preuve |
| --- | --- | --- | --- |
| Mode urgence | `backend/core/emergency_operating_mode.py` | IAmina Safety & Compliance | Mode `SELF_CARE_ONLY`, **pas de surveillance humaine automatique** ; exactitude des disclosures FR/EN/AR/Darija, contacts/limites et escalade |
| Réponse aux incidents | `backend/core/incident_response.py` | IAmina Safety & Security | Chaîne et noms des 5 rôles, sévérités SEV1–SEV4, objectifs de délais, détection, notification et traçabilité |
| Rétention/suppression | `backend/core/retention_policy.py` | IAmina Privacy & Security | Six catégories : médias bruts IA 0 jour, staging export 7 j, jetons reset 1 j, enregistrements patients 30 j, logs sécurité 2190 j, sauvegardes 35 j. Confirmation juridique et preuves de suppression/hold |

**Gate humaine :** responsable clinique/Safety, sécurité et confidentialité/juridique doivent examiner les pièces et confirmer explicitement la validité ou corriger les règles de fond. Seulement après signature/validation traçable, saisir de **vraies** nouvelles dates de revue avec références de preuve et relancer la CI complète. Une modification de date pour faire passer les tests serait une fausse validation.

## À exécuter après revue autorisée
1. Contrôler branche, HEAD, politiques réellement approuvées et références de revue.
2. Corriger les règles seulement si le contenu a été validé, puis tests unitaires et revue indépendante.
3. Obtenir une CI générale SQLite + PostgreSQL verte sur le SHA modifié, vérifier logs et seuils, poursuivre le contrôle navigateur sécurisé côté D14.
4. Documenter preuve exact HEAD, compte rendu de revue, approbation et risques résiduels ; rester Draft sans release/merge/déploiement avant GO séparé.

## Exclusions et continuité
- **D18 explicitement exclue** à la demande utilisateur : pas d'accès ni de modification.
- Aucun déploiement Vercel autorisé. Aucun appel fournisseur ni donnée patient réelle utilisés.
- D14 [Draft #1245](https://github.com/hraaaaf/IAMINA-MVP/pull/1245) reste un chantier distinct : vérification Web photo, permission médias en trois points et preuve de non-sortie réseau ; ne pas convertir la réussite D24 ciblée en certif D14.

**Décision : préflight D24 vérifié, release NO-GO / gate humain policies.**
