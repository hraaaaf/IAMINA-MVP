# IAMINA — D7 / First User Experience — patient revenant modifier son profil

**Date :** 31 octobre 2026. **Décision : D7 — Déclaration du type de diabète et des traitements réellement pris, sans prescription ni inférence automatique.**
**Lot de consolidation :** [PR #1208](https://github.com/hraaaaf/IAMINA-MVP/pull/1208) (Web, Draft, sans merge). **Référence clinique / FUE :** [D7 gate canonique](2026-10-29-d7-web-fue-coverage-gate.md), [règles qualité](../QUALITY_SCORING_POLICY.md).

## Choix de la FUE et objectif

**Persona :** un patient déjà utilisateur d'IAMINA revient dans son espace pour corriger ce qu'il a *déclaré*. L'objectif n'est pas de valider un formulaire isolé : il doit pouvoir reconnaître ses choix, les modifier, les enregistrer, les retrouver après réouverture, sans changement de traitement imposé par IAMINA.

**Goal :** une personne peut distinguer et éditer indépendamment type de diabète, traitements effectivement pris et choix « rien à déclarer / je ne sais pas », avec un statut de sauvegarde exact et une conservation sûre des informations du bon coffre.

**Succès observable :** scénario sans erreur sur le **vrai produit Flutter Web** au SHA testé, sur données synthétiques, avec preuves par état avant/après, sauvegarde persistante, rechargement, sécurité du verrou, FR/AR RTL et viewports 390×844, 768×1024, 1280×900. La FUE doit couvrir aussi les erreurs et la récupération. **100 % des cas requis = PASS** pour la validation binaire D7 ; NOT_RUN ou FAIL implique FUE_NO_GO. Aucune conclusion médicale ni score inventé.

## Parcours utilisateur principal — FUE-D7-01

1. **F01 — Entrée et retour.** Ouvrir IAMINA Web sur navigateur neuf ; choisir le parcours local autorisé, configurer/déverrouiller le coffre, terminer l'onboarding ; revenir dans « Profil > Suivi médical ». Le formulaire et les actions doivent être accessibles sans blocage ni donnée médicale fictive.
2. **F02 — Déclaration initiale.** Choisir « Type 2 » et déclarer volontairement « Médicaments oraux » et « Insuline ». Enregistrer : vérifier l'absence de message « synchronisé serveur » sans acquittement ; les éléments sont bien deux choix distincts.
3. **F03 — Persistance.** Fermer/réouvrir l'écran, recharger physiquement la page, déverrouiller ; retrouver exactement type 2 et les deux traitements (ni perdu, ni dupliqué).
4. **F04 — Correction de type.** Passer de type 2 à type 1, enregistrer/recharger ; les deux traitements restent inchangés. Aucun conseil thérapeutique automatique.
5. **F05 — Incertitude puis décision explicite.** Passer de type 1 à « Je ne sais pas / plus tard » ; garder les traitements. Sélectionner explicitement « Aucun traitement à déclarer », sauvegarder/recharger ; la déclaration passe à « aucun », sans prétendre que l'utilisateur ne prend aucun médicament au sens clinique.
6. **F06 — Retour au choix.** Déclarer explicitement « Insuline », enregistrer/recharger : « aucun » est remplacé par la déclaration volontaire, sans restauration cachée d'anciens choix.
7. **F07 — Résilience réseau et statut.** Répéter une sauvegarde en local/pas de réseau, puis restaurer la connexion : le libellé ne doit pas annoncer un succès distant non vérifié ; aucune requête vers un domaine non autorisé, aucune erreur JS/PWA bloquante.
8. **F08 — Présentation et accessibilité.** Capturer les états initial, « type inconnu » et « aucun traitement » sur 390×844, 768×1024 et 1280×900 ; vérifier intégrité du formulaire, CTA visibles, clavier/focus, AR en RTL et FR, textes non prescriptifs. Même viewport/état pour les comparaisons BEFORE→AFTER.

## Parcours associé au correctif #1208 — FUE-D7-02 (consentement et verrou)

Ce parcours est **dans le périmètre produit** de la PR #1208 ; la FUE-D7-01 seule ne le clôt pas.

- **C01 — Choix libre.** Sur la Preview QA protégée et épinglée au SHA exact, sélectionner « Continuer sans IA » ; pas de consentement implicite, le profil reste utilisable.
- **C02 — Verrou explicitement ignoré.** Si « continuer sans verrouillage » a été choisi, le bouton « Accepter » ne doit pas enregistrer de consentement ; le parcours doit offrir « Activer le verrouillage ».
- **C03 — Consentement effectif.** Activer/déverrouiller le coffre, puis accepter explicitement la notice versionnée ; le serveur doit confirmer l'enregistrement, et la navigation doit être cohérente.
- **C04 — Échec et récupération.** Si l'API refuse/échoue, afficher un message explicite, sans fausse acceptation ni fuite de données ; « Continuer sans IA » reste possible.
- **C05 — Retrait / retour.** Vérifier que le retrait du consentement reste contrôlable, et que l'état ne se rétablit pas silencieusement.

**Attention :** le retour iPhone positif de l'utilisateur valide le parcours qu'il a réellement essayé sur la Preview `2fe625cf...`, **pas automatiquement les états négatifs, les viewports supplémentaires ou le SHA de #1208**. Pas d'accès à l'environnement protégé ni de déploiement sans permission spécifique. Les identifiants, tokens, captures nominatives et données de santé ne doivent jamais être versés dans les artifacts.

## Frontière conditionnelle — isolation A → B → A

Le cœur D7 est **un patient revenant sur son dossier**. Réutiliser la preuve W02 d'isolation lorsque son SHA/frontière reste applicable. Pour les frontières modifiées par #1208 (verrou/consentement), ajouter une vérification **ciblée et non destructive** de changement de session A→B→A si les preuves W02 ne couvrent pas le risque. Ne pas ouvrir `GET /api/v1/profile` dans le BFF simplement pour faire passer un test : le coffre clinique reste local-first et protégé.

## Exécution et registre de preuves (à compléter, sans présumer des résultats)

| Cas | Preuve attendue | Statut initial |
| --- | --- | --- |
| F01–F06 | Vrai Chrome + Flutter Web / WebAuthn / SQLite WASM IndexedDB, états avant/après et reload | NOT_RUN pour cette PR |
| F07 | Network egress/offline et vérité du statut de sauvegarde | NOT_RUN pour cette PR |
| F08 | 9 captures comparables 390/768/1280 ; FR/AR RTL ; clavier/focus et erreurs | NOT_RUN pour la FUE intégrée complète |
| C01–C05 | Recette vraie Preview QA du consentement, verrou et retrait sur le SHA correct | NOT_RUN sur cette PR |
| Isolation owner si applicable | Preuve W02 compatible ou A→B→A ciblé, sans données réelles | À justifier / NOT_RUN |
| Revue clinique/privacy | Choix non prescriptifs, sécurité, stockage, CNDP et absence de faux ACK | PENDING |
| Exécution et adversarial / Perfection Pass | Scores sur preuves, analyse des écarts, dernier passage de perfection | NOT_RUN |

### Banc automatisé de départ

Le test `scripts/d7_web_actual_profile_e2e.py` est repris de la branche QA D7 : **huit phases** sur le vrai Web local, un coffre synthétique, Chrome et WebAuthn, **neuf captures** (type 2 / inconnu / aucun × 3 viewports). Il peut prouver F01–F06 partiellement et une partie de F07/F08. Il utilise des libellés anglais pour les interactions automatisées ; les widgets FR/EN/AR et leurs responsive tests sont exécutés séparément. **Ce banc ne certifie ni FR/AR sur la navigation complète, ni consentement distant, ni permissions réelles, ni A→B→A authentifié.**

Le workflow `.github/workflows/d7-fue-returning-patient-web.yml` est **sans secrets**, uniquement Pull Request, avec conservation bornée des PNG synthétiques et du verdict JSON. Toute sortie `PASS` de ce banc est une **preuve partielle** et ne transforme pas la FUE globale en PASS.

**Décision de closeout :** ne pas sortir la PR #1208 de Draft et ne pas merger tant que la matrice complète n'est pas à 100 % PASS, que les dimensions critiques et le Perfection Pass de `docs/QUALITY_SCORING_POLICY.md` ne sont pas satisfaits et que le gate humain de fusion n'a pas été donné. Aucun déploiement Vercel autorisé par cette fiche.

## 31/10/2026 — Perfection Pass / adversarial finding: withdrawal must be fail-closed

**BEFORE — confirmed source finding on deployed main `ed8c67e0`:** `ProfileScreen._confirmWithdrawConsent()` discarded the bool result of `ApiClient.withdrawConsent()` and always showed the success Snackbar even when DELETE returned false/failed. This violated the C05 negative/recovery case and represented a **blocking privacy/truthfulness defect**. It also did not clear `ConsentEvidenceStore`, allowing stale local proof to remain. **No prod user records were read or modified to establish this code-level finding.**

**Goal:** a withdrawal click immediately disables the local AI gate, saves a durable *patient-vault-scoped* pending-withdrawal marker before network contact, explicitly validates the server's `ai_consent_given=false` receipt, clears local notice evidence and DB only after verified remote revocation, and preserves a visible retry action across page reload if remote withdrawal is unconfirmed. Never show `Consentement retiré` on a failed remote result. Clear pending only after both server and local writes are confirmed. An explicit new verified grant may clear a previous pending marker.

**Prepared patch under PR `fix/d7-consent-revocation-fue-20261031`:** introduces `d7_consent_withdrawal.dart`, owner-scoped marker in secure storage, fail-closed ConsentService, startup pending-state restoration, Profile retry CTA and explicit success/warning messages FR/EN/AR, exact server response check in ApiClient. New C05 tests exercise success, rejection, offline exception, marker failure, cleanup failure, retry and misleading 2xx receipt. Workflow D7 adds these synthetic cases before Chrome patient-profile FUE.

**Important limits / binary gates:** synthetic test suite on a PR can prove only these controlled conditions; it is not evidence for real hosted auth/WebAuthn/remote consent across FR/AR or an independent privacy signoff. **FUE D7 remains NOT_VERIFIED** until all required C01–C05 cases on a real permitted QA environment, profile persistence/negative states, actual viewport comparisons, and Perfection Pass score are reviewed with adequate evidence. Old production remains on `ed8c67e0` unless a separate authorized deployment follows.
