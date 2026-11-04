# IAMINA PERF-WEB — baseline premier affichage public — 2026-11-03

## Décision
- **Goal :** mesurer le premier affichage du frontend Flutter Web depuis GitHub Actions, sans donnée patient, secret ni déploiement Vercel.
- **Succès observable :** locale Chromium valide ; ≥2/3 vrais rendus Flutter par cible et mode froid/chaud ; preuves publiées dans les artefacts GitHub.
- **Preuve :** [GitHub Actions #41730039062](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41730039062), completed/success, SHA 7e8069145fb698d4716846604d2057b9671ec56b.

## Cause du faux négatif initial
[Run #41728880127](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41728880127) : Chromium GitHub sans locale forcée avait navigator.language = en-US@posix. Intl.Locale rejette cette chaîne avec RangeError Incorrect locale information provided. Avec en-US, fr-FR, ar-MA ou fr, les deux frontends rendent Flutter (8/8 cas de la matrice). Il s'agissait d'un faux négatif du benchmark, pas d'une preuve de défaillance utilisateur.

**Correction du banc de test uniquement :** Playwright utilise une locale Chromium explicite en-US ; la CI devient rouge si moins de 2/3 cas Flutter sont réellement rendus pour chaque frontend et phase. La Preview Vercel protégée SSO reste exclue de cette comparaison anonyme.

## Résultats du dernier run certifié
[Run #41730039062](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41730039062) ; [artefact JSON + Markdown #13275249386](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41730039062/artifacts/13275249386). Chromium GitHub 390×844, 3 navigations froides et 3 chaudes par frontend. 12/12 rendus Flutter et 0 erreur JavaScript relevée.

| Mesure médiane | Frontend actuel | Ancienne version |
| --- | ---: | ---: |
| Premier affichage à froid | 1291 ms | 1261 ms |
| Premier affichage à chaud | 673 ms | 643 ms |
| Hôte Flutter à froid | 960 ms | 912 ms |
| Hôte Flutter à chaud | 423 ms | 419 ms |
| TTFB à froid | 72 ms | 72 ms |
| TTFB à chaud | 22 ms | 22 ms |

Les médianes diffèrent de +30 ms pour le premier affichage sur le frontend actuel. Trois essais seulement par condition et versions différentes : **pas de preuve de régression de performance**. Premier frame anonyme ≠ disponibilité du parcours clinique authentifié.

Backend Django, healthcheck séparé : 9177/346/533 ms, DB OK et cache indisponible aux trois appels. Aucun lien causal entre cet endpoint et le premier affichage Flutter n'a été démontré.

## État et limites
- **Validé :** correction de la locale du harness, benchmark anonyme, 12/12 rendus Flutter et artefacts publiés.
- **Non validé :** lenteur ressentie sur iPhone Safari, IndexedDB déjà peuplé, coffre patient local, authentification, verrouillage et chronométrage réel du parcours connecté.
- **Preview :** écran de login Vercel SSO : aucune vraie comparaison Flutter possible dans ce runner non autorisé.
- **Sécurité :** zéro dossier médical, zéro identifiant patient, zéro token ; aucun changement runtime ; aucune migration DB ; aucun déploiement Vercel.
- **Chantier :** sous-lot premier affichage public techniquement validé ; investigation de la lenteur utilisateur non clôturée. Pourcentage chantier global inconnu.

## Next exact
Instrumenter les étapes de pré-runApp sur un environnement de test entièrement synthétique avec stockage local initialement vierge puis peuplé : initialisation auth, inspection base locale protégée, verrouillage, réconciliation du coffre. Mesurer le temps par phase sur Chromium et WebKit. Ne modifier les chemins runtime sensibles qu'après preuve reproductible sans dégrader l'isolation du patient. Aucun merge ou déploiement Vercel dans ce lot.


## Sous-lot suivant — coffres synthétiques IndexedDB (état provisoire, RED)

- **Goal :** chronométrer une partie du démarrage local avec Drift/IndexedDB, coffre synthétique vide puis 300 enregistrements synthétiques, Chromium et WebKit Linux.
- **Succès observable :** tests navigateurs, persistance et isolation des coffres, artefact chiffré JSON/Markdown, aucune donnée patient. **Non atteint à ce stade.**
- **Run RED :** [#41733184033](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41733184033), HEAD 2129815efb0603b6c3ab4868cb04467658989349. Compilation Flutter et installation des navigateurs OK. Expiration Playwright 90000 ms pendant l'attente du premier titre d'état, aucune mesure ni artefact. Cause technique non connue.
- **Action de diagnostic :** commit a7576528551c22c519f6ef3ff560b9df51f98332, dans le banc uniquement : titres des sous-phases Dart, timeout borné à 20 secondes, fichier perf_web_synthetic_vault_debug.json retraçant uniquement les éléments techniques autorisés (étape, langue navigateur, chargements de ressources, premiers frames, compteur des erreurs). Aucune donnée clinique ni contenu d'exception libre.
- **Run de suivi :** [#41734274519](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41734274519), sur HEAD a7576528551c22c519f6ef3ff560b9df51f98332, IN_PROGRESS au dernier contrôle ; résultat non certifié.
- **Limites :** ne mesure ni AuthService réel ni AppLockService ni un patient connecté ; WebKit Linux n'est pas Safari physique sur iPhone.
- **Next exact :** lire le diagnostic du nouveau run, identifier la phase exacte du blocage, corriger et retester uniquement PERF-WEB, puis documenter la comparaison vide/rempli si la CI devient GREEN. Aucun merge ni déploiement Vercel.


### Correction du faux signal du second run (en vérification)

- [Run #41734274519](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41734274519) : RED. Le premier rendu Flutter a bien été observé dans la phase seed, sans rejet JavaScript ; cependant, le titre HTML est vide alors que le test attend un suffixe PASS. Le titre n'est pas un oracle fiable pour un écran Flutter utilisant MaterialApp. L'état effectif des données Drift demeure non démontré par ce run.
- **Changement de stratégie après deux échecs :** le nouvel oracle est un reçu structuré et uniquement synthétique conservé dans localStorage, avec phase et état de réussite ou classe d'échec. Le test doit également observer l'hôte Flutter et le premier frame ; le titre document n'est plus une condition de réussite. L'étape exacte d'exécution est aussi stockée dans une clé technique indépendante.
- **Nouveau commit test-only :** 4d00b67893e66026e43618714bd4a2c2840c8b58 ; [run #41734802258](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41734802258), IN_PROGRESS au premier contrôle. Aucune mesure acquise avant sa certification.
- **Next :** vérifier les reçus locaux et l'intégrité du coffre vide/300 lignes via Chromium et WebKit. Si réussite, consigner médianes et limites ; sinon, corriger la cause attestée par le reçu ou les étapes.

### Contrôle du 03/11/2026 à 23:02 UTC — en attente

- Run [#41734802258](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41734802258), HEAD de code `4d00b67893e66026e43618714bd4a2c2840c8b58` : **IN_PROGRESS**.
- Build/analyse Flutter **GREEN** ; installation des navigateurs **IN_PROGRESS** ; mesure des coffres et upload **PENDING**. Aucun JSON de mesure ni médiane ne peut être certifié.
- **Next exact :** vérifier fin du run, puis contrôler reçu synthétique, frame Flutter, intégrité des coffres et les 24 échantillons attendus. En cas de RED, analyser l'artefact debug avant de modifier le banc. Aucun merge ni déploiement.


### Run RED WebKit — cause à isoler

- [Run #41734802258](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41734802258) : compiler/analyser Flutter et installer les navigateurs = GREEN ; **12/12 échantillons Chromium validés**, 6 coffre vide et 6 coffre rempli de 300 logs synthétiques ; premier échantillon WebKit coffre vide réussi ; premier coffre rempli WebKit = FAIL avec classe d'exception minifiée, sans preuve du mécanisme exact.
- Le test n'échoue plus sur l'ancien oracle du titre : l'échec est un **reçu FAIL émis par la fixture Dart dans la phase populated**. Il ne faut pas conclure que WebKit ne sait pas stocker les données en l'absence du stage.
- [Run #41737035938](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41737035938), commit 538854576677fc8236926d54a969e3a3c3126b06 : nouvelle instrumentation de diagnostic, **IN_PROGRESS au contrôle**. Sur FAIL, conserver l'étape réelle (avant écrasement par 'failure'), une catégorie d'assertion allowlistée et les échantillons partiels en artefact, sans données patient ou message libre.
- **Next exact :** lire le reçu FAIL et identifier si WebKit échoue à l'ouverture, au guard, à la persistance ou à la réconciliation ; ne corriger qu'après attribution technique et tests.


### Verdict du comptage WebKit et test isolation locale (03/11/2026)

- [Run #41738985327](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41738985327) **RED**. [Artefact #13280597024](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41738985327/artifacts/13280597024) : 12/12 mesures Chromium réussies. WebKit empty passe une fois, mais la réouverture WebKit populated retourne 0 logs et 0 profils au lieu de 300 logs et 1 profil. Le guard false est cohérent avec le stockage vide. Non-persistance prouvée en environnement de CI ; backend Drift réellement choisi non déterminé.
- Docs primaires : https://drift.simonbinder.eu/platforms/web/ et https://www.sqlite.org/wasm/doc/trunk/persistence.md. OPFS peut dépendre de COOP/COEP et SharedArrayBuffer ; cette explication pour WebKit reste hypothétique.
- Commit test-only 586e5d0f5a6214c540621ef7e3cdd44a0feef243 : serveur loopback CI avec COOP same-origin, COEP require-corp et MIME wasm ; capture des capacités isolées, API OPFS, SAB, SharedWorker et IndexedDB. Aucun changement du runtime, de la CSP ni du déploiement Vercel.
- [Run #41740199293](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41740199293) QUEUED au contrôle de lancement. Si GREEN, preuves de persistance des 300 logs via 24 mesures ; sinon, explorer le backend sélectionné dans la fixture, sans effacer ni masquer le guard.
- Next exact : vérifier le nouveau run et son JSON. L'environnement Linux WebKit Playwright ne certifie pas Safari iPhone.


### Contrôle final #41740199293 — RED (03/11/2026 23:43 UTC)

- Code exact `586e5d0f5a6214c540621ef7e3cdd44a0feef243`, documentation précédente `88d2f4328980b9d0025d99b0da87a39268fe1318`. [Run #41740199293](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41740199293) completed/failure ; build Flutter, navigateurs et upload GREEN ; étape mesure RED. [Artefact #13281009562](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41740199293/artifacts/13281009562) contient `perf_web_synthetic_vault_debug.json` et `perf_web_synthetic_vault_partial.json`, aucun rapport final certifié.
- Échantillons partiels : 12/12 Chromium PASS (6 vides, 6 remplis, 300 logs synthétiques préservés après réouverture). WebKit Linux : premier vide PASS ; premier rempli FAIL à `filled_raw_counts` : 0 log / 0 profil observés, attendus 300 / 1 ; guard=false correct sur stockage vide. Total 13/24 mesures, aucune médiane finale certifiable.
- Capabilities sur WebKit FAIL : `crossOriginIsolated=true`, `SharedArrayBuffer=true`, `OPFS=false`, `SharedWorker=true`, `IndexedDB=true`. Chromium : les cinq capacités true, OPFS compris. COOP/COEP isolent correctement WebKit mais **ne rendent pas OPFS disponible**. Backend Drift WASM réellement sélectionné (inMemory, IndexedDB ou OPFS) **non identifié** : ne pas attribuer l'échec à OPFS sans trace du backend effectif.
- Next exact : instrumenter dans le seul harness le choix effectif de backend Drift/SQLite WASM et le résultat des ouvertures/écritures/réouvertures, avec catégories allowlistées sans données patient ; retester WebKit, garder guard fail-closed. Ne pas changer runtime, Vercel, ni merger. WebKit Linux Playwright ≠ Safari iPhone.


### Test du mode de stockage effectivement choisi — run #41741895614

- **But :** savoir si la non-persistance WebKit observée sur le runner provient d'un repli `inMemory`, d'un mode `sharedIndexedDb` défaillant, ou d'une autre sélection Drift, sans désactiver la garde.
- **Rappel de preuve :** [#41740199293](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41740199293) RED ; `crossOriginIsolated=true`, `SharedArrayBuffer=true`, `OPFS=false`, `SharedWorker=true`, `IndexedDB=true` ; 0/300 logs et 0 profil après réouverture WebKit ; 12/12 Chromium OK. COOP/COEP en local n'a pas corrigé le problème.
- **Code test-only** commit `4466f536b7c6cd2a641c42b5c9ce3dd0c939d5f8` : le test ouvre les mêmes noms de bases avec le même `driftDatabase`, mêmes ressources WASM/worker et même schéma généré, en ajoutant l'observateur officiel `DriftWebOptions.onResult`. Il consigne les seuls identifiants d'énumération `chosenImplementation` / `missingFeatures`, y compris sur FAIL. Le contrôleur est le vrai `PatientVaultSessionController`, alimenté par une fausse identité et une factory injectée sans différence de stockage. Code runtime d'IAMINA inchangé.
- **CI :** [#41741895614](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41741895614), IN_PROGRESS au premier contrôle ; aucune sélection effective du backend ne peut être déclarée avant la lecture de l'artefact.
- **Limites :** Linux Playwright WebKit n'est pas Safari iPhone ; 300 lignes et IDs synthétiques, aucun dossier médical/credential réel. Ne pas imputer le problème à un appareil réel sans répétition.
- **Next exact :** lire la CI, vérifier si l'observateur s'exécute et enregistrer le mode exact. Si `inMemory`, prouver la limitation et maintenir l'échec du test de persistance ; si `sharedIndexedDb`, analyser les transactions/fermetures WebKit. Corriger et retester seulement après attribution, puis mettre à jour Notion.


## Pivot PERF-WEB — instrumentation du vrai démarrage (reprise autorisée)

- **Décision / Goal** : remplacer le banc synthétique WebKit à répétition par un diagnostic direct du chemin critique de démarrage Flutter Web et du premier écran utilisateur.
- **Succès observable** : jalons entre navigation, auth, sondage de coffre legacy + coffre courant, app lock, reconcile, runApp et premier écran hôte. Le premier frame Flutter ne suffit pas à certifier un écran utilisable.
- **BEFORE** : pas d'accès aux durées des initialisations dans le vrai build ; les tests précédents mesuraient des fixtures ou le premier frame public. Le précédent run public #41730039062 12/12 premiers frames n'est pas une preuve du retour patient Safari.
- **Mockup** : petit bouton « ⏱ Chrono » en bas à droite, volet blanc 342px max avec « Écran prêt », « Copier », « Actualiser », « Fermer » et horodatages numériques sans aucune donnée personnelle. Identique visuellement sur 390, 430, 768, 1280px ; caché sans paramètre URL.
- **Isolation** : drapeau de compilation IAMINA_STARTUP_TRACE=true ET paramètre startup_perf=1 pour les jalons Dart. Le script du volet n'est même pas chargé sans startup_perf=1. Aucune donnée patient, identifiant, token, URL complète, requête réseau ou stockage durable n'est exporté. Le jalon « écran prêt » reste manuel et surestime le temps de disponibilité.
- **Implémentation envisagée / en validation** : nouveaux fichiers du tracer et volet ; modifications purement additives dans main.dart et l'hôte patient. Ne jamais supprimer ni raccourcir les contrôles fail-closed pour gagner du temps artificiellement.
- **AFTER / contrôle de conformité** : build release de l'application réelle avec Chromium, BEFORE sans paramètre et AFTER volet ouvert pour 390×844, 430×932, 768×1024 et 1280×900, captures, premiers frames et jalons; lire l'artefact et comparer visuellement. Un seul run indépendant de WebKit Linux, qui n'a aucun droit de certifier Safari iPhone.
- **Human gate** : tests Safari sur iPhone réel et éventuelle preview Vercel nécessitent une autorisation explicite de déploiement. Aucune preview ni merge dans ce lot.
- **État** : travaux préparés ; validation et score visuel non encore démontrés.
