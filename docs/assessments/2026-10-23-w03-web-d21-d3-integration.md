# IAMINA WEB — W03 / Livraison intégrée D21 + D3 — 23/10/2026

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
