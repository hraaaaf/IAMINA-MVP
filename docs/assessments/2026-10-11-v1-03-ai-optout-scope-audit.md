# IAMINA V1-03 — Audit opt-out IA, surfaces et persistance

Date: 2026-10-11 | Baseline: `15cfe25fcc93fff00a1198d705fb683c7a2eb960` | Branche: `parallel/v1-03-optout-transport-inventory-20261011` | Issue: #924
Statut : **durcissement fail-closed client #934 certifié sur SHA 55aefac2038deef2389aa4f2955962526f939bb3 (16/16)** ; nouveaux tests de caractérisation redémarrage / preuve sécurisée / portée inter-appareils ajoutés ensuite, **CI exact-HEAD à établir**. Gate produit/privacy restant OPEN.

## Goal / succès / preuve
Goal: vérifier ce que « Continuer sans IA » interdit immédiatement, au redémarrage et sur un autre appareil.
Critère: refus effectif avant HTTP sur chaque voie patient IA et sémantique non ambiguë entre session locale et révocation serveur. Preuve : code et CI GitHub exact-HEAD du durcissement client, plus nouveaux tests synthétiques de reconstruction de service ; véritables redémarrages de l'application, multi-device et offline/reconnexion restent NON prouvés.

## Inventaire sourcé
1. `frontend/lib/features/auth/consent_screen.dart:55-58` : le bouton « sans IA » n'appelle que `ConsentService.declineLocally()` puis retourne dashboard. `frontend/lib/services/consent_service.dart:87-95` : indicateur local **mémoire non persistée**. Aucun `DELETE /account/consent` sur ce bouton.
2. Au lancement `frontend/lib/main.dart:72-85` recrée `ConsentService` depuis `ConsentEvidenceStore` sécurisé et horodatage local du profil : un consentement antérieur durable peut redevenir valide après redémarrage malgré un refus local passé. **Risque de sémantique/continuité prouvé par le code, scénario runtime non rejoué**. Même appareil et multi-device sont distincts.
3. Le parcours conversationnel `frontend/lib/features/companion/companion_conversation_screen.dart:123-141` injecte `AuthService` et `ConsentService` dans `CompanionService`. `frontend/lib/main.dart:111-115` injecte de même `ConsentService` au `ApiClient` global. `frontend/lib/features/journal/widgets/amina_chat_view.dart:175-198` utilise le `ApiClient` fourni. Les méthodes `sendChatMessage`, voix, chat SSE, photo et web OCR effectuent un gate si le service est injecté.
4. **Historique sur base #932** : `CompanionService` et `ApiClient` autorisaient leur chemin patient IA si le `ConsentService` facultatif était `null`. **Corrigé en PR #934 et prouvé 16/16 sur SHA 55aefac...** : requêtes IA patient sans injection maintenant refusées avant authentification/transport. Plusieurs surfaces construisent encore `CompanionService()` pour GET et opérations déterministes ; ce sont des usages distincts, pas la preuve d'une fuite LLM. Ne pas élargir le contrat consentement IA aux seuls endpoints déterministes sans revue.
5. `frontend/lib/features/profile/profile_screen.dart:370-400` offre **un flux distinct de retrait global** : appelle `ApiClient.withdrawConsent()`, vérifie réponse `ai_consent_given=false`, puis ferme porte locale et supprime données durables. `backend/core/api/v1/account.py:129-161` révoque consentement serveur/receipts/grants. Ne jamais assimiler ce flux au bouton local.
6. Tests existants `frontend/test/services/consent_service_test.dart` couvrent refus local, mémoire et masquage immédiat, `frontend/test/features/profile/profile_consent_withdraw_contract_test.dart` couvre ordre de révocation (contrat de source), tests réseau négatifs réalisés dans #922; **ni redémarrage réel ni cross-device certifiés ici**.

## Verdict
- **Vérifié :** « sans IA » est un refus de session locale, pas un retrait de consentement serveur ; les voies patient IA principales et les clients sans injection refusent désormais avant egress (durcissement certifié sur SHA 55aefac...).
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

Le test `frontend/test/services/v1_03_local_decline_network_gate_test.dart` ajoute deux cas négatifs : appel texte et voix sans gate `CompanionService`; SSE, chat, voix, STT, photo repas et web OCR sans gate `ApiClient`, tous avant token et HTTP. Les fixtures de clients synthétiques consentis injectent maintenant une `ConsentService()..markVerifiedConsent()` explicite au lieu de profiter du bypass ancien. **CI vérifiée 16/16 sur SHA 55aefac2038deef2389aa4f2955962526f939bb3**, dont E2E navigateur et PostgreSQL.

**Ne résout PAS** la différence locale persistante versus retrait serveur, ni la continuité après redémarrage, ni le consentement multi-appareils. Le serveur reste autorité finale. Le code du durcissement #934 est certifié sur 55aefac... ; les NOUVEAUX tests de caractérisation redémarrage sont un changement ultérieur, et doivent obtenir leur propre CI avant toute conclusion.

