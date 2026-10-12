# IAMINA V1-03 — Gate pré-lancement local-first, installation neuve et confidentialité
*12 octobre 2026 — **version corrigée selon l'information directe du propriétaire : 0 client**. Cette version remplace intégralement l'ancien cadrage « migration de clients distribués » de ce fichier.*

> **Source de vérité :** `docs/ROADMAP.md` (séquence P5 et décision humaine de release), `docs/LOCAL_FIRST_RUNTIME_BOUNDARY.md` (patient local-first, Vercel/Django/Neon de développement/certification uniquement). **Aucun client actuellement. Aucune migration de parc patient à conduire.** Statut du développement : `CI_GREEN_25_OF_25 / NOT_MERGED / NOT_DEPLOYED / NOT_PATIENT_AUTHORIZED`.

## 1. Goal → succès → preuve

**Goal immédiat :** préparer et qualifier une **première installation IAMINA V1**, depuis un appareil/profil propre, sans chemin patient GET SSE dans le code nouveau, avec consentement local persistant et app usable hors ligne. Le fait que l'ancien code GET existe sur un environnement **de revue/certification** ne constitue pas une migration de clients ni une fuite de données patient.

**Succès engineering** = CI intégrée exacte verte, premier lancement/installation synthétique et reprise offline sans serveur, refus IA installé avant tout appel auth/réseau, SSE POST JSON sans texte libre dans URL, GET legacy fermé sans redirect ni provider, P3 dormant et OCR OFF. **Succès release patient** = supplémentaires : architecture réelle figée, validations techniques réelles ciblées, revue qualifiée security/privacy/clinique pour les fonctions actives, autorisations P5/traitements avant première donnée de santé identifiable.

