# IAMINA V1-03 — Audit opt-out IA, surfaces et persistance

Date: 2026-10-11 | Baseline: `15cfe25fcc93fff00a1198d705fb683c7a2eb960` | Branche: `parallel/v1-03-optout-transport-inventory-20261011` | Issue: #924
Statut: **audit statique documenté, gate produit/privacy ouvert**. Aucun code patient modifié, aucun test runtime supplémentaire exécuté.

## Goal / succès / preuve
Goal: vérifier ce que « Continuer sans IA » interdit immédiatement, au redémarrage et sur un autre appareil.
Critère: refus effectif avant HTTP sur chaque voie patient IA et sémantique non ambiguë entre session locale et révocation serveur. Preuve: call sites Git à SHA exact + tests existants; les scénarios multi-device restent non testés.

## Inventaire sourcé
1. `frontend/lib/features/auth/consent_screen.dart:55-58` : le bouton « sans IA » n'appelle que `ConsentService.declineLocally()` puis retourne dashboard. `frontend/lib/services/consent_service.dart:87-95` : indicateur local **mémoire non persistée**. Aucun `DELETE /account/consent` sur ce bouton.
2. Au lancement `frontend/lib/main.dart:72-85` recrée `ConsentService` depuis `ConsentEvidenceStore` sécurisé et horodatage local du profil : un consentement antérieur durable peut redevenir valide après redémarrage malgré un refus local passé. **Risque de sémantique/continuité prouvé par le code, scénario runtime non rejoué**. Même appareil et multi-device sont distincts.
3. Le parcours conversationnel `frontend/lib/features/companion/companion_conversation_screen.dart:123-141` injecte `AuthService` et `ConsentService` dans `CompanionService`. `frontend/lib/main.dart:111-115` injecte de même `ConsentService` au `ApiClient` global. `frontend/lib/features/journal/widgets/amina_chat_view.dart:175-198` utilise le `ApiClient` fourni. Les méthodes `sendChatMessage`, voix, chat SSE, photo et web OCR effectuent un gate si le service est injecté.
4. `frontend/lib/services/companion_service.dart:186-196` et `frontend/lib/services/api_client.dart:184-189` : **si le service facultatif vaut null, le garde local retourne sans refus**. Plusieurs écrans utilisent `CompanionService()` par défaut (`companion_screen.dart`, `companion_premium_screen.dart`, `dashboard_{today,insight,next_action}_section.dart`). Leurs usages directs observés sont surtout **GET de faits gouvernés** (overview/preview) et POST d'évaluation déterministe, et ne constituent PAS une preuve de fuite vers un LLM. Ils restent une dette de cohérence de l'injection; tout futur branchement chat/voix via ces objets serait dangereux sans gate.
5. `frontend/lib/features/profile/profile_screen.dart:370-400` offre **un flux distinct de retrait global** : appelle `ApiClient.withdrawConsent()`, vérifie réponse `ai_consent_given=false`, puis ferme porte locale et supprime données durables. `backend/core/api/v1/account.py:129-161` révoque consentement serveur/receipts/grants. Ne jamais assimiler ce flux au bouton local.
6. Tests existants `frontend/test/services/consent_service_test.dart` couvrent refus local, mémoire et masquage immédiat, `frontend/test/features/profile/profile_consent_withdraw_contract_test.dart` couvre ordre de révocation (contrat de source), tests réseau négatifs réalisés dans #922; **ni redémarrage réel ni cross-device certifiés ici**.

## Verdict
- **Vérifié:** « sans IA » est un refus de session locale, pas un retrait de consentement serveur; les surfaces conversationnelles principales utilisent l'injection correcte et des vérifications locales.
- **Risque avéré dans la conception:** après redémarrage, le refus volatile ne fait plus écran contre un consentement durable préexistant; communication produit « sans IA » doit le préciser ou changer les garanties.
- **Non prouvé:** fuite de données patient, franchissement du gate serveur, chemin patient de chat actif utilisant directement une instance `CompanionService()` non injectée.
- **Gate humain:** choisir A refus local persistant par appareil (avec description claire et tests) ou B révocation globale serveur de l'utilisateur sur cette action (changement durable et multi-device). Aucun choix implicite.

## Validation restante
- Matrice de tests sur consentement serveur antérieur × refus local × redémarrage × deuxième appareil × offline/reconnexion; vérifier **zéro envoi IA non autorisé** avec clients espion et serveurs synthétiques.
- Renforcer le contrat d'injection des services sur chemins patient, sans bloquer abusivement des endpoints déterministes non IA. Garder le retrait du profil et le consentement notice-versionné indépendants.
- Contrôle cohérence FR/AR/Darija/a11y et BEFORE/AFTER si UI modifiée.

Next exact: obtenir l'arbitrage A/B au gate produit/privacy ou mettre en sécurité par défaut la persistance locale avec consentement serveur inchangé si c'est contractuellement autorisé; ne pas prétendre « global » sans serveur.

## Complement technique — 2026-10-11
- Test de caractérisation ajouté : `frontend/test/services/v1_03_optout_scope_regression_test.dart`. Il protège injection du consentement dans les chemins principaux et séparation du refus local de la révocation serveur.
- Il ne choisit ni ne certifie la politique redémarrage / multi-appareils, encore soumise au gate privacy/produit. Verdict CI exact-head à établir.

## Durcissement fail-closed local — 2026-10-11

**Correctif de sécurité sans changement de politique produit ni modification UI :** les clients `ApiClient` et `CompanionService` peuvent toujours être construits sans service de consentement pour les appels déterministes/lecture, mais **tous les appels IA patient qu'ils émettent directement doivent être bloqués en l'absence du `ConsentService` injecté**. Le code retourne `ai_consent_unverified_locally` avant récupération de token ou HTTP. Une exception locale reste explicitement permise pour la démo d'audit sans egress IA patient dans `CompanionService` : pas de traitement patient réel.

Le test `frontend/test/services/v1_03_local_decline_network_gate_test.dart` ajoute deux cas négatifs : appel texte et voix sans gate `CompanionService`; SSE, chat, voix, STT, photo repas et web OCR sans gate `ApiClient`, tous avant token et HTTP. Les fixtures de clients synthétiques consentis injectent maintenant une `ConsentService()..markVerifiedConsent()` explicite au lieu de profiter du bypass ancien.

**Ne résout PAS** la différence locale persistante versus retrait serveur, ni la continuité après redémarrage, ni le consentement multi-appareils. Le serveur reste autorité finale; ancien test CI 16/16 ne certifie pas ces nouveaux commits. Exiger CI Flutter tests/analyze et full suite exact-head avant de conclure.

**Certification requise pour ce durcissement :** le HEAD doit déclencher `pull_request` vers `main` afin d'exécuter Flutter analyze/tests/PWA, backend SQLite/PostgreSQL et les protections historiques. Toute réponse sans CI exacte est provisoire ; la base finale de revue demeure #932 (et non `main`).
