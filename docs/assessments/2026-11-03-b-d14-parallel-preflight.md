# IAMINA B / D14 — Photo de repas Web : préflight, confidentialité et gates (03/11/2026)

## Décision D14 — Goal / succès / preuve
**Goal :** un patient Web ne peut analyser une photo sans consentement IA versionné **et** grant explicite `meal_vision/image` du propriétaire ; chaque révocation, verrouillage, changement de compte ou réponse tardive doit refuser le traitement sans réutiliser une proposition. Zéro donnée patient réelle utilisée pendant les recettes.

**Succès préflight :** 30 parcours synthétiques de révocation/proposition, six visuels FR/AR/RTL, vrai AuthService/Django PostgreSQL16 et coffre Web A→B→A sur 390/768/1280, aucun appel provider, zéro requête de police tierce ; service worker doit precacher les fallbacks locaux et rester apte à l'offline.

**La réussite de la recette n'est PAS une autorisation de traitement médical ou transfert vers un prestataire externe.** D14 reste DRAFT et NO-GO patient ; D24 garde la décision serveur finale.

## Baseline / correction vérifiée
- Base de comparaison : `main@6adf3fbeecb0f6645f9c7a9e3934177ef9eca6c7`.
- Ancien HEAD D14 `74f50fea` : [14/14 workflows PASS](https://github.com/hraaaaf/IAMINA-MVP/pull/1245/checks) pour les fonctions synthétiques, mais [E2E #41686069107](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41686069107) révélait **441 tentatives de `fonts.gstatic.com`**, toutes bloquées par Playwright. L'écran arabe présentait des carrés à la place de certains textes, notamment CTA photo et snackbar.
- Premier candidat local-icons `ef2d9dd2` : la réduction des emoji a diminué les tentatives à **197**, mais les tests stricts ont échoué : correctif insuffisant. Les URL ciblées appartiennent aux polices fallback Noto Sans Arabic et Noto Sans Symbols.
- Fix moteur `bfbe4095` : configuration Flutter documentée `fontFallbackBaseUrl` dans `frontend/web/flutter_bootstrap.js` vers `iamina-font-fallback/` first-party ; deux fichiers statiques reprennent les blobs TTF locaux Noto déjà livrés sous les URLs de glyphes attendues par Flutter. Les pictogrammes des catégories et repas Web utilisent des icônes/dessins locaux ; version native préservée. La politique D18/CSP n'a pas été modifiée. **Le changement du bootstrap commun doit néanmoins être revu avant fusion**.
- [E2E Django/Chrome #41695352092](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41695352092) sur `bfbe4095` : deux jobs FR+AR **PASS**, six parcours 390/768/1280 **PASS**, **0 tentative de fallback externe** et **0 appel fournisseur IA**, trois authentifications synthétiques par scénario. Artefacts : FR `13260702536`, AR `13260247941`.
- L'analyse photo reste une `Future` locale synthétique, jamais une vraie image patient.

## BEFORE / AFTER — six comparatifs même viewport
Référence UI : mêmes chips, mêmes libellés, même largeur de panneau, remplacement des glyphes emoji distants par MaterialIcons embarqués, correction de lisibilité AR, conservation de la navigation RTL.

Les scores ci-dessous mesurent **la stabilité des pixels** (seuil de différence 16 par canal) et non une note de qualité UX :
| Langue | 390×844 | 768×1024 | 1280×900 |
| --- | ---: | ---: | ---: |
| FR | 9,944/10 (0,565 % modifiés) | 9,947/10 (0,528 %) | 9,959/10 (0,411 %) |
| AR | 9,460/10 (5,397 % modifiés) | 9,750/10 (2,495 %) | 9,772/10 (2,285 %) |

Le delta AR mobile sous 9,5 est **une amélioration visuelle intentionnelle et visible** : textes auparavant rendus en carrés de glyphes manquants → arabe lisible. Ne pas déguiser ce changement en stabilité 10/10. Les captures de référence proviennent des artefacts du E2E antérieur et du fix moteur.

## Protections actives et cas testés
- `AddLogSheet` utilise `ConsentService.hasConsent` et refuse les anciennes dates sans preuve consentement validée.
- `MealCapturePanel` invalide immédiatement les propositions et les `Future` en cours au retrait, protège la réactivation, n'ajoute jamais de repas sans confirmation, efface en mémoire les octets après l'essai.
- `MealCapturePanel._pickAndRecognize` exige `ApiClient` injecté par le coffre propriétaire, `canSyncClinicalData`, puis une consultation fraîche de l'autorisation média `meal_vision/image` **avant galerie** et **après lecture**.
- `ApiClient.analyzeMealImage` contrôle à nouveau le grant avant toute tentative d'envoi : pas de droit caché à travers A/B/A, le transport clinique local-only reste fail-closed.
- `backend/diabetes/api/v1/profile.py` possède déjà les endpoints owner-scoped GET/PUT/DELETE `/profile/ai-media-consents/{purpose}/{modality}`. Contrat de sécurité du serveur D24 indépendant.
- `frontend/web/iamina_service_worker.js` ajoute les deux ressources de fallback à la liste de préchargement PWA et au cache first static.
- Le banc Chrome D14 rejette désormais toute tentative extérieure à l'origine de l'application AFTER. Sur le BEFORE historique uniquement, les demandes font sont satisfaites localement dans Playwright pour empêcher tout accès réel à Google lors du test.

## Dernière exécution HEAD et limites de certification
**HEAD candidat : `96e56dd853fe3e8b14c73461f1f1aec0d89cf81e` au dernier contrôle de rédaction**, PR [Draft #1245](https://github.com/hraaaaf/IAMINA-MVP/pull/1245). Résultats déjà vus sur CE HEAD :
- [E2E réel A/B/A #41696244504](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41696244504) : FR/AR **2 jobs SUCCESS**.
- [PWA offline #41696244449](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41696244449), [PWA update/recovery #41696244337](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41696244337), [PWA persistance #41696244555](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41696244555) : **SUCCESS**.
- [CI Flutter principale #41696244536](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41696244536) et [30 scénarios/six paires Chrome #41696244588](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41696244588) : **IN_PROGRESS au dernier contrôle** ; lire résultats exacts et corriger avant certification.
- Aucun Preview, production, base patient réelle, appel IA fournisseur ou merge déclenché.

## Gates et prochaines actions
1. Sur le SHA exact, vérifier Flutter analyze/tests/build et Chrome 30 scénarios + 6 captures BEFORE/AFTER ; si erreur, diagnostiquer et corriger sans masquer une tentative réseau.
2. Vérifier dans un navigateur Web autorisé la politique réseau/RTL et la compatibilité hors Chromium si nécessaire ; revue privacy/clinique et attestation des conditions de consentement.
3. D24 exige une revue qualifiée des politiques urgences/incident/rétention expirées le **02/11/2026** ; ne modifier aucune date de revue sans preuve et décision compétente.
4. Si certifié, mettre à jour le closeout/roadmap et lier les artefacts, puis validation explicite avant merge/Preview Vercel/activation patient. **D18 explicitement exclue** : aucune modification ni intervention sur sa branche.

**Conclusion prouvée :** le Web D14 a une preuve forte de suppression de l'egress de polices et d'isolation de comptes sur un banc synthétique ; release patient **NO-GO**.

## 03/11/2026 — Closeout du correctif CanvasKit dans le préflight D14 Web (HEAD a766d0c9)

**Exact HEAD de preuve :** `a766d0c9f9557c942a0785976142b10145abbdfe`, PR Draft [#1245](https://github.com/hraaaaf/IAMINA-MVP/pull/1245). Il succède au HEAD historique `96e56dd8` décrit plus haut. **18/18 workflows GitHub Actions COMPLETED/SUCCESS** (vérification réelle sur ce SHA). Aucun merge ni Vercel.

- [D14 Chrome photo #41713564554](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41713564554) PASS. Le workflow isolé avait auparavant échoué en tentant d'importer CanvasKit JS depuis `www.gstatic.com` après un build omettant `--no-web-resources-cdn`. Sur le HEAD courant, `.github/workflows/d14-web-photo-consent-cert.yml` active ce flag officiel Flutter 3.41 et exige les assets `canvaskit/canvaskit.js` et `canvaskit/canvaskit.wasm` livrés par le même hôte. **Le blocage Playwright off-origin n'a pas été assoupli** et ni le bootstrap de production ni D18 n'ont été modifiés dans ce correctif.
- [D14 réel AuthService/Django/PostgreSQL16 A→B→A #41713564623](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41713564623) PASS. [CI générale #41713564285](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41713564285) PASS. PWA offline #41713564310, persistance #41713564322 et update/recovery #41713564279 PASS.
- **Audit indépendant de l'artefact Chrome #13269791312 :** 43 fichiers, `browser-report.json` HEAD/base exacts ; 30/30 scénarios FR/AR aboutis et six paires BEFORE/AFTER, `errors=[]`, **0 off-origin attempt**, **0 provider request**. Les six PNG BEFORE sont SHA256-identiques aux références certifiées du `main@6adf3fbe` (artifact original #13247088428). Tous les scores recalculés en indépendant à partir des pixels (seuil 16 par canal) concordent avec le rapport :

| Surface | FR (/10) | AR (/10) |
| --- | ---: | ---: |
| Mobile 390×844 | 9,947 | 9,915 |
| Tablette 768×1024 | 9,955 | 9,939 |
| Desktop 1280×900 | 9,952 | 9,941 |

**Évidence visuelle :** captures mobile FR/AR BEFORE et AFTER examinées côte à côte ; panneaux, libellés, contrôles, direction RTL et icônes présents. Ces chiffres sont des scores de **stabilité pixel**, pas des scores de qualité clinique ou UX.

**Durabilité des preuves :** artefact original #13247088428 expire le **10/11/2026** ; copie ZIP d'origine (SHA256 `93b0eb74f6f8d5d857b8d10b240a3ea557b0a4bb5c9519b89c22661091b414b1`) et copie HEAD actuelle (SHA256 `1a96fa27805a867428b3ad032b8671968f1c669ea247ccf9f7d5db269f0618d8`) archivées durablement dans [Notion chantier B](https://app.notion.com/p/40777c66336281729c03c9bb294e71b7). **Limite restante :** le workflow GitHub Chrome continue de récupérer l'artefact original et ne sera plus rejouable tel quel après expiration ; stocker une fixture immuable exploitable directement par CI reste nécessaire avant certification durable.

**Conclusion bornée :** le correctif CI CanvasKit et le préflight D14 Web synthétique **PASS sur a766d0c9**. Cela ne démontre PAS de transfert réel à un fournisseur IA ni de sûreté clinique du produit complet. Consentement média effectif côté serveur, revues qualifiées privacy/clinique, dépendances de coffre Web et arbitrage humain de release/merge demeurent **NO-GO patient**. D18 non modifiée.

## D14 — 03/11/2026 : baseline CI permanente et revue ciblée (suite du closeout)

**Fixture versionnée :** les six captures PNG BEFORE exactes, leurs SHA256 (manifeste verrouillé par l'empreinte `8abd98446e69f95d44f08d7d41c44b58b62845dc43abbabb305a075fef151899`) et le rapport d'origine `main@6adf3fbe` ont été importés dans `tools/fixtures/d14/main-6adf3fbe/` au commit [19f0a268](https://github.com/hraaaaf/IAMINA-MVP/commit/19f0a268d59b5181c72cf34b5f57aaa9950df707) par un processus GitHub limité à la seule PR #1245 et vérifiant les six SHA256 avant écriture. Le workflow temporaire `d14-freeze-baseline-once.yml` est **supprimé dans le même arbre final** qui remplace son utilisation par la fixture ; aucun permissionnement `contents: write` ne subsiste dans le workflow Chrome.

**Nouveau workflow Chrome D14 :** plus aucune dépendance au téléchargement de l'artefact GitHub #13247088428 expirant le 10/11. Les six fichiers sont lus depuis Git ; le SHA256 de `baseline-sha256.txt`, les six PNG, et les SHA `main`/`head` du rapport historique sont vérifiés avant les 30 scénarios + six paires BEFORE/AFTER. Les garde-fous zéro off-origin et seuil de stabilité >=9,5/10 sont inchangés. **PASS de la fixture CI définitive à vérifier sur le nouveau SHA**, aucune revendication anticipée.

**Audit technique de sécurité/privacy/clinique** : [constats et checklist indépendants demandés sur PR #1245](https://github.com/hraaaaf/IAMINA-MVP/pull/1245#issuecomment-6615712886). Observé côté client : consentement versionné, média granulaire propriétaire relu, auth epoch/coffre/intercepteur et confirmation explicite des repas, invalidation des réponses tardives. Non attesté : refus serveur race/révocation en production, stockage/logs/base64, évaluations d'erreurs nutritionnelles, photo réelle, avis professionnel tiers. Aucun avis clinique/juridique indépendant n'est acquis ; D14 reste DRAFT/NO-GO patient.

**Next exact :** lire 18 CI du HEAD final, analyser les nouveaux 30 scénarios et 6 PNG / scores ; corriger tout échec et maintenir la séparation D18/D24. Aucune Preview Vercel, aucun merge.

## 03/11/2026 — D14 Web préflight : certification finale du code 3935c163 et gate patient

**Décision D14 — Goal :** bloquer tout usage de la photo de repas sans consentement IA courant et permission média explicite `meal_vision/image` du propriétaire, et rejeter toute proposition ou confirmation tardive après révocation, sans fuite ni réutilisation inter-patient. **Succès technique observable :** six captures FR/AR à la même taille que `main@6adf3fbe`, seuil de stabilité pixel ≥ 9,5/10 ; 36 scénarios synthétiques qui passent ; zéro appel fournisseur ni requête off-origin ; authentification Web réelle avec Django/PG16 A→B→A ; 18/18 GitHub Actions vertes.

**Code HEAD certifié :** `3935c163c09e9a5d9850f2d345e112ef0bf75265`, branche `test/iamina-b-d14-meal-photo-20261103`, PR Draft [#1245](https://github.com/hraaaaf/IAMINA-MVP/pull/1245) **ouverte, non fusionnée**. **GitHub Actions : 18/18 COMPLETED/SUCCESS** sur CE SHA. [Chrome D14 #41724221542](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41724221542) SUCCESS, [CI générale #41724221854](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41724221854) SUCCESS, [E2E AuthService/Django/PostgreSQL16 #41724221607](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41724221607) SUCCESS. Aucun workflow en attente/échoué sur ce commit au contrôle.

**Artifact et inspection indépendante :** [Chrome artifact #13274442142](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41724221542/artifacts/13274442142) téléchargé et `browser-report.json` ouvert, 49 fichiers, base `6adf3fbeecb0f6645f9c7a9e3934177ef9eca6c7`, head `3935c163c09e9a5d9850f2d345e112ef0bf75265`, `errors=[]`. 36/36 scénarios `step=done`, 6/6 paires BEFORE/AFTER, **0 requête off-origin** et **0 appel fournisseur** pour chacun des 36. Les six `revoke-media-pending` montrent consentement global `allowed=true`, permission `mediaGrantActive=false`, `recognitionCalls=1`, `proposalVisible=false`, `selectedIds=[]` dans les six contextes FR/AR × mobile/tablette/desktop. Zéro donnée patient réelle ; analyse strictement synthétique.

| Viewport | FR stabilité pixel | AR stabilité pixel |
| --- | ---: | ---: |
| Mobile 390×844 | 9,947/10 | 9,915/10 |
| Tablette 768×1024 | 9,955/10 | 9,939/10 |
| Desktop 1280×900 | 9,952/10 | 9,941/10 |

Les scores mesurent la **stabilité des pixels**, et non la qualité visuelle ou clinique. ZIP de preuve Chrome SHA-256 : `c9a6b7b00f76299891b634efa0aa73cf831aebf40e0fc67cd77450b54617234f`, également archivé sur [Notion chantier B](https://app.notion.com/p/40777c66336281729c03c9bb294e71b7). Les six captures BEFORE historiques et leurs SHA256 sont versionnés dans `tools/fixtures/d14/main-6adf3fbe/` ; le workflow n'utilise plus l'artefact GitHub original éphémère ; le workflow one-shot à permission d'écriture a été supprimé.

**Correctif de révocation :** [f3503804](https://github.com/hraaaaf/IAMINA-MVP/commit/f35038044ac39a1dceace4f5160c54259d33c8a1) ajoute deux validations de grant média (post-réponse, pré-confirmation), et deux tests widgets ; [3935c163](https://github.com/hraaaaf/IAMINA-MVP/commit/3935c163c09e9a5d9850f2d345e112ef0bf75265) porte le nouvel essai `revoke-media-pending` au navigateur Chrome (6 combinaisons). Les contrôles serveur dans `backend/core/ai_egress.py` exigent un consentement global versionné et un grant média valide avant toute nouvelle émission ; cette preuve ne signifie **pas** que le fournisseur annule une requête déjà envoyée.

**Gate de clôture :** **Préflight technique synthétique D14 PASS sur 3935c163** ; **activation patient NO-GO**, PR toujours Draft. Restent **externes et non certifiés** : validation indépendante sécurité/confidentialité/juridique, évaluation clinique/nutrition réelle par personnel habilité (fiabilité, erreurs de portions, corrections humaines), preuve d'architecture serveur/protection média sur opération réelle et revue coffre Web D18 par son chantier, puis décision humaine avant toute preview Vercel, merge ou activation. **Aucune preview/deploy Vercel, aucun merge, aucune modification D18/D24.**

**Next exact :** publication documentaire de cette preuve sur PR/Notion, vérifier toute nouvelle CI lancée par la mise à jour du fichier canonique, puis demander les seules approbations externes réellement nécessaires avant d'envisager le GO patient. La section historique plus haut sur l'artefact expirant est **supplantée** par le correctif pérenne effectivement certifié.