**Preuve intégration obtenue** : [PR #941](https://github.com/hraaaaf/IAMINA-MVP/pull/941) DRAFT, HEAD `d3562e814e39d412516f421e66cb285fa7df50ce`, **25/25 workflows SUCCESS** ; [CI `38252290789`](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38252290789) 6/6 jobs, SQLite **2865 passés**, PostgreSQL **2869 passés**, Flutter **688 passés** + web build ; [Chrome PWA update/recovery `38252290695`](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38252290695) SUCCESS en rerun ; [Android TD-008 `38252291102`](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/38252291102) émulateur SUCCESS. Cela prouve les tests automatisés indiqués, **pas** des utilisateurs réels, des appareils physiques ou l'autorisation de traiter des données patients.

## 2. État initial et attribution exacte des risques

| Élément | Fait vérifié / information propriétaire | Interprétation pré-lancement |
| --- | --- | --- |
| Base utilisateurs | **0 client**, confirmé par le propriétaire le **12 octobre 2026** | **Retirer** les gates « recenser les clients installés », « migrer le parc », « protéger des données clients historiques » : ils ne correspondent pas à la situation. Les installations de test développeur ne sont pas des clients et se réinitialisent en environnement contrôlé. |
| Architecture patient V1 | `docs/LOCAL_FIRST_RUNTIME_BOUNDARY.md` : soins/état clinique en stockage et logique **locaux** ; premier enrollment et réouverture **sans** Vercel, Neon, Firebase ou SMTP | Préparer un **first-install neuf sans réseau** ; les APIs distantes sont facultatives et ne doivent pas effacer ou bloquer l'état local. Ne pas assimiler certification Django distante et production patient. |
| Vercel review | Frontend `iamina-review` commit `1e44ba57ad63638b1eb15af916adc54d0f8c15fc`, service worker source `0.1.0+1`, client Dart source avec `chatStream GET?message` | **Risque du code historique**, non preuve d'une fonction web exécutée : [audit binaire antérieur](2026-10-11-v1-03-deployed-sse-url-privacy-divergence.md) a lu `main.dart.js` servi, n'a trouvé **aucun `chat/stream`**, et le parcours web actif `CompanionConversationScreen` utilise **POST /ai/chat**. Ne pas dire « les clients actuels envoient GET ». |
| Vercel certified | Backend certifié, déploiement cible `production` Vercel `dpl_7SogpUMHNHd9rF7s7rfALccKduv7`, source `df004bcb25d2ae5c9004825ebee092306696b9e5` contenant GET SSE | **Infra de dev/cert**, non topologie patient. Les libellés Vercel `production` et le risque de routes héritées n'établissent pas de traitement de patients. |
| Candidat #941 | Flutter+SW+bootstrap `0.1.0+2`, `ApiClient.chatStream` POST JSON, backend POST SSE après auth/CSRF, GET 405, opt-out persistant, P3 dormant | **Premier build de référence** pour QA vierge. Le numéro de cache distinct prévient les collisions lors de tests techniques, mais pas de parc patient à convertir. |
| Drains / logs Vercel | Vercel `list_drains` et connecteurs HTTP **404**, `list_project_routes=[]`, flags projet de protection visibles | Configuration drains, rétention et transformations **inconnues**. Contrôle d'hygiène **sur infra dev** avec marqueurs synthétiques ; vérification liée au **runtime patient réellement activé** avant toute première donnée identifiable, non inventaire imaginaire de logs clients. |

Les métadonnées de projets/déploiements n'établissent aucune diffusion vers une clientèle ; le **zéro client** est une information explicite du propriétaire, non inférée de Vercel, du nombre de GitHub Releases ou d'un rapport de télémétrie.

## 3. Plan corrigé : paralléliser les tâches réelles

| Lot | Goal | Succès observable | Preuve / état |
| --- | --- | --- | --- |
| **A — Première installation local-first** | Tester un premier démarrage PWA + Android + iOS sans ancien profil et sans réseau, enrollment, écriture/lecture clinique locale, redémarrage, reconnexion facultative | Aucune dépendance à Vercel/Neon pour les actes locaux ; données et accès conservés ; capture appareil/build et preuve sans patient | CI PWA/émulateur 25/25 verte ; **vrais appareils encore non vérifiés** |
| **B — IA et transport** | Sur build #941, refus local IA durable par installation, puis SSE POST JSON auth/CSRF ; GET legacy 405 sans redirect | Avant réacceptation explicite, **0 appel AI/voix/image/stream** (incluant redémarrage et offline) ; aucune URL contenant message synthétique ; séparation comptes et rollback sûrs | Unit/integration synthétiques verts ; contrôle vrai OS/platform encore ouvert |
| **C — Infrastructure et hygiène pré-lancement** | Documenter uniquement les services réellement **activés** sur la topologie cible (local-first patient + dev/cert séparé) | Inventaire traitements et politiques de logs/rétention du futur runtime de **premier patient**, test canary synthétique de dev autorisé ; aucun faux classement de Vercel/Neon comme production patient | Frontières documentées ; Vercel drains/logs encore non audités ; ils n'empêchent pas à eux seuls **merge d'ingénierie** |
| **D — OCR dormant et revue clinique** | Vérifier absence d'activation accidentelle et de sauvegarde implicite | OCR **OFF** prouvé en test ; si activation demandée ultérieurement : corpus contrôlé avec unité explicite, HI/LO, 401–600 mg/dL, confirmation avant toute écriture, revue clinicien | Non-activation/guards synthétiques verts ; **validation clinique requise avant activation, pas pour une fonctionnalité OFF** |
| **E — Intégration/code et gouvernance** | Conserver #941 exact-HEAD certifié et constituer dossier de revue du code à merger sans perdre la frontière local-first | CI 25/25 ; revue des 87 fichiers de pile et dépendances ; décisions fermées/revues traçables ; docs alignées | CI acquise ; PR **DRAFT**, 0 revue indépendante enregistrée au dernier contrôle |

**Pas de « migration clients `0.1.0+1` → `0.1.0+2` »** comme critère de sortie V1-03. Un *test de robustesse* du SW entre builds de laboratoire est utile et déjà présent en CI, mais ce n'est pas une précondition client externe. **Pas de fenêtre de bascule patient** ni de purge de logs historiques sans incident et données réellement observés.

## 4. Séquence et vrais gates

1. **Maintenant, ingénierie autonome :** QA de premier lancement avec données synthétiques, vérification du code/release candidate, diagnostics non sensibles, tests ciblés ; corriger puis recertifier toute mutation de #941 au nouvel HEAD.
2. **Revue indépendante de l'ingénierie** (security/privacy et clinique uniquement pour ce qui est réellement activé). Tant que l'OCR reste OFF, ne pas inventer une exigence d'avis clinique pour fusionner ses gardes de désactivation.
3. **Human gate Git :** autorisation explicite de **merge**. Puis CI post-merge exacte et closeout des docs canoniques.
4. **Human gate Vercel distinct :** aucune modification/deploy Vercel sans autorisation explicite, même pour l'environnement distant **de dev/cert**. L'autorisation d'y déployer ne signifie **pas** une autorisation patient.
5. **Avant la première donnée de santé identifiable :** appliquer le **vrai séquencement `docs/ROADMAP.md` §9** : nouveau gel exact de release, réactiver les gates P5-6A/#318 et P5-6B/#320, figer la topologie *effectivement choisie*, lister les processeurs réellement activés, audits fail-closed et décision humaine explicite d'essai réel. Le local-first patient demeure la référence tant qu'un changement d'architecture n'est pas approuvé.

**Verdict de ce document :** `PRE-LAUNCH_ZERO_CLIENTS / FIRST_INSTALL_NOT_YET_DEVICE_CERTIFIED / CI_25_OF_25_GREEN / NO_CLIENT_MIGRATION_REQUIRED / NOT_MERGED / NOT_DEPLOYED / NOT_PATIENT_AUTHORIZED`. P5 historique `6/12 = 50 %` (roadmap), pas de pourcentage V1-03 inventé.
