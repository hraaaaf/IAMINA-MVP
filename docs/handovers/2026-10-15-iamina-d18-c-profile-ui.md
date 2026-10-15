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


## D18-D — Android émulateur GREEN confirmé et limites de certification — 15 octobre 2026

**Goal borné :** faire fonctionner exclusivement les données D18 (#18) dans un vrai APK Android de test, coffre SQLite sur disque, A→B→A après fermeture et réouverture, historique de poids déclaré, année/identité facultatives, refus de la restauration d'un autre propriétaire et section D18 visible seulement lorsque le verrou du banc de test est déverrouillé. **Pas** de test CGM, PWA, chat, sécurité générale ni D20.

**Preuve directe au HEAD produit `c25784b136641d3f58e8b659cc5e4f27008b59a3`** :
- [D18 Android-native #38771342438](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38771342438) **COMPLETED / SUCCESS**, job `116547648195` ; journal : `✓ Built build/app/outputs/flutter-apk/app-debug.apk`, `Installing ...app-debug.apk`, test `D18 Android disk A B A and actual ProfileScreen native gate`, puis `00:06 +1: All tests passed!`. Les assertions de `frontend/integration_test/d18_android_patient_profile_test.dart` portent sur les coffres distincts A=994734/B=994812, les informations D18, le retour A, le rejet du backup A dans B, la conservation d'historique et le panneau `ProfileScreen`.
- [D18 Flutter ciblé #38771342901](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38771342901) **SUCCESS**, 28 tests D18, deux tests de rendu ; le dernier correctif Android `c25784b1` ne modifie pas les composants de production.
- Le premier run natif #38769131036 échouait **à la compilation du seul test** sur `PatientProfileData.weight`, champ Drift inexistant ; suppression de cette assertion non valide, puis vert au commit ci-dessus.

**Audit adversarial de la trace Android :** Drift émet un *warning* `created the database class AppDatabase multiple times` pendant que le test ouvre simultanément A et B pour simuler une restauration croisée ; les bases sont physiquement séparées et le test passe, mais ce warning **ne démontre pas** une absence de course dans toutes les configurations. Le gestionnaire réel `PatientVaultSessionController` retire l'ancien coffre avant l'ouverture du nouveau ; son parcours avec authentification réelle n'a pas été instrumenté ici. Le test utilise `_AppLockFixture` (faux verrou), non biométrie ou identification authentique. Ne pas qualifier les résultats d'essai sur téléphone physique ni de certification sécurité/clinique.

**Scoring provisoire — périmètre D18 seulement, politique `docs/QUALITY_SCORING_POLICY.md`** :
- Technique D18 : EXECUTION_SCORE 8.6/10 ; ADVERSARIAL_SCORE 8.0/10, écart 0.6 → investigation nécessaire avant une future vérification ; aucun score 9+ autorisé. Cause de l'écart : verrou et authentication synthétiques, avis indépendant absent, avertissement Drift de concurrence.
- Visuel D18 : scores préexistants EXECUTION 7.5, ADVERSARIAL 7.2 ; retenu **au plus 7.2/10** faute de comparaison native finale et revue indépendante ; et la certification globale du lot est **NOT_VERIFIED / NO_GO**.
- Gate externe réel : contrôler avec un compte de démonstration sur application native la visibilité D18 après verrouillage/auth et le devenir d'un export JSON D18 (la fonction `LocalBackup.exportVaultJson` produit du JSON clair, n'affirme pas le chiffrement). Faire examiner uniquement ces chemins D18 par une personne/agent indépendant ; ensuite Perfection Pass et, si seuils atteints, merges séquentiels + tests ciblés post-merge. Pas de déploiement Vercel.

**Next exact :** dossier de preuves PR #1066/issue #1069/Notion à synchroniser et relire, sans modifications de production ; gate d'accès à une installation native à authentification réelle et une revue indépendante ciblée, puis certification ou correction D18 selon leurs résultats. Les PR #1060/#1064/#1066 demeurent DRAFT/non fusionnées. P5 50 % historique inchangé.


## D18-D — BLOQUANT PRODUIT PROUVÉ : authentificateur fort natif indisponible (15/10/2026)

**Code vérifié** : `frontend/lib/services/app_lock_authenticator_factory.dart` lie le stub de `app_lock_authenticator_stub.dart` hors Web (`dart.library.js_interop` faux) ; le stub retourne systématiquement `AppLockCapability.unavailable` et rejette `enroll`/`unlock`. `AppLockService.configure()` refuse tout authentificateur dont la capacité n'est pas `supported`. Le vrai `ProfileScreen._unlockedNativeD18Vault()` n'affiche D18 que si `AppLockService.isUnlocked == true` et si le coffre Django natif existe. **Conséquence :** le parcours D18 n'est pas ouvrable avec le fournisseur de verrou par défaut sur Android/iOS actuellement. Le run Android GREEN antérieur utilisait volontairement un faux `AppLockService` déverrouillé et ne démontrait PAS l'accès en production.

**Contrôle ajouté au run Android D18** : `checkNativeD18AccessReleaseGate()` exécute la **vraie factory native** sur émulateur et exige `unavailable` comme preuve négative explicite, avec trace `D18_NATIVE_ACCESS_RELEASE_GATE=BLOCKED`. Cette assertion doit évoluer **avec une implémentation sécurisée effective** (et non être supprimée ou remplacée par un contournement). Les assertions de coffre SQLite A→B→A et celles du panneau D18 avec verrou fictif restent séparées. Ce test est attendu VERT si l'absence de support est bien observée ; **VERT n'autorise pas la mise en service du verrou**.

**Sécurité / politique `QUALITY_SCORING_POLICY.md`** : l'absence d'un authentificateur natif utilisable est bloquante pour l'usage patient D18, score de livraison D18 plafonné à **5.9/10**, `BLOCKED / NO_GO`, même si tous les tests des écritures locales réussissent. Aucun déverrouillage sans authentification ne doit être ajouté. Un correctif sûr nécessite une décision d'architecture authentification forte native et sa validation sur appareil avec garanties de matériel/certificat, avant Perfection Pass, revue indépendante et merges. Cette dépendance D18 doit être notée séparément du périmètre D18 (ne pas recertifier les autres modules).

**Export D18** : `LocalBackup.exportVaultJson` produit en mémoire du JSON contenant les champs D18 ; **ceci n'est pas une preuve de fuite**, ni d'écriture de fichier ni d'upload, mais la destination et la protection éventuelle de ce résultat doivent être vérifiées avant d'autoriser un export réel. Ne pas ajouter un chiffrement fictif dans le sérialiseur pour obtenir un faux PASS.

**Goal** : fournir la preuve de blocage réelle sans prétendre qu'un widget déverrouillé synthétiquement représente un authentificateur utilisateur. **Succès du présent lot de détection** : Android ci réel vérifie `unavailable` et annonce `BLOCKED`; la vraie certification D18 reste rouge. **Next exact** : vérifier le run Android sur nouveau SHA et mettre à jour les gates ; décision humaine nécessaire pour choisir un implémenteur/contrat de déverrouillage natif sécurisé, puis test réel/auth et revue indépendante D18.


## Option A acceptée — implémentation candidate de verrou cryptographique natif (15 octobre 2026)

**Décision utilisateur :** option A, sans dérogation ni fallback à une simple vérification booléenne, authentificateur fort local Android/iOS. **Goal** : autoriser le panneau D18 uniquement après une signature vérifiée par une clé non exportable dont chaque utilisation nécessite une biométrie forte ; interrompre l'opération si le contexte patient/auth change. Succès final = tests sur appareils + revue indépendante D18, non simplement compilation.

**Implémentation en PR #1066** :
- `frontend/lib/services/app_lock_authenticator_native.dart` utilise `MethodChannel('ma.iamina.app/native_app_lock_v1')` sur Android/iOS. Le contrat de `AppLockCredential` existant reste sérialisé avec origine dédiée `https://native.iamina.invalid` et `rpId=ma.iamina.app` ; WebAuthn et clé native ne sont pas confondus. Une réponse `verified` absente ou clé SPKI malformée est refusée.
- `frontend/android/app/src/main/kotlin/ma/iamina/app/MainActivity.kt` crée une clé EC P-256 Android Keystore authentifiée par utilisation (`setUserAuthenticationParameters(0, AUTH_BIOMETRIC_STRONG)`, `setInvalidatedByBiometricEnrollment(true)`) et passe l'opération `Signature` réelle dans `BiometricPrompt.CryptoObject`. Chaque déverrouillage signe un défi aléatoire de 32 octets et vérifie la signature ECDSA avec la clé publique du même Keystore, sans exporter la clé privée. Appareils Android < API 30, sans `BIOMETRIC_STRONG`, ou erreur/annulation : refus.
- `frontend/ios/Runner/AppDelegate.swift` crée un P-256 Secure Enclave avec `SecAccessControl` `.privateKeyUsage` + `.biometryCurrentSet` et stockage `ThisDeviceOnly`, puis exige `SecKeyCreateSignature` et `SecKeyVerifySignature` sur un défi aléatoire, après recherche `SecItemCopyMatching` liée au `LAContext`. iOS simulateur/sans biométrie : refus. `Info.plist` inclut un motif Face ID.
- `AppLockService` garde `AuthEpoch` et un compteur d'opérations : aucun résultat biométrique retardé ne publie un déverrouillage après un `lock()` ou changement A↔B. Tests ciblés `d18_native_app_lock_boundary_test.dart`.
- L'intégration Android D18 contrôle explicitement **le vrai channel natif** et constate son état `unavailable` sur **émulateur CI non enrôlé**. Un test vert dans cet état prouve le refus sûr et la présence du channel ; **ne prouve PAS la biométrie sur matériel**.
- CI D18 Android étendue au test de race ; compilation iOS isolée `.github/workflows/d18-ios-biometry-compile.yml` ajoutée ; résultats à reporter seulement après runs au HEAD exact.

**Limites non résolues / vérification indépendante requise** : compilation Kotlin/Swift et test Android sur HEAD final, iOS sans signature, preuve du chemin d'enrôlement biométrique + signature réelle sur matériel Android/iOS, ajout/retrait de biométrie, annulation/lockout, bascule authentifiée A→B→A ; vérifier `LocalBackup.exportVaultJson` au point d'utilisation et la revue clinique/UX FR/AR du panneau. **Aucune attestation matérielle ni chiffrement de la base démontrés** : il s'agit d'un authentificateur d'accès, pas du chiffrement de SQLite. Les identifiants WebAuthn préexistants sur mobile restent incompatibles et doivent échouer fermés plutôt qu'être silencieusement reconnus.

**État :** candidat implémenté, CI en cours/à lancer, **D18-D NO_GO** avant preuves ci-dessus. Les PR DRAFT et la séquence de merge restent inchangées. Références de conception : Android docs BiometricPrompt.CryptoObject/KeyGenParameterSpec ; Apple Protecting Keys with Secure Enclave/SecAccessControl.biometryCurrentSet ; Flutter FlutterImplicitEngineDelegate.


## OPTION A — closeout candidat et BLOCKER CI sans runner (15/10/2026)

**Goal D18 strict** : chiffrement cryptographique de l'opération d'accès (pas de chiffrement de la base garanti), Android Keystore avec BiometricPrompt.CryptoObject, iOS Secure Enclave et biométrie `biometryCurrentSet`, blocage par défaut si matériel absent ; empêcher que A reçoive un résultat d'authentification décalé au moment où B devient actif. **Critère de succès release** : compilation Android+iOS, vrais essais d'enrôlement, signature/vérification, annulation/lockout/invalidation biométrique, absence de fuite A→B→A, revue indépendante ciblée D18, scoring/Perfection Pass ; **preuves du code candidat ≠ certification release**.

**État source** : HEAD candidat avant cette mise à jour `7b47f2ed5a7f342a44e81c3ae988bcefa3ae1439`, PR #1066 DRAFT/base D18-B. Android `MainActivity.kt`, iOS `AppDelegate.swift`, canaux Flutter/Dart native authenticator, garde `AuthEpoch` et tests D18 ciblés. `app_lock_localized_copy.dart` distingue désormais le verrou mobile **biométrique fort sans PIN de secours** de l'option WebAuthn navigateur. BEFORE était un texte générique incluant PIN ; AFTER un texte mobile limité à Face ID/empreinte forte ; **captures natives BEFORE/AFTER sur les mêmes viewports non réalisées**, donc ne pas revendiquer fidélité visuelle validée. Le chemin `LocalBackup.exportVaultJson` produit du JSON en mémoire sans opération réseau/écriture directe connue ; aucune fuite ni protection finale d'export revendiquée.

**CI exact-HEAD** : [run Android #38779467079](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38779467079) et [iOS #38779467080](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38779467080), plus 5 workflows GitHub, tous `COMPLETED/FAILURE` au HEAD `7b47f2ed5a7f342a44e81c3ae988bcefa3ae1439` en ~3-6 secondes, **0 step, runner vide**. Relance unique des deux jobs D18 (`run_attempt=2`) : encore failure **sans runner ni compilation**. Les logs des jobs absents ; **on ne peut pas qualifier Kotlin/Swift de rouge ou vert**, aucune assertion de ce nouveau code n'a tourné. GitHub Status officiel le 15 octobre 2026 : Actions opérationnel, origine de l'échec spécifique repo/compte non vérifiée (billing/quota/runner/permissions pistes seulement). Ne pas multiplier les runs tant que le refus de lancement n'est pas diagnostiqué ; contrôler l'avertissement explicite dans UI GitHub.

**Preuves précédemment acquises mais STALE pour option A** : tests backend D18-A 15+10 ; frontend 28+2 ; APK Android A→B→A sur ancien faux verrou au code `c25784b1` — valident l'historique D18/isolement, pas la biométrie candidate. **RETAINED_SCORE release ≤5.9 / 10, BLOCKED/NO_GO**, sans avis indépendant ni essais matériels. Aucune PR fusionnée, aucun Vercel.

**Next exact** : faire rétablir l'exécution des jobs dans le dépôt (message précis de la bannière GitHub Actions requis), puis relancer **une** CI Android et iOS ciblée sur HEAD final ; corriger le code seulement sur erreur concrète, refaire images BEFORE/AFTER sur mêmes viewports après toute retouche UI, tester biométrie matérielle et reprise A→B→A, revue indépendante ciblée, perfection pass, scoring, merges séquentiels A/B/C puis validation D18 post-merge. Roadmap P5 50 % historique inchangé.


## D18-D — clôture CI option A vérifiée au HEAD e677044c (15/10/2026)

**Goal D18 option A**, limité au profil progressif #18 : démontrer que l'authentificateur natif candidat Android Keystore/P-256 et iOS Secure Enclave/P-256 compile, refuse toute ouverture sans clé/biométrie forte, rejette les réponses d'authentification reçues après une transition de patient, et que les données D18 restent isolées sur vrai SQLite A→B→A. **Success technique CI** : Android Flutter + APK installé + 1 test d'intégration ciblé, iOS Dart + Xcode app unsigned, même SHA. **Preuves exactes** ci-dessous.

- **PR #1066 code HEAD `e677044ced3fadbe97c6e7d34561c26b3babee58` : 7/7 workflows GitHub COMPLETED/SUCCESS**, dont les seuls workflows D18 d'acceptation [Android #38786798125](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38786798125), [iOS #38786798297](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38786798297) et [raster Flutter #38786802854](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38786802854). Les autres 4 sont des workflows génériques déclenchés, **pas des gates supplémentaires du #18**.
- **Android #38786798125 SUCCESS**, job `116600760572`. Journal : `00:00 +2: All tests passed!` pour le test D18 de transition AuthEpoch ; `✓ Built build/app/outputs/flutter-apk/app-debug.apk` ; `Installing ...app-debug.apk` ; test `D18 Android disk A B A and actual ProfileScreen native gate` ; trace `D18_NATIVE_BRIDGE=CONNECTED STRONG_BIOMETRY=UNAVAILABLE_UNENROLLED_CI_EMULATOR` ; `00:06 +1: All tests passed!`. L'émulateur est **sans biométrie forte enrôlée**, donc le refus d'accès est attendu et sûr. Les vraies SQLite locales A→B→A, données de poids kg/lb datées, champs démographiques facultatifs et refus backup inter-patient sont vérifiés par le test. Warning Drift « multiple AppDatabase » dû au montage de deux coffres dans la fixture, conservé : la CI ne prouve pas l'absence universelle de courses.
- **iOS #38786798297 SUCCESS**, job `116600756265`. Journal : `00:00 +2: All tests passed!` (fin d'authentification obsolète après transition A→B) ; `Xcode build done` ; `✓ Built build/ios/iphoneos/Runner.app (83.6MB)` via `flutter build ios --release --no-codesign`. Il s'agit d'une **compilation Swift/Security sur runner macOS**, PAS d'un test Face ID, de signature par Secure Enclave ou d'application signée/distribuée.
- L'ancien Android [#38785044308](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38785044308) était rouge **uniquement parce que le test Dart importait deux fonctions `createPlatformAppLockAuthenticator`**. Import resserré `show NativeAppLockAuthenticator` au commit `e677044c`, puis run Android vert. Les anciens runs sans runner et l'annulation D18 par conflit de concurrence D20 sont résolus : Android workflow groupé par PR depuis `e28c0a5d`.
- Backend D18-A [#38765074553](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38765074553) : 15 tests + 10 sous-tests PASS. Tests Flutter D18-B/C : 28 tests ciblés et deux tests de rendu intégrés PASS antérieurement, nouveaux tests de verrou tardif 2 PASS exact code. Tout ceci certifie la **validation automatisée bornée**, et NON l'absence d'effets cliniques ou de failles sur tout IAMINA.

**Gate D18-D, libération non autorisée / NOT_VERIFIED / NO_GO** malgré CI GREEN : (1) Android réel avec biométrie forte enrôlée : création clé OS/auth-per-use et signature ECDSA démontrées, annulation, lockout, changement de biométrie invalidant clé, reboot, credential hérité/recovery ; (2) iPhone réel Face ID/Touch ID : `biometryCurrentSet` et clé Secure Enclave, interruption, annulation, invalidation ; (3) A connecté → lock/logout → B connecté → lock → retour A, absence de fuite de données et de preuve biométrique tardive ; (4) vérifier au point de consommation tout éventuel export `LocalBackup.exportVaultJson`, lequel ne chiffre pas son JSON en mémoire ; (5) revue indépendante cryptographie/privacy et clinique/UX du panneau D18 en FR/AR/RTL, vue BEFORE/AFTER aux mêmes viewports pour le changement de message du verrou mobile, puis double scoring et Perfection Pass. Aucune de ces preuves physiques/indépendantes n'est acquise. L'ordinateur Remote Desktop `DESKTOP-3MAJEEH` est **offline** au contrôle ; aucune installation matérielle distante n'a été réalisée. Ne pas remplacer les preuves matérielles par un `_AppLockFixture`, une réponse `capability` ou un APK compilé.

**État de clôture de l'automatisation sur code `e677044c` : GREEN.** Les PR #1060 (backend), #1064 (vault), #1066 (UI + auth native candidat) restent **DRAFT/non mergées**, #1069 OPEN, **aucun déploiement**. Le SHA final de ce document est un commit de **documentation seulement**, donc CI déclenchées à part et à vérifier ; ne pas prétendre que son SHA était dans les logs ci-dessus. **Next exact** : relire le résultat de CI du nouveau SHA documentaire, mettre à jour Notion/PR/issue avec références, puis human gate (appareils biométriques et revue indépendante) avant décision de certification/merge. P5 global 50 % historique inchangé.


## Deux environnements natifs D18 — demande « deux Ubuntu » (15/10/2026)

**Précision technique obligatoire** : un simulateur iOS Apple ne s'installe pas sur Ubuntu ; Xcode et CoreSimulator exigent macOS. La solution exécutée est **Ubuntu runner + émulateur Android API35** et **macOS runner + simulateur iOS iPhone**, tous deux isolés. L'équivalent exact de deux Ubuntu n'existe pas pour des tests iOS natifs. Réf. Apple Xcode system requirements et « Running your app on simulated or physical devices ».

**Goal** : ne pas se contenter d'une compilation iOS. Installer/tester sur **deux systèmes invités indépendants** la même application D18 : physique SQLite local, comptes synthétiques A→B→A, deux poids historisés, année/identité facultatives, rejet restauration croisée, masquage du vrai `ProfileScreen` sous verrou simulé, test de la factory native réelle sans biométrie enrôlée. Au changement `AuthEpoch`, refus d'un déverrouillage biométrique tardif. Les traces de `testWidgets` deviennent « D18 native disk ... » et la ligne de preuve native identifie un **simulateur non enrôlé**, quel que soit l'OS.

**Implémentation** : workflow `.github/workflows/d18-ios-biometry-compile.yml` étendu : `xcrun simctl list devices available` puis boot iPhone, commande `flutter test -d "$D18_IOS_SIMULATOR_ID" integration_test/d18_android_patient_profile_test.dart`. Le workflow Android Ubuntu existant compile et installe déjà sur Pixel 5 API35 avec `reactivecircus/android-emulator-runner` ; les deux sont déclenchés par les modifications du test d'intégration. Chacune des deux preuves doit afficher une réussite individuelle sur le **même HEAD** avant de déclarer le double simulateur validé.

**Caveats** : Android/iOS simulateurs ne démontrent pas la biométrie matérielle, une clé Secure Enclave réelle, l'authentification de vrais comptes, l'absence universelle de race Drift ni la sécurité d'un export JSON. Il faut une revue indépendante et un vrai Android/iPhone pour un GO D18 release. Aucun serveur/deploy ni mutation des données cliniques hors D18.
