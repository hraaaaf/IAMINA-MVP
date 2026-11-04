# IAMINA — ROADMAP CANONIQUE UNIQUE · Web/PWA · D1–D38

**Édition :** 2026-11-04 (arbitrages O1–O10 intégrés) · **Statut : 11 CHOIX PRODUIT EXPLICITEMENT VALIDÉS pendant l'onboarding ; ROADMAP CANDIDATE à ADOPTER, NON FUSIONNÉE, NON CERTIFIÉE et AUCUNE AUTORISATION DE DÉPLOYER.**
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

## 2. Roadmap EXÉCUTABLE — ordre unique par risque, dépendances et valeur

Le numéro de décision ne définit **jamais** l'ordre de travaux. Seules les tranches suivantes constituent l'ordre prospectif. Chaque tranche peut contenir des validations concurrentes si indépendantes, mais aucune ne contourne une dépendance sécurité. Les clôtures précédentes ne doivent pas être refaites sans régression observée.

### L00 · Vérité et onboarding des décisions — PRIORITÉ IMMÉDIATE

**Goal :** une matrice D1–D38 complète, sans doubles statuts ni arbitrages tacites, et un accord explicite sur les nouveaux parcours (compte invité, stockage, ancienne identité, photo, habitudes et paramètres). **Succès :** 38/38 identifiants répertoriés avec périmètre, état vérifié/proposé, dépendance, lot et critère de preuve ; les décisions en débat sont clairement « proposées » jusqu'à choix utilisateur. **Preuve :** sources GitHub/Notion datées, PR documentaire Draft, validation du propriétaire au fil de l'onboarding. Pas de développement clinique dans L00. **Onboarding produit O1–O10 : 10 thèmes arbitrés / 11 choix approuvés** (O4 couvre D36 et D38), traçabilité GitHub et Notion au §4. **Reste :** vérification documentaire du SHA, CI, revue des dépendances puis adoption explicite de la roadmap ; l'adoption ne constitue ni merge ni certification ni déploiement.

### L01 · Frontière visiteur/compte et conservation des anciens coffres — P0 BLOQUANT

**Décisions : D30, D37, D11, D9, D10, D18, D24, D26, D33.** Architecture de session avec trois classes **visiteur volatile / compte patient vérifié / utilisateur historique local à récupérer**. Router, DB et API interdisent par défaut toute lecture/écriture clinique et tout fetch métier au visiteur. Supprimer l'ouverture de coffres persistants pour le vrai visiteur **seulement après** distinguer l'audit technique des comptes utilisateur ; rendre la connexion explicite au clic sur une fonction protégée. Séparer reconnexion et déverrouillage local. Flux A→déconnexion→B→A et deux onglets. **O2-A VALIDÉ :** chemin de reprise manuelle volontaire du coffre legacy après connexion, seulement après preuve de possession et certification du mécanisme ; zéro rattachement/effacement/migration automatique, abandon sans mutation si ambigu. **O3-A VALIDÉ pour la granularité IA uniquement** ; autres exigences D10/D24/D26 encore ouvertes.

