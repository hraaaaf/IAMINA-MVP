## 22/10/2026 — D21 FUE-03 : candidat correction du piège de focus dans les sections repliées

**BEFORE prouvé sur SHA `1945da588b9ba2cb3597712922faeadd1d749f68` :** [FUE #39701003352](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39701003352) FAIL 5/6 profils FR/AR × 390/768/1280 ; les 5 échecs exclusivement `FUE-03`, le reste PASS. Artefact #12393561090 téléchargé : `Shift` DOM trusted vrai, mais Tab reste sur l'en-tête « Confidentialité & compte » jusqu'à 11 fois ; ancien harnais `page.keyboard.press()` du run #39693543949 échouait identiquement : ce n'est **pas** seulement une mauvaise injection CDP.

**Hypothèse technique à éprouver** : `ExpansionTile(maintainState:true)` garde les descendants repliés sous `Offstage`, qui n'interdit pas leur focus clavier ; plusieurs champs invisibles peuvent absorber le parcours sans changer le focus AX/DOM visible. Ce problème n'est pas définitivement prouvé avant nouveau test réel.

**Goal UI/UX (aucune modification visuelle attendue)** : conserver l'état des champs non sauvegardés lors de la fermeture, mais exclure immédiatement du focus les descendants des sections repliées ; la section réouverte rétablit leur focus. Pas de `unfocus()`, pas de relâchement du FUE (trois cibles visibles distinctes + Shift+Tab arrière + Shift trusted) et pas de données patient.

**Mockup/référence** : profils du FUE #39701003352, FR/AR aux mêmes viewports 390×844, 768×1024, 1280×900. **Candidat** : `ProfileFocusSafeExpansionTile` conserve `maintainState:true`, observe `onExpansionChanged` et enveloppe chaque enfant dans `ExcludeFocus(excluding: !expanded)` (proxy sans dimensions). `frontend/test/features/profile/profile_focus_safe_expansion_tile_test.dart` vérifie refus du focus invisible, restauration à la réouverture et maintien des saisies.

**AFTER requis** : exécuter tests Flutter + CI exacte et FUE Chromium 6/6 aux mêmes viewports ; comparer les 18 PNG BEFORE/AFTER et le trace AX/DOM/Shift ; vérifier que les sections visuelles restent identiques, calculer le score et corriger tout échec. **Statut candidat/non certifié ; pas de merge/Vercel ; W01 toujours NO-GO.**

---
# IAMINA Web — W03 / D21 : masquer Ramadan dans le Profil

Date : 2026-10-20. Périmètre : **Flutter Web uniquement**. Décision source : D21, `docs/ROADMAP.md` (W03), `docs/assessments/2026-10-15-w00-web-inventory.md` et le registre Notion des 29 décisions.

**Statut au 21/10/2026 : VALIDATION TECHNIQUE WEB SYNTHÉTIQUE 9/9 SUCCESS sur `db314db6bf61c501984b5a3e016d279629707c2a` ; `FUE_NO_GO` (FIRST USER EXPERIENCE de D21 incomplet), CLOSEOUT FINAL OUVERT ; PR prête pour revue au sens GitHub, NON MERGÉE/NON DÉPLOYÉE.** La nouvelle décision propriétaire **supprime le reviewer indépendant comme gate systématique** : le FUE doit couvrir toutes les fonctionnalités D21 avec preuves réelles, pas seulement le changement visuel. Voir la section FUE en fin de document et [PR gouvernance #1138](https://github.com/hraaaaf/IAMINA-MVP/pull/1138), non encore fusionnée. W01 NO-GO, W02 gelé ; le code et les données historiques Ramadan sont conservés. Les anciennes sections ci-dessous sont des jalons datés, non la règle de clôture actuelle.

## Goal → Succès → Preuve

- **Goal exact** : masquer la section saisonnière Ramadan du Profil **dans le Web** sans supprimer ses modèles, migrations, traitements historiques ou la version native ; aucune action Web pour saisir/enregistrer des dates Ramadan ne doit rester accessible via le Profil.
- **Succès observable** : dans un vrai navigateur Web, Profil montre `Informations médicales → IAmina → Données → Compte`, sans carte Ramadan ni boutons de dates/enregistrement. Les autres sections, la langue et la navigation sont inchangées.
- **Preuve requise** : Flutter analyze/tests+build ; captures BEFORE/AFTER strictement mêmes états/viewports Chromium **390×844, 768×1024, 1280×900**, FR/AR RTL, clavier et focus ; revue indépendante. Pas de score visuel >7,5/10 sans Target↔Render réel.

## BEFORE → cible/mise en page → AFTER candidat

**BEFORE code vérifié sur `main` :** `frontend/lib/features/profile/profile_screen_presentation.dart` construit `_buildMedicalSection`, puis `_buildRamadanSection` (avec dates de début/fin et `ramadan-save-period`), puis `_buildProfileSection` IAmina. La section Ramadan est visible par défaut si le profil est consultable. Ce constat était celui du démarrage le 20/10 ; les captures BEFORE/AFTER FR/AR sur même état et mêmes viewports ont depuis été produites et examinées (voir closeout ci-dessous).

**Cible/mockup écrit :** conserver la mise en page existante, le rythme vertical de 14 px, tous les intitulés/états des cartes. Dans le Profil Web, les cartes `Médical` et `IAmina` deviennent adjacentes ; les cartes Données et Compte restent identiques. Ne pas créer de remplacement décoratif ni supprimer des données.

**AFTER code candidat :**
- `profile_screen.dart` : `kWebRamadanUiEnabled=bool.fromEnvironment('IAMINA_WEB_RAMADAN_UI',defaultValue:false)`, plus `shouldShowRamadanProfileSection(isWeb:...)`.
- `profile_screen_presentation.dart` : `_buildRamadanSection` et son espacement sont ensemble derrière cette garde avec `kIsWeb`; Web par défaut OFF, code natif/conservation historique inchangés.
- `frontend/test/features/profile/w03_d21_ramadan_visibility_test.dart` : garde Web OFF, native non affectée, section et commandes restent compilables et regroupées, build Vercel n'active pas le flag.
- **Aucun backend, API, migration, calcul clinique, donnée patient, plugin, avis médical ou variable Vercel modifié.** Le code historique Ramadan existe toujours ; ce sous-lot ne prouve pas à lui seul qu'aucun autre module ne lit d'anciens champs Ramadan.

## Exclusions et décision de livraison

D2 notifications demeure sur PR #1135 distincte. D3 rappels sur PR #1085 DRAFT ancienne et CI rouge ; pas de réécriture concurrente du dashboard. W01 durcissement Production, restauration Neon et matrices de certification sont volontairement réservés aux décisions finales suivant instruction propriétaire. **Aucun Vercel deployment sans autorisation expresse** ; **aucun merge** avant CI, visuels et revue exigés.

**Next exact actuel (21/10)** : obtenir une revue indépendante par un reviewer distinct, valider manuellement le focus clavier/AR RTL (notamment 10 Shift+Tab FR desktop), puis closeout final et décision de merge séparée. Aucune action Vercel autorisée.


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

## Closeout technique avant revue indépendante — 21/10/2026

**Référence immuable vérifiée** : [PR #1136](https://github.com/hraaaaf/IAMINA-MVP/pull/1136) OPEN/DRAFT ; HEAD `f0e565f977cc15154b57616f2e3cfced0a4d4072` ; base `main@31380a7f4c8f61a3ec886ec9d2d66d26c2bf222b`. Aucun merge ni déploiement Vercel effectué dans ce lot. Ce document est l'état avant commit documentaire ; toute modification de ce document produit un nouveau HEAD dont les contrôles doivent être vérifiés selon les workflows applicables.

### Succès et preuves observables

- **Masquage Web** : code relu sur le HEAD : `profile_screen.dart` définit `kWebRamadanUiEnabled` à `false` par défaut ; `shouldShowRamadanProfileSection(isWeb:kIsWeb)` encadre à la fois `_buildRamadanSection` et l'espacement associé dans `profile_screen_presentation.dart`. Les anciennes fonctions de sélection, sauvegarde, les dates et champs historiques restent présentes ; aucune preuve d'exécution native réelle, uniquement préservation source et tests.
- **Preuve UI BEFORE → AFTER** : [artefact exact #12341954912](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39593197148/artifacts/12341954912), [run RTL+clavier #39593197148](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39593197148), **24 fichiers contrôlés = 12 PNG + 12 rapports JSON** : `FR, AR` × `390×844, 768×1024, 1280×900` × `BEFORE, AFTER`. Dans tous les 6 BEFORE : `ramadan_in_ax=true` ; dans tous les 6 AFTER : `ramadan_in_ax=false`. Les captures ont été ouvertes et comparées : navigation, sections médicales, IAmina, Données et Compte conservées, décalage naturel sans carte Ramadan ; composition RTL AR visuellement cohérente. Les assertions de langue, nombre de nœuds AX et largeur de document sont passées sur cette grille. Cette preuve est **navigateur synthétique**, pas authentification/production.
- **Clavier synthétique** : les 6 AFTER ont `forward_unique_targets >= 3`, `reverse_to_earlier_target=true` et `problems=[]`. Première cible déjà visitée récupérée après **2** Shift+Tab (FR mobile), **5** (FR tablette), **10** (FR desktop), **4** (AR mobile), **6** (AR tablette), **6** (AR desktop). Les historiques BEFORE peuvent aussi exiger **5 à 10** frappes pour le retour. L'amélioration d'oracle a supprimé l'assertion DOM `Tab` invalide, mais exige un `keydown Shift` reçu et une vraie cible AX antérieure. **Risque a11y résiduel** : répétition de focus/délai de retour, surtout FR desktop ; le PASS synthétique ne remplace pas l'essai clavier humain indépendant, notamment sur accessibilité des éléments internes. Ne pas attribuer de score 10/10 ni d'attestation WCAG sans audit.
- **CI GitHub exacte sur `f0e565f` : 9/9 completed/SUCCESS**. [CI générale #39593197274](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39593197274), [RTL/clavier #39593197148](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39593197148), [captures Chrome standard #39593197271](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39593197271), [géométrie #39593197235](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39593197235), [first-use #39593197189](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39593197189), [E2E pilote #39593197178](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39593197178), [rapports mobile #39593197639](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39593197639), [onboarding Chrome #39593197126](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39593197126), [Dashboard P7 #39593197201](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39593197201). Le workflow de captures standard était initialement rouge **uniquement** sur `dashboard-768×1024.png` sous le seuil de 10 000 octets (4 465 octets) après erreurs de connexion DevTools, **avant** d'atteindre le Profil. Sa relance ciblée a réussi sur le même SHA : **3/3 jobs Chrome SUCCESS**, incluant tablette `768×1024`. Aucune modification du code patient pour cette instabilité CI. Le scope D21 n'a pas fait passer les tests backend non lancés/ignorés.
- **UI score borné** : score historique visuel FR comparatif **9,0/10** pour trois tailles, sans hausse arbitraire. AR RTL : comparaison favorable aux mêmes états, **pas de score certifié indépendant**. La précédente limite provisoire 7,9/10 reste un indicateur de certification globale, **non levée** sans revue humaine. Les tests de clavier synthétique ne prouvent pas la conformité accessibilité en usage réel.

### Audit croisé et gates restants

1. **Contrat produit/code** : Web masqué par défaut, natif/historique non supprimé ; source et tests Flutter passés. Rien ne prouve une neutralisation des effets Ramadan hors de l'UI Profil ; hors scope.
2. **Contrat preuve/CI** : rendre visibles les 12 PNG/JSON, contrôler les valeurs AX et la relance Chrome exacte. **Ceci est un deuxième examen des preuves par le même assistant, pas un reviewer humain indépendant**.
3. **Gate humain restant** : aucune revue GitHub indépendante observée sur la PR à la date du présent document ; pas de reviewer demandé/identifié par la PR ni de CODEOWNERS trouvé. Exiger une revue par autre personne (Web/Flutter/a11y), essai manuel Tab/Shift+Tab et confirmation RTL, puis consignation de son verdict/observations et correction si nécessaire. **D21 ne doit pas être marqué CERTIFIED / CLOSED / READY FOR PROD** avant ce gate.
4. **Intégration/Release** : ne pas merger automatiquement. Après revue APPROVED et nouveaux tests si corrections, synchroniser PR/documents/Notion, décider merge explicitement selon politique projet, vérifier post-merge avant fermeture. Aucun déploiement Vercel sans autorisation du propriétaire. W01 NO-GO et W02 gelé restent inchangés.

**Next exact** : solliciter un reviewer humain éligible indépendant avec accès au repository (identité absente des métadonnées PR), qui doit contrôler les artefacts #12341954912 et la lenteur du focus inverse (jusqu'à 10 touches). Après approbation effective, revalider le HEAD exact, closeout final et intégration autorisée ; aucun avancement global chiffré sans méthode.

## Décision propriétaire — 21/10/2026 : FUE remplace le gate de reviewer indépendant

**Règle applicable à D21 et aux autres décisions D :** le FUE (FIRST USER EXPERIENCE) doit couvrir **l'ensemble des fonctionnalités et comportements de la décision**, pas seulement le widget modifié. Le gate « reviewer indépendant » anciennement décrit dans ce document est **supersédé**. Source normative en cours d'intégration : [AGENTS.md / PR gouvernance #1138](https://github.com/hraaaaf/IAMINA-MVP/pull/1138), commit `b873f67dc4e38b24ed76119ce10c837c92f13b1d`. Les validations de sécurité, clinique et privacy spécifiquement nécessaires restent obligatoires.

**FUE Goal** : pour un premier utilisateur dans Flutter Web, D21 masque Ramadan sans laisser ses commandes ni effet non voulu accessibles ; les autres fonctions du Profil restent utilisables et les données antérieures ne sont pas détruites. **Succès** : 100 % des scénarios FUE requis `PASS` avec résultats observés et preuves sur les 3 viewports et FR/AR RTL. **Preuve** : interactions réelles navigateur et matrice FUE, complétées par captures, traces, tests et CI exact SHA.

| Cas D21 | Parcours utilisateur couvrant la fonctionnalité | Preuve actuelle | Verdict FUE |
| --- | --- | --- | --- |
| FUE-01 | Première ouverture Profil dans Flutter Web, absence de Ramadan et de ses commandes date/enregistrement en FR/AR, 390×844 / 768×1024 / 1280×900 | 12 PNG/JSON BEFORE/AFTER, [artefact #12345128620](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/39599479683/artifacts/12345128620) | PARTIEL : rendu/AX, pas test interactif complet |
| FUE-02 | Depuis Profil, ouvrir/fermer Médical, IAmina, Données, Compte ; scroller, naviguer ailleurs puis revenir sans régression | Sections et ordre visibles aux trois viewports | NOT_RUN : parcours interactif |
| FUE-03 | Parcours clavier Tab/Shift+Tab, activation des sections, focus visible, RTL AR ; qualifier les focus internes et la lenteur jusqu'à 10 touches | Trace AX synthétique 6/6 après ; pas de test d'activation de toutes les commandes | PARTIEL |
| FUE-04 | Profil vierge puis profil existant (synthétiques), recharger, changer FR↔AR : aucune donnée Ramadan historique perdue ou écrasée | Garde source, tests Flutter unitaires ; sauvegarde réelle non testée | NOT_RUN |
| FUE-05 | Tentative d'accès aux commandes Ramadan Web et vérification des effets saisonniers dans **tout le périmètre D21**, y compris le cas historique persistant | Carte masquée et code conservé ; `docs/ROADMAP.md` demande « Ramadan masqué, code et effets neutralisés » | NOT_RUN : neutralisation des effets Web hors Profil non démontrée |
| FUE-06 | Vérifier états vides/erreur, nav/touch, absence d'overflow, autres réglages Profil, ressaisie et retour selon fonctions concernées | Layout FR/AR et absence d'overflow synthétiques ; autres parcours non prouvés | PARTIEL |

**Couverture actuelle : 0/6 cas FUE intégralement PASS.** Des sous-assertions CI/visuelles sont vertes, mais cela ne suffit pas pour convertir les lignes en PASS. **Verdict : `FUE_NO_GO`**, sans prétendre constater 6 bugs : les cases non exécutées sont un manque de preuve, pas des échecs produit démontrés.

**Next exact :** construire/exécuter les parcours FUE manquants en navigateur réel avec données synthétiques et des oracles action/état, documenter les preuves et corriger les vrais défauts si détectés ; relancer les CI du HEAD final, calculer les scores et effectuer le Perfection Pass. Puis closeout et décision d'intégration. **Pas de reviewer humain générique à solliciter, aucun merge/Vercel automatique.**
