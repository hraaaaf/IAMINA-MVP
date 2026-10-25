# IAMINA W01-C1 — pré-revue des risques Pulper et critères de passage

**Date : 25 octobre 2026 · périmètre Web/PWA · état : DRAFT TECHNIQUE / NON CERTIFIÉ.**

Source de vérité : [roadmap W01](../ROADMAP.md), [audit C1/C2](2026-10-25-w01-c1-c2-staging-vercel-neon-readonly.md), [PR expérimentale #1151](https://github.com/hraaaaf/IAMINA-MVP/pull/1151). Ce document **ne constitue pas la revue indépendante security/privacy exigée en G7**. Il ne permet aucun déploiement, merge, traitement patient ou activation SQL clinique.

## Goal / Succès / Preuve

**Goal :** supprimer la dépendance Redis du **parcours d'extraction documentaire temporaire** et permettre l'effacement normal des comptes, tout en évitant la conservation de PHI de staging dans les sauvegardes PostgreSQL et en empêchant les doubles confirmations.

**Succès observable :** A→B isolé, Bearer invalide refusé ; brouillon perdu/expiré/révoqué refuse toute confirmation ; deux confirmations concurrentes donnent **exactement une persistance clinique** ; suppression normale sans 500 quand le support temporaire est sain ; aucune donnée documentaire transitoire en clair dans Neon/WAL/PITR ; comportement offline, 502/503 et uploads bornés.

**Preuve requise :** tests unitaires + PostgreSQL sur **deux connexions indépendantes** + Web navigateur sur environnement strictement synthétique ; inspection du schéma/du stockage et des logs ; attestation de revue sécurité/privacy indépendante ; certificat final exact-SHA. Rien de cela n'est encore démontré pour la proposition cryptographique.

## État vérifié, distinct des hypothèses

- **Code actif actuel :** `backend/diabetes/api/v1/documents.py` conserve temporairement `PulperOutput` dans le cache Redis, `cache.add(:consume)` avant confirmation, `TTL=3600` ; `backend/media/documents/pending_cache.py` utilise Redis `scan_iter/delete` pour la purge. `DELETE /account` exécute les hooks avant effacement. En panne Redis, échec de l'effacement normal **fail-closed**.
- **Spike PostgreSQL #1151 :** sur SHA `ed0714f3`, 20/20 workflows GitHub réussis. Le JSON clinique en PostgreSQL reste exposé à WAL/PITR ; aucune preuve de suppression physique après 1 h. `DEBUG`/`PYTEST_CURRENT_TEST`/absence de `VERCEL` réduisent le risque d'activation accidentelle mais **ne prouvent jamais que les données soient fictives**.
- **Option A envisagée :** navigateur en mémoire volatile, token serveur opaque **AEAD** lié au patient et à une échéance, registre d'usage unique **sans contenu clinique** dans PostgreSQL. Proposition de design **non validée, non implémentée**.

## Menaces / oracles de refus avant tout GO

| ID | Scénario adversarial / fail-closed | PASS à démontrer |
| --- | --- | --- |
| **C1-01** | Auth Bearer A, token d'extraction de B (y compris ancienne session). | 401/403, aucune lecture/écriture B, aucune divulgation via réponse ou journal. |
| **C1-02** | Jeton chiffré falsifié, mauvais AAD (`patient_id`, contexte, version), clé de déchiffrement manquante ou rotation. | Refus strict, zéro persistance ; politique de rotation et récupération documentée. |
| **C1-03** | Jeton expiré à 3600 s, `issued_at` futur, relecture après logout ou suppression du compte. | Refus au serveur indépendant de l'horloge du navigateur ; aucun renouvellement implicite. |
| **C1-04** | Confirmations A1/A2 simultanées via deux connexions PostgreSQL différentes, dont une bloquée sur verrou. | Exactement **une confirmation validée**, une seule transaction durable, seconde refusée ; rollback intégral si persistance échoue. |
| **C1-05** | Échec PostgreSQL entre marque anti-rejeu et écriture clinique ; timeout 502 après commit puis nouvelle tentative. | État explicite / replay contrôlé, jamais de doublon clinique ; ne pas promettre exactly-once global sans preuves d'idempotence. |
| **C1-06** | Reconstruire le brouillon depuis logs, traces, URL/query, cookies, localStorage, sessionStorage, service-worker cache, analytics, erreurs ou télémétrie. | Aucun PHI de staging dans ces supports ; revue des payloads et tests négatifs, `Cache-Control: no-store`. |
| **C1-07** | Fenêtre XSS : lecture de la mémoire client ou interception du token. | Contrôles CSP/XSS observables ; modèle de menace résiduel accepté explicitement, car AEAD protège stockage/transport mais **ne protège pas contre un script exécuté dans le navigateur**. |
| **C1-08** | Limite BFF 4 MiB alors que l'API accepte des documents jusqu'à 15 MiB ; boundary 4/15 MiB, transfert multipart/chunked. | Stratégie d'upload compatible même origine décidée et testée, ou taille Web plafonnée clairement et refusée **avant egress** ; aucun élargissement BFF arbitraire. |
| **C1-09** | Ancien état Redis avec extraction PHI existante alors que nouveau staging n'utilise plus Redis ; suppression compte. | Stratégie de transition prouvant l'expiration / purge des anciennes clés, **sans désactiver le hook fail-closed** prématurément. |
| **C1-10** | Protection SSO Preview, cookie Vercel, Authorization Bearer, CSRF hybride et panne d'API. | Cookies non transmis vers Django par BFF, 401/403/503 sans fallback identitaire, méthodes mutantes jamais réessayées automatiquement. |
| **C1-11** | Registre anti-rejeu PostgreSQL sauvegardé et restauré depuis PITR. | Schéma et échantillons **sans PHI**, index patient/tombstone/expiration, réaction aux restaurations et aux replays documentée ; aucun secret AEAD dans DB. |
| **C1-12** | Destruction/effacement des données après expiration, en cas d'export ou arrêt brutal navigateur et après suppression compte. | Limites de mémoire et de copies temporaires reconnues ; attestation d'absence d'archives de PHI de staging, contrat de conservation approuvé. |

## Plan d'implémentation conditionnel (ne pas exécuter avant décision sécurité)

1. Définir la représentation canonique des champs extraits autorisés, le schéma de preuve de confirmation, et la version du format. Vérifier que l'API actuelle confirme par `POST /documents/confirm/{batch_id}` **sans** payload : un token côté navigateur exige un changement explicite du contrat HTTP, OpenAPI et du client Flutter Web, sans token en URL.
2. Prototyper **hors production, uniquement avec données entièrement fictives**, primitive AEAD éprouvée, aléa/nonce sûr, AAD lié patient+périmètre+version+expiration, limites en octets, absence de fuite de clé.
3. Ne stocker en PostgreSQL que des marqueurs anti-rejeu non médicaux ; transaction unique persistance clinique + consommation ; prouver l'isolation sur deux connexions et le comportement en panne.
4. Préciser la transition de l'ancien cache Redis (sans contourner sa purge), puis l'effacement normal. Tester sans Redis uniquement une fois l'absence d'anciennes clés prouvée.
5. Tester client Web/Chrome/Safari et API BFF au HEAD réellement déployé **uniquement après GO Vercel Preview** ; appliquer BEFORE→AFTER sur chaque écran modifié.
6. Sécurité indépendante : rejeter tout BLOCKER/MAJOR, documenter la confidentialité et la rétention de ciphertext/clé, les choix irréversibles et le protocole de retour arrière, puis CI exact SHA et dossier G7.

**Décision à ce jour :** STOP pour toute activation d'un staging clinique, même expérimental en Preview publique. Les deux CI vertes attestent uniquement le code existant testé ; **G5/G6/G7 demeurent OPEN**. Prochain travail sans gate : audits et tests unitaires purement fictifs, hors déploiement et hors données réelles.