**Certification requise pour ce durcissement :** le HEAD doit déclencher `pull_request` vers `main` afin d'exécuter Flutter analyze/tests/PWA, backend SQLite/PostgreSQL et les protections historiques. Toute réponse sans CI exacte est provisoire ; la base finale de revue demeure #932 (et non `main`).

## Correction après analyse de CI du 2026-10-11 — E2E chat (sans modifier la protection patient)
Le commit de sécurité `a6f3090078acaf9417266036ea6242fcbfbbcb32` a obtenu **15/16 workflows success** mais **1 échec réel** dans [Companion real chat E2E screenshots, run #38142335923](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38142335923). La [CI générale #38142335968](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38142335968) était SUCCESS avec les tests backend PostgreSQL/Flutter, mais **cela ne suffit pas à clôturer la branche**.

**Preuve dans les logs du job `real-chat-proof`, étape `Run Chrome real exchange and capture states` :** `RuntimeError: No /api/v1/ai/chat response captured from the app`. Le navigateur utilisait le harnais indépendant `frontend/lib/ui_companion_chat_e2e_main.dart`, qui créait `CompanionService(authService: _E2EProxyAuthService(), baseUrl: companionApiBaseUrl)` **sans `ConsentService`**, précisément le bypass que le nouveau garde bloque. Cela explique l'absence de demande IA; aucun besoin de réactiver un bypass dans les services.

**Correctif minimal effectué :** seulement dans cet entrypoint E2E non patient, `ConsentService()..markVerifiedConsent()` est créé explicitement et injecté dans `CompanionService` pour l'identité synthétique et le proxy du runner. Un test Flutter dans `v1_03_optout_scope_regression_test.dart` exige l'injection explicite et vérifie que le vrai `lib/main.dart` ne fait ni appel à l'entrypoint E2E ni `markVerifiedConsent()` en contournement. Le backend conserve l'authentification de la fixture synthétique et son contrôle d'egress.

**Validation du correctif E2E réalisée :** HEAD `55aefac2038deef2389aa4f2955962526f939bb3`, 16/16 workflows SUCCESS, [CI #38147733716](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38147733716) et [E2E #38147733767](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38147733767) verts. PR #934 revenue sur base #932, mergeable, DRAFT, non mergée au closeout. Cela n'apporte aucune preuve de retrait global, de persistance offline/multi-device, d'innocuité clinique ou de mise en production.

## Tests de caractérisation redémarrage / deux appareils — 2026-10-11 (sous-lot suivant)

**Goal :** mesurer exactement la portée session-only actuelle **sans choisir la nouvelle politique**. Dans `frontend/test/services/consent_service_test.dart`, trois tests supplémentaires :
- Réutiliser le même profil Drift synthétique et `hasVerifiedEvidence: true` dans une *nouvelle instance* `ConsentService` après `declineLocally()` : le refus de la session 1 coupe l'IA immédiatement, mais la session 2 redevient `hasConsent=true` car `_hasDeclinedLocally` n'est pas persisté. **Caractérisation d'un risque produit, pas approbation de ce comportement.**
- Même profil avec preuve de notice absente au redémarrage : `hasConsent=false`, fail-closed confirmé par simulation.
- Deux instances de `ConsentService` (simulant des appareils indépendants) : refus local A ne révoque pas B. **Ce n'est PAS** un test multi-device réel, ni un test du serveur, ni de l'absence de provider egress après reconnexion.

**Non implémenté** : persistance de refus sur l'appareil ou révocation serveur globale, migration de profil et UX. Cette décision reste humaine (#924). **Les tests ci-dessus ne sont pas encore certifiés exact-HEAD** ; attendre CI GitHub avant d'en faire des assertions exécutées. Le durcissement précédent reste certifié sur son propre SHA.

## Matrice de test CI : suivi du SHA (preuve après exécution)

Ce complément est lancé sur la branche DRAFT #934 temporairement ciblée sur `main` pour activer GitHub Actions `pull_request` : l'ancien parent #932 reste inchangé. Les 3 nouveaux tests doivent passer avec les vérifications Flutter, backend PostgreSQL et E2E sans aucune simulation de patient réel. La CI n'est **pas** une autorisation de changer le comportement consentement ou d'exposer les alias P3. Après succès exact-HEAD, restaurer la base `safety/v1-03-glucose-ocr-unit-provenance-20261011`, actualiser GitHub/Notion/roadmap et conserver DRAFT/non-fusionné.

## DÉCISION PRODUIT — Option A explicitement choisie (2026-10-11)

**Décision utilisateur : A.** « Continuer sans IA » est un **refus persistant sur cet appareil**, **pas** une révocation du consentement sur le serveur ni sur un autre appareil. Les passages historiques de cet audit parlant de « session-only », de l'arbitrage A/B ouvert ou du test de caractérisation antérieur décrivent **la baseline avant cette décision**, et non la cible actuelle.

### Goal / succès / preuves requises

**Goal exact :** aucune requête IA patient depuis un appareil ayant enregistré le refus, y compris après reconstruction de l'application, tant qu'aucune nouvelle acceptation explicite et vérifiée ne l'a levé. Le serveur garde son consentement indépendant et fait son propre contrôle. **Succès observable :** refus durable dans `FlutterSecureStorage`, lecture avant `ApiClient/CompanionService`, fail-closed sur lecture inconnue/erreur, aucune navigation annonçant « sans IA » avant écriture confirmée, réactivation uniquement après serveur + notice + profil + suppression du marqueur ; un autre appareil reste indépendant.

**Implémentation :**
- `ConsentEvidenceStore` ajoute un marqueur sécurisé séparé `iamina.ai_consent.local_declined_v1` (présent = refus, valeur inconnue non-nulle = refus). `hasPersistedLocalDecline()`, `persistLocalDecline()`, `clearPersistedLocalDecline()` ne changent ni receipt notice ni serveur.
- `main.dart` attend les deux lectures; en cas d'erreur du marqueur, initialise un refus local (fail-closed). `ConsentService(initiallyDeclinedLocally: ...)` est initialisé avant le `ApiClient` partagé; la profile stream ne peut pas lever la suppression.
- `ConsentScreen` supprime l'IA locale immédiatement **sans notifier le routeur** jusqu'au succès de l'écriture, puis émet la notification et navigue. Échec d'écriture = rester sur l'écran, afficher erreur et garder la session IA bloquée; ne pas prétendre avoir sauvegardé. Après nouvelle acceptation exacte serveur, notice et profil, supprimer le marqueur **avant** de rappeler `markVerifiedConsent()` ; toute erreur garde la porte fermée.
- Le routeur permet de revisiter `/consent` en cas de refus local ; le profil montre l'état « IAmina désactivée sur cet appareil » et un bouton d'acceptation volontaire. L'enregistrement du refus ne déclenche aucune révocation serveur.
- Limites honnêtes : stockage sécurisé réellement indisponible = impossibilité de garantir la persistance au prochain démarrage ; l'UI refuse donc de confirmer l'action. Le refus existant avant cette mise à jour n'avait pas de trace durable : aucune migration rétroactive fictive. Ce marqueur est **par installation**, pas par compte ou appareil distant.

### UI/UX — BEFORE → target → AFTER → test visuel

**BEFORE code source :** profil compte avec simple état « Consentement IAmina non activé » sans lien de réacceptation; routeur renvoyant un utilisateur ayant refusé de `/consent` vers accueil; bouton de refus naviguant immédiatement. Viewports de référence navigateur existants : **390×844, 768×1024, 1280×900**, artefacts de [run #38147733708](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38147733708), surfaces `profile`. Ces références ne montrent pas de bouton d'opt-out durable car il n'existait pas.

**Target mockup logique dans la section Compte étendue (sans refonte visuelle) :**
```text
Compte / Confidentialité
IAmina désactivée sur cet appareil
[ Réactiver IAmina avec mon consentement ]
Zone sensible
  Déconnexion
```
**AFTER prévu :** état et bouton profil uniquement si refus local, libellés FR / EN / AR, minimum 48px, route consentement explicite ; section Compte fermée par défaut hors fixture. Workflow `ui-browser-screenshot.yml` étendu à une **surface exclusivement synthétique** `profile-ai-disabled` avec section compte étendue pour les trois viewports, sans données patient. Les captures après et score visuel ne peuvent être revendiqués qu'après workflow vert et inspection des captures mêmes viewports.

**Tests ajoutés :** tests Mocktail du stockage sécurisé (écriture, lecture après nouvelle instance, effacement, marqueur invalide, erreur), tests Flutter widget consentement (écriture bloquée, navigation différée, erreur de stockage fail-closed, réacceptation, erreur de suppression fail-closed), tests `ConsentService` avec profil et preuve préexistants, divergence indépendante entre appareils simulés, contracts source bootstrap/routes/UX. Les précédents tests « le refus disparaît après restart » sont **remplacés** par le contrat option A ; jamais faire passer une caractérisation ancienne comme produit approuvé.

**Statut :** implémentation sur PR #934 DRAFT, **pas encore certifiée sur le HEAD courant**. Exact-head GitHub CI, captures 390/768/1280, tests fonctionnels, audits sécurité/privacy puis décision merge restent obligatoires. La CI antérieure de caractérisation `8c2b545...` a eu un échec **Android packaging** sur résolution externe `org.jetbrains.kotlin:...:2.0.21` dans Gradle, sans preuve de défaut du produit ; ne pas compter comme succès. Aucun merge, Vercel, patient réel ou levée du gate clinique global.
