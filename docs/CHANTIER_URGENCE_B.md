# IAMINA — CHANTIER D’URGENCE B — Reprise canonique Web/PWA

**Autorité d'exécution :** [Notion — Chantier d'urgence B, décisions dépendantes](https://app.notion.com/p/40777c66336281729c03c9bb294e71b7) ; [Chantier A, décisions autonomes](https://app.notion.com/p/40777c6633628173b672cd02104a0003) est exécuté séparément. [Tri D1–D30](https://app.notion.com/p/40777c6633628177b325d3cb5412fc18) est un registre de distribution. **Décision explicite du propriétaire le 29/10/2026 : A et B, et non `docs/ROADMAP.md` / W00–W14, dictent désormais l'ordre.** Conserver l'ancien fichier comme historique technique ; il ne justifie aucun changement de priorité dans B. Ce Markdown est un **miroir/handover B**, non une troisième roadmap.

**Dépôt :** `hraaaaf/IAMINA-MVP`. **Base de l'audit D8 :** `main@9ba0f737e184e1c65ca83a4db14b3b22f220c0ae` (29/10/2026). **Cible exclusive :** Flutter Web/PWA. **Aucun déploiement Vercel** sans autorisation explicite.

## Périmètre / ordre strict B (17 décisions)

1. **D7** — Type de diabète et traitements modifiables
2. **D22** — Unité avant objectifs glycémiques
3. **D8** — Unité suggérée selon pays mais modifiable
4. **D10** — Récupération et verrouillage facultatif
5. **D9** — Retour patient existant sans onboarding imposé
6. **D24** — Désactivation IA effective côté API
7. **D26** — Confidentialité, déconnexion, suppression
8. **D28** — Intelligence déterministe gouvernée
9. **D2** — Notifications intelligentes consenties
10. **D4** — Rapports PDF/CSV/XLSX
11. **D14** — Photo repas : suggestion IA incertaine et validation patient
12. **D15** — Brouillon repas multimodal unique
13. **D20** — Tendances pondérales et alertes descriptives optionnelles
14. **D23** — Paramètres Application et IAmina centralisés
15. **D29** — Retour de première utilisation facultatif
16. **D1** — CGM sans Nightscout obligatoire
17. **D25** — Données/appareils : connexion et révocation

**Ne jamais emprunter D16/W03 ni les autres décisions du chantier A.** Le travail sur A (D30, D19, D5, D16…) est hors de notre propriété d'exécution ; son code/CI peut être consulté uniquement pour vérifier les dépendances de B. Un seul lot produit actif par chantier ; audit/preflight d'une décision future permis, **pas de fermeture hors ordre**.

## État vérifié, sans confusion des sous-lots

| Décision B | Statut précis | Dépendance / preuve | Next |
| --- | --- | --- | --- |
| **D7** | **OPEN / FUE_NO_GO** ; tests limités et documentation fusionnés, pas D7 produit | [#1164](https://github.com/hraaaaf/IAMINA-MVP/pull/1164), [#1172](https://github.com/hraaaaf/IAMINA-MVP/pull/1172) ; verdict D30 du chantier A et FUE patients/profils encore à vérifier | Après clôture D30, prouver les parcours réels D7 Web (types, traitements, persistance, FR/AR RTL, A/B, offline) |
| **D22** | **OPEN / FUE_NO_GO** ; préflight uniquement terminé | [#1173](https://github.com/hraaaaf/IAMINA-MVP/pull/1173), [#1174](https://github.com/hraaaaf/IAMINA-MVP/pull/1174), [#1175](https://github.com/hraaaaf/IAMINA-MVP/pull/1175) : préflight tests/docs fusionnés et exact-SHA CI/postmerge verts, **sans correctif produit** ; D19 clinique [#920](https://github.com/hraaaaf/IAMINA-MVP/pull/920) sous autorité A, décisions G1–G7 sans approbation | Contrat clinique et privacy/RTL validés, puis correction Web des unités/objectifs avec FUE complète |
| **D8** | **AUDIT PRÉPARATOIRE SEULEMENT ; OPEN** | Dépend de D5 (A) et D22 (B) ; [issues #964](https://github.com/hraaaaf/IAMINA-MVP/issues/964) et [#965](https://github.com/hraaaaf/IAMINA-MVP/issues/965) ouvertes | Ne pas activer de mapping pays→unité avant politique et contrats approuvés |
| **D10…D25** | Non examinées dans ce sous-lot | Respecter l'ordre et les dépendances propres détaillées dans Notion B | Auditer à tour de rôle après gates, sans anticipation de clôture |

**Événement externe observé :** PR D30 [#1169](https://github.com/hraaaaf/IAMINA-MVP/pull/1169) du chantier A **MERGED** à `main@9ba0f737e184e1c65ca83a4db14b3b22f220c0ae`. **Cela ne prouve pas que D30 est complètement certifiée** (postmerge, sécurité/privacy, FUE et statuts canoniques doivent être contrôlés par A). Aucune mutation D30 par le chantier B.

## D8 — préflight source statique, sans implementation

**Goal D8 fonctionnel (ultérieur) :** après D5 + D22, suggérer au besoin une unité de glycémie en fonction du pays **explicitement choisi**, selon une convention documentée/validée, tout en laissant chaque personne choisir et changer librement l'unité. **Le pays n'est ni une ordonnance, ni une géolocalisation vérifiée, ni un fuseau horaire implicite.**

**Source sur main `9ba0f737` :**

| Source | Constat dans code principal | Conséquence |
| --- | --- | --- |
| `frontend/lib/features/auth/onboarding_chat_screen.dart` | `String _unit = 'mg/dL'`, indépendamment de `_country` ; deux choix UI `mg/dL`/`mmol/L` ; la sélection `_unit` reste explicite et éditable | **Aucune suggestion conditionnelle pays→unité prouvée** ; le défaut de valeur de départ universelle doit être étudié avant un changement |
| Même écran `didChangeDependencies` | En mode `preferencesOnly`, relit `profile?.unitPreference` et le pays local connu ; IP peut seulement suggérer le pays non encore touché | Une suggestion D8 ne doit **jamais écraser une préférence persistée** |
| Même écran `_finish()` | Enregistre séparément `country: _country!` et `unitPreference: _unit` ; les bornes `targetRangeLow:70` et `targetRangeHigh:180` sont toujours écrites, quelle que soit l'unité | **GATE D22 obligatoire** : ne pas introduire de conversion ou objectif implicite |
| `frontend/lib/services/locale_preference_service.dart` | `suggestCountryFromIp()` est faillible et ne persiste pas le pays ; `setExperience` vérifie le code ISO choisi et le stocke explicitement ; pas de politique pays→unité dans ce service | Séparer géo-IP indicative, choix de pays D5, préférence unité D8 ; ne pas dépendre du réseau |
| `frontend/lib/services/country_choices.dart` | Liste ISO hors-ligne de pays/territoires ; pas de matrice d'unité clinique approuvée | Ne pas supposer `MA=mg/dL` ou `FR=mmol/L` |
| Tests actuels `onboarding_ip_country_test.dart`, `onboarding_explicit_country_boundary_test.dart` | 249 entrées ISO attendues ; échec de pays `OTHER` et `ZZ` ; langue seule n'écrit jamais un pays ; choix explicite de pays conservé | Tests D5 existants utiles mais **ne sont pas une validation de suggestion D8** |

**Choix non autorisés :** inventer une table `MA/FR/autres → unité` fondée sur la langue ou l'adresse IP, déduire la cible clinique, changer les seuils ou interpréter les valeurs legacy sans provenance, activer `g/L` sans contrat complet, auto-écraser une sélection ancienne. Voir [#964](https://github.com/hraaaaf/IAMINA-MVP/issues/964) : la France utilise également le g/L dans certaines pratiques ; la conformité d'une suggestion locale précise demande une validation. Le mapping D8 est donc **PENDING** et n'est pas inclus dans cette PR.

### Tests de réception D8 à exécuter ultérieurement

| Cas | Attendu | Statut |
| --- | --- | --- |
| Pays réellement choisi, policy approuvée disponible | Suggestion libellée comme suggestion, deux unités manuellement sélectionnables | NOT_RUN |
| Pays inconnu / IP non disponible / politique absente | Aucune suggestion mensongère ; choix utilisateur disponible | NOT_RUN |
| Pays modifié après une sélection manuelle | Préférence explicite jamais effacée ni remplacée à l'insu du patient | NOT_RUN |
| Ancien compte / profil déjà configuré | Préférence persistée conservée ; aucune réinterprétation des objectifs/mesures | NOT_RUN |
| Objectifs hérités sans unité/provenance | Pas de classification ou conversion clinique par simple convention pays | NOT_RUN |
| FR/AR RTL, clavier et mobiles/tablettes/desktop | BEFORE → Goal → mockup → AFTER mêmes viewports 390×844, 768×1024, 1280×900 ; navigation, offline/reload, isolation A→B | NOT_RUN |
| Home/Reports/IAmina/exports et synchronisation | Même unité affichée sans altérer quantité/source ni introduire d'effective target | NOT_RUN |

**Human gates :** D5 contrat pays réellement sélectionné, D19/D22 contrat clinique des cibles/calculs approuvé, politique de suggestion par pays sourcée et validée par les spécialistes compétents, privacy/FR-AR-RTL ; FUE produit complète, CI exact HEAD, merge/postmerge. **Aucune FUE D8 exécutée par ce preflight.**

## Closeout et continuité

- **Sous-lot actuel :** cadrage de priorité B et audit D8 **documentation uniquement**, pas de code clinique ni UI, DB ou Vercel. [PR #1176](https://github.com/hraaaaf/IAMINA-MVP/pull/1176) **MERGED** par squash `main@4c91748c2f09a2f0c3836a85e786297dba35dcf3`. Diff : **1 Markdown ajouté**, aucun fichier runtime/CI/schéma/API modifié. Prémerge exact HEAD `dcd7fc143b13ce3d1c55c7851737ed91cb139abf` : [CI #40852496845](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40852496845) **SUCCESS**. Postmerge sur le SHA exact : [CI #40852619779](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40852619779) **SUCCESS** (scope et secret verts ; tests frontend/backend volontairement SKIPPED, car documentation uniquement). `main` a été vérifiée sur le SHA du merge. Aucun Vercel : `vercel.json` `git.deploymentEnabled=false` relu.
- **Revue critique bornée :** la distribution A/B concorde avec les deux pages Notion ; l'ancienne roadmap est gardée en archive, non supprimée ; la preuve D8 est statique et non un contrat de suggestion, une FUE ou une approbation clinique. L'analyse n'est pas une revue de sécurité/clinique indépendante. Succès observable : provenance des 17 décisions B et audit D8 traçables, CI pré/post exactes vertes, aucune mutation produit. Le sous-lot **documentaire** peut être clos ; **D7, D22 et D8 restent OPEN/FUE_NO_GO ou NOT_RUN** sans transfert de score ou de certification.
- **Next exact :** vérifier le closeout D30 du chantier A, sans intervenir sur A. Dès preuve des gates A, reprendre **D7** avec FUE Web ; **D22** seulement après les signatures cliniques D19, puis **D8** après D5 et D22. Si ces gates restent ouverts, continuer seulement une préparation B indépendante et non une implémentation clinique.
- **Verdict décisions B :** aucune fermeture produit D7/D22/D8 revendiquée par le présent fichier. Aucun pourcentage chantier calculé sans périmètre prouvé. Aucun Vercel sans accord explicite.


## 29/10/2026 — D7 : régressions Web réelles vs certification clinique (post-D30)

**Goal D7 :** le patient peut modifier son type de diabète et déclarer librement les traitements **qu'il suit déjà** ; ces modifications appartiennent exclusivement au coffre du patient, persistent, n'infèrent jamais un traitement et ne sont jamais annoncées comme synchronisées sans accusé validé.

**D30/A :** [#1169](https://github.com/hraaaaf/IAMINA-MVP/pull/1169) fusionnée, closeout Web du choix compte/verrou facultatifs documenté dans `docs/assessments/2026-10-29-d30-web-local-first-candidate.md` ; ne pas extrapoler au gate clinique ou à l'isolation clinique complète. Le chantier B n'a pas modifié A.

| Preuve D7 Web | SHA / CI exacte | Conclusion bornée |
| --- | --- | --- |
| [PR #1179](https://github.com/hraaaaf/IAMINA-MVP/pull/1179) **MERGED** | Prémerge `f2abbddb392c97c59ccee430b9c7a6432c4e6a15` : [Chrome widget #40854287805](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40854287805) **SUCCESS**, [Flutter analyze + tests + build PWA #40854287690](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40854287690) **SUCCESS**, [E2E pilote #40854287644](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40854287644) **SUCCESS** ; squash `main@6c84447fa849af89e66b8f183bb02d8340924dca` | Test **synthetique** du sélecteur D7 type2→type1→unknown→gestational, 390×844 / 768×1024 / 1280×900, FR/EN/AR RTL ; aucun traitement déclaré ne change sans interaction. 2 nouveaux fichiers de test/workflow seulement |
| #1179 postmerge | [E2E #40855016788](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40855016788) **SUCCESS** sur `6c84447f` ; [CI générale #40855016852](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40855016852) **CANCELLED** après nouveau commit main | Ne **pas** compter CI cancelled comme verte |
| [PR #1180](https://github.com/hraaaaf/IAMINA-MVP/pull/1180) **MERGED** | Prémerge `676a71e86d38671e8d0d4b7d5344ba63945cdf19` : [CI #40855399739](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40855399739) **SUCCESS**, [E2E #40855399717](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40855399717) **SUCCESS** ; squash `main@8bd92d3276a3f1db898575504d8a1c17068519f2` | Nouveau **test Flutter widget intégrant ProfileScreen** : changement de type synthétique et sauvegarde du profil 734, traitements préservés, une autre ligne profil 812 non modifiée, fermeture/réouverture écran, puis `none_declared` écrit après choix explicite en état `pending`. Un fichier de test seulement |
| #1180 postmerge | [CI #40856299121](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40856299121), [E2E #40856299440](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40856299440) | **COMPLETED/SUCCESS les deux au SHA exact `8bd92d3276a3f1db898575504d8a1c17068519f2`**. Sous-lot test-only #1180 : merge + postmerge vérifiés ; D7 produit toujours ouverte. |
| [PR #1182](https://github.com/hraaaaf/IAMINA-MVP/pull/1182) **MERGED** | Source `c94c0e18e21373984d2668693c61f884ecaf0c0c` : [Chrome IndexedDB #40857425023](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40857425023) **SUCCESS** et [CI Flutter/tests/PWA #40857425106](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40857425106) **SUCCESS** ; merge exact `main@563788f58d62dcadef89b12017376de18843c2b7` | 3 fichiers de **harness synthétique CI-only**. Coffres physiques IndexedDB A/B distincts ; navigation A→B→A→B, hard reload ; type2→type1 n'altère pas les traitements d'A ; B passe à `none_declared` par action explicite uniquement ; `sync_status=pending` et `patient_declared` contrôlés. **Ni authentification ni FUE UI patient prouvées.** |
| #1182 postmerge | [CI #40858356581](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40858356581) | **COMPLETED/SUCCESS sur le SHA exact `563788f58d62dcadef89b12017376de18843c2b7`**. Sous-lot de tests Chrome/IndexedDB clôturé techniquement, **D7 produit toujours OPEN/FUE_NO_GO**. |

**Sécurité des conclusions :** le test #1180 utilise des coffres/records synthétiques et `NativeDatabase.memory()` ; le Chrome #1179 vérifie le widget/renderer sans coffre persistant ni authentification. Le #1182 apporte **en complément une vraie preuve Chrome/IndexedDB synthétique**, mais son application/entrée de test n'est **pas** le parcours utilisateur produit, ne se connecte pas à une identité Django, n'exerce pas le consentement patient ni le login hébergé, ne démontre pas le zéro egress en session ni la sécurité clinique. Les preuves ne sont **pas** une FUE D7 complète. Aucun nouveau traitement, posologie, unité ou objectif clinique n'a été mis en production par ces PR ; pas de changements de code produit ni Vercel.

### D7 — critères de clôture produit encore **NOT_RUN** / NON CERTIFIÉS

1. **FUE Chrome intégrée 390×844 / 768×1024 / 1280×900, FR/AR RTL** : vrai parcours avec coffre synthétique isolé Onboarding → Profil → édition déclarative → Enregistrer → retour/rafraîchissement ; prouver affichage sans overflow, clavier et choix accessibles. Captures BEFORE/AFTER si toute UI modifiée.
2. **Persistance navigateur/offline** : fermer/recharger le navigateur, vérifier `PatientTreatmentDeclarationStore` et le type dans le même coffre IndexedDB réel, sans code/heure/valeur imputée à tort ; traitement `not_answered` / `unsure` / `none_declared` distinct.
3. **Changement de coffre A→B→A** : ne voir ni écrire les données de A dans B ni inversement ; protéger epoch et refus d'accès sans identité/coffre ; tests d'isolement sans données personnelles.
4. **Confidentialité / clinique** : prouver garde-fou egress des données déclarées en local-only, absence de confirmation serveur fictive ; avis qualifiés clinique, sécurité/privacy et libellés arabes natifs si nécessaire avant tout GO santé.
5. **Revue et CI FUE exact SHA, fusion et postmerge** pour chaque lot ; résultat documenté, pas de verdict basé seulement sur le nombre de tests verts.

**Verdict actuel : D7 OPEN / FUE_NO_GO ; sous-lots #1179, #1180 et #1182 test-only MERGED ; aucune fermeture de décision complète.** D22 OPEN/FUE_NO_GO dépend toujours de D19 (chantier A) et des décisions G1–G7. D8 OPEN dépend D5 (A) et D22 (B). **Next exact :** sous-lot #1182 techniquement clos avec CI pré/postmerge exact SHA SUCCESS. Compléter FUE **vraie application Web** avec comptes tests et environnements QA explicitement attestés, ou déclarer chaque gate inaccessible au lieu d'inventer un PASS ; revue clinique/privacy requise. Aucun Vercel sans autorisation et aucune intervention sur A.


## 29/10/2026 — D7 Web : FUE réelle, verdict borné après postmerge #1182

**Décision D7 : FUE_NO_GO / OPEN.** Les sous-lots test-only **#1179**, **#1180**, **#1182** sont **MERGED**, et leurs tests ciblés Chrome/Flutter/SQLite WASM/IndexedDB sont verts. [#1182 postmerge CI #40858356581](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40858356581) **SUCCESS sur `563788f58d62dcadef89b12017376de18843c2b7`** ; [closeout #1184](https://github.com/hraaaaf/IAMINA-MVP/pull/1184) **MERGED** `main@b30eb164099e83756c30bfae89a6fae8f4f04509`, [CI prémerge #40859289298](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40859289298) et [postmerge #40859345133](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40859345133) **SUCCESS** (docs-only).

**Rapport FUE Web / matrice F01–F08 :** [`docs/assessments/2026-10-29-d7-web-fue-coverage-gate.md`](assessments/2026-10-29-d7-web-fue-coverage-gate.md). Ce rapport distingue chaque preuve synthétique du parcours authentifié hébergé **NOT_RUN**. Le SSO Vercel Preview est encore actif ; l'unique Preview QA W01+D2 observée, deployment `dpl_4o5sLYhZywjthETgPbmtAmbo6SNr` au SHA `8a417041...`, **ne correspond pas** au `main@b30eb164...` courant. La Preview contient 2 comptes fictifs et 2 profils confirmés par SQL SELECT **seulement**, aucune session QA A/B exécutée ni mot de passe inspecté.

**BLOQUÉ HUMAN GATE :** accès privé SSO QA pour un navigateur autorisé **et** GO distinct Vercel Preview au SHA courant avant FUE hébergée certifiante ; ensuite préflight BFF/Neon 4/4, F01–F06 sur 390/768/1280 FR/AR, F07 sécurité/clinique/privacy, closeout F08. Sans ces gates, **ne pas déclarer la FUE terminée**. Ni déploiement Vercel, ni code runtime, ni mutation Neon lors de cette consolidation.


### 29/10/2026 — FUE Web D7 : closeout CI documentaire #1186

- [PR #1186](https://github.com/hraaaaf/IAMINA-MVP/pull/1186) **MERGED** `main@54bf418ec451dcd45a942bdacef23bba376148ea`, [CI prémerge #40860142061](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40860142061) **SUCCESS** sur `266e7811028ea2b569caad16879eb50fdb0d67a1` ; [CI postmerge #40860238260](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40860238260) **COMPLETED/SUCCESS** sur exact merge SHA. **Tests Flutter/build SKIPPED** par conception : deux Markdown seulement. Les tests du produit demeurent ceux des #1179/#1180/#1182 au SHA documenté.
- **État de la vraie FUE Web hébergée : NON EXÉCUTÉE / NO-GO.** Uniquement la matrice de [preuves/gates F01–F08](assessments/2026-10-29-d7-web-fue-coverage-gate.md) a été fusionnée : Preview QA sous SSO au SHA ancien `8a417041...`, `main@54bf418e...` non déployé en Preview QA. Pas d'accès SSO automatisé qualifié, ni revue clinique/privacy. Aucune activation patient, aucun usage de mots de passe, aucun déploiement ou mutation DB.
- **Next exact :** human gate explicite pour un accès navigateur privé SSO et un **GO Vercel Preview distinct au SHA exact** ; préflight BFF/Neon QA 4/4, puis F01–F06, F07 avis qualifié, F08 closeout et décision D7. Aucun % de FUE complet attribué.


### 29/10/2026 — D7 Web, alternative Chrome gratuite : #1188 MERGED, postmerge à vérifier

- **Décision :** remplacer la dépendance au crédit TinyFish pour les contrôles reproductibles du front Web par un banc GitHub Actions/Chrome headless, **sans paiement**. [PR #1188](https://github.com/hraaaaf/IAMINA-MVP/pull/1188) **MERGED**, squash `main@9862389939dd5fcdb80b428bdb5a1bb6751382e7`. Tests exact HEAD `ad93e0ce6833df4d65facdb76d976328e8d635dd` : [CI générale #40889058062](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40889058062) **SUCCESS** et [Chrome gratuit #40889058139](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40889058139) **SUCCESS**.
- **Preuve limitée mais réelle :** `ProfileScreen` owner/save sur DB synthétique en mémoire, D7 sélecteur en vrai Chrome sur 3 viewports FR/EN/AR, compilation de l'application **Web réelle** locale et contrôle de l'amorçage Flutter, hard reload, maintien de la coquille déjà chargée lors de la déconnexion réseau. Un échec initial [#40882903610](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40882903610) venait d'un oracle de casse `IAMINA` contre `IAmina`; corrigé uniquement dans le script test puis contrôles verts sur nouveau HEAD. Le test offline ne certifie **pas** le redémarrage PWA hors ligne à froid.
- **CI postmerge générale :** [#40889689991](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40889689991), `main@98623899`, **COMPLETED/SUCCESS sur le SHA exact `9862389939dd5fcdb80b428bdb5a1bb6751382e7`** ; lot technique #1188 clôturé, décision D7 réelle toujours OPEN/FUE_NO_GO.
- **D7 reste OPEN / FUE_NO_GO** : ce lot CI gratuit ne remplace pas F01–F08 authentifiés dans la Preview réelle, l'isolation clinique serveur A/B, les contrôles privacy, la validation de consentement et les signatures qualifiées. Preview isolée READY au SHA précédent `a80bf804...` : une preuve sur ce site ne qualifie pas automatiquement le dernier `main`. Aucun déploiement Vercel/Production, aucun mot de passe patient ou écriture Neon dans #1188.
- **Next exact :** valider CI et fusionner ce closeout documentaire, puis vérifier son postmerge ; en parallèle poursuivre D7 FUE Web avec vraie authentification A/B seulement sous mapping QA confirmé et environnement prévu, sans confondre banc local et recette hébergée.