**Sous-gate parallèle D18 P0-A…D :** aucune bascule automatique de coffre historique plaintext→sqlite3mc. La vraie VFS Drift est IDB v1 avec stores blocks/files dans le Chromium CI testé ; la montée artificielle v1→v2 **n'empêche pas le stale opener sans version et empêche la réouverture Drift de la source**, malgré conservation des blocs. Le test 15/15 est une preuve d'INCOMPATIBILITÉ de cette option, pas de sécurité clinique. [Worker #41839588272](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41839588272) et [WebKit #41839588203](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41839588203) SUCCESS sur la PR Draft [#1265](https://github.com/hraaaaf/IAMINA-MVP/pull/1265), sans certification clinique. D18 bloque tout nouveau coffre chiffré **réel** jusqu'à preuve de clé, récupération, auth, stabilité VFS et audit ; la restriction invitée ne supprime PAS la dette sur anciens clients.

**W01 indispensable à la partie serveur :** preuve Preview Web→API→Postgres, identité patient A/B, permission par objet, rétention, isolation Neon, sauvegarde/restauration, journal d'accès, confidentialité et revues. Les anciens runs ou l'état de simple Preview READY ne certifient pas les flux patient.

**Critères L01 :** invité non authentifié ouvre l'app puis explore ; 0 coffre/écriture santé invité ; clic Ajouter mesure / photo / historique / appareil / API retourne vers login AVANT stockage/fetch ; retour à la tâche après login sans données médicales invitées ; test clavier, refresh, offline, onglet ancien, navigateurs, A/B et accès direct API. 0 patient perdu/migré. **BLOCAGE CLINIQUE ENCORE ACTIF.**

### L02 · Saisie sûre et onboarding clinique minimal — P0/P1

**Décisions : D13, D12, D7, D5, D8, D22, D9, D18 (champs progressifs), D15 (manuel), D29.** Reprendre D13 (prévenir perte de saisie ou double insertion), fiabiliser saisie manuelle glycémie/repas, unités explicites **mg/dL/mmol/L** avant objectifs, traitements multiples facultatifs, profil minimal et anciennes sessions sans onboarding imposé. D5 pays choisi explicite ; D8 **modifiée par le propriétaire puis livrée** : unité choisie par l'utilisateur, **sans présélection automatique pays/IP**. Aucune donnée démo dans un compte neuf. **O7-A VALIDÉ :** brouillon de saisie récupérable pour compte authentifié uniquement, jamais journalisé sans confirmation, anti-doublon sur retry/offline ; aucune persistance médicale invitée. Implémentation et tests restent conditionnés à D18/W01.

**Succès :** cycle ouverture/saisie→retour accidentel→reprise ou refus de sortie, 1 Save=1 entrée, invalides refusées, pas d'insuline implicite, datetime/unité cohérentes, synthétique FR/AR+Safari/Chrome. **Preuve :** PR [#1250 D13](https://github.com/hraaaaf/IAMINA-MVP/pull/1250) Draft 12/12 CI antérieures, [#1257 D15](https://github.com/hraaaaf/IAMINA-MVP/pull/1257) Draft ; D12 livraison ciblée/branche et revue Web à réconcilier. Aucune certification globale inférée.

### L03 · Paramètres et contrôle utilisateur — P1

**Décisions : D36, D38, D23, D25, D26, D24, D10, D20.** Une page « Paramètres » à la place de « Profil », sections Compte/Profil, Données, CGM & appareils (inventaire sans branchement fabricant), AI, unités et objectifs, rappel/notification, confidentialité/consentement, suppression/déconnexion et app-lock. « Paramètres de l'application » **fermés par défaut**, expansion volontaire mémorisée au maximum dans la session d'UI, sans ouvrir un coffre pour cela. Ne pas exposer CGM comme connecté s'il n'est pas testé. **O4/D36-A et D38-A VALIDÉS :** une seule entrée Paramètres, accordéon « Paramètres de l'application » fermé au rendu initial. **O3-A VALIDÉ :** consentements IA distincts, révocables et OFF par défaut pour photo D34, habitudes D35 et compagnon si disponible ; protection à démontrer côté Web ET API. D10/D24/D26 ne sont pas certifiés.

**Succès :** BEFORE→mockup→implémentation→AFTER sur 390/430/768/1280, FR/AR RTL, clavier/zoom, mêmes viewports ; suppression/revoke protégés, IA OFF propagée à client ET API, aucune préférence de patient A visible dans compte B. Gate D24 privacy requis.

### L04 · Repas photo, multimodal et apprentissage des aliments — P1/P2

**Décisions : D14, D15, D34, D24, D13.** Réévaluer la suspension explicite de D14 avant activation. Capture photo→propositions alimentaires et portions (modèle vision/VLM léger **candidat, aucun fournisseur choisi**)→l'utilisateur corrige, retire, ajoute un repas inconnu ou sauvegarde dans ses favoris→**un seul brouillon** photo/voix/texte/formulaire→Save explicite. L'app peut accélérer les prochaines propositions à partir des corrections confirmées, jamais à partir d'une reconnaissance non vérifiée. Évaluer qualité FR/AR/Darija, plats marocains, faux positifs, portions, latence, coût, batterie, disponibilité sans réseau et fuite de métadonnées. Pas de recommandation insulinique. **O5/D34-A VALIDÉ :** assistant photo à confirmation humaine, inconnus ajoutables, favoris confirmés ; saisie manuelle préservée. Le modèle, le fournisseur, la fuite de métadonnées et les consentements restent à évaluer ; la pause D14 n'est pas levée.

**Succès :** 0 écriture avant confirmation/Save ; IA OFF et absence consentement bloquent le modèle et toute sortie externe, sans bloquer saisie manuelle ; cas non reconnu → ajout manuel ; rapport d'erreurs et droit à l'effacement de favoris. Test photos **fictives/synthétiques uniquement** en préflight. D14 [PR #1245](https://github.com/hraaaaf/IAMINA-MVP/pull/1245) Draft, D15 [PR #1257](https://github.com/hraaaaf/IAMINA-MVP/pull/1257) Draft ; ne pas les marquer GO.

### L05 · Habitudes utiles et personnalisation responsable — P2

**Décisions : D35, D28, D24, D19, D32.** Commencer par déterministe **exprimé et vérifiable** : horaires habituels de saisie, repas favoris/repas répétés, préférences de portion confirmées, rappel volontaire, heures de sommeil **seulement si saisies volontairement ou source explicitement autorisée**. Préférer stockage contrôlé par patient, désactivation, consultation et effacement, avec fenêtre/rétention définie. Un LLM peut aider à formuler ou classer **après** benchmark et filtrage, pas inférer diagnostic, causalité, traitement ni observance. Jamais de collecte comportementale invisible. **O6/D35-A VALIDÉ :** apprentissage progressif sur opt-in explicite, désactivé par défaut, avec transparence/correction/effacement. La rétention et l'isolation patient restent à spécifier et tester ; commencer déterministe sans profilage caché.

**Succès :** première utilisation sans profilage ; après plusieurs repas confirmés les favoris reviennent correctement et modifiables ; désactivation arrête immédiatement l'apprentissage et supprime l'état concerné conformément à la règle validée ; pas d'accès inter-patients ni de collecte en mode invité.

### L06 · Intelligence clinique et rapports déterministes — P2 GATE TRANSVERSAL

**Décisions : D19, D22, D32, D28, D4, D20.** Vérifier formules, provenance CGM vs manuel, unités, dates, arrondis, données manquantes et portée des tendances. Les exports PDF/CSV/XLSX doivent refléter exactement les vues autorisées ; notifications poids seulement descriptives et volontaires. D32 = validation scientifique/clinique distincte ; aucun calcul en attente de cet avis n'est présenté comme un conseil médical. **Succès :** oracles indépendants backend/Flutter, relecture humaine santé, tests A/B, export sans PHI d'un autre utilisateur, absence d'inférence causale. **O8-A VALIDÉ :** V1 Web factuelle (mesures et tendances descriptives), rapports sourcés/unités/fenêtres/incertitudes, calculs déterministes **seulement après évaluation indépendante D32**, rappels D2 consentis ; aucun diagnostic, suggestion de dose ou adaptation de traitement. D19/D32 ne sont pas certifiés.

### L07 · Engagement et finitions Web — P2/P3

**Décisions : D2, D3, D16, D17, D21, D27, D29, D6, D5.** Ne refaire que les manques : D2 notification/proactivité consentie, cadence/retenue, purge J+7 **non certifiée ni planifiée**, tests hosted A/B ; D3 vrais rappels déjà ciblés ; D16 étendre copie au-delà de la sélection Companion si pertinent ; D17 détails « i » ; D21 Ramadan masqué ; D27 avatar Accueil seulement ; D29 feedback volontaire, non intrusif. Régression UX et accessibilité FR/AR. **O8-A :** notifications de rappel consenties et révocables seulement, pas d'explication thérapeutique automatisée ni de proactivité clinique supposée.

**Succès :** pas de notification santé sans consentement explicite, aucune annonce mensongère de scheduler ; feedback non obligatoire ; comportements livrés non régressés. D2 [PR #1153](https://github.com/hraaaaf/IAMINA-MVP/pull/1153) Draft très large, à réduire/auditer avant fusion.

### L08 · CGM et appareils — DERNIER CHANTIER FONCTIONNEL

**Décisions : D1 (historique, D-DERNIER), D25, D19, D22, D32, D24.** Après les lots précédents et leurs contrôles, intégrer sources CGM via connecteurs officiels quand les permissions le permettent ; Nightscout **facultatif**. D25 Paramètres peut préparer l'inventaire de sources à L03, mais **ne pas activer de connexion CGM avant L08**. Validation indépendante de TIR/TAR/TBR, qualité des fenêtres, délais, données perdues, révocation, API, fabricant, CGM simulé et appareil. Pas d'activation médicale à partir d'un graphique démo. **O9-A VALIDÉ :** intégration progressive **une source officiellement autorisée à la fois**, pays/contrat/API à prouver ; Nightscout facultatif. Le support simultané multi-fabricants n'est pas retenu au lancement.

**Succès :** connexion réelle autorisée + consentement/autorisation, isolation, temps/fraîcheur, déco/révocation, tests sur appareils pris en charge, erreurs fail-closed, validation clinique D32. **D1 conserve son ID, sans renumérotation.**

### L09 · W14 — certification Web/PWA et lancement contrôlé — DERNIER

**Décisions : toutes via critères de risque ; D31 uniquement si un chantier natif futur est relancé.** Préprod sans patient, A→B→A, offline/récupération, navigateurs Safari/Chromium, sécurité/privacy/clinique/réglementaire, sauvegarde/restauration, revues indépendantes, QA visuelle 390/430/768/1280 FR/AR 200 %, runs CI exact SHA, closeout/merge/postmerge puis autorisation du propriétaire **pour tout déploiement Vercel**, et pilote progressif. Aucun « 100 % / production-ready » sans reçu réel. **O10-A VALIDÉ :** gates GO/NO-GO séparés (identité/offline/backup ; privacy/consentements ; clinique D32 ; QA Web/accessibilité ; conformité/revue ; CI SHA exact ; pilote progressif). **Aucun GO n'est acquis.** Autorisation explicite **distincte pour chaque déploiement Vercel Preview ou Production** ; aucune fusion automatique, y compris si elle déclencherait un déploiement.

## 3. Index complet D1–D38 — statut au 04/11/2026

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

## 4. Handover — décisions d'onboarding validées le 04/11/2026

**État exact : 10 thèmes O1–O10 arbitrés, soit 11 choix produit ACCEPTÉS** (O4 a deux décisions distinctes D36/D38). Chaque approbation est **un choix produit seulement**, pas une preuve d'implémentation, de sécurité, de certification, de merge ou de disponibilité. L'ordre unique prospectif reste L00→L01→…→L09.

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

**Suite L00 après cette réconciliation :** vérifier index D1–D38, cohérence des 10 lots et des gates, diff limité au Markdown, CI exact HEAD, miroir Notion et PR Draft ; présenter le plan pour **adoption explicite**. **Aucun merge ni déploiement Vercel autorisé.**

## 5. Preuves de départ, liens et limites

- [Résumé officiel des D1–D29](https://app.notion.com/p/3fa77c66336281aaaff4f2781d86cc21), [registre D1–D30 et réconciliation A/B](https://app.notion.com/p/40777c6633628177b325d3cb5412fc18), [Chantier B / D8 livré](https://app.notion.com/p/40777c66336281729c03c9bb294e71b7), [D18 SAFE-HOLD](https://app.notion.com/p/40d77c663362812381dfe50543c8471f).
- GitHub main observé au départ de cette refonte : **d7d650a082300486764019c8238f591057210d54**. [D8 #1269](https://github.com/hraaaaf/IAMINA-MVP/pull/1269) MERGED et Web production confirmée dans le registre B ; [D18 #1265](https://github.com/hraaaaf/IAMINA-MVP/pull/1265) Draft, avec [Chromium #41839588272](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41839588272) et [WebKit #41839588203](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41839588203) SUCCESS préclinique ; D18 NO-GO ; [D32 issue #1248](https://github.com/hraaaaf/IAMINA-MVP/issues/1248).
- PRs ouvertes vérifiées au contrôle documentaire : [D13 #1250](https://github.com/hraaaaf/IAMINA-MVP/pull/1250), [D15 #1257](https://github.com/hraaaaf/IAMINA-MVP/pull/1257), [D24 #1244](https://github.com/hraaaaf/IAMINA-MVP/pull/1244), [D14 #1245](https://github.com/hraaaaf/IAMINA-MVP/pull/1245), [D10 #1246](https://github.com/hraaaaf/IAMINA-MVP/pull/1246), [D9 #1159](https://github.com/hraaaaf/IAMINA-MVP/pull/1159), [D2/W01 #1153](https://github.com/hraaaaf/IAMINA-MVP/pull/1153) et [D19 #920](https://github.com/hraaaaf/IAMINA-MVP/pull/920) : toutes Draft à cet instant.
- L'environnement connecté est un **snapshot**, pas un audit de tous les commits, tickets et serveurs. Les certifications patient, hébergement serveur, sauvegarde, restauration et réglementation ne sont PAS acquises par cette opération documentaire. Respecter les prérequis vérifiés avant chaque lot.
