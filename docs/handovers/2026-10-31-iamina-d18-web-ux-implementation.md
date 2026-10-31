# IAMINA — D18 Web / profil progressif + sauvegarde chiffrée — 2026-10-31

## Goal
Intégrer l'UX approuvée au vrai `ProfileScreen` Web IAMINA : données facultatives, poids daté et corrigeable, coffre patient local-first, export chiffré et restauration D18 uniquement. **Pas de synchronisation automatique des données D18 ni de déploiement Vercel.**

## Décisions validées
- Web local-first (option A), profil sans obligation d'onboarding.
- Export manuel chiffré ET restauration testée comme critères bloquants D18.
- Direction UX validée avec obligation d'adaptation aux cartes/typos/couleurs/interaction existantes d'IAMINA. Ce n'est pas une autorisation de merge/deploy.

## État vérifié avant certification
- Base main au démarrage : `fc0366f4c55f2bb25c2b9e2a15367d9241567c76`.
- Branche : `feat/iamina-d18-web-progressive-profile-20261031`.
- PR brouillon : https://github.com/hraaaaf/IAMINA-MVP/pull/1207
- Intégration : `frontend/lib/features/profile/profile_screen.dart` + `profile_screen_presentation.dart` (Web uniquement), et widgets D18 propres au thème `AminaVisualLanguage`.
- Données : `patient_progressive_demographics_store.dart`, `patient_weight_history_store.dart`. PatientVaultScope contraint physiquement le stockage ; pas d'appropriation du coffre legacy.
- Sauvegarde : `d18_encrypted_backup.dart` ; AES-256-GCM avec AAD v1 ; PBKDF2-HMAC-SHA256 600000 itérations + sel aléatoire ; wrapper sans identité ni données patient ; file picker dédié dans Données et appareils. Restauration uniquement si données D18 destination vides, transaction D18-only, vérification après écriture. Jamais `LocalBackup.restoreVaultJson` qui écrase des tables médicales étrangères à D18.
- Poids : version correcte écrite comme nouvelle observation liée à la précédente ; écran n'affiche que la dernière version ; suppression explicite purge la famille.
- Tests ajoutés/portés : démographie indépendante du profil médical, historique + correction/suppression, crypto, altération/mauvaise phrase secrète, mauvais propriétaire, import non destructif, transfert local volontaire.

## 31/10/2026 — D18 Web — CI FUE étendue VERTE sur HEAD exact (nouvelle preuve, sans certification produit)

**Goal :** profil facultatif, historique de poids append-only, export chiffré/restauration D18 via vrais widgets Web, persistance et suppression patient-scoped. **Critère de succès du sous-lot automatisé :** 3 rapports obligatoires PASS au même SHA et leur artefact examiné, aucune assertion supprimée pour obtenir le vert.

