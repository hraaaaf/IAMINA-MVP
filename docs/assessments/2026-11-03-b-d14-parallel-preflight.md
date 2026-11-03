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
