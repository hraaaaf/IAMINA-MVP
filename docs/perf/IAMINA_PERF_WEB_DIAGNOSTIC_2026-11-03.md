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
