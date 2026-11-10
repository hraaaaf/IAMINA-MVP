# IAMINA — ROADMAP CANONIQUE UNIQUE · Décisions RESTANTES · Web/PWA

**Édition : 10/11/2026. Statut : CANDIDAT DOCUMENTAIRE / NON FUSIONNÉ / NON DÉPLOYÉ.** Un seul chantier, une décision d'exécution à la fois. Cette page est la **seule roadmap prospective** IAMINA. Conserver le registre historique D1–D38 mais ne pas réinsérer dans l'ordre actif les fonctionnalités déjà entièrement fusionnées et acceptées sur leur périmètre.

**Traçabilité :** [Notion canonique](https://app.notion.com/p/3df77c66336281f5b308ec17f7f0a63b) · [ancienne roadmap Web W00–W14 archivée intégralement](archive/roadmap-pre-single-active-2026-11-10.md) · [arbitrages D1–D38 adoptés le 04/11](https://github.com/hraaaaf/IAMINA-MVP/pull/1270). Les notes d'implémentation et les preuves fusionnées sont historiques, **pas un second plan**. Baseline de départ : `main@61f51ee7bbbfec829acfd1160761b99e36a1c48c` (10/11/2026). Les PR et le runtime doivent être revérifiés à chaque nouvelle décision.

**Garde permanente :** priorité Web/PWA Flutter (FR/AR, RTL, 390/430/768/1280 et accessibilité), aucune donnée de patient réelle dans les essais, autorité clinique déterministe, consentement et séparation par patient, anciens coffres préservés. GOAL / SUCCESS / PROOF vérifiables par lot. **Aucun merge, migration patient ou déploiement Vercel Preview/Production n'est autorisé par l'adoption de cette roadmap ; Vercel exige le GO explicite du propriétaire pour chaque déploiement.**

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

## 3. Provenance et gouvernance

Les identifiants D1–D38 demeurent des **références historiques de décision**, sans obligation de recréer les livraisons fusionnées. Le registre Notion du [04/11 (D1–D30)](https://app.notion.com/p/40777c6633628177b325d3cb5412fc18), la [roadmap D1–D38 de travail](https://github.com/hraaaaf/IAMINA-MVP/pull/1270) et l'[ancienne roadmap main archivée](archive/roadmap-pre-single-active-2026-11-10.md) restent consultables. Toute preuve ancienne est limitée à son exact SHA, périmètre, environnement et revue.

**Critère de clôture :** preuve technique réelle, vérification de sécurité et clinique adaptée, CI sur HEAD exact, validation UX BEFORE/AFTER pour changements significatifs, revue, merge/postmerge si applicable et actualisation de ce fichier et de Notion. Une PR mergée partiellement ne prouve pas un objectif clinique complet. Un GO produit n'est pas un GO de déploiement.

**Next unique : R01 / D37, puis R02 / D18**, sans contournement du SAFE-HOLD ni des gates de consentement et de confidentialité.
