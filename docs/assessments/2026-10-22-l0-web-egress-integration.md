## 22/10/2026 — L0 Web RELEASE : étape 0 du wizard CGM auparavant trompeuse

**BEFORE (preuve image)** : [artifact CGM #12459412459](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39854645209/artifacts/12459412459) capturé 390×844, 768×1024, 1280×900 : « Quel capteur utilisez-vous ? » avec Dexcom/Libre/LinX cliquables et schéma Nightscout→IAMINA, alors que `CgmService` refuse en Web RELEASE tout transport CGM. Le panneau des connexions avait bien été désactivé, mais pas ce wizard principal.

**Goal** : l'utilisateur Web RELEASE voit immédiatement l'indisponibilité CGM et ne peut ni initier le parcours sensor ni saisir des credentials Nightscout. Aucun changement de transport, pas de stockage de secret. **Mockup** : en-tête `Connecter mon CGM` conservé, surface centrale compacte avec verrou et texte explicite dans la langue locale (FR/EN/AR), sans cartes de capteurs, sans boutons de connexion.

**Implémentation candidate** : `CgmScreen` verrouillé sur `kIsWeb && kReleaseMode`, mode de test `forceLocalOnlyDisabledForTests` **ne pouvant forcer que le verrouillage**, jamais activer un transport. Guide d'origine conservé pour builds DEBUG et ses tests éducatifs. Ajout de 9 tests widget couvrant FR/EN/AR × 390/768/1280 et absence de commandes Dexcom/Libre/LinX/Nightscout.

**AFTER exigé** : CI et browser cert exact-HEAD sur 390×844/768×1024/1280×900 ; captures visuelles, comparées au BEFORE, preuve du retrait d'affordances trompeuses ; ne pas présenter un simple changement attendu de maquette comme un score pixel 10/10. **Statut CANDIDAT, non livré**, revue clinique/UX humaine encore manquante pour textes et secours ; PR #1140 DRAFT, W01 NO-GO/W02 gelée, zéro Vercel.

---
## 22/10/2026 — CURRENT INTEGRATION / UI BLOCKER REMEDIATION

**PR #1140** source `main@8ada5aab8e8006bbbdc275eabbabf014a4714e0b`. Initial HEAD `5111d3c4`: 9 workflows, **8/9 SUCCESS**, le seul rouge est [UI desktop Chrome CDP #39797088586](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39797088586) : `127.0.0.1:9222` refused connection avant assertions, mobile/tablette de ce workflow SUCCESS. **Les huit autres workflows dont Companion no-egress sont SUCCESS**, pas une certification clinique.

**Remédiation UX** : `CgmConnectionsSection` détecte `clinical_transport_disabled_local_only` et **désactive** configuration en montrant l'indisponibilité FR/EN/AR. `CompanionConversationScreen` en Web RELEASE masque entièrement saisie/suggestions/enregistrement audio, évite initialization providers/TTS, montre indisponibilité + non-surveillance des urgences et renvoi aux services locaux (message générique à revue clinique/linguistique). Un booléen test-only peut **forcer la désactivation**, jamais l'activation réseau en release. Deux suites widget vérifient CGM disabled FR/EN/AR et Companion aucun input/send FR/EN/AR × 390/768/1280. Workflow CDP mise à jour pour capturer l'écran réellement désactivé plutôt que prétendre envoyer une requête via champ inexistant. **Candidate seulement tant que la nouvelle CI n'a pas PASS.**

**BEFORE / GOAL / mockup / AFTER** : BEFORE repo source et anciens artefacts de l'UI Companion accessible/CGM configuration trompeuse ; Goal = aucune fausse interaction clinique disponible en pilote local-only ; référence = en-tête inchangé + carte explicite + informations d'urgence non personnalisées sans chat ; AFTER = captures Chrome 390/768/1280 FR/AR et comparaison/score *encore à faire*.

**Gates cliniques/risques** : [#1134](https://github.com/hraaaaf/IAMINA-MVP/issues/1134) OPEN pour triage d'urgence local et traduction, revue indépendante privacy/clinique ouverte. Aucune mise en Production, aucune activation CGM ni chat; L0 statut NO-GO/score plafonné 5.9 pour blocage risque clinique, ne pas merger sans preuves/reviews nécessaires.

---

## 22/10/2026 — L0-HARDENING-UI-01 : affordances fail-closed locales (candidat non certifié)

**BEFORE observé dans le code main/PR #1140 :** `CgmConnectionsSection` transforme `clinical_transport_disabled_local_only` en erreur `cgmUnavailable` tout en laissant le bouton Configurer activé. `CompanionConversationScreen` affiche encore une zone de saisie, des suggestions et un micro malgré le refus `kReleaseMode` côté services ; il n'existe aucun parcours d'urgence local qualifié (issue #1134).

**Goal visuel et fonctionnel :** Web RELEASE local-only n'offre aucune fausse capacité CGM/chat/voix ; affiche FR/EN/AR l'indisponibilité, avec avis non prescriptif que le chat ne traite pas les urgences. Boutons CGM configuration désactivés ; aucun champ texte/micro/envoyer sur l'écran chat RELEASE. Aucun changement backend/auth/vault ni transport clinique. Les callbacks de test peuvent uniquement forcer le mode désactivé, pas activer le réseau.

**Mockup texte** : écran chat → en-tête IAmina inchangé → surface centrée icône verrou + explication indisponibilité + urgence locale ; pas de composer. Écran CGM → message d'indisponibilité déjà dans le slot d'erreur + boutons Configurer disabled, cartes d'information conservées.

**Tests ajoutés** : 3 locales CGM (bouton disabled), 3 langues × 390/768/1280 chat (aucun champ/bouton, message explicite). **AFTER Chrome RELEASE vrai aux mêmes viewports, captures, RTL/keyboard/escape et zéro réseau à prouver**. Les scénarios Chat E2E antérieurs qui simulent l'envoi de patient dans une UI RELEASE doivent être mis à jour à l'oracle honest-disabled, sans effacer leurs tests de service. **Ne pas déclarer GO avant CI/AFTER et revue de traduction/clinique humaine.**

**Statut** : candidat DETACHED, aucune nouvelle CI/déploiement initiée pendant les 9 jobs de la PR #1140. La revue #1134 reste ouverte pour une future expérience locale cliniquement qualifiée, cet écran étant une simple désactivation honnête.

# IAMINA WEB — L0 : intégration candidat des barrières réseau Companion + CGM — 22 octobre 2026

## Goal → succès → preuve
**Goal exact :** réconcilier [CGM #1096](https://github.com/hraaaaf/IAMINA-MVP/pull/1096) et [Companion #1133](https://github.com/hraaaaf/IAMINA-MVP/pull/1133) sur `main@8ada5aab8e8006bbbdc275eabbabf014a4714e0b` pour le pilote **Web local-only**, sans transmettre d'informations médicales au serveur par leurs clients HTTP indépendants.

**Succès observable nécessaire :** (1) en build Flutter Web RELEASE, toutes les méthodes CGM refusent AVANT lecture de token et AVANT HTTP ; (2) Companion overview/proactive/next-action ne fait aucun HTTP ; chat/voix patient refusent AVANT bearer/network ; chat démo non authentifié reste strictement local et déterministe ; (3) aucune porte de contournement par callback synthetic en mode RELEASE ; (4) UX indique avec vérité FR/EN/AR la fonction indisponible, sans promesse de sécurité clinique non démontrée ; (5) aucune régression auth/CSRF/consent/profil; (6) FUE navigateur + traces réseau réelles + scores/avis qualifiés.

**Preuves héritées (PAS preuve d'intégration) :** #1096 **3/3 CI SUCCESS** au SHA `c73588cc`; #1133 **8/8 CI SUCCESS** au SHA `45685254`. Les PRs initiales restent OPEN/DRAFT, non fusionnées ; leurs tests ne certifient pas le comportement combiné.

## Audit source avant intégration
- Sources des PRs examinées, différences local-only connues, 10 chemins contrôlés contre les deux bases git indépendantes et le HEAD actuel de main. Tous les blobs main des chemins modifiés étaient **strictement identiques** aux ancêtres respectifs. Les 10 blobs retenus sont copiés bit pour bit des PRs sources, sans réécriture de protections.
- CGM `CgmService._headers` applique `kReleaseMode || callbackSynthetic != true` → refus 403 avant `AuthService.getIdToken`. Aucune autorisation distante pour l'application release.
- Companion `_clinicalTransportAllowed = !kReleaseMode && callbackSynthetic==true` : refus par défaut ; méthode de chat patient renvoie `clinical_transport_disabled_local_only`, message UX FR/EN/AR spécifique.
- Précaution : cette intégration **désactive** l'accès serveur CGM et Companion chat/voix ; ce n'est **pas** un remplacement local qualifié ni une fonction clinique terminée. Vérifier le parcours urgence et les affordances avant toute livraison.

## Tests / décisions requises
| Gate | Attendu | État initial |
| --- | --- | --- |
| SHA main et compatibilité des 10 fichiers | base exacte, pas de changements masqués | **PASS source** (Git trees) |
| Flutter tests CGM + Companion | zéro HTTP, zéro bearer et refus synthétiques appropriés | **À EXÉCUTER sur L0** |
| Release Web runtime HTTP no-egress | trace réseau Chrome, aucun payload patient, 390/768/1280 | **À EXÉCUTER sur L0** |
| UX BEFORE→AFTER FR/AR | messages vrais, bouton chat/voix et erreur, focus/touch, toutes tailles | **À EXÉCUTER sur L0** |
| Clinique urgence / option locale | aucun faux assistant médical, écran sécurité adéquat | **BLOQUANT : issue #1134** |
| Privacy/sécurité/clinique indépendantes | revue humaine de l'impact et du refus egress | **BLOQUANT** |
| Vercel / Production / merge | autorisation explicite distincte après tous gates | **NON AUTORISÉ** |

**Perfection Pass et scores** : différés jusqu'aux résultats sur SHA exact. Tant que la sécurité du chemin clinique urgence est ouverte, status `BLOCKED` (cap score 5.9/10), **pas de GO produit/Production**.

**Dépendances** : [W01 #1128](https://github.com/hraaaaf/IAMINA-MVP/pull/1128) NO-GO ; W02 gelé ; D21 Preview distincte. Aucun changement de Neon/API, aucune donnée patient, aucun déploiement Vercel voulu pour la construction de cette branche.

**Next exact :** créer PR DRAFT d'intégration, vérifier CI exact SHA et preuve Chrome sans réseau, corriger régressions, comparer UX, documenter reviewers/gates cliniques ; puis poursuivre L0 autres PRs sécurité en branch indépendante. Ne pas fusionner si impact clinique/UX non résolu.
