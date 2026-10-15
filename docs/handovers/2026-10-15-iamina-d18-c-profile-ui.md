# IAMINA — D18-C Profil progressif — Handover opérationnel

**Date** : 2026-10-15. **État** : CANDIDATE / non certifiée / PR DRAFT, aucun merge ni déploiement.
**PR** : [#1066](https://github.com/hraaaaf/IAMINA-MVP/pull/1066), branche `feat/v1-d18-c-profile-progressive-ui-20261015`, fondée sur D18-B #1064. Base GitHub `main` temporaire pour déclencher CI uniquement ; **NE JAMAIS MERGER sous cette base**.
**Référence produit** : décision 18, option A, Notion 2026-10-08.

## Goal → Success → Proof

**Goal** : rendre le poids daté/historisé, l'année de naissance et l'identité de genre facultatifs et éditables, sans forcer l'onboarding ni créer des données médicales/inférences.
**Succès observable** : patient natif, coffre sélectionné et déverrouillé → saisie explicite → sauvegarde LOCALE uniquement → relecture historique sans écraser, avec kg/lb, horodatage, provenance. Coffre vide reste vide ; entrées invalides refusées ; aucun accès depuis Web non sécurisé.
**Preuve requise** : tests Flutter widgets/intégration réels, parcours A→B→A natif/PWA, tests de session verrouillée, captures BEFORE/AFTER par viewport, score visuel, reviewers privacy/clinique indépendants, CI exact-head.

## BEFORE connu (source vérifiée, pas capture)

- `frontend/lib/features/profile/profile_screen_presentation.dart` sur `main@851117c` : sections existantes médical/Ramadan/IAmina/données/compte, **aucune section D18**.
- `frontend/lib/features/profile/profile_screen.dart` ne consomme pas encore les magasins locaux D18-B.
- Capture visuelle BEFORE du vrai écran Profil aux viewports requis **NON EFFECTUÉE**. Aucune certification UI ne peut être attribuée.

## Target/mockup de travail (spécification, pas rendu validé)

- **390×844**, petit écran : section indépendante « Informations personnelles facultatives » après la section médicale, fermée au chargement; ouverture par accordéon; année de naissance (vide autorisé) et identité de genre déclarée (vide/effacement autorisés) puis bouton d'enregistrement explicite; séparateur; nouvelle pesée (valeur, kg/lb, date+heure, ajouter); historique affichant valeur et date source, plus récent en premier.
- **768×1024** : même ordre de lecture, sans perte d'accès au bouton ou troncature de valeur/unité ; navigation clavier, lecteurs d'écran.
- **1280×900** : même hiérarchie dans la surface de contenu du profil, pas de modal ni flux secondaire obligatoire.
- **FR/EN/AR et RTL** : libellés compréhensibles, nombres/unités non inversés, états chargement/vide/refus/enregistré distincts.
- Le message doit préciser : « enregistré dans ce coffre uniquement », pas de promesse de sync ni d'adaptation thérapeutique.

## Implementation candidate

- `frontend/lib/features/profile/d18_profile_panel.dart` : composant Flutter local, explicite, pas de réseau ni modèle génératif. Horodatage **explicitement confirmé** via les deux sélecteurs date et heure, sinon ajout bloqué ; date locale convertie UTC, provenance `patient_declared`. Aucun horodatage inventé à l'ouverture du formulaire.
- `profile_screen.dart` + `profile_screen_presentation.dart` : section visible uniquement pour **coffre natif Django déverrouillé**, **pas sur Web** tant que #1054 (IndexedDB/chiffrement/contrôle du propriétaire) reste ouvert.
- `frontend/test/features/profile/d18_profile_panel_test.dart` : scénarios défaut vide, année facultative, pesées multiples, erreurs de saisie, absence de profil local; **résultats CI à vérifier**.
- Aucune conversion genre → paramètre biologique, aucune date de naissance inventée, aucune modification de traitement ou cible, aucun upload automatique.
- **D18-D** demeure séparé : appareils réels A→B→A, consentement sync D30 et privacy reviewer.

## Validation et limites

- D18-A [#1060](https://github.com/hraaaaf/IAMINA-MVP/pull/1060) HEAD `953e7ef` : 2/2 workflows CI/migration SUCCESS.
- D18-B [#1064](https://github.com/hraaaaf/IAMINA-MVP/pull/1064) HEAD `bd04e1b` : 5/5 CI/PWA/P5-5 SUCCESS.
- D18-C PR #1066 : CI à vérifier **sur HEAD final**, les workflows lancés sur d'anciens commits C ne prouvent pas le dernier HEAD.
- **Visual certification : NO_GO** tant que BEFORE→Target→AFTER identiques, tests d'accessibilité et score visuel ne sont pas observés. Cap de score fidélité **≤7.5/10**. Pas de notation globale trompeuse.
- **Release : NO_GO** : revues spécialisées/manuelles absentes, D18-A/B non mergées, pas de preuve 2 appareils, D10 Web risque ouvert.
- **Pas de Vercel D18 sans nouvelle autorisation explicite.** Aucun patient réel. P5 historique 50 % inchangé.

## Next exact

1. Inspecter les workflows #1066 au SHA actuel ; corriger les erreurs Flutter/analyze/screenshot sur la branche C, revalider SHA final.
2. Revue adversariale : idempotence dans les retries, propriétaire après changement de compte, verrouillage réel, erreurs et provenance ; corriger les findings de périmètre.
3. Capturer le vrai Profil BEFORE, produire le mockup visuel cible, puis AFTER mêmes viewports avec comparaison+tests RTL/accessibilité et score.
4. Retarget PR #1066 vers D18-B #1064 **après** confirmation des SHAs et diff limité au lot UI ; reviews → Release Certifier → merge/postmerge uniquement si gates réellement franchis.
5. D18-D vrais tests device/PWA + consentement ; handover Notion, retour roadmap. Aucun passage à 100 % sans preuve.

## Revue adversariale corrective — 15/10/2026

- Défaut corrigé : horodatage initial fixé à l'ouverture et réutilisé malgré une mesure réelle différente. Date et heure doivent désormais être confirmées avant chaque pesée ; champ réinitialisé après ajout. Test dédié.
- Défaut corrigé : sauvegarde des deux champs démographiques même quand un seul était modifié (risque d'écraser une déclaration plus récente). Drapeaux de modification séparés ; test de mise à jour concurrente. Contrôles désactivés pendant sauvegarde.
- Les captures navigateur Web ne certifient pas le widget D18 natif, volontairement interdit Web tant que #1054 n'est pas résolu. Visuels BEFORE/AFTER réels et revue indépendante sont encore ouverts. CI du nouveau HEAD à vérifier avant tout verdict.

- Correction UX complémentaire : bouton « Actualiser » désactivé lorsqu'une déclaration démographique reste modifiée mais non enregistrée ; évite l'effacement silencieux du brouillon. Régression Flutter ajoutée.

- Traçabilité UI complémentaire : l'historique montre désormais une provenance lisible par pesée (« Déclaré par le patient » / EN / AR), et l'année maximale est comparée à l'année UTC comme dans le store. Test Flutter de provenance visible ajouté.

## CI rouge corrigée — 15/10/2026

- `d9fe9401` : [CI #38729845687](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38729845687) FAILED, Flutter **808 tests passed / 1 failed / 1 skipped** ; seul échec : test `D18 initial empty, explicit edit and dated append are local`, assertion `TextButton.onPressed == null` effectuée avant le `pump` après `enterText`. Les autres tests D18 (stores, A/B, sauvegardes, formats d'écran) ont passé. 
- Correctif minimal de test : `await tester.pump()` après `enterText`, avant lecture de l'arbre. Aucune logique produit modifiée. Le HEAD suivant doit repasser CI exacte ; ancienne CI rouge reste explicitement conservée comme preuve.

## CI proof trigger — 2026-10-15

- Parent D18-B is the intended permanent PR base. The repository `.github/workflows/ci.yml` triggers full CI only for pull requests targeting `main` or `dev`; therefore #1066 was temporarily retargeted to `main` **for CI only**. Never merge under this base.
- Previous `d9fe9401` frontend full CI [#38729845687](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38729845687) failed 1/810 tests because a widget assertion lacked `tester.pump()` after `enterText`. The application code remained unchanged. The latest test fix requires its own full CI result; this documentation-only commit deliberately triggers an exact new PR synchronize event. Restore the D18-B base after full CI verdict.


## D18-C raster proof / CI exact-head refresh — 15 October 2026

- Initial isolated Flutter golden experiment with real DejaVu font (commit c1194d3f) was replaced after an observed screenshot problem: Material icons were blank squares because the Flutter test engine had not loaded its MaterialIcons font. The loading was fixed in test-only commit 62e6ef13; no production code changed. The screenshot artifact from the earlier run MUST NOT be used for visual scoring.
- Confirmed **SUCCESS**: [D18 real-font Flutter raster run #38737063847](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38737063847), exact screenshot-code HEAD 62e6ef133288a0314dea2ff200a2b47d0cbd5e14, [artifact ID 11974532182](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38737063847/artifacts/11974532182). **24/24 PNGs**, 2 actual languages **FR/AR RTL**, 4 dimensions **360×560, 390×844, 768×1024, 1280×900**, each **closed / open top / open bottom**. SHA256SUMS verified against every downloaded file, 0 mismatches; 20 distinct image hashes (large-screen top and bottom states sometimes identical). Real DejaVu text and MaterialIcons now render, rather than Ahem/squares. Synthetic isolated SQLite vault; no real patients.
- This is **actual Flutter widget raster** in Linux test engine, NOT historical pre-D18 BEFORE; NOT a full ProfileScreen render with native installed navigation, OS accessibility or real Android/iOS; NOT two-device A→B→A and NOT clinical/privacy independent review. Material design icon issue in test harness resolved, app product code unchanged.
- Real historical BEFORE screen capture, exact Target↔Render for fully integrated installed ProfileScreen and independent visual scoring are still missing. Visual fidelity cap **≤7.5/10** per docs/QUALITY_SCORING_POLICY.md. No FINAL execution/adversarial overall score can honestly be recorded yet; UI release binary gate NO_GO.
- [Issue #1069 D18-D](https://github.com/hraaaaf/IAMINA-MVP/issues/1069) opened for device physical A→B→A, RTL/accessibility, independently reviewed privacy+clinical, backup, no inferred treatment/targets, correct dates/provenance. Desktop Commander DESKTOP-3MAJEEH is offline at inspection, thus true native proof unavailable; human/device gate OPEN.
- The historic full CI on earlier 884a9c67 was 7/7 SUCCESS (Flutter 809 passed, 1 skipped). Full CI **must be revalidated** for later HEAD with screenshot test/CI workflow changes; no inherited green status. GitHub PR #1066 must remain DRAFT based on D18-B #1064 after temporary test trigger, with no merge and no Vercel deployment. P5 overall history 50% unchanged.

### Gate-sensitive next
1. Obtain exact final-HEAD full Flutter CI and verify new raster and generic Web UI workflow statuses.
2. Compare the legible screenshot set critically to target, note coverage gaps. No certificate 9+/10 without native full-screen BEFORE/AFTER, two real physical devices, independent reviewer and Perfection Pass.
3. D18-D issue #1069 human gate, then D18-A/B/C review and sequential merging only if all binary release/security gates verified, followed by postmerge roadmap/Notion closeout. Do not merge a PR targeting main purely to launch CI.


## Reprise frontend canonique — 15 octobre 2026

**Constat contradictoire corrige :** le precedent test `d18_profile_capture_test.dart` utilise un `Scaffold` et `ThemeData` isoles, pas le frontend produit. Ses images restent des preuves widget uniquement. La capture conforme est maintenant `d18_profile_integrated_capture_test.dart` : instancie le **vrai `ProfileScreen`** avec `AminaVisualLanguage.harmonize(AminaTheme.light)`, `AminaMobilePageHeader`, `ResponsiveContentSurface`, sections medicale / D18 / Ramadan / preferences / donnees / compte, coffre SQLite synthetique et verrou fictif uniquement pour l'audit. Aucune donneee reelle.

**Goal :** D18 doit etre integre dans l'architecture visuelle du Profil IAMINA actuel et rester utilisable en FR/AR RTL 360×560, 390×844, 768×1024 et 1280×900. **Target/mockup de reference :** les cartes existantes du Profil definies par `_buildProfileSection` : meme `AminaTheme.radius2XL`, bordure `AminaVisualLanguage.controlBorder`, ombre, icone verte 40px, espacements et typographie. Conserver champs facultatifs / provenance et flux de sauvegarde local.

**BEFORE mesure :** vrai `ProfileScreen`, run [#38748788263](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38748788263), HEAD `486efa62` ; 24 captures FR/AR : D18 visuellement non aligne sur les autres cartes, titre AR en carres (Georgia latin). **AFTER code :** `AminaMobilePageHeader` n'impose plus `Georgia` en arabe ; `D18ProfilePanel` reprend la decoration et les dimensions de `_buildProfileSection`, sans modifier ses operations de lecture/ecriture. Le banc d'audit charge `Inter`/`Roboto` via police de lisibilite DejaVu et la vraie police du titre FR `IAMINASerif-Bold-subset.ttf` pour eviter les rectangles Ahem. **AFTER automatise :** [run #38750503737](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38750503737) SUCCESS sur `6bd36f9`, 24 vraies captures ecran Profil + 24 captures widget, 4 viewports FR/AR, et manifeste SHA256; artefact id 11982015025. **Limite** : le rendu flutter_test utilise toujours les polices substituees pour Inter/Roboto, un verrou fictif, et non une app installee sur Android/iOS. Ce n'est pas un BEFORE historique de D18-A/B.

**Controle de risque :** aucune retouche de traitements/cibles/alertes, horodatage ni proprietaire dans ce lot de style. Les assertions verifient `ProfileScreen` affiche et la section D18 presente, le titre arabe ne force pas Georgia, absence d'exception, historique 72.50 kg donnees synthetiques. Les workflows geometry [#38750503665](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38750503665), CGM onboarding [#38750503675](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38750503675) et first-use [#38750503670](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38750503670) SUCCESS, Chrome [#38750503817](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38750503817) a verifier ; CI complete du HEAD documentaire final a relancer/attester.

**Double notation sous la politique :** EXECUTION_SCORE 7.5/10 ; ADVERSARIAL_SCORE 7.5/10 ; ecart 0 ; RETAINED_SCORE **au plus 7.5/10**, car pas de BEFORE historique de l'application native installee ni de Target↔Render physique complet / review independante. Statut **NOT_VERIFIED / RELEASE NO_GO** ; Perfection Pass final et score >=9 impossibles sans vrais appareils et reviewers. Voir [D18-D #1069](https://github.com/hraaaaf/IAMINA-MVP/issues/1069).

**Next exact :** CI complete exact-HEAD via PR temporairement base main (CI trigger seulement), restauration immediate de la base D18-B, verifier tous les runs et faire relire metadata GitHub/Notion. Ensuite vrai A→B→A sur 2 terminaux, revues privacy/clinique et comparaison native BEFORE/AFTER, scores et certification puis merges si et seulement si gates verts. Aucun Vercel.

### Exact-head CI trigger — 15 October 2026
The final documentation-only commit was made while PR #1066 temporarily targets `main` **solely** to trigger `.github/workflows/ci.yml`, which listens to PR `opened`/`synchronize` targeting main/dev. **Never merge PR #1066 under main directly**; restore base to D18-B after runs start. The previous integrated real-ProfileScreen raster evidence remains on the same product source tree; documentation does not change runtime or screenshots. Track CI on the new SHA; no success claims before exact-head verdict.

## VRAI frontend — comparaison finale, audit Flutter de 15/10/2026

- **Goal** : la section facultative D18 adopte la hiérarchie et la charte visuelle du `ProfileScreen` IAMINA réel.
- **BEFORE** : run [#38748788263](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38748788263), 24 écrans intégrés au SHA `486efa623a2b778b87e1bb45e68d13cd768cfeed`, 4 tailles × FR/AR × top/ouvert/historique.
- **Cible** : composants de production `_buildProfileSection`, `AminaMobilePageHeader`, `AminaVisualLanguage`, `AminaTheme`, `ResponsiveContentSurface`.
- **AFTER** : run [#38752803040](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38752803040) SUCCESS SHA `57edde39b2c91f3b167e1e139e5efeac5359e993` : 24 vraies captures `ProfileScreen` et 24 isolées, FR/AR × 360×560,390×844,768×1024,1280×900. ZIP 11981253476 téléchargé : 48 PNG présents, SHA256 de chaque PNG comparé et validé. Le titre « Mon Profil » et son équivalent arabe sont lisibles ; les cartes D18 ont désormais les mêmes bordures, coins, ombres et styles que les autres cartes. `Georgia` AR évité, `Inter`/`Roboto` de repli pour titres Georgia à glyphes manquants.
- **Résidu constaté** : certains libellés de commandes de `flutter_test` restent en rectangles Ahem ; l'essai d'injection de police audit Ahem→DejaVu n'a changé **aucune** des 48 images en comparant les SHA256 du run précédent `3df09fb9` et `57edde39`. **Ne pas présenter ces images comme une lecture typographique complète**, ni une preuve de rendu de l'app installée. Le banc remplace Inter et Roboto par DejaVu, coffre/AppLock simulés. L'app Web continue de masquer D18 tant que #1054 est ouvert.
- **Scores provisoires sous `docs/QUALITY_SCORING_POLICY.md`** : Execution 7.5/10, adversarial 7.2/10 (écart 0.3), retenu **≤7.2/10** ; plafond applicable fidélité visuelle 7.5 en absence de vrai Target↔Render natif BEFORE/AFTER, absence revue indépendante, textes de commandes incomplets. **NOT_VERIFIED / NO_GO release**, Perfection Pass complet et seuil ≥9 hors de portée sans [D18-D #1069](https://github.com/hraaaaf/IAMINA-MVP/issues/1069).
- Ancienne CI globale [#38751662466](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38751662466) SUCCESS au SHA `edeeaaf8` mais n'atteste pas le SHA produit plus récent. Ce commit documentaire déclenche la **CI exact-head** avec base PR temporaire `main` ; restaurer immédiatement D18-B après lancement. **Aucun merge ni Vercel**.


## D18 only — preuve de validation ciblée 2026-10-15 (lot #18, sans modules voisins)

**Périmètre exact** : poids facultatif à historique append-only avec unité kg/lb, date/heure explicitement confirmée et provenance patient ; année de naissance facultative ; identité de genre autodéclarée facultative ; effacement de ces deux derniers champs ; données D18 isolées par coffre patient, sans effet sur traitements, diagnostics, cibles ou alertes. Notifications de poids (#20), CGM, chat, autres pages, pilotes globaux hors périmètre.

**Goal** : confirmer les comportements ci-dessus, les refus d'entrée invalide, le rejet d'un autre propriétaire, le repli A→B→A et la présentation locale au sein du vrai Profil.

**Preuves en CI spécifiquement D18** :
- D18-A PR [#1060](https://github.com/hraaaaf/IAMINA-MVP/pull/1060), commit `337495367bdcbfd3ae4a8ea916d8b5737423523a`, [run D18 backend #38765074553](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38765074553) **SUCCESS** : `pytest core/tests/test_d18_progressive_weight_history.py diabetes/tests/test_d18_progressive_profile_http.py` → **15 tests PASS, 10 sous-tests PASS** ; invalid inputs/units/timestamps, owner bearer A/B, absence de données créées implicitement, patch année/identité + effacement, conversion, append-only/idempotence. CI générale A [#38765074460](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38765074460) SUCCESS.
- D18-B/C PR [#1066](https://github.com/hraaaaf/IAMINA-MVP/pull/1066), commit code `37c02500a385d259eaaf0073c7d1b6c3868865a7`, [run Flutter D18 #38765508426](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38765508426) **SUCCESS** : 4 suites D18 locales (`d18_progressive_demographics_store_test.dart`, `d18_weight_backup_boundary_test.dart`, `patient_weight_history_store_test.dart`, `d18_profile_panel_test.dart`) → **27 tests PASS**. 2 suites de capture D18 isolé et vrai `ProfileScreen` → 1+1 test PASS. Artefact 11988176981 vérifié : **48/48 PNG**, manifeste SHA256 correct, 24 vues du Profil réel, images **bit-identiques 48/48** au précédent état visuel `3fe53c27`. Aucune modification de présentation, seulement tests/élimination fuite d'état date picker.
- Correctif D18-C : `_selectTime` capture coffre et epoch avant `showDatePicker` / `showTimePicker` ; refuse un timestamp issu d'un précédent patient si changement de coffre pendant le dialogue. Test supplémentaire : effacement volontaire de l'année et du genre, invariance `diabetesType`, `treatment`, `targetRangeLow/High`, `unitPreference`.
- Les audits Chrome génériques et autres fonctions ne servent **pas** de preuves D18. Aucune synchronisation inter-appareils prévue pour ces champs locaux ; aucun test double téléphone imposé. Test réel d'ouverture/lock/nom de coffre natif et confirmation indépendante limitée aux données D18 restent des **gates non revendiqués** avant merge.

**Resultat observable** : suites ciblées D18 backend et frontend réussies au code ci-dessus ; les captures du vrai `ProfileScreen` n'ont subi aucune régression visuelle pixel-par-pixel. **Statut** : validation automatisée D18 PASS ; lot D18 **PAS certifié release**, sans prétendre revue native de sécurité/données par tiers ou visuel physique Target↔Render. UI scoring cap défini plus haut inchangé. [Issue D18-D #1069](https://github.com/hraaaaf/IAMINA-MVP/issues/1069) réduite au périmètre #18.

**Next exact** : vérifier la réexécution ciblée au commit final documentation+workflow ; inscrire son run dans PR/Notion sans nouveau commit si vert. Garder les 3 PR en DRAFT tant que derniers gates D18 stricts non satisfaits ; ensuite intégration séquentielle, tests D18 post-merge et .md, sans déploiement Vercel.
