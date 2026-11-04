# IAMINA — ROADMAP CANONIQUE UNIQUE · Web/PWA · D1–D38

**Édition :** 2026-11-04 · **Statut : PROPOSITION À ARBITRER PAR ONBOARDING avec le propriétaire, PAS une certification ni une autorisation de déployer.**
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

Ces identifiants correspondent **aux numéros 33 à 38 donnés par le propriétaire** ; ils sont une **proposition de spécification**, à fixer ensemble pendant l'onboarding. D31 (tests physiques historiques) et D32 (science/clinique) restent des références distinctes, pas des numéros réutilisables.

| ID | Besoin fourni | Spécification candidate / objection | Validation |
|---|---|---|---|
| **D33** | Focus Web first | Flutter Web/PWA avant natif ; appareils mobiles réels pour tester le Web | Orientation propriétaire explicite ; périmètre détaillé à confirmer |
| **D34** | Reconnaissance photo avec modèle léger, apprentissage repas | **Modèle vision ou vision-langage léger (VLM), pas un LLM texte seul** ; propositions d'aliments/portions incertaines, confirmation humaine obligatoire, ajout de repas non reconnus, favoris et accélération de la saisie | Périmètre autorisé, modèle et coûts à benchmarker ; photo patient désactivée tant que D24/privacy ouverts |
| **D35** | Apprendre les habitudes utiles (sommeil, heures de saisie et repas, aliments…) | Personnalisation **opt-in**, locale de préférence, déductible des entrées **autorisées et déclarées** ; corrections/suppression possibles ; aucune déduction clinique causale, ni surveillance cachée de sommeil ou horaires | Arbitrage consentement, rétention, source des données et contrôles de confidentialité |
| **D36** | « Profile » → « Settings » | Page **Paramètres** avec sous-sections Compte et profil, Unités/objectifs, Données/exports, CGM/appareils, IA/consentements, Notifications, Confidentialité/sécurité et Préférences | Maquette/ordre et traduction FR/AR à confirmer ; fusionner D23/D25/D26, pas recréer des écrans concurrents |
| **D37** | Connexion sans compte limitée | **Exploration sans inscription**, puis écran connexion/inscription **avant toute lecture/écriture DB ou fetch métier** ; aucune persistance de santé en visiteur ; préserver le chemin historique | Arbitrage immédiat du parcours invité + identité ; Gate L01 |
| **D38** | « Application setting » fermé par défaut | Accordéon fermé au rendu initial, état et clavier/accessibilité testés ; renommer/repositionner selon D36 | Priorité à la mise en place D36 ; maquette BEFORE/AFTER |

**Point UX à fixer avec le propriétaire en premier :** accès à l'interface de l'app dès l'entrée (shell complet et navigation possible), mais écrans vides/fictifs sans aucune lecture ou écriture de DB ni fetch métier en mode invité ; toute action nécessitant des données ou un service conduit immédiatement à connexion/inscription. Une proposition ne vaut pas activation.

## 2. Roadmap EXÉCUTABLE — ordre unique par risque, dépendances et valeur

Le numéro de décision ne définit **jamais** l'ordre de travaux. Seules les tranches suivantes constituent l'ordre prospectif. Chaque tranche peut contenir des validations concurrentes si indépendantes, mais aucune ne contourne une dépendance sécurité. Les clôtures précédentes ne doivent pas être refaites sans régression observée.

### L00 · Vérité et onboarding des décisions — PRIORITÉ IMMÉDIATE

**Goal :** une matrice D1–D38 complète, sans doubles statuts ni arbitrages tacites, et un accord explicite sur les nouveaux parcours (compte invité, stockage, ancienne identité, photo, habitudes et paramètres). **Succès :** 38/38 identifiants répertoriés avec périmètre, état vérifié/proposé, dépendance, lot et critère de preuve ; les décisions en débat sont clairement « proposées » jusqu'à choix utilisateur. **Preuve :** sources GitHub/Notion datées, PR documentaire Draft, validation du propriétaire au fil de l'onboarding. Pas de développement clinique dans L00.

