# IAMINA — Chantier B / D7 Web — FUE : preuves et arrêt de sécurité

**Date :** 29 octobre 2026  
**Autorité :** [Chantier B dans Notion](https://app.notion.com/p/40777c66336281729c03c9bb294e71b7) ; reprise Git [`docs/CHANTIER_URGENCE_B.md`](../CHANTIER_URGENCE_B.md).  
**Périmètre :** Flutter **Web/PWA uniquement**, D7 (type déclaré de diabète et traitements déclarés modifiables). Ne concerne **pas** le chantier A, D19, D22 ou la mise en production patient.

## Décision / Goal / critère de succès / preuve

**Décision D7 :** une personne déclare librement son type de diabète et les traitements *effectivement pris* ; changer le type ne prescrit, n'infère ni n'efface aucun traitement ; les changements sont persistés uniquement pour le bon propriétaire, en local-first et sans fausse confirmation de synchronisation.

**Succès FUE complet attendu :** utiliser le **vrai produit Web** sur une Preview QA autorisée, au SHA effectivement déployé, avec identité A et B distinctes, navigation Onboarding → Profil → choix → sauvegarde → sortie/retour/rechargement/offline → A→B→A ; captures adaptées à 390×844, 768×1024, 1280×900, en FR/AR RTL (EN selon le contrat), vérification de lecture/écriture owner-scoped, aucune fuite de données/egress non consentie, puis revue clinique, sécurité et privacy qualifiée. **État : NOT_RUN pour la session hébergée intégrée**, donc **FUE_NO_GO**.

### Preuves réelles obtenues sur le code de test

| Contrôle | Résultat vérifié | Portée exacte |
| --- | --- | --- |
| [PR #1179](https://github.com/hraaaaf/IAMINA-MVP/pull/1179), merge `6c84447fa849af89e66b8f183bb02d8340924dca` | [Chrome #40854287805](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40854287805), [CI #40854287690](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40854287690) et [E2E pilote #40854287644](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40854287644) **SUCCESS** au source SHA `f2abbddb...`; postmerge [E2E #40855016788](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40855016788) SUCCESS, [CI #40855016852](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40855016852) CANCELLED | Widget D7 Chrome réel ; type2→type1, unknown, gestational, déclaration conservée ; 390×844/768×1024/1280×900, FR/EN/AR RTL. **Pas** de login, coffre Web persistant ni product E2E. |
| [PR #1180](https://github.com/hraaaaf/IAMINA-MVP/pull/1180), merge `8bd92d3276a3f1db898575504d8a1c17068519f2` | [CI prémerge #40855399739](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40855399739), [E2E #40855399717](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40855399717), [CI postmerge #40856299121](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40856299121), [E2E postmerge #40856299440](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40856299440) : **SUCCESS** aux SHA correspondants | Test Flutter `ProfileScreen` réel avec **NativeDatabase.memory** et comptes fictifs 734/812 : sauvegarde owner-scoped, fermeture/réouverture écran, traitement `none_declared` seulement après action explicite. **Pas** d'IndexedDB ni login serveur. |
| [PR #1182](https://github.com/hraaaaf/IAMINA-MVP/pull/1182), merge `563788f58d62dcadef89b12017376de18843c2b7` | [Chrome + vrai IndexedDB #40857425023](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40857425023), [CI prémerge #40857425106](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40857425106), [CI postmerge #40858356581](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40858356581) **SUCCESS** ; SHA de test `c94c0e18...` | **App de banc d'essai CI-only** sur vraie SQLite WASM/IndexedDB : 2 coffres A/B fictifs physiquement isolés, navigation, hard reload, Type2→Type1 sans effacement des traitements ; état patient-declared/pending. **Pas** de vrai `ProfileScreen` authentifié hébergé, ni offline complet. |
| [PR #1184](https://github.com/hraaaaf/IAMINA-MVP/pull/1184), merge `b30eb164099e83756c30bfae89a6fae8f4f04509` | [CI prémerge #40859289298](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40859289298) **SUCCESS**, [postmerge #40859345133](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40859345133) **SUCCESS** | Closeout Markdown seulement. Aucun test produit supplémentaire par cette PR. |

**Conclusion technique bornée :** tests synthétiques et CI pré/postmerge **verts**, fournissant une partie importante des preuves. **Aucune FUE Web complète sur des comptes QA authentifiés n'a été réalisée dans ce lot**, ne pas transformer ces tests en certification patient/clinique.

### Baseline QA hébergée vérifiée en lecture seule

- **Preview séparée** de Production : Vercel `iamina-review` deployment [`dpl_4o5sLYhZywjthETgPbmtAmbo6SNr`](https://vercel.com/achraf-benmoussa-s-projects/iamina-review/4o5sLYhZywjthETgPbmtAmbo6SNr), **READY, target=null**, source **`8a417041e5e2b0e9054c1561d9a2a3e0c12dc43d`** de `integration/w01-d2-preview-only-20261027`. Ce **n'est pas** `main@b30eb164...` testé/mergé aujourd'hui, donc une FUE sur cette Preview ne qualifierait **pas le HEAD Web du Chantier B**.
- **Protection SSO constatée via Vercel `get_project` :** `ssoProtection.enabled=true`, `deploymentType=preview`. **Aucun compte navigateur TinyFish enregistré comme connecté à Vercel** au contrôle des profils. Ne pas désactiver SSO, fabriquer de token, produire de lien partage public ou réécrire la sécurité pour passer ce gate.
- Anciennes [PR #1153](https://github.com/hraaaaf/IAMINA-MVP/pull/1153) / [issue #1161](https://github.com/hraaaaf/IAMINA-MVP/issues/1161) décrivent les 2 comptes synthétiques. **SELECT indépendant** effectué sur Neon **Preview uniquement** : `noisy-truth-00115950 / br-sweet-frog-b9ok6ptp / iamina925_empty` a `auth_user=2` et `core_basepatientprofile=2` ; identifiants A `w01-a@example.invalid` (15) et B `w01-b@example.invalid` (16), champs `first_name`/`last_name` vides. **Aucune authentification, inspection de secrets/mot de passe, INSERT/UPDATE/DELETE ou migration effectuée** ; les liens runtime déployé→QA doivent être revalidés avant login.
- L'ancienne autorisation de FUE hébergée A/B fut **reportée** (issue #1161). La nouvelle demande de l'utilisateur autorise le travail FUE, **pas** un déploiement Vercel, la désactivation SSO, l'accès Production ou une mutation/destruction de comptes sans gate séparé.

### Matrice FUE produit restant à exécuter (NON exécutée, pas de faux PASS)

| ID | Scénario de recette **vrai site Web** | État |
| --- | --- | --- |
| D7-F01 | Login QA A via la Preview reliée au bon backend/branche QA ; ouvrir le Profil (390×844, FR) ; vérifier état initial et libellés patients non prescriptifs | **NOT_RUN — SSO + SHA Preview** |
| D7-F02 | A : modifier type2→type1 ; enregistrer ; vérifier traitements auto-conservés, pas de nouvelle prescription, save local-only/pending non annoncé « serveur confirmé » | **NOT_RUN — SSO + SHA Preview** |
| D7-F03 | A : choisir explicitement none/unsure/unknown puis revenir à un traitement ; vérifier aucun écrasement implicite, rechargement dur et réouverture | **NOT_RUN — SSO + SHA Preview** |
| D7-F04 | B : login distinct, stockage et traitements distincts ; bascule A→B→A avec logout/auth epoch, onglets, session périmée ; 0 fuite, 0 écriture croisée | **NOT_RUN — SSO + SHA Preview** |
| D7-F05 | Réseau offline/reload/persistance du **vrai client** ; vérification mode local, zéro sync/égress clinique non approuvé ; re-synchronisation uniquement après autorisation et ACK vérifiable | **NOT_RUN — SSO + SHA Preview** |
| D7-F06 | Même parcours aux viewports 768×1024 et 1280×900, FR/AR RTL, accessibilité/clavier ; captures comparables et revue visuelle | **NOT_RUN — SSO + SHA Preview** |
| D7-F07 | Revue indépendante clinique, confidentialité, stockage/chiffrement, CNDP/personnes qualifiées, traçabilité des captures anonymisées et suppression contrôlée de QA si ordonnée | **HUMAN GATE — NON VALIDÉ** |
| D7-F08 | Bilan exact SHA prémerge, merge, postmerge, déploiement Preview **autorisé séparément** au SHA testé, publication du verdict avec preuves sans secrets | **NON ATTEINT** |

**Important :** ne pas tester le login QA en Production ; ne pas lancer le workflow historique « Production first-user E2E » non sécurisé ; ne pas changer la route vers Neon ou réutiliser l'ancienne Preview pour certifier `main` actuel. Aucun déploiement Vercel sans accord explicite.

### Blocage réel, prochaine action exacte, séquence restante

- **Blocage n°1 (accès) :** la Preview D7 accessible à la FUE est sous SSO Vercel, aucun navigateur autorisé n'est actuellement prouvé connecté. Un propriétaire doit ouvrir une session SSO Preview via le navigateur/profil autorisé, ou approuver explicitement un autre accès limité équivalent. **Ne pas désactiver SSO ni créer de lien partage sans autorisation.**
- **Blocage n°2 (SHA) :** Preview isolée existante SHA `8a417041...` ≠ Git `main@b30eb164...`. Une Preview Web QA au SHA testé serait à déployer **seulement après GO Vercel distinct** et après confirmation du backend Preview vers la branche Neon synthétique 4/4.
- **Gates hors technique :** données médicales/identité/consentement, clinique, sécurité/privacy, revue arabe RTL par personnes qualifiées. Aucun des tests CI ne remplace leurs signatures.
- **Next exact :** obtenir (1) session SSO QA Preview autorisée et (2) GO explicite d'un déploiement Preview au code Web courant si la FUE doit certifier le HEAD actuel ; puis préflight BFF/Neon 4/4 en lecture seule → tests F01–F06 3 viewports FR/AR → preuves et revue F07 → closeout F08 → seulement alors décider D7 GO / NO_GO et passage à D22 après gate D19.
- **Verdict au 29/10/2026 : D7 OPEN / FUE_NO_GO.** Aucun pourcentage inventé, aucune action Production/Neon mutation/Vercel déploiement.
