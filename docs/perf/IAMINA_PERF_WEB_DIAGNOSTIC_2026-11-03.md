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
