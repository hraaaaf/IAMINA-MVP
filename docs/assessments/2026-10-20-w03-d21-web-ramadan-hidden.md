# IAMINA Web — W03 / D21 : masquer Ramadan dans le Profil

Date : 2026-10-20. Périmètre : **Flutter Web uniquement**. Décision source : D21, `docs/ROADMAP.md` (W03), `docs/assessments/2026-10-15-w00-web-inventory.md` et le registre Notion des 29 décisions.

**Statut : CANDIDAT — non déployé / non certifié visuellement.** W01 reste NO-GO, W02 gelé. Ce quick win est indépendant de W01/W02 selon la roadmap et ne touche ni la sécurité Production ni les notifications D2 (PR #1135).

## Goal → Succès → Preuve

- **Goal exact** : masquer la section saisonnière Ramadan du Profil **dans le Web** sans supprimer ses modèles, migrations, traitements historiques ou la version native ; aucune action Web pour saisir/enregistrer des dates Ramadan ne doit rester accessible via le Profil.
- **Succès observable** : dans un vrai navigateur Web, Profil montre `Informations médicales → IAmina → Données → Compte`, sans carte Ramadan ni boutons de dates/enregistrement. Les autres sections, la langue et la navigation sont inchangées.
- **Preuve requise** : Flutter analyze/tests+build ; captures BEFORE/AFTER strictement mêmes états/viewports Chromium **390×844, 768×1024, 1280×900**, FR/AR RTL, clavier et focus ; revue indépendante. Pas de score visuel >7,5/10 sans Target↔Render réel.

## BEFORE → cible/mise en page → AFTER candidat

**BEFORE code vérifié sur `main` :** `frontend/lib/features/profile/profile_screen_presentation.dart` construit `_buildMedicalSection`, puis `_buildRamadanSection` (avec dates de début/fin et `ramadan-save-period`), puis `_buildProfileSection` IAmina. La section Ramadan est visible par défaut si le profil est consultable. Aucun screenshot contrôlé du même état Web n'a encore été capturé : ne pas inventer une preuve visuelle.

**Cible/mockup écrit :** conserver la mise en page existante, le rythme vertical de 14 px, tous les intitulés/états des cartes. Dans le Profil Web, les cartes `Médical` et `IAmina` deviennent adjacentes ; les cartes Données et Compte restent identiques. Ne pas créer de remplacement décoratif ni supprimer des données.

**AFTER code candidat :**
- `profile_screen.dart` : `kWebRamadanUiEnabled=bool.fromEnvironment('IAMINA_WEB_RAMADAN_UI',defaultValue:false)`, plus `shouldShowRamadanProfileSection(isWeb:...)`.
- `profile_screen_presentation.dart` : `_buildRamadanSection` et son espacement sont ensemble derrière cette garde avec `kIsWeb`; Web par défaut OFF, code natif/conservation historique inchangés.
- `frontend/test/features/profile/w03_d21_ramadan_visibility_test.dart` : garde Web OFF, native non affectée, section et commandes restent compilables et regroupées, build Vercel n'active pas le flag.
- **Aucun backend, API, migration, calcul clinique, donnée patient, plugin, avis médical ou variable Vercel modifié.** Le code historique Ramadan existe toujours ; ce sous-lot ne prouve pas à lui seul qu'aucun autre module ne lit d'anciens champs Ramadan.

## Exclusions et décision de livraison

D2 notifications demeure sur PR #1135 distincte. D3 rappels sur PR #1085 DRAFT ancienne et CI rouge ; pas de réécriture concurrente du dashboard. W01 durcissement Production, restauration Neon et matrices de certification sont volontairement réservés aux décisions finales suivant instruction propriétaire. **Aucun Vercel deployment sans autorisation expresse** ; **aucun merge** avant CI, visuels et revue exigés.

**Next exact** : créer PR DRAFT dédiée depuis `main`, obtenir le verdict CI SHA exact ; ensuite capture Web synthétique avant/après et comparaison FR/AR aux trois tailles. Si les captures ne sont pas disponibles, classer D21 candidat partiel, pas VERIFIED et continuer aux autres décisions W03/W11 sans prétendre fermer D21.


## AFTER observé — Chrome aux viewports canoniques (20/10/2026)

**CI du code candidat `f863fc76c9a1c4f465171f9b0c1007e67860a201` :** **4/4 workflows SUCCESS** exactement sur ce SHA : [main CI #39461485585](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39461485585) avec Flutter analyze + tests + PWA build SUCCESS, [Chrome screenshots #39461485674](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39461485674) trois jobs SUCCESS, [UI geometry #39461485591](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39461485591) SUCCESS, [P5-5 E2E #39461485590](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39461485590) SUCCESS. Les jobs backend ont été SKIPPED pour diff frontend-only : ne pas les compter comme tests back réussis.

**Provenance BEFORE contrôlée** : captures précédentes produites dans [Chrome run #39460086407](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39460086407) sur PR D2 avant W03 (SHA `7b1fc0b96d0b74f47506a58604cf00738d8b0676`), dont les blobs Profil ont été **vérifiés identiques** à `main` sur les deux fichiers `frontend/lib/features/profile/profile_screen.dart` (`22aee4e505990f7fc149f102b62a2501f7807d41`) et `profile_screen_presentation.dart` (`992790c2a9f1607ac573a3745e4aa3f03a36b4cb`). Captures AFTER issues de [#39461485674](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39461485674) sur code D21 `f863fc76`. Les six PNG exacts `profile-[390x844|768x1024|1280x900].png` ont été extraits et **inspectés visuellement**, sans OCR.

| Viewport Chrome FR | BEFORE | AFTER | Comparaison |
|---|---|---|---|
| **390×844 mobile** | « Période de Ramadan » visible entre « Suivi médical » et « IAmina & préférences », confidentialité sous le fold | Ramadan absent ; IAmina adjacente au médical et « Confidentialité & compte » devient visible au premier écran | Conforme, aucun contenu fictif ajouté |
| **768×1024 tablette** | Carte Ramadan intermédiaire dans panneau central | Carte absente, 14px d'espacement normal conservé entre cartes | Conforme, pas de décalage anormal |
| **1280×900 desktop** | Carte Ramadan entre les mêmes sections dans contenu centré | Carte absente, IAmina et Données remontées naturellement, sidebar intacte | Conforme, aucune régression visuelle observée |

**Artefacts source exacts :** BEFORE [390×844](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39460086407/artifacts/12284880175), [768×1024](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39460086407/artifacts/12283937482), [1280×900](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39460086407/artifacts/12283807335) ; AFTER [390×844](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39461485674/artifacts/12284586435), [768×1024](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39461485674/artifacts/12284896199), [1280×900](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39461485674/artifacts/12283849737).

**Évaluation bornée et falsifiable :** UI FR à ces trois tailles **9,0/10** sur le critère visuel purement comparatif (une seule carte cachée, état et ordre des autres cartes préservés). Material step : Execution **8,5/10**, examen adversarial interne **8,2/10** (écart 0,3) ; **score retenu provisoire plafonné à 7,9/10** faute de preuves complètes **AR RTL + clavier/focus + revue indépendante**. Pas de `VERIFIED`, aucun merge. Le contraste/safe-area et le comportement natif doivent encore être vérifiés sur leurs contrats exigés ; la seule preuve de préservation native est la garde de code et le test unitaire, pas un appareil natif.

**Next exact :** fournir test et rendu ciblés AR RTL et interactions clavier puis revue indépendante, requalifier CI si changement de SHA, ne pas déployer sans accord explicite. W01/W02 restent à part, gel de certification W01 reporté à fin des décisions par le propriétaire. 


## Revue adversariale du protocole clavier — 21/10/2026 (à certifier)

**Inspection indépendante des artefacts par un second examen de preuves, pas une revue humaine indépendante qualifiée.** Run `39501629812` sur `ae6ccb5be228db4330e4d7f94f3355009cd77695` : 9/9 CI GitHub SUCCESS sur ce HEAD, 12 PNG et 12 rapports JSON récupérés et examinés. Résultats : Ramadan présent dans les 6 captures BEFORE et absent dans les 6 AFTER (FR/AR, 390/768/1280), aucune largeur de document excédentaire. Les photos du Profil AR montrent une composition RTL correcte sur le périmètre synthétique examiné ; aucune navigation patient authentifié/production testée.

**Défaut probatoire constaté** : le test `keyboard_focus_trace` de ce SHA exigeait seulement qu'une cible AX soit détectée. Or les 6 traces AFTER montrent un focus souvent répété sans progression ; dans 4/6 scénarios, les quatre `Shift+Tab` ne donnent aucun changement de cible. La réussite du job **ne démontre pas une navigation clavier inverse accessible**. Hypothèses : cadence CDP trop rapide ou défaut de focus réel ; impossible de conclure sans épreuve renforcée. **Ne pas classer D21 VERIFIED en s'appuyant sur ce test.**

**Correction de preuve candidate** (prochain SHA, non encore validé par CI lors de cette rédaction) : instrumenter explicitement `ShiftLeft`, attendre stabilisation après chaque Tab, enregistrer cibles avant/arrière, exiger trois cibles avant distinctes **et** retour Shift+Tab sur une cible précédemment visitée ; faute de quoi job FAIL, et diagnostic nécessaire. Source D21 produit inchangée. Revue humaine indépendante, stabilité et accessibilité à confirmer. Aucun merge/Vercel/Neon.


## RTL/keyboard RED — diagnostic de régression requise (21/10/2026)

**État vérifié SHA `cd41dacc2825527bec8f1423a65858517e5ef7a1`** : 8/9 workflows SUCCESS, [workflow W03 D21 #39589122042](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39589122042) FAILURE. Étape `Capture and assert D21 AFTER in real Chrome` : **FR tablette 768×1024**, `Shift+Tab did not return to a previously focused Profile target`. Les logs montrent la compilation et le mobile FR passés, mais l'échec arrête la matrice avant AR et BEFORE. Artefact partiel [#12340894066](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39589122042/artifacts/12340894066) : en tablette, la cible « Données & appareils » reste active sur les quatre Shift+Tab ; sur mobile, elle revient vers une cible plus ancienne. **Cause indécidable** sans distinguer un défaut de livraison des événements Chrome du focus Flutter : ne pas appeler cela un bug RTL arabe confirmé ou attribuer faussement une réussite d'accessibilité.

**Suite technique** : sur le prochain SHA, capturer la grille FR/AR × 3 × BEFORE/AFTER même si un scénario échoue, enregistrer les `keydown` réellement reçus par le document (shiftKey, trusted), comparer les séquences et assertions de focus sur source main identique avant toute réparation du produit. La synthèse finalise en FAIL si AFTER ne navigue pas à rebours. Aucune régression D21 prouvée actuellement ; aucun merge/Vercel.


## Analyse causale des 12 traces FR/AR — run #39591176064 (21/10/2026)

**Résultat exact sur `1e9159107b0daa0d05de9cb77dae78c8a06995e2`** : 8/9 GitHub Actions SUCCESS ; workflow dédié RTL/clavier [#39591176064](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39591176064) FAILURE. Artefact [#12342372819](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39591176064/artifacts/12342372819) téléchargé et inspecté : **12 PNG + 12 JSON**, grille complète FR/AR × 390/768/1280 × BEFORE/AFTER. Ramadan présent dans 6 BEFORE, absent dans 6 AFTER. La comparaison établit que le retour clavier inverse ne passe **dans aucun des six BEFORE**, tandis que les deux AFTER mobiles passent et les quatre AFTER tablette/desktop ne passent pas sur quatre pressions. L'anomalie de focus n'est donc pas démontrée comme régression introduite par la suppression de Ramadan. Aucune preuve de bug spécifique à l'arabe.

**Défaut dans l'oracle supplémentaire** : le capteur DOM voit des `keydown Shift` avec `shiftKey=true` dans les 12 cas, mais **aucun `keydown Tab`**, ni BEFORE ni AFTER, alors que le focus AX/DOM progresse bien avec Tab. Les événements Tab sont vraisemblablement consommés par la navigation focus de Chromium/Flutter avant l'écouteur DOM ; l'absence de `keydown Tab` n'est donc pas une preuve d'échec de livraison CDP. L'assertion qui rendait les 6 AFTER rouges uniquement pour cette absence était invalide.

**Nouveau protocole candidat** : conserver les 12 Tab avant, étendre la phase inverse à 16 Shift+Tab pour traverser les arrêts de focus internes qui ne changent pas de nom AX ; exiger un retour réel à une cible antérieure (sinon FAIL), un `keydown Shift` effectivement reçu, et enregistrer la première pression inverse qui change la cible ainsi que toute stagnation initiale. Ceci reste un test synthétique et ne remplace pas une validation humaine d'accessibilité : un parcours inverse anormalement lent devra être examiné même si le test finit vert. Pas de modification produit, aucun merge ni déploiement.