### L01 · Frontière visiteur/compte et conservation des anciens coffres — P0 BLOQUANT

**Décisions : D30, D37, D11, D9, D10, D18, D24, D26, D33.** Architecture de session avec trois classes **visiteur volatile / compte patient vérifié / utilisateur historique local à récupérer**. Router, DB et API interdisent par défaut toute lecture/écriture clinique et tout fetch métier au visiteur. Supprimer l'ouverture de coffres persistants pour le vrai visiteur **seulement après** distinguer l'audit technique des comptes utilisateur ; rendre la connexion explicite au clic sur une fonction protégée. Séparer reconnexion et déverrouillage local. Flux A→déconnexion→B→A et deux onglets.

**Sous-gate parallèle D18 P0-A…D :** aucune bascule automatique de coffre historique plaintext→sqlite3mc. La vraie VFS Drift est IDB v1 avec stores blocks/files dans le Chromium CI testé ; la montée artificielle v1→v2 **n'empêche pas le stale opener sans version et empêche la réouverture Drift de la source**, malgré conservation des blocs. Le test 15/15 est une preuve d'INCOMPATIBILITÉ de cette option, pas de sécurité clinique. [Worker #41839588272](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41839588272) et [WebKit #41839588203](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41839588203) SUCCESS sur la PR Draft [#1265](https://github.com/hraaaaf/IAMINA-MVP/pull/1265), sans certification clinique. D18 bloque tout nouveau coffre chiffré **réel** jusqu'à preuve de clé, récupération, auth, stabilité VFS et audit ; la restriction invitée ne supprime PAS la dette sur anciens clients.

**W01 indispensable à la partie serveur :** preuve Preview Web→API→Postgres, identité patient A/B, permission par objet, rétention, isolation Neon, sauvegarde/restauration, journal d'accès, confidentialité et revues. Les anciens runs ou l'état de simple Preview READY ne certifient pas les flux patient.

**Critères L01 :** invité non authentifié ouvre l'app puis explore ; 0 coffre/écriture santé invité ; clic Ajouter mesure / photo / historique / appareil / API retourne vers login AVANT stockage/fetch ; retour à la tâche après login sans données médicales invitées ; test clavier, refresh, offline, onglet ancien, navigateurs, A/B et accès direct API. 0 patient perdu/migré. **BLOCAGE CLINIQUE ENCORE ACTIF.**

### L02 · Saisie sûre et onboarding clinique minimal — P0/P1

**Décisions : D13, D12, D7, D5, D8, D22, D9, D18 (champs progressifs), D15 (manuel), D29.** Reprendre D13 (prévenir perte de saisie ou double insertion), fiabiliser saisie manuelle glycémie/repas, unités explicites **mg/dL/mmol/L** avant objectifs, traitements multiples facultatifs, profil minimal et anciennes sessions sans onboarding imposé. D5 pays choisi explicite ; D8 **modifiée par le propriétaire puis livrée** : unité choisie par l'utilisateur, **sans présélection automatique pays/IP**. Aucune donnée démo dans un compte neuf.

**Succès :** cycle ouverture/saisie→retour accidentel→reprise ou refus de sortie, 1 Save=1 entrée, invalides refusées, pas d'insuline implicite, datetime/unité cohérentes, synthétique FR/AR+Safari/Chrome. **Preuve :** PR [#1250 D13](https://github.com/hraaaaf/IAMINA-MVP/pull/1250) Draft 12/12 CI antérieures, [#1257 D15](https://github.com/hraaaaf/IAMINA-MVP/pull/1257) Draft ; D12 livraison ciblée/branche et revue Web à réconcilier. Aucune certification globale inférée.

### L03 · Paramètres et contrôle utilisateur — P1

**Décisions : D36, D38, D23, D25, D26, D24, D10, D20.** Une page « Paramètres » à la place de « Profil », sections Compte/Profil, Données, CGM & appareils (inventaire sans branchement fabricant), AI, unités et objectifs, rappel/notification, confidentialité/consentement, suppression/déconnexion et app-lock. « Paramètres de l'application » **fermés par défaut**, expansion volontaire mémorisée au maximum dans la session d'UI, sans ouvrir un coffre pour cela. Ne pas exposer CGM comme connecté s'il n'est pas testé.

**Succès :** BEFORE→mockup→implémentation→AFTER sur 390/430/768/1280, FR/AR RTL, clavier/zoom, mêmes viewports ; suppression/revoke protégés, IA OFF propagée à client ET API, aucune préférence de patient A visible dans compte B. Gate D24 privacy requis.

### L04 · Repas photo, multimodal et apprentissage des aliments — P1/P2

**Décisions : D14, D15, D34, D24, D13.** Réévaluer la suspension explicite de D14 avant activation. Capture photo→propositions alimentaires et portions (modèle vision/VLM léger **candidat, aucun fournisseur choisi**)→l'utilisateur corrige, retire, ajoute un repas inconnu ou sauvegarde dans ses favoris→**un seul brouillon** photo/voix/texte/formulaire→Save explicite. L'app peut accélérer les prochaines propositions à partir des corrections confirmées, jamais à partir d'une reconnaissance non vérifiée. Évaluer qualité FR/AR/Darija, plats marocains, faux positifs, portions, latence, coût, batterie, disponibilité sans réseau et fuite de métadonnées. Pas de recommandation insulinique.

**Succès :** 0 écriture avant confirmation/Save ; IA OFF et absence consentement bloquent le modèle et toute sortie externe, sans bloquer saisie manuelle ; cas non reconnu → ajout manuel ; rapport d'erreurs et droit à l'effacement de favoris. Test photos **fictives/synthétiques uniquement** en préflight. D14 [PR #1245](https://github.com/hraaaaf/IAMINA-MVP/pull/1245) Draft, D15 [PR #1257](https://github.com/hraaaaf/IAMINA-MVP/pull/1257) Draft ; ne pas les marquer GO.

### L05 · Habitudes utiles et personnalisation responsable — P2

**Décisions : D35, D28, D24, D19, D32.** Commencer par déterministe **exprimé et vérifiable** : horaires habituels de saisie, repas favoris/repas répétés, préférences de portion confirmées, rappel volontaire, heures de sommeil **seulement si saisies volontairement ou source explicitement autorisée**. Préférer stockage contrôlé par patient, désactivation, consultation et effacement, avec fenêtre/rétention définie. Un LLM peut aider à formuler ou classer **après** benchmark et filtrage, pas inférer diagnostic, causalité, traitement ni observance. Jamais de collecte comportementale invisible.

**Succès :** première utilisation sans profilage ; après plusieurs repas confirmés les favoris reviennent correctement et modifiables ; désactivation arrête immédiatement l'apprentissage et supprime l'état concerné conformément à la règle validée ; pas d'accès inter-patients ni de collecte en mode invité.

### L06 · Intelligence clinique et rapports déterministes — P2 GATE TRANSVERSAL

**Décisions : D19, D22, D32, D28, D4, D20.** Vérifier formules, provenance CGM vs manuel, unités, dates, arrondis, données manquantes et portée des tendances. Les exports PDF/CSV/XLSX doivent refléter exactement les vues autorisées ; notifications poids seulement descriptives et volontaires. D32 = validation scientifique/clinique distincte ; aucun calcul en attente de cet avis n'est présenté comme un conseil médical. **Succès :** oracles indépendants backend/Flutter, relecture humaine santé, tests A/B, export sans PHI d'un autre utilisateur, absence d'inférence causale.

### L07 · Engagement et finitions Web — P2/P3

**Décisions : D2, D3, D16, D17, D21, D27, D29, D6, D5.** Ne refaire que les manques : D2 notification/proactivité consentie, cadence/retenue, purge J+7 **non certifiée ni planifiée**, tests hosted A/B ; D3 vrais rappels déjà ciblés ; D16 étendre copie au-delà de la sélection Companion si pertinent ; D17 détails « i » ; D21 Ramadan masqué ; D27 avatar Accueil seulement ; D29 feedback volontaire, non intrusif. Régression UX et accessibilité FR/AR.

**Succès :** pas de notification santé sans consentement explicite, aucune annonce mensongère de scheduler ; feedback non obligatoire ; comportements livrés non régressés. D2 [PR #1153](https://github.com/hraaaaf/IAMINA-MVP/pull/1153) Draft très large, à réduire/auditer avant fusion.

### L08 · CGM et appareils — DERNIER CHANTIER FONCTIONNEL

**Décisions : D1 (historique, D-DERNIER), D25, D19, D22, D32, D24.** Après les lots précédents et leurs contrôles, intégrer sources CGM via connecteurs officiels quand les permissions le permettent ; Nightscout **facultatif**. D25 Paramètres peut préparer l'inventaire de sources à L03, mais **ne pas activer de connexion CGM avant L08**. Validation indépendante de TIR/TAR/TBR, qualité des fenêtres, délais, données perdues, révocation, API, fabricant, CGM simulé et appareil. Pas d'activation médicale à partir d'un graphique démo.

**Succès :** connexion réelle autorisée + consentement/autorisation, isolation, temps/fraîcheur, déco/révocation, tests sur appareils pris en charge, erreurs fail-closed, validation clinique D32. **D1 conserve son ID, sans renumérotation.**

### L09 · W14 — certification Web/PWA et lancement contrôlé — DERNIER

**Décisions : toutes via critères de risque ; D31 uniquement si un chantier natif futur est relancé.** Préprod sans patient, A→B→A, offline/récupération, navigateurs Safari/Chromium, sécurité/privacy/clinique/réglementaire, sauvegarde/restauration, revues indépendantes, QA visuelle 390/430/768/1280 FR/AR 200 %, runs CI exact SHA, closeout/merge/postmerge puis autorisation du propriétaire **pour tout déploiement Vercel**, et pilote progressif. Aucun « 100 % / production-ready » sans reçu réel.

## 3. Index complet D1–D38 — statut au 04/11/2026

**Légende :** LIVRÉ BORNÉ = preuve sur périmètre indiqué, non certification générale ; PARTIEL = code ou livraisons limitées ; DRAFT = PR non fusionnée ; OPEN = résultat non attesté ; PROPOSÉ = à arbitrer au cours de cet onboarding. Les statuts historiques viennent du registre Notion D1–D30, des chantiers A/B et des PR GitHub consultées ; **un status sans PR/live vérifiés aujourd'hui reste une photographie documentaire**, jamais un constat d'exécution immédiate.

| Décision et scope historique | État le mieux justifié | Lot principal |
|---|---|---|
| D1 — Hub CGM, Nightscout non obligatoire | OPEN, **dernière fonction** | L08 |
| D2 — Notifications intelligentes consenties | PARTIEL ; scheduler/hosted non certifiés, #1153 Draft | L07 |
| D3 — Rappels Accueil programmés | LIVRÉ BORNÉ Web | L07 régression |
| D4 — Exports PDF/CSV/XLSX cohérents | OPEN | L06 |
| D5 — Pays choisi explicitement | LIVRÉ BORNÉ Web | L02 régression |
| D6 — Ton du compagnon fixe (pas de sélecteur) | LIVRÉ BORNÉ Web | L07 régression |
| D7 — Diabète/traitements multiples | ACCEPTÉ BORNÉ, validation clinique restant | L02 |
| D8 — Unité choisie avant usage, **sans suggestion pays** | **LIVE / CLOSED Web borné** (#1269) | L02 régression |
| D9 — Retour compte existant sans re-onboarding | PARTIEL, #1159 Draft et A→B→A ouvert | L01/L02 |
| D10 — App-lock, récupération, réversibilité | PARTIEL ; #1246 Draft, revue sécurité ouverte | L01/L03 |
| D11 — Compte vierge, démo isolée | LIVRÉ BORNÉ | L01 régression |
| D12 — Saisie glycémie précise slider/clavier | LIVRÉ BORNÉ dans chaîne D13, fusion main à vérifier | L02 |
| D13 — Sauvegarde/brouillon sans perte | DRAFT #1250, CI ciblées vertes, non fusionné | L02 |
| D14 — Photo repas confirmée par l'utilisateur | **PAUSED**, #1245 Draft ; réévaluation requise | L04 |
| D15 — Un brouillon repas photo/voix/texte | PARTIEL, #1257 Draft ; pas activation photo réelle | L02/L04 |
| D16 — Copier textes utiles | PARTIEL, sélection Companion seulement | L07 |
| D17 — Détails techniques sous « i » | LIVRÉ BORNÉ Web | L07 régression |
| D18 — Données progressives + protection du coffre | **NO-GO clinique** pour migration/chiffrement | L01/L02 |
| D19 — Calculs cliniques cohérents | PARTIEL, #920 Draft, revue scientifique ouverte | L06 |
| D20 — Poids/tendance et messages volontaires | PARTIEL, PR historiques Draft | L06/L07 |
| D21 — Ramadan masqué sous feature flag | LIVRÉ BORNÉ Web | L07 régression |
| D22 — Unités avant objectifs, fail-closed | TECHNIQUEMENT ACCEPTÉ / MERGED, D32 ouvert | L02/L06 |
| D23 — Préférences App/compagnon regroupées | OPEN ; fusion avec D36 | L03 |
| D24 — IA OFF, consentement et API | DRAFT #1244 ; sécurité/clinical ouverts | L01/L03 |
| D25 — Données et appareils / CGM | OPEN ; inventaire L03, connecteurs L08 | L03/L08 |
| D26 — Confidentialité, déconnexion/suppression | OPEN ; W02 prérequis non certifiés | L01/L03 |
| D27 — Avatar IAmina Accueil uniquement | LIVRÉ BORNÉ Web | L07 régression |
| D28 — Intelligence gouvernée avant dialogue | OPEN ; moteur partiel sans clôture produit | L05/L06 |
| D29 — Feedback volontaire après premier usage | OPEN | L02/L07 |
| D30 — Choix local/sans compte et privacy-first | LIVRÉ BORNÉ Web ; **révisé par D37** | L01 |
| D31 — Gate tests matériels natifs historiques | OPEN ; **différé hors priorité Web** | après L09 si natif |
| D32 — Validation scientifique/clinique G1–G7 | OPEN, indépendante des CI UI | L06/L08, transverse |
| D33 — Focus Web first | **NOUVELLE ORIENTATION, à détailler** | tous |
| D34 — Photo, VLM léger, repas inconnus et favoris | **NOUVEAU À FIXER**, sans fournisseur choisi | L04 |
| D35 — Apprentissage habitudes utiles | **NOUVEAU À FIXER**, consentement/rétention | L05 |
| D36 — Profil → Paramètres détaillés | **NOUVEAU À FIXER**, regroupe D23/D25/D26 | L03 |
| D37 — Entrée sans compte, login au besoin DB/fetch | **NOUVELLE ORIENTATION PRIORITAIRE** | L01 |
| D38 — « Application setting » fermé par défaut | **NOUVEAU À FIXER**, dépend D36 | L03 |

## 4. Handover et points d'onboarding à fixer dans l'ordre

**Décisions à arbitrer avec l'utilisateur, une par une** (proposition initiale, alternative et conséquence notées avant validation) :

1. **O1 / D37 — visiteur :** quel périmètre est navigable sans compte ? **A** : visiter toute l'interface et ses rubriques en mode lecture statique (états vides et exemples fictifs), avec connexion/inscription AVANT toute lecture/écriture DB, appel API ou fetch métier — **RECOMMANDÉ, plus fidèle à l'orientation utilisateur mais exige un audit de tous les fetchs automatiques au montage des écrans**. **B** : quelques écrans de découverte seulement, plus simple techniquement mais moins démonstratif. Aucune donnée patient affichée ni créée dans les deux cas. La règle « dès DB/fetch » est acquise comme direction ; on valide maintenant la navigation invitée.
2. **O2 / D30/D9/D18 — anciennes données :** voie de récupération manuelle après connexion, rétention de l'ancien coffre et refus de liaison automatique. Sans preuve de migration sûre, pas de blocage brutal des utilisateurs locaux existants.
3. **O3 / D10/D24/D26 — compte et consentements :** identifiant stable, verrou local/offline, IA OFF effectif, droit d'effacer, API patient.
4. **O4 / D36/D38 — Paramètres :** hiérarchie/maquette, catégories, accordéon fermé initialement.
5. **O5 / D14/D34 — photo :** capture, propositions non certaines, quantité corrigée, plats personnalisés, évaluation du VLM et consentement.
6. **O6 / D35 — habitudes :** quelles habitudes, données sources, période, consentement, affichage et suppression.
7. **O7 / D13/D15 — saisie :** brouillon, sauvetage, confirmations, doublons, offline.
8. **O8 / D19/D32/D2/D4 — clinique, rapports et notifications :** limites d'interprétation, consentements, évaluation indépendante.
9. **O9 / D1/D25 — CGM en dernier :** fabricants, autorisations, pays, statut des connecteurs.
10. **O10 / W14 — recette, risque et diffusion :** QA Web, sécurité/privacy/clinique, étapes preview et autorisations de déploiement explicites.

**Règle de suivi :** une décision peut passer de PROPOSÉ à ACCEPTÉ seulement par choix explicite, et d'ACCEPTÉ à LIVRÉ seulement avec tests/preuves/merge/release de portée appropriée. Aucun pourcentage global « certifié » à partir du nombre de décisions classées.

## 5. Preuves de départ, liens et limites

- [Résumé officiel des D1–D29](https://app.notion.com/p/3fa77c66336281aaaff4f2781d86cc21), [registre D1–D30 et réconciliation A/B](https://app.notion.com/p/40777c6633628177b325d3cb5412fc18), [Chantier B / D8 livré](https://app.notion.com/p/40777c66336281729c03c9bb294e71b7), [D18 SAFE-HOLD](https://app.notion.com/p/40d77c663362812381dfe50543c8471f).
- GitHub main observé au départ de cette refonte : **d7d650a082300486764019c8238f591057210d54**. [D8 #1269](https://github.com/hraaaaf/IAMINA-MVP/pull/1269) MERGED et Web production confirmée dans le registre B ; [D18 #1265](https://github.com/hraaaaf/IAMINA-MVP/pull/1265) Draft, avec [Chromium #41839588272](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41839588272) et [WebKit #41839588203](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41839588203) SUCCESS préclinique ; D18 NO-GO ; [D32 issue #1248](https://github.com/hraaaaf/IAMINA-MVP/issues/1248).
- PRs ouvertes vérifiées au contrôle documentaire : [D13 #1250](https://github.com/hraaaaf/IAMINA-MVP/pull/1250), [D15 #1257](https://github.com/hraaaaf/IAMINA-MVP/pull/1257), [D24 #1244](https://github.com/hraaaaf/IAMINA-MVP/pull/1244), [D14 #1245](https://github.com/hraaaaf/IAMINA-MVP/pull/1245), [D10 #1246](https://github.com/hraaaaf/IAMINA-MVP/pull/1246), [D9 #1159](https://github.com/hraaaaf/IAMINA-MVP/pull/1159), [D2/W01 #1153](https://github.com/hraaaaf/IAMINA-MVP/pull/1153) et [D19 #920](https://github.com/hraaaaf/IAMINA-MVP/pull/920) : toutes Draft à cet instant.
- L'environnement connecté est un **snapshot**, pas un audit de tous les commits, tickets et serveurs. Les certifications patient, hébergement serveur, sauvegarde, restauration et réglementation ne sont PAS acquises par cette opération documentaire. Respecter les prérequis vérifiés avant chaque lot.
