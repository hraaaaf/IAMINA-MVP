# IAMINA — Handover canonique V1-03 / Privacy CurlInterceptor #930 / PR #931
**Date :** 2026-10-11. Autorité de statut produit : `docs/ROADMAP.md`. Ce lot est **distinct de #928** ; code parent conservé et jamais mergé.

## Goal — succès — preuve
- **Goal :** éliminer de l'API client Flutter le journal de requêtes `curl` qui peut contenir en-tête Bearer et payload patient, sans modifier les requêtes, les décisions clinique/IA, les cookies, le routage, ni les politiques auth.
- **Succès technique observable :** `CurlInterceptor()` absent de la chaîne partagée et garde de test statique empêchant son retour ; Auth/Retry/Timeout conservés ; test Flutter/PWA, SQLite/PG, Chrome/iOS et 15 workflows exact-head verts.
- **Preuve établie sur HEAD `590d627f045bff406ad8a054ed13cb48c119bbd3` :** [CI #38105654095](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38105654095) **15/15 completed/success**, les six jobs internes de la CI principale verts. Ancêtre `a99e57b0ed4194646a291d003811d942315be593` contient les deux changements ; `590d627f` est un commit vide d'activation de workflows avec arbre identique. La présente édition des docs créera un **nouveau SHA** qui doit être certifié à nouveau.
- **Cause source inspectée :** dans `frontend/lib/services/api_client.dart`, `AuthInterceptor` ajoute `Authorization: Bearer`, et `CurlInterceptor` de Chopper sérialise en log les en-têtes et, selon le type de requête, le corps ; cette construction pouvait exposer les données à un collecteur de logs **s'il était actif**. Le code source de Chopper et le verrouillage `pubspec.lock` 8.5.1 motivent la suppression. **Aucune fuite réelle, journal collecté ou incident patient démontré.**

## Diff et contrôles
- Repo `hraaaaf/IAMINA-MVP`.
- Parent [PR #928](https://github.com/hraaaaf/IAMINA-MVP/pull/928) DRAFT, SHA `3be13de431460f72c25faac3229e58f6c661f3f4`, base #926 ; son HEAD 15/15 SUCCESS, aucune modification effectuée sur cette branche.
- Enfant [PR #931](https://github.com/hraaaaf/IAMINA-MVP/pull/931) DRAFT, branche `security/v1-03-strip-client-curl-logger-20261011`. Avant docs, compare au parent : **ahead 2 / behind 0 / 2 fichiers**, mergeable, non mergée.
- Runtime : retirer une ligne `CurlInterceptor(),` dans `frontend/lib/services/api_client.dart`. Test `frontend/test/services/no_sensitive_chopper_logging_contract_test.dart` (25 lignes) vérifie les intercepteurs autorisés et l'absence de `CurlInterceptor`/`HttpLoggingInterceptor`. Les clients réseau bruts (SSE, multipart) et les logs d'erreurs de types/stack n'ont pas été modifiés ; l'absence totale d'autres sinks tiers n'est **pas** prouvée.
- Scope parent #928 : garde CSRF 28 opérations `SessionAuth` et tests 15/15 verts conservés ; pas de relâchement de sécurité pour compenser.

## Revue adversariale / gate humain
**EXECUTION_SCORE provisoire : 8.0/10 ; ADVERSARIAL_SCORE provisoire : 7.8/10 ; RETAINED provisoire : 7.8/10**, sans indépendance ni valeur de certification release. La correction supprime la voie d'enregistrement identifiée ; le contrat global de logs tiers, du proxy, de l'OS/app et des outils de monitoring n'a pas de certification indépendante.

**Human gate réel :** revue de sécurité/privacy par un autre intervenant qualifié ; déclaration explicite sur logs, jetons, captures d'erreur, observabilité, consentement et données identifiables ; arbitrages complémentaires de #928 (login-CSRF, cookie+Bearer, urgence sans CSRF, ingress), #923, #924, #929 et processor/CNDP/pilotes. **NO-GO merge/release/Vercel/usage patient.**

## Next exact / séquence de clôture
1. Obtenir **15/15 CI exact-head** du dernier commit de docs sur base temporaire `main` ; si rouge, diagnostiquer/corriger/tester.
2. Restaurer la base de #931 vers `security/v1-03-cross-route-cookie-csrf-20261010` (#928), vérifier HEAD/diff/ahead/behind/DRAFT/mergeable sans nouveau commit.
3. Mettre à jour les commentaires GitHub issue #930/PR #931 et Notion **sans changer le HEAD** ; garder DRAFT.
4. Avis indépendant sécurité/privacy + arbitrages humains, puis seulement certificateur indépendant et gate de merge humain. Ne pas déclencher merge ou Vercel automatiquement.

## Statut
**Correction testée sur l'ancien HEAD, CI finale docs à obtenir / NO-GO release / NON MERGÉ / NON DÉPLOYÉ**. Roadmap V1 : 29/29 décisions approuvées, 0/29 entièrement livrées. Historique P5 6/12 lots clos, métrique distincte.