**HEAD vérifié :** `91956649e826e18d149e4622cbe3275860b89e38` sur `feat/iamina-d18-web-progressive-profile-20261031` / [PR #1207](https://github.com/hraaaaf/IAMINA-MVP/pull/1207) OPEN/DRAFT. [D18 Web #41211784682](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41211784682) **SUCCESS** (job #124568181629, contrôle final « Strict D18 release gate — all independent evidence required » SUCCESS). [CI générale #41211784767](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41211784767) **SUCCESS**. [Artefact #13046393733](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41211784682/artifacts/13046393733) téléchargé, extrait et ses JSON effectivement lus :
- `report.json` **6/6 PASS** : vues réelles Flutter Chrome FR et AR RTL, 390×844, 768×1024, 1280×900, profil fermé/ouvert et dialogues export/restauration, sans erreurs reportées ; 24 captures dans l'artefact.
- `ui-file-roundtrip-report.json` **passed=true, 23/23 étapes PASS** : année 1994, identité préférant ne pas répondre ; pesée réelle 72,50 kg ; correction append-only 73,00 kg, lecture du même coffre SQLite physique (1 puis 2 lignes, chaîne `replaces_uuid`) via **sonde de lecture seule strictement dans l'hôte de test synthétique**, téléchargement Blob d'un fichier `.iamina` chiffré (1233 octets), sélection de fichier dans un nouveau contexte Chromium, déchiffrement/aperçu/consentement/restauration, rechargement et contrôle de la présence des deux versions, année et identité, suppression de la famille de versions puis vérification base vide après reload. 12 captures de ce parcours. La sonde `d18_e2e_proof=1` n'est **pas compilée dans `main.dart`** ; ne pas interpréter sa réussite comme un audit d'authentification hébergée.
- `encrypted-recovery-report.json` **8/8 PASS** : isolation A/B/A synthétique, mauvais secret et fichier altéré rejetés, transfert/validation C, refus de restauration destructrice.
- Vérification visuelle additionnelle des 8 vues sur planche contact : hiérarchie et sens de lecture FR/AR corrects sur états sélectionnés ; **aucun score de fidélité Target↔Render attribué**, les captures comparables `main` vs PR à mêmes états/hosts restent manquantes.

**Matrice de preuves partielle (FUE de décision, sans prétendre tout le périmètre clos) :**
| Fonction / risque D18 | Preuve et état |
| --- | --- |
| Profil / année / genre facultatifs, persistance | PASS synthétique Chrome + SQLite ; validation métier négative en test Dart, revue clavier réelle non complète |
| Poids daté, édition append-only et suppression après reload | PASS sur réel Chrome + lecture seule du coffre physique, 23 étapes communes |
| Export fichier chiffré / re-import avec consentement / persistance | PASS réel navigateur, reports exact-HEAD et WebCrypto |
| FR / AR RTL, mobile/tablette/desktop sur écrans et dialogues | PASS screenshots géométrie 6 cas ; **Tab/Shift+Tab/focus/lecteur d'écran NOT_RUN ou sans preuve complète** |
| Compte hébergé patient A→B→A, verrouillage et accès par identité | **NOT_RUN pour D18 hébergé**, séparation A/B/A démontrée seulement en navigateur synthétique via test crypto |
| Sécurité/confidentialité navigateur : IndexedDB, session locale, XSS, récupération et gestion de clé | **OPEN** : dossier de risque + approbation requises, pas de chiffrement IAMINA au repos ; sauvegarde `.iamina` chiffrée uniquement |
| Target ↔ Render Web BEFORE/AFTER strictement comparables aux mêmes états / host / tailles | **OPEN** : précédents hôtes de captures non équivalents ; score dimension visuelle **plafonné à 7,5/10**, pas de note inventée |

**Verdict correct :** `D18_AUTOMATED_E2E_PASS` au SHA ci-dessus, mais `D18_FUE_NO_GO / DECISION_OPEN / RELEASE_NOT_AUTHORIZED` tant que les preuves requises manquantes, arbitrages sécurité/privacy et Perfection Pass ne sont pas réalisés. En vertu de `docs/QUALITY_SCORING_POLICY.md`, pas de `VERIFIED`, pas de note totale ≥9 sans tous gates ; *deux reviewers indépendants ne sont pas obligatoires par défaut* (sauf note conservée ≥9,5 ou risque spécifique). Les anciennes phrases de ce handover mentionnant deux reviewers comme gate systématique sont historiques et **supplantées** par AGENTS.md et QUALITY_SCORING_POLICY.md.

**Perfection Pass, encore ouvert :** étudier une comparaison réellement équivalente BEFORE↔AFTER ; Tab/Shift+Tab/focus/RTL ; revue des menaces IndexedDB non chiffré et authentification hébergée multi-identités A→B→A ; statuer protection par chiffrement au repos, dérivation/conservation/récupération des clés et consentement. Le scénario d'anciennes sauvegardes pouvant ressusciter une donnée effacée est divulgué mais doit rester dans le modèle de menace. Corriger les défauts trouvés, relancer les preuves concernées, établir séparément EXECUTION_SCORE et ADVERSARIAL_SCORE (score conservé min), puis gate humain et merge **seulement après autorisation applicable**.

**Next exact :** confirmer sur PR et Notion l'état automatisé PASS et les limitations ; dresser la revue sécurité/privacy ciblée et matrice FUE restante, puis décider explicitement avec le responsable humain si IndexedDB non chiffré est acceptable pour une fonction clinique Web. Pas de déploiement Vercel sans accord explicite distinct. Après toute modification GitHub du document canonique, l'ancien SHA reste la preuve d'exécution des tests et ne vaut pas validation automatique du nouveau SHA docs.

---

## Reprise vérifiée — 31/10/2026 — REVUE PRE-FUSION

**Statut :** fonctionnel en Web synthétique, **NO GO merge / production** : gate UX et privacy à lever. PR [#1207](https://github.com/hraaaaf/IAMINA-MVP/pull/1207) OPEN/DRAFT ; `feat/iamina-d18-web-progressive-profile-20261031`. Baseline fonctionnelle avant cette modification de divulgation : `1acb97048a3c60f08c6b790ae702cee2b3cdd316`.

**Preuves automatisées exactes au SHA 1acb970** :
- [CI générale #41199621553](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41199621553) **SUCCESS** ;
- [D18 Web #41199621556](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41199621556) **SUCCESS** ; [artefact #13042555691](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41199621556/artifacts/13042555691) vérifié par extraction ;
- `report.json` 6/6 : Flutter profil réel FR/AR RTL 390×844, 768×1024, 1280×900, géométrie/browser sans erreur détectée ;
- `ui-file-roundtrip-report.json` true (8 checks) : formulaire Web, passphrase, téléchargement réel .iamina chiffré, nouvel environnement Chromium, sélection du fichier, aperçu, consentement, restauration et relecture année 1994 après reload ;
- `encrypted-recovery-report.json` 8/8 : A→B→A, wrong passphrase / tampering rejetés, transfert vers nouveau coffre C, vérification postimport et refus d'écraser C.
- Ce sont des tests **sur patients synthétiques** ; pas de vraie session hébergée multi-patient ni audit externe complet.

**Revue visuelle interne (review 1/2, pas d'approbation humaine)** : captures FR/AR aux 3 breakpoints examinées ; hiérarchie cartes, couleurs et typographies compatibles avec l'UX native IAMINA ; pas de débordement constaté ; les dialogues export/restauration sont présents. BEFORE main provient de [run #41184549732](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41184549732). AFTER synthétique est dans #41199621556. **Les hosts/fixtures diffèrent** (main app avec navigation inférieure et profil initial non complété contre D5 audit host avec profil fictif complété et alerte pays). Ne pas attribuer une note pixel-perfect : exiger une comparaison à host, états et viewports identiques, double reviewer et acceptation visuelle du SHA.

**UX de restauration et effacement :** une ancienne sauvegarde peut réintroduire des données supprimées. Le dialogue Web comporte désormais une mise en garde FR/EN/AR et le FUE vérifie sa présence en FR/AR. `D18BackupPreview.hasDemographics` ne signale plus « présentes » quand la ligne stockée contient les deux champs facultatifs à null ; test Dart ajouté. Ces changements de sécurité/UX attendent leur validation CI au nouveau SHA.

**Revue sécurité/privacy par inspection du code** :
- Le fichier `.iamina` est chiffré AES-256-GCM ; clé dérivée via PBKDF2-HMAC-SHA256 600k et sel aléatoire ; secret non persisté dans le formulaire ; enveloppe validée, D18-only, restauration transactionnelle, non destructive, testée dans navigateur réel.
- **Le coffre local SQLite Wasm / IndexedDB n'est PAS chiffré par IAMINA au repos**. Le chiffrement du fichier exporté ne protège pas le profil navigateur contre un accès local malveillant ni un XSS de même origine. Références primaires : [OWASP client-side databases](https://cheatsheetseries.owasp.org/cheatsheets/HTML5_Security_Cheat_Sheet.html), [OWASP Cryptographic Storage](https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html). Données navigateur évincées/supprimées selon [MDN Storage quotas](https://developer.mozilla.org/en-US/docs/Web/API/Storage_API/Storage_quotas_and_eviction_criteria).
- Correctif information utilisateur dans cette PR : avertissement FR/EN/AR sous `D18BackupSection` : **export chiffré ≠ stockage navigateur chiffré** ; test navigateur FR/AR ajouté.
- Pas de conclusion de conformité ou protection contre XSS : décider un modèle de menace, tester session réelle A→B→A, vérifier confidentialité/données de santé et stockage local. Pour usage clinique, arbitrage réel **chiffrement au repos + gestion de clé** vs exploitation sur appareils maîtrisés et information/acceptation explicites ; ne pas choisir en silence.
- Session controller retire l'accès au coffre précédent sur transition d'auth, mais parcours réel connecté D18 multi-identités à tester.

**CI externe non Web** au précédent SHA 1acb970 : 14/15 workflows verts ; [TD-008 Android #41199621412](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41199621412) rouge car **Dart Development Service failed to start** sur émulateur, 0 test métier exécuté. Une seule relance ciblée du job `124532669723` lancée sur le même SHA, tentative 2. Conserver comme run séparé, non lié au D18 Web.

## Gates restant OPEN — ne pas merger
1. CI et D18 test ciblé verts au **HEAD produit + avertissement privacy** ; actualiser SHA preuves.
2. Capture BEFORE/AFTER réellement comparables, double revue UX/accessibilité, score et approbation humaine au SHA final.
3. Revue indépendante sécurité/privacy + arbitrage explicite du stockage IndexedDB au repos et preuve auth réelle A→B→A avant clinique.
4. Suivre TD-008 natif séparément ; après accord humain, merge et postmerge avec nouveaux états prouvés.
5. **Pas de Vercel sans autorisation explicite distincte.**

## Next exact
Vérifier CI et D18 au nouveau HEAD, reviewer UX 390/768/1280 + RTL sur contexte identique, modéliser les menaces local/XSS et demander décision humaine sur le stockage au repos et signoff visuel ; ne jamais déclarer D18 DONE prématurément.

## Rappel
Chantier A = 4/13 (30,8%) closes ; D18 OPEN.
