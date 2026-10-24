# IAMINA WEB — W03 / Livraison intégrée D21 + D3 — 23/10/2026

## CLOSEOUT W03 — revue du 24/10/2026 — code et CI GREEN, gate tactile maintenu

**Périmètre : W03 Web D21 + D3 exclusivement.** PR [#1148](https://github.com/hraaaaf/IAMINA-MVP/pull/1148) OPEN/DRAFT, commit produit et tests `970e6cf1f7aa5276f9bf3fda1cdaa849083ff924`; `main@8ada5aab8e8006bbbdc275eabbabf014a4714e0b` inchangé. Aucun merge, aucun déploiement Vercel. Ce bloc est le constat à date, les sections plus bas retracent les hypothèses/protocoles antérieurs.

**Succès observable et preuves effectives sur le SHA ci-dessus :**
- **14/14 workflows GitHub SUCCESS, 0 FAILURE, 0 en cours** ; [CI générale #40001551809](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40001551809), Flutter **812 PASS + 1 SKIP historique**, build Web RELEASE OK. Analyse `--no-fatal-infos` rapporte aussi **862 diagnostics infos/lints non bloquants** ; ne pas prétendre `0 warnings`. Back-end écarté (scope frontend Web) et non compté comme prouvé.
- **D21 [FUE #40001551638](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40001551638)** : **6/6 PASS**, FR/AR × 390×844 / 768×1024 / 1280×900, `issues=[]` dans les six fichiers JSON, artefact [#12523102719](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40001551638/artifacts/12523102719). La suppression des contrôles Ramadan Web conserve l'intervalle historique exact après reload dans la fixture et ne crée pas d'historique sur état vierge ; usage synthétique de Chromium, pas de preuve d'un appareil tactile physique.
- **D21 [RTL/clavier #40001551811](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40001551811)** : 6/6 AFTER sans Ramadan dans l'arbre accessible, absence de débordement, `problems=[]`, artefact [#12523560136](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40001551811/artifacts/12523560136). **Réserve reproductible** : sur FR et AR en 768/1280, retour vers une cible antérieure après **7 pressions Shift+Tab**, avec stagnation des quatre premières ; en mobile 390, retour en **1 pression**. Workflow SUCCESS ne prouve pas une accessibilité clavier parfaite.
- **D3 [preuves BEFORE/AFTER #40001551745](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40001551745)** : **8/8 couples PNG** FR/AR × 390×844, 430×932, 768×1024, 1280×900, images du même état synthétique et mêmes dimensions ; trois prochaines **dates** locales futures activées visibles dans AFTER, absentes du BEFORE ; aucun intitulé médical fictif affiché. [Artefact #12523176742](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40001551745/artifacts/12523176742). Inspection des 16 images : textes FR/AR lisibles et composition directionnelle conforme dans le rendu de test, pas une capture de PWA complète. Date synthétique de janvier 2099, non une échéance réelle. Aucun score ≥9 attribué à ce rendu de widget seul.
- **D3 confidentialité/état** : tests Flutter #40001551809 passent pour dates triées et filtrées (future + enabled + max 3), absence de titre patient sur Home, 0/1/N, A→B→A (ancienne date immédiatement absente après changement de coffre) et 390/768/1280 sans exception. **Dashboard responsive Chrome #40001551616** : 9/9 captures distinctes, mais fixture Chrome ne contient pas ces dates futures ; cette preuve Chrome ne saurait remplacer la preuve D3 spécifique.
  
**Statut de certification :** **W03 intégration technique GREEN sur `970e6cf1`**, **W03 VERIFIED/score retenu ≥9.0 non acquis**. Dernier score adversarial D21 connu : **8,8/10** (ne pas l'augmenter en se fondant seulement sur CI ou widget-golden). Human gate exact : tester la PWA Web sur appareil tactile réel, vérifier clavier inverse FR/AR tablette/desktop, observer la carte D3 avec échéances sur vrai navigateur PWA et comparer aux maquettes ; obtenir validation de qualité indépendante si nécessaire. Exige Preview mise en ligne uniquement après autorisation Vercel distincte. Aucun événement patient réel ni réseau de rappels testé ici.

**NEXT exact :** vérification de la CI sur ce *commit de documentation uniquement* (ne pas confondre avec le commit produit vert), puis audit du verdict et Notion. S'il est vert, fermer uniquement le sous-lot technique W03 ; sinon corriger puis réexécuter. Conserver Draft, aucune fusion/déploiement sans human gate.

## Goal, critères de succès, preuve

**Goal exact :** apporter les 2 correctifs Web W03 déjà codés/testés dans **un même HEAD candidat**, sans fusionner en Production : (D21) retirer les réglages Ramadan de l'UI Profil sans perdre les anciennes données ni le focus clavier ; (D3) afficher sous Tendance une carte de rappels **locaux** ne révélant aucun intitulé médical sur l'accueil.

**Succès observable** : compilation/analyze/tous tests sur le HEAD joint, FUE D21 6/6 FR/AR × 390/768/1280, navigation Tab/Shift+Tab, rappel 0/1/N depuis l'instance Drift du compte courant (A→B→A), aucun titre patient ni réseau depuis la carte, aucun impact négatif sur Tendance ou les données de Ramadan existantes, captures BEFORE/AFTER au même état sur 390×844, 768×1024, 1280×900. La preuve d'intégration et les revues qualifiées précèdent tout statut VERIFIED.

## BEFORE → Mockup → implémentation → AFTER

**BEFORE** : `main@8ada5aab8e8006bbbdc275eabbabf014a4714e0b` : le panneau Profil propose encore les options Ramadan ; Dashboard Tendance suivie des Outils sans résumé de rappels. **Référence** : [D21 #1136](https://github.com/hraaaaf/IAMINA-MVP/pull/1136) et [D3 #1137](https://github.com/hraaaaf/IAMINA-MVP/pull/1137), ainsi que les captures FUE D21 [run #39771874599](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39771874599).

**Mockup écrit** : Profil sans sections Ramadan, zones de formulaire repliées exclues du focus tout en préservant la saisie. Accueil : « Tendance » inchangée → petite carte blanche « Rappels », icône calendrier + statut local 0/1/N actifs sans noms → « Outils ». Conserver le design system et les directions FR/AR RTL.

**Implémentation** : copier **à l'identique 15 blobs D21 + 4 blobs D3** dans une tree fondée sur `main@8ada5aab8e8006bbbdc275eabbabf014a4714e0b`. Vérification automatisée des arbres Git : ces 19 chemins étaient inchangés entre `main` et la base commune `31380a7f4c8f61a3ec886ec9d2d66d26c2bf222b`, et D21/D3 ont **zéro chemin commun**. Ne pas faire une fusion aveugle des commits historiques. Les documents sources sont préservés.

**Preuve historique, pas preuve de la combinaison** : D21 **13/13 CI SUCCESS**, FUE synthétique **6/6**, Preview Vercel READY au SHA `8f42bcbf`. D3 **8/8 CI SUCCESS** au SHA `7425a017`. Ces résultats ne certifient pas encore le nouveau HEAD.

**AFTER requis** : CI nouvelle PR au SHA exact, audit du FUE 6/6, captures comparables au pixel sur mêmes viewports, test tactile réel de la Web Preview après permission spécifique, score visuel et note adversariale. Ne pas inventer de note avant avoir la preuve.

## Dépendances et vrai gate

- **D3 complétion UI (candidat)** : la carte affiche désormais, en plus du compteur 0/1/N, jusqu'à **3 vraies prochaines échéances locales** : dates futures et activées uniquement, triées chronologiquement. Les intitulés sensibles ne sont pas rendus sur l'Accueil ; rien ne quitte le coffre local, aucune notification OS n'est simulée. Reference UI : « Tendance [inchangée] → Rappels : compteur + Prochaines échéances (1–3 lignes dd/MM/yyyy HH:mm) → Outils ». En l'absence d'échéances futures, conserver seulement le compteur. Les vues FR/EN/AR, RTL, A→B→A et les largeurs 390/768/1280 sont couvertes par tests ciblés à exécuter sur le nouveau SHA. Statut **candidat en attente CI/captures AFTER** ; ne pas prononcer VERIFIED sans preuve physique/visuelle.
- **D2 #1135** modifie aussi `dashboard_premium_screen.dart` ; une intégration ultérieure doit conserver l'ordre Tendance→Rappels→Outils et résoudre ce chevauchement. Le D21 `add_log_sheet.dart` croise les correctifs de glycémie [L0 #1141](https://github.com/hraaaaf/IAMINA-MVP/pull/1141) : pas de merge simultané non réconcilié.
- **W01 #1128** NO-GO et W02 gelée : pas de preuve de l'authentification hébergée, de l'isolation de comptes A→B→A sous SSO/Neon/Redis/DR sur cette branche. Aucune donnée médicale réelle.
- **Vercel** : aucun nouveau déploiement Preview, Production, promotion ni fusion implicitement autorisés ici. La Preview D21 précédemment autorisée est distincte de ce candidat intégré.
- **Human gate** : revue indépendante/score ≥9.0 et test tactile réel, sécurité+clinique et autorisation explicite de toute mise en ligne.

**Next exact :** publier une PR DRAFT unique, lire ses workflows sans attente passive, inspecter échecs et captures, corriger puis refaire tests exact SHA ; finaliser doc/score/gates ; seulement ensuite évaluer une fusion et ses effets Vercel.

## W03 D3 — preuve visuelle ciblée à confirmer au nouveau SHA

**BEFORE unique** : W03 combiné `130161c6` (carte compteur seul). **AFTER** : nouveau HEAD D3 avec jusqu'à trois échéances. **Même mockup** : carte dans son conteneur clair à 16px de marge, maxWidth 600px, même police/theme, données synthétiques identiques, FR et AR aux viewports 390×844, 430×932, 768×1024, 1280×900. Une fixture de quatre dates futures, un rappel désactivé et des titres fictifs sensibles est fournie par `dashboard_reminders_visual_proof_test.dart`. Les titres sont absents du rendu. Workflow `w03-d3-reminders-visual-proof.yml` compare huit captures AVANT et huit APRÈS et échoue si elles sont identiques, tailles différentes, scénario manquant ou test Flutter rouge. Ces images sont **des captures du renderer widget Flutter en CI**, non des captures Chromium d'une Preview patient. Les captures Chromium existantes utilisent un scénario sans échéances ; **ne pas prétendre que les dates y ont été vues**.

À renseigner seulement à réception : run/artefact, comparaison visuelle effective, score, éventuelles régressions. **Aucun merge ni Vercel.**

## W03 D3 — séparation harness golden / CI standard

La capture visuelle (test avec fichiers golden non versionnés) doit s'exécuter **uniquement** sur `flutter test --dart-define=IAMINA_W03_D3_GOLDEN_PROOF=true --update-goldens` dans le workflow W03 dédié. La CI ordinaire exécute le test sentinel sans accès à des golden inexistants ; elle exécute par ailleurs **tous les vrais tests fonctionnels D3** (`dashboard_reminders_summary_card_test.dart`). Le témoin golden charge une fonte lisible FR/AR et, si présent dans le SDK runner, les icônes MaterialIcons. L'artefact #12522006670 du run #40000813389 prouve déjà 8/8 différences avec textes FR/AR lisibles ; cette révision exige une nouvelle CI au SHA exact avant closeout.
