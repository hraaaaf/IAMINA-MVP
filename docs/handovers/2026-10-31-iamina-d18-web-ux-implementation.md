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
