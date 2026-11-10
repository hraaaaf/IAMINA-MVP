# IAMINA — ROADMAP CANONIQUE UNIQUE · Web/PWA · D1–D38

**Édition :** 2026-11-10 — consolidation prospectif uniquement (archive du plan adopté le 04/11 ci-dessous) (arbitrages O1–O10 intégrés, adoption explicite du plan) · **Statut : PLAN WEB/PWA D1–D38 ADOPTÉ PAR LE PROPRIÉTAIRE le 04/11/2026 ; 11 CHOIX PRODUIT VALIDÉS ; PR DRAFT NON FUSIONNÉE, LOGICIEL NON CERTIFIÉ, AUCUNE AUTORISATION DE MERGE NI DE DÉPLOYER.**
**Source unique du plan prospectif :** ce document, `docs/ROADMAP.md`. Notion « 01 — ROADMAP CANONIQUE » sert de miroir et de parcours de décision. Les autres roadmaps, registres A/B, W00–W14, handovers et notes de release sont des **sources de preuve ou archives**, jamais un deuxième ordre de travail. Ancienne version archivée dans [roadmap-web-v2-2026-11-04.md](archive/roadmap-web-v2-2026-11-04.md).

## 0. Doctrine immédiatement applicable

1. **D33 : Web/PWA d'abord** (mobile 390/430, tablette 768, desktop 1280 ; Safari iPhone/Chromium, FR/AR RTL et zoom 200 %). Les chantiers purement natifs Android/iOS sont différés ; D31 physique n'est pas automatiquement un prérequis de publication Web.
2. **D37 + D30 : ouvrir l'application sans compte pour explorer**. Une personne sans compte peut parcourir seulement des écrans, explications et simulations avec données **fictives et statiques**. **Dès la première action nécessitant un accès à une base, un enregistrement, la consultation d'informations personnelles, un fetch métier/API ou un service externe, demander une connexion ou inscription AVANT l'action.** Ne pas demander de compte pour télécharger les assets de l'app, la traduction statique, le cache d'interface ou de la documentation publique : ces requêtes techniques ne sont pas des fetchs métier. La barrière réelle existe à la fois dans le routeur, le code d'accès DB et l'API ; un écran seul n'est pas une protection.
3. **Pas de chrono obligatoire.** L'idée des « 5 minutes » est **remplacée** par le déclencheur au besoin : pas de coupure arbitraire, pas de faux mécanisme de sécurité basé sur le temps. CTA de connexion au point d'usage.
4. **Invité = aucune donnée de santé ni coffre persistant** (pas de nouvelle DB clinique SQLite/IndexedDB/OPFS pour un visiteur, pas de données cliniques en localStorage, aucune consultation du coffre d'un autre utilisateur). Démonstrations synthétiques isolées ; les outils QA loopback/audit ne sont pas des comptes invités utilisateurs.
5. **Compte = identité stable vérifiée et portée patient explicite.** Une session locale enrôlée, le mode audit, une session Firebase anonyme et un token restauré hors ligne **ne valent pas automatiquement un compte distant vérifié**. Un seul patient par scope et permissions serveur sur chaque requête ; la reconnexion réseau n'est pas forcément requise à chaque action **après authentification**, si le coffre chiffré local et son déverrouillage hors ligne sont ultérieurement certifiés. Séparer « se connecter » et « déverrouiller localement ».
6. **Utilisateurs existants = zéro confiscation/suppression de données.** Les coffres historiques device-only/anonymous/plaintext sont préservés sous politique SAFE-HOLD et doivent avoir un chemin de reprise sécurisé avant tout changement d'accès. Ne jamais attribuer silencieusement le coffre historique au prochain compte connecté. Les anciennes PWA/offline peuvent continuer à écrire : **une nouvelle connexion obligatoire ne résout PAS D18 P0-A**.
7. **Aucune sortie externe d'information de santé, photo ou habitudes sans contrat de finalité, consentement pertinent, minimisation, contrôle d'AI OFF et revue privacy.** Aucune suggestion ML/LLM n'est une donnée clinique certaine ni un conseil de dose. D19/D32 restent les autorités pour toute règle médicale.
8. **Aucune fusion dans main, migration patient, déploiement Vercel Preview ou Production sans gates pertinents et autorisation explicite pour Vercel.** Un merge susceptible de déployer n'est pas autorisé implicitement. Chaque lot : Goal → succès observable → preuve exacte SHA + comportement navigateur → docs → revue → merge/postmerge selon autorisations.

## 1. Arbitrage D33–D38 (nouveaux points du 04/11)

Ces identifiants correspondent **aux numéros 33 à 38 donnés par le propriétaire**. D34, D35, D36, D37 et D38 ont reçu une **décision produit explicite le 04/11/2026** ; D33 reste l'orientation Web-first déjà formulée. Les choix ne prouvent aucune implémentation. D31 (tests physiques historiques) et D32 (science/clinique) restent des références distinctes, pas des numéros réutilisables.

| ID | Besoin fourni | Spécification candidate / objection | Validation |
|---|---|---|---|
| **D33** | Focus Web first | Flutter Web/PWA avant natif ; appareils mobiles réels pour tester le Web | Orientation propriétaire explicite ; périmètre détaillé à confirmer |
| **D34** | Reconnaissance photo avec modèle léger, apprentissage repas | Modèle vision/VLM léger à benchmarker ; propositions incertaines d'aliments/portions, correction/ajout humain, enregistrement explicite, favoris confirmés ; saisie manuelle maintenue IA OFF | **CHOIX A ACCEPTÉ** (O5) ; fournisseur, coûts, précision et D24/privacy non validés ; D14 demeure PAUSED |
| **D35** | Apprendre les habitudes utiles (sommeil, heures de saisie et repas, aliments…) | Apprentissage **opt-in désactivé par défaut**, depuis entrées confirmées/déclarées ; consultation, correction, effacement et arrêt ; sommeil uniquement déclaré ou source autorisée ; règles déterministes privilégiées, sans inférence clinique | **CHOIX A ACCEPTÉ** (O6) ; rétention, architecture et tests privacy restent à prouver |
| **D36** | « Profile » → « Settings » | **Page unique Paramètres remplaçant Profil** ; compte, unités, données, IA/consentements, notifications, confidentialité et inventaire appareils/CGM non activé ; pas de seconde entrée Profil | **CHOIX A ACCEPTÉ** (O4) ; maquette, accessibilité FR/AR et QA Web restant à faire |
| **D37** | Connexion sans compte limitée | **Navigation dans l'intégralité du shell Web/PWA** avec états vides et exemples explicitement fictifs ; authentification AVANT DB/stockage clinique/fetch métier ou service externe ; aucun coffre invité ni chrono | **CHOIX A ACCEPTÉ** (O1) ; audit auto-fetch, isolation et D18/W01 restent gates L01 |
| **D38** | « Application setting » fermé par défaut | Accordéon **replié par défaut**, ouverture volontaire, état accessible clavier/lecteur d'écran et FR/AR RTL ; pas de persistance clinique de l'état UI invité | **CHOIX A ACCEPTÉ** (O4) ; BEFORE/AFTER et QA non réalisés |

**Décision UX O1/D37-A VALIDÉE :** accès au shell complet dès l'entrée, uniquement écrans vides/fictifs et ressources publiques ; connexion/inscription obligatoire avant données ou service métier. **Cette décision n'est pas une activation et n'écarte pas D18/W01.**

## 2. ROADMAP ACTIVE CONSOLIDÉE — 10/11/2026 — UNIQUEMENT LE RESTE À FAIRE

**Un chantier, une décision d'exécution à la fois.** Cette section remplace les ordres L00–L09, W00–W14, A/B et les numéros D1–D38 comme files d'attente concurrentes. Les numéros D conservent leur sens historique mais n'imposent aucun ordre. L00 a achevé la réconciliation documentaire initiale le 04/11 ; il n'est plus un lot prospectif. Les travaux déjà fusionnés et acceptés sur leur périmètre sont **exclus de la file active**, même lorsqu'un autre lot porte encore une obligation transverse. Une fonctionnalité livrée n'est réouverte que sur défaut nouveau, preuve manquante d'une exigence distincte ou contradiction vérifiée.

**Base de comparaison :** main@61f51ee7bbbfec829acfd1160761b99e36a1c48c observé le 10/11/2026 ; [D7 QA #1334](https://github.com/hraaaaf/IAMINA-MVP/pull/1334) fusionnée mais D7 hébergé non certifié ; [W03 #1302](https://github.com/hraaaaf/IAMINA-MVP/pull/1302) fusionnée mais non déployée. La présente consolidation est préparée dans [PR documentaire #1270](https://github.com/hraaaaf/IAMINA-MVP/pull/1270), **DRAFT/NON FUSIONNÉE**. Aucun changement de code, DB ou Vercel par cette opération.

### DÉJÀ LIVRÉ / HORS FILE ACTIVE — ne pas réimplémenter

- **D3** rappels Accueil ([#1230](https://github.com/hraaaaf/IAMINA-MVP/pull/1230) merged), **D5** pays explicite ([#1205](https://github.com/hraaaaf/IAMINA-MVP/pull/1205) merged), **D8** unité choisie sans suggestion par IP ([#1269](https://github.com/hraaaaf/IAMINA-MVP/pull/1269) merged), **D22** unité avant objectifs et affichage fail-closed ([#1249](https://github.com/hraaaaf/IAMINA-MVP/pull/1249) closeout merged), **D30** accès local livré à son périmètre ancien ([#1169](https://github.com/hraaaaf/IAMINA-MVP/pull/1169) merged).
- **D6, D11, D17, D21, D27** : décisions livrées bornées d'après la réconciliation Notion du 04/11 ; conserver leurs preuves, ne pas créer de lots correctifs sans régression reproductible. **D16** : copie sélective Companion fusionnée, ne pas refaire cette livraison ; extension non exigée explicitement exclue à ce stade.
- **D7** : livraison médicale limitée et tests GitHub #986, #1334 fusionnés ; **les preuves D7 hébergées et les gates clinique/privacy non couverts ne sont pas clôturés** et sont regroupés avec la frontière de compte/consentement ci-dessous, sans rouvrir les composants déjà livrés.
- **D12** : PR [#1251](https://github.com/hraaaaf/IAMINA-MVP/pull/1251) merged **dans la branche D13, pas attestée sur main** au registre. Réconcilier le delta seulement au lot D13 ; ne pas recommencer la saisie fonctionnelle déjà acceptée.

### File de décisions restantes, dans cet ordre de dépendances

#### R01 — D37 · Frontière VISITEUR → COMPTE (D30 seulement en compatibilité)
**GOAL :** shell Web/PWA accessible sans compte, uniquement écrans vides/fictifs ; login avant accès à DB santé, coffre, fetch métier, photo ou service externe. Aucune durée arbitraire. **SUCCESS :** 0 lecture/écriture clinique et 0 coffre invité ; retour utile à l'action après authentification. **PROOF :** Chrome/Safari FR/AR RTL 390/430/768/1280, route directe, offline, auto-fetch, API 401/403, A→B→A ; captures BEFORE/AFTER. **GATE :** anciennes PWA et D18 non neutralisés par simple changement de route.

#### R02 — D18 · Coffre, reprise legacy et sécurité (résidu D9/D10/D26/D7, W01/W02)
**GOAL :** préserver sans perte les anciens coffres device-only, vérifier séparation des comptes, sessions Django, app-lock et récupération volontaire sûre ; aucune réattribution automatique, aucune suppression/synchronisation implicite. **SUCCESS :** vieux onglets/offline bloqués à l'écriture incohérente, récupération après preuve de possession, isolation A→B→A, purge/révocation gouvernées, aucune donnée clinique d'un autre propriétaire. **PROOF :** tests réels Drift/IndexedDB/VFS, Chrome/Safari, PostgreSQL16 éphémère, auth+API et backup/restore indépendants ; pré/post-migration sans perte. **BLOCKER :** D18 SAFE-HOLD/NO-GO clinique ; PR D9 [#1159](https://github.com/hraaaaf/IAMINA-MVP/pull/1159), D10 [#1246](https://github.com/hraaaaf/IAMINA-MVP/pull/1246), D18 [#1265](https://github.com/hraaaaf/IAMINA-MVP/pull/1265) encore Draft ; D7 hosted C01–C05 et revues clinique/privacy non signés. Travaux préflight fictifs seulement jusqu'aux gates.

#### R03 — D24 · Consentements granulaires IA et révocation serveur (D26)
**GOAL :** consentements photo, habitudes et compagnon indépendants, OFF par défaut, révocables ; pas de sortie santé sans finalité, identité et payload minimal. **SUCCESS :** un retrait coupe immédiatement serveur et UI, même avec requête concurrente ouverte ; saisie manuelle fonctionne IA OFF ; aucune donnée inter-patients. **PROOF :** tests API négatifs, sécurité/egress, Web FR/AR et revues privacy ; [#1244](https://github.com/hraaaaf/IAMINA-MVP/pull/1244) Draft. **GATE :** consentement réel non déduit de la seule UI.

#### R04 — D13 · Sauvegarde et reprise de brouillon (D15 manuel, résidu D12)
**GOAL :** sauvegarder une seule fois après validation, prévenir sortie accidentelle/perte/duplication, récupérer uniquement le brouillon d'un compte authentifié ; aucune persistance de santé invitée. **SUCCESS :** après offline, refresh, mauvais appui ou deux Save, aucune perte ni double insertion ; champs glycémie/unités/nutrition inconnue explicites. **PROOF :** vrai Save Drift, tests de retry + navigation + multi-onglet, FR/AR ; [#1250](https://github.com/hraaaaf/IAMINA-MVP/pull/1250) Draft ; réconcilier [#1251](https://github.com/hraaaaf/IAMINA-MVP/pull/1251) uniquement si delta absent de main. **GATE :** R01/R02 pour stockage clinique.

#### R05 — D36 · Page unique Paramètres (D38, D23, D25 inventaire, D26)
**GOAL :** remplacer Profil par Paramètres, organiser compte/données/unités/consentements/notifications/sécurité ; D38 « Paramètres de l'application » replié par défaut ; appareils/CGM affichés uniquement comme inventaire, pas comme connectés. **SUCCESS :** une seule entrée de navigation, état accessible, A/B isolés, contrôle explicite des fonctions réellement implémentées. **PROOF :** BEFORE → cible → AFTER aux mêmes viewports 390/430/768/1280, FR/AR RTL, clavier, zoom 200 %, tests UX. **GATE :** ne pas exposer une action de suppression/consentement non certifiée.

#### R06 — D34 · Photo alimentaire et repas multimodal (D14 PAUSED, D15)
**GOAL :** avant activation, lever explicitement le PAUSED D14 ; benchmarker modèle vision/VLM léger sur plats MENA et incertitude ; photo/voix/texte dans un seul brouillon à confirmation humaine, aliments inconnus ajoutables et favoris. **SUCCESS :** aucune proposition transformée en vérité clinique ou ajoutée sans Save, aucun egress sans D24, IA OFF laisse la saisie manuelle. **PROOF :** corpus synthétique, tests négatifs, précision par aliment/portion, coût et rétention, FUE FR/AR ; [#1245](https://github.com/hraaaaf/IAMINA-MVP/pull/1245) et [#1257](https://github.com/hraaaaf/IAMINA-MVP/pull/1257) Draft. **GATE :** R03/R04 + revue clinique/privacy.

#### R07 — D35 · Habitudes utiles consenties (résidu D28 non clinique)
**GOAL :** horaires de repas/saisie, favoris et sommeil uniquement déclaré/autorisés, opt-in OFF par défaut, correction/effacement ; moteur déterministe en premier. **SUCCESS :** aucun profilage invité, pas d'inférence de maladie ou de traitement, retrait effectif et patient A/B isolé. **PROOF :** tests provenance, suppression/retenue, offline/sync et audit privacy. **GATE :** R03/R02 et règle de rétention approuvée.

#### R08 — D32 · Validation clinique indépendante (résidu D19/D28/D20)
**GOAL :** certifier l'autorité déterministe, formules, unités, calculs CGM vs mesures ponctuelles, dates, manque de données, tendances descriptives et absence de conseil thérapeutique. **SUCCESS :** aucune règle clinique patient visible sans source applicable, validation humaine qualifiée et oracles indépendants ; pas de dose ni diagnostic. **PROOF :** matrice D32 G1–G7, comparaisons backend/Flutter, cas limites FR/AR, revue endocrinologique ; [#920](https://github.com/hraaaaf/IAMINA-MVP/pull/920) Draft. **GATE :** scientifique/clinique humain ; D22 technique déjà fusionnée ne doit pas être refaite.

#### R09 — D4 · Rapports et exports médicaux (CAL-12)
**GOAL :** exports PDF/CSV/XLSX fidèles aux données, consentement d'export distinct, destinataire professionnel, révocation, conservation/purge, FUE Flutter Web authentifiée. **SUCCESS :** fichier exact, lisible FR/AR, A→B→A refusé, aucun export d'un autre patient, identité et consentement revalidés au moment de la livraison. **PROOF :** vrai Flutter Web+coffre+API/PG16 et revues R1 médical/R3 privacy/R4 arabe-assistive/R6 produit, non remplacées par un PDF fictif. **GATE :** CAL12_REAL_PATIENT_EXPORT=NO_GO ; [#1332](https://github.com/hraaaaf/IAMINA-MVP/pull/1332), [#1333](https://github.com/hraaaaf/IAMINA-MVP/pull/1333), [#1335](https://github.com/hraaaaf/IAMINA-MVP/pull/1335), [#1336](https://github.com/hraaaaf/IAMINA-MVP/pull/1336) Draft et empilées ; #1336 ne prouve qu'une UI HTML synthétique/CI, non la vraie app. R02 et R08 prérequis.

#### R10 — D2 · Notifications consenties, poids et feedback (D20/D29)
**GOAL :** préférences de notification réelles, cadence maîtrisée, historique/aperçu, purge J+7 et revocation, tendance de poids purement descriptive, feedback libre non intrusif. **SUCCESS :** aucun envoi sans opt-in ; scheduler vérifié sans fuite/retard non signalé ; suppression vérifiable ; aucun conseil thérapeutique. **PROOF :** tests web/API multi-comptes, sécurité du scheduler, rollback/PITR et preuves hosted sur source autorisée ; [#1153](https://github.com/hraaaaf/IAMINA-MVP/pull/1153) Draft très large, ne pas fusionner en bloc sans réconciliation. **GATE :** R02/R03/R08 selon notification et politique légale.

#### R11 — D1 · CGM officiels — DERNIÈRE fonctionnalité (D25 connexion)
**GOAL :** intégrer **une seule source fabricant/API officiellement autorisée à la fois**, Nightscout facultatif, lecture seule, preuve d'unité, horodatage, trous, révocation et confidentialité. **SUCCESS :** provenance des capteurs, absence de TIR artificiel si données insuffisantes, aucun pouvoir de traitement, déconnexion fail-closed. **PROOF :** tests API, device simulé/autorisé, métriques D32 et sécurité/privacy. **GATE :** R08 et précédents, autorisation de source/pays. Aucune connexion fabricant supposée active.

#### R12 — W14 · Certification Web/PWA et lancement contrôlé — DERNIER
**GOAL :** préproduction sans patient, sessions et coffres, sécurité/consentements, clinique, accessibilité, conformité, CI exact SHA, review indépendante, pilote borné. **SUCCESS :** contrôles GO/NO-GO vérifiés par domaine ; aucun BLOCKER/MAJOR ouvert ; PR merge/postmerge vérifiés. **PROOF :** matrice de tests, captures FR/AR 390/430/768/1280 + Safari/Chromium et 200 % zoom, rétablissement DB, audits et validation humaine. **GATE :** aucune publication Vercel Preview ou Production sans **autorisation explicite distincte**. D31 essais natifs physiques sont différés **hors chantier Web**, sauf test d'un navigateur sur téléphone réel.

### Arbitrages remplacés, simplifiés ou mis en archive

- D8 « suggestion automatique selon pays » **REMPLACÉE** par choix manuel explicite de l'unité, déjà fusionné (#1269).
- D30 ancien mode « sans compte avec coffre local » **NON APPLICABLE au nouveau visiteur D37** ; préserver les données legacy sans les ouvrir au visiteur, traiter R02.
- D24 éventuel consentement IA unique **REMPLACÉ** par trois finalités granulaires indépendantes, OFF par défaut.
- Ancienne consigne « login après cinq minutes » **ABANDONNÉE** ; authentification au besoin, avant action métier.
- D14 **PAUSED malgré** décision D34-A sur la direction produit ; aucun fournisseur photo autorisé implicitement.
- W00–W14, A/B, P5 et L00–L09 : **archives de preuve et de provenance, pas autre file de travail**.
- D31 : essais physiques natifs **DIFFÉRÉS** (Web first). D33 : doctrine transversale, **pas lot d'implémentation**. D32 : revue clinique encore ouverte, non confondue avec D22 technique.
- Les statuts de décisions complètes déjà fusionnées sont gardés dans l'index §3 **à titre historique seulement**. Aucun pourcentage d'avancement global calculé sans oracle.

**NEXT unique : R01/D37** — inspecter le routeur Web, les accès aux coffres Drift/IndexedDB et les fetchs métier avec une matrice invité/compte vérifié/legacy, puis produire le test de refus avant toute modification. Conserver R02/D18 en garde de sécurité non contournable. Aucun nouveau merge ni déploiement autorisé par cette consolidation.

## 3. INDEX HISTORIQUE DE TRAÇABILITÉ D1–D38 — HORS ROADMAP ACTIVE (snapshot 04/11/2026)

**Cet index conserve les décisions et preuves historiques, y compris les éléments déjà fusionnés. Il ne constitue ni un ordre d'exécution ni une liste de tâches ouvertes. Seule la section 2 fait foi pour les travaux prospectifs.**

**Légende :** LIVRÉ BORNÉ = preuve sur périmètre indiqué, non certification générale ; PARTIEL = code ou livraisons limitées ; DRAFT = PR non fusionnée ; OPEN = résultat non attesté ; PROPOSÉ = à arbitrer au cours de cet onboarding. Les statuts historiques viennent du registre Notion D1–D30, des chantiers A/B et des PR GitHub consultées ; **un status sans PR/live vérifiés aujourd'hui reste une photographie documentaire**, jamais un constat d'exécution immédiate.

| Décision et scope historique | État le mieux justifié | Lot principal |
|---|---|---|
| D1 — Hub CGM, Nightscout non obligatoire | **O9-A stratégie produit approuvée** ; connecteurs non autorisés/non livrés, **dernière fonction** | L08 |
| D2 — Notifications intelligentes consenties | PARTIEL ; **O8-A limite aux rappels consentis**, scheduler/hosted non certifiés, #1153 Draft | L07 |
| D3 — Rappels Accueil programmés | LIVRÉ BORNÉ Web | L07 régression |
| D4 — Exports PDF/CSV/XLSX cohérents | OPEN ; **O8-A périmètre factuel et sourcé**, implémentation non validée | L06 |
| D5 — Pays choisi explicitement | LIVRÉ BORNÉ Web | L02 régression |
| D6 — Ton du compagnon fixe (pas de sélecteur) | LIVRÉ BORNÉ Web | L07 régression |
| D7 — Diabète/traitements multiples | ACCEPTÉ BORNÉ, validation clinique restant | L02 |
| D8 — Unité choisie avant usage, **sans suggestion pays** | **LIVE / CLOSED Web borné** (#1269) | L02 régression |
| D9 — Retour compte existant sans re-onboarding | PARTIEL ; **O2-A récupération volontaire approuvée**, #1159 Draft et A→B→A ouvert | L01/L02 |
| D10 — App-lock, récupération, réversibilité | PARTIEL ; **O3-A ne porte que sur consentement IA**, #1246 Draft, revue sécurité ouverte | L01/L03 |
| D11 — Compte vierge, démo isolée | LIVRÉ BORNÉ | L01 régression |
| D12 — Saisie glycémie précise slider/clavier | LIVRÉ BORNÉ dans chaîne D13, fusion main à vérifier | L02 |
| D13 — Sauvegarde/brouillon sans perte | **O7-A produit approuvé**, DRAFT #1250, CI ciblées vertes, non fusionné | L02 |
| D14 — Photo repas confirmée par l'utilisateur | **PAUSED** #1245 Draft ; **D34-A direction photo acceptée**, gate D14 non levé | L04 |
| D15 — Un brouillon repas photo/voix/texte | PARTIEL ; **O7-A brouillon confirmé**, #1257 Draft ; aucune activation photo/voix réelle | L02/L04 |
| D16 — Copier textes utiles | PARTIEL, sélection Companion seulement | L07 |
| D17 — Détails techniques sous « i » | LIVRÉ BORNÉ Web | L07 régression |
| D18 — Données progressives + protection du coffre | **NO-GO clinique maintenu** ; **O2-A reprise manuelle cible seulement**, aucune migration | L01/L02 |
| D19 — Calculs cliniques cohérents | PARTIEL ; **O8-A pas de thérapeutique**, #920 Draft, revue scientifique D32 ouverte | L06 |
| D20 — Poids/tendance et messages volontaires | PARTIEL, PR historiques Draft | L06/L07 |
| D21 — Ramadan masqué sous feature flag | LIVRÉ BORNÉ Web | L07 régression |
| D22 — Unités avant objectifs, fail-closed | TECHNIQUEMENT ACCEPTÉ / MERGED, D32 ouvert | L02/L06 |
| D23 — Préférences App/compagnon regroupées | OPEN ; fusion avec D36 | L03 |
| D24 — IA OFF, consentement et API | DRAFT #1244 ; **O3-A consentement granulaire accepté**, gardes API/sécurité non certifiés | L01/L03 |
| D25 — Données et appareils / CGM | OPEN ; **O9-A sources progressives acceptées**, inventaire L03, connecteurs L08 non activés | L03/L08 |
| D26 — Confidentialité, déconnexion/suppression | OPEN ; **O3-A ne certifie pas l'effacement**, W02 prérequis non certifiés | L01/L03 |
| D27 — Avatar IAmina Accueil uniquement | LIVRÉ BORNÉ Web | L07 régression |
| D28 — Intelligence gouvernée avant dialogue | OPEN ; moteur partiel sans clôture produit | L05/L06 |
| D29 — Feedback volontaire après premier usage | OPEN | L02/L07 |
| D30 — Choix local/sans compte et privacy-first | LIVRÉ BORNÉ ancien ; **O1/D37-A shell invité, O2-A legacy approuvés**, sécurité non prouvée | L01 |
| D31 — Gate tests matériels natifs historiques | OPEN ; **différé hors priorité Web** | après L09 si natif |
| D32 — Validation scientifique/clinique G1–G7 | **OPEN**, indépendante des CI UI ; **O8-A ne la remplace pas** | L06/L08, transverse |
| D33 — Focus Web first | **NOUVELLE ORIENTATION, à détailler** | tous |
| D34 — Photo, VLM léger, repas inconnus et favoris | **D34-A PRODUIT ACCEPTÉ**, fournisseur/privacy/test non validés | L04 |
| D35 — Apprentissage habitudes utiles | **D35-A PRODUIT ACCEPTÉ**, opt-in OFF initial, rétention/test à définir | L05 |
| D36 — Profil → Paramètres détaillés | **D36-A PRODUIT ACCEPTÉ**, page unique, UI non implémentée | L03 |
| D37 — Entrée sans compte, login au besoin DB/fetch | **D37-A PRODUIT ACCEPTÉ**, shell complet fictif, gates L01 ouverts | L01 |
| D38 — « Application setting » fermé par défaut | **D38-A PRODUIT ACCEPTÉ**, fermé par défaut, QA non réalisée | L03 |

## 4. ARCHIVE — décisions d'onboarding validées le 04/11/2026 (ne crée pas de seconde roadmap)

**État exact : 10 thèmes O1–O10 arbitrés, soit 11 choix produit ACCEPTÉS** (O4 a deux décisions distinctes D36/D38). Chaque approbation est **un choix produit seulement**, pas une preuve d'implémentation, de sécurité, de certification, de merge ou de disponibilité. L'ancien ordre L00→L09 est archivé ; seule la section 2 (R01→R12) fixe l'ordre prospectif depuis le 10/11/2026.

1. **O1 / D37-A — visiteur : ACCEPTÉ.** Shell Web/PWA entièrement navigable en statique/fictif ; login avant DB/stockage patient/fetch métier ; aucune création de coffre invité, aucun chrono. [Décision](https://github.com/hraaaaf/IAMINA-MVP/pull/1270#issuecomment-6632954086). **Gate** : L01 audit auto-fetch, routeur+API+stockage, W01/D18.
2. **O2 / D30-D9-D18-A — anciennes données : ACCEPTÉ.** Récupération volontaire après login, seulement après preuve de possession et sécurité certifiée ; original conservé, zéro rattachement/suppression/conversion automatique ; état ambigu = aucune mutation. [Décision](https://github.com/hraaaaf/IAMINA-MVP/pull/1270#issuecomment-6633315382). **Gate** : D18 P0-A SAFE-HOLD/NO-GO clinique ; W01 et vieux clients PWA.
3. **O3 / D10-D24-D26-A — consentement IA par fonction : ACCEPTÉ POUR CET ARBITRAGE SEULEMENT.** Photo D34, habitudes D35, compagnon IA distincts ; OFF par défaut ; retrait indépendant et garde Web + API ; saisie manuelle toujours possible. [Décision](https://github.com/hraaaaf/IAMINA-MVP/pull/1270#issuecomment-6633364789). **Restent ouverts** : app-lock D10, isolation/identité, effacement D26, implémentation et audit D24, rétention.
4. **O4 / D36-A + D38-A — Paramètres : DEUX CHOIX ACCEPTÉS.** Remplacer Profil par une page unique Paramètres contenant Compte et profil, données, unités, consentements, notifications, sécurité et inventaire appareils ; **aucun branchement CGM précoce**. Section « Paramètres de l'application » **fermée par défaut** et ouvrable volontairement. [D36](https://github.com/hraaaaf/IAMINA-MVP/pull/1270#issuecomment-6633141316) · [D38](https://github.com/hraaaaf/IAMINA-MVP/pull/1270#issuecomment-6633206362). **Gate** : maquette, BEFORE/AFTER, responsive, accessibilité FR/AR RTL.
5. **O5 / D14-D34-A — photo alimentaire : ACCEPTÉ COMME DIRECTION.** Vision/VLM léger candidat ; aliments/portions incertains, correction et confirmation obligatoire, repas inconnus et favoris, saisie manuelle de secours. [Décision](https://github.com/hraaaaf/IAMINA-MVP/pull/1270#issuecomment-6633012424). **Gate** : D14 reste PAUSED, D24 consentement/egress et benchmark modèle non faits.
6. **O6 / D35-A — habitudes : ACCEPTÉ.** Opt-in explicite OFF par défaut, données confirmées/déclarées uniquement, favoris/horaires/sommeil volontaire, contrôle/correction/suppression ; statistiques déterministes privilégiées. [Décision](https://github.com/hraaaaf/IAMINA-MVP/pull/1270#issuecomment-6633078310). **Gate** : rétention, isolation, effacement et consentement D24.
7. **O7 / D13-D15-A — brouillons : ACCEPTÉ.** Récupération protégée pour compte authentifié, journal médical distinct, confirmation explicite et anti-doublon sur retry/offline. Aucun brouillon médical en invité. [Décision](https://github.com/hraaaaf/IAMINA-MVP/pull/1270#issuecomment-6633439730). **Gate** : D18/W01, D13 #1250 et D15 #1257 non fusionnées.
8. **O8 / D19-D32-D2-D4-A — clinique/rapports/notifications : ACCEPTÉ POUR V1 WEB.** Mesures/tendances factuelles, calculs déterministes seulement après évaluation D32 indépendante, rapports sourcés avec unités/périodes/limites, rappels consentis ; **pas de diagnostic, dose ni adaptation de traitement**. [Décision](https://github.com/hraaaaf/IAMINA-MVP/pull/1270#issuecomment-6633519546). **Gate** : D19 et D32 non certifiés, D2 et D4 non prouvés.
9. **O9 / D1-D25-A — CGM : ACCEPTÉ.** Dernier lot fonctionnel L08 ; intégrer une source autorisée à la fois, avec accès fabricant/API/pays, consentement, révocation, tests dispositifs et D32 ; Nightscout facultatif. [Décision](https://github.com/hraaaaf/IAMINA-MVP/pull/1270#issuecomment-6633581955). **Gate** : aucune compatibilité fabricant ou pays supposée ; pas de connecteur activé.
10. **O10 / W14-A — certification : ACCEPTÉE COMME PROTOCOLE.** Gates GO/NO-GO successifs : identité et anciens coffres/backup/offline ; confidentialité et consentement ; clinique scientifique ; UX Web et accessibilité ; conformité et revue indépendante ; CI sur SHA exact ; pilote borné. [Décision](https://github.com/hraaaaf/IAMINA-MVP/pull/1270#issuecomment-6633646492). **Gate** : aucune certification accomplie, et **autorisation explicite séparée avant chaque Preview/Production Vercel** ; pas de merge automatique.

**Règle de statut :** ACCEPTÉ=arbitrage produit décidé ; LIVRÉ exige preuve de code+tests+comportement+release autorisée ; CERTIFIÉ exige contrôles indépendants et traces. **Ni le nombre de choix ni la CI documentaire ne constituent un pourcentage de chantier certifié.**

**Clôture documentaire L00 :** index D1–D38 unique, lots L00–L09, 11 liens d'arbitrage, diff Markdown seul, CI SHA exact et miroir Notion ont été vérifiés lors de la réconciliation du 04/11/2026. **Adoption du plan par le propriétaire : OUI (réponse explicite « Go », 04/11/2026).** Cela **n'autorise pas** la fusion de la PR #1270, le déploiement Vercel Preview/Production ou la manipulation de données de patients ; les blocages D18, W01 et D32 persistent. **Ancien Next L01 (archivé) :** établir la baseline router/mount/DB/fetch et la matrice invité/compte/legacy. **Next actif au 10/11/2026 : R01/D37 (section 2), avec D18/R02 en garde de sécurité.** Aucune migration, suppression, nouvelle ouverture patient ni activation sans preuve et revue dédiée.

## 5. Preuves de départ, liens et limites

- [Résumé officiel des D1–D29](https://app.notion.com/p/3fa77c66336281aaaff4f2781d86cc21), [registre D1–D30 et réconciliation A/B](https://app.notion.com/p/40777c6633628177b325d3cb5412fc18), [Chantier B / D8 livré](https://app.notion.com/p/40777c66336281729c03c9bb294e71b7), [D18 SAFE-HOLD](https://app.notion.com/p/40d77c663362812381dfe50543c8471f).
- GitHub main observé au départ de cette refonte : **d7d650a082300486764019c8238f591057210d54**. [D8 #1269](https://github.com/hraaaaf/IAMINA-MVP/pull/1269) MERGED et Web production confirmée dans le registre B ; [D18 #1265](https://github.com/hraaaaf/IAMINA-MVP/pull/1265) Draft, avec [Chromium #41839588272](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41839588272) et [WebKit #41839588203](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41839588203) SUCCESS préclinique ; D18 NO-GO ; [D32 issue #1248](https://github.com/hraaaaf/IAMINA-MVP/issues/1248).
- PRs ouvertes vérifiées au contrôle documentaire : [D13 #1250](https://github.com/hraaaaf/IAMINA-MVP/pull/1250), [D15 #1257](https://github.com/hraaaaf/IAMINA-MVP/pull/1257), [D24 #1244](https://github.com/hraaaaf/IAMINA-MVP/pull/1244), [D14 #1245](https://github.com/hraaaaf/IAMINA-MVP/pull/1245), [D10 #1246](https://github.com/hraaaaf/IAMINA-MVP/pull/1246), [D9 #1159](https://github.com/hraaaaf/IAMINA-MVP/pull/1159), [D2/W01 #1153](https://github.com/hraaaaf/IAMINA-MVP/pull/1153) et [D19 #920](https://github.com/hraaaaf/IAMINA-MVP/pull/920) : toutes Draft à cet instant.
- L'environnement connecté est un **snapshot**, pas un audit de tous les commits, tickets et serveurs. Les certifications patient, hébergement serveur, sauvegarde, restauration et réglementation ne sont PAS acquises par cette opération documentaire. Respecter les prérequis vérifiés avant chaque lot.
