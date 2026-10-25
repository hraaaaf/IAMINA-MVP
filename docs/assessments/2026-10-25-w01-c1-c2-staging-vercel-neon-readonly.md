# IAMINA W01 — C1/C2 : revue de staging Pulper et Vercel/Neon en lecture seule

Date de preuve : **25 octobre 2026**. Périmètre **Web/PWA + API Django + Neon exclusivement**. Ce document est une revue d'architecture et un inventaire read-only : **aucun Vercel deploy, aucune création/écriture SQL Neon, aucune modification de secrets, aucun compte patient ni merge**. Statut **W01 NO-GO**.

## 1. Goal, succès, preuve

**C1 Goal :** remplacer l'indisponibilité Redis du staging Pulper sans dégrader la suppression ordinaire d'un compte, l'isolation patient ou la rétention d'une extraction transitoire d'une heure. **Succès** : un import inspecté puis confirmé une seule fois, authentifié et patient-scoped, sans PHI documentaire persistée dans Neon sauvegardé, avec suppression normale testée même sans Redis. **Preuves exigées** : schéma de flux, revue de sécurité indépendante, code + SQLite/PostgreSQL/Chrome, course A/B simultanée, échecs 401/403/429/502/503, logs/caches/backups et effacement.

**C2 Goal :** inventorier le routage Vercel réel et les paramètres non secrets de Preview/Production. **Succès** : projets, SSO, variables par cible, artefacts exact SHA et dette d'anciennes URLs vérifiables sans produire de trafic médical. **Preuve** : réponses Vercel/Neon directement lues le 25 octobre 2026 et fichiers du repo.

## 2. C1 — Ce que fait le code actuel (vérifié à W01 HEAD de départ)

| Frontière | Code constaté | Conséquence observable / qualification |
| --- | --- | --- |
| Import et confirmation | `backend/diabetes/api/v1/documents.py` : staging `cache.set` + vérification `cache.get`; confirmation avec `cache.add(:consume)`, `get` et `delete`, TTL **3600 s**. | La disponibilité de Redis est requise pour conserver un brouillon Pulper ; une panne retourne **503 à l'ingest** / confirmation refusée. Le mécanisme de réservation limite la course sans constituer une garantie générale d'idempotence des écritures cliniques. |
| Effacement d'un compte | `backend/core/api/v1/account.py` exécute `run_account_delete_hooks` avant `user.delete()`; `backend/diabetes/apps.py` enregistre la purge Pulper ; `backend/media/documents/pending_cache.py` appelle `get_redis_connection`, `scan_iter` puis `delete`. | Sans Redis accessible, le hook échoue et la suppression **normale** est bloquée (500). **Ne pas rendre cette purge fail-open** : le mécanisme refuse justement de déclarer les données effacées quand le stockage n'est pas maîtrisé. La procédure exceptionnelle de nettoyage de 2 comptes synthétiques ne ferme pas ce parcours normal. |
| Exigence de durée | `backend/media/documents/retention.py` : `destructive_ttl_seconds=3600`. | Un TTL logique ne démontre pas un effacement physique du support ou des sauvegardes. La solution retenue devra définir une preuve proportionnée de suppression, y compris rétention indirecte et logs. |
| Spike #1151 | `backend/diabetes/services/documents/w01_postgres_pending.py` stocke un JSON clinique dans `PendingDocumentExtraction` puis le supprime ; `DEBUG=True` + flag sont requis. HEAD `62ca7aad`, **20/20 GitHub workflows COMPLETED/SUCCESS sur ce SHA**. | **Prototypage PostgreSQL synthétique uniquement**, aucune activation Vercel/Production. `raw_text` supprimé du JSON, mais mesures cliniques toujours présentes ; `DELETE` et TTL ne prouvent aucun effacement WAL/snapshot/PITR. `DEBUG` ne prouve pas que les identités soient synthétiques. Ce spike ne doit pas être mergé/activé tel quel. |

### 2.1 Options comparées (arbitrage non encore ratifié)

**Option A — Recommandée pour une preuve de concept séparée (pas encore autorisée pour patients).** Le navigateur garde le brouillon **uniquement en mémoire**, tandis que l'API retourne un **jeton opaque chiffré et authentifié (AEAD)** contenant les champs extraits et une échéance courte, bornée à 3600 s. Pas de PHI documentaire persistée dans la table Neon de staging ; seul un registre PostgreSQL **sans données médicales** stocke identifiant aléatoire, identifiant propriétaire, empreinte de jeton non réversible, expiration et état de consommation. L'API exige un Bearer encore valide, vérifie liaison propriétaire/AAD/expiration/intégrité, relit les champs relus/confirmés, puis assure consommation unique et persistance clinique **dans la même transaction**. Déconnexion ou reload = perte du jeton (réimport requis). **Risques à tester :** exposition par logs/surveillance/erreurs/analytics, XSS côté client, taille du payload vers BFF, gestion/rotation du secret AEAD côté serveur, rejeu concurrent à deux connexions, sauvegarde du registre non-PHI, échec de confirmation et rollback. Aucun `localStorage`, cookies ou URL/query string pour ce jeton ; headers HTTP `Cache-Control: no-store`, désactivation egress tiers. La **non-rétention de PHI dans PostgreSQL est un objectif de conception, non un résultat prouvé** ; les champs médicaux volontairement confirmés seront ensuite sauvegardés selon leur propre politique.

**Option B — Redis éphémère réellement isolé et qualifié.** Conserver la voie existante avec service Redis dédié, garantie de TTL/purge, backup/persistence désactivés **si contractuellement vérifiés**, contrôle d'erreurs, audit de coût et règles d'exploitation. Avantage : delta de code inférieur. Inconvénients : fournisseur/service supplémentaire, clés, disponibilité et revue de confidentialité. **Le propriétaire a demandé d'éviter Upstash pour le moment** ; ne pas provisionner ni souscrire sans décision.

**Option C — PostgreSQL JSON clinique à TTL logique (#1151 actuel).** **Rejetée comme solution patient au contrat 1 h tant que la persistance PITR/WAL n'est pas résolue**. Les tests unitaires et les locks transactionnels ne remplacent pas les garanties de confidentialité / destruction en sauvegardes.

**Décision C1 à ce stade :** poursuivre **Option A comme conception à auditer**, **pas** comme autorisation d'implémenter un mécanisme cryptographique clinique ni comme GO W01-G5. Garde fail-closed actuelle inchangée ; code du spike #1151 conservé en Draft, aucune mutation Production/Preview. Besoin d'une revue indépendante privacy/security avant activation.

### 2.2 Critères de conception de l'option A

1. Token ciphertext opaque, AEAD vérifié, `patient_id` lié au Bearer, nonce sûr, `exp <= issued_at + 3600`, validation stricte de taille/type/schéma ; double-check serveur des champs cliniques avant le commit.
2. Table de revendication **sans PHI clinique** ; patient-scoped et non prédictible, unique, transaction PostgreSQL permettant exactement une confirmation réussie et rollback sûr si `persist` échoue ; suppression account par cascade et refus de tokens anciens.
3. Aucun jeton ni PHI dans Vercel logs, query strings, URL, analytics, telemetry, cache/CDN, stockage durable navigateur ; tests de reboot/logout/reload et protection XSS.
4. Échec de chiffrement/clé, DB, navigateur, SSO/OIDC/Bearer, conflit de transaction et taille >4 MiB → réponse fail-closed claire, aucun succès artificiel.
5. Privacy review sur la rétention effective du ciphertext et clés ; tests E2E sur infrastructure synthétique autorisée avant tout usage patient.

## 3. C2 — Inventaire live read-only Vercel/Neon (25/10/2026)

| Sujet | Résultat direct observé | Portée / dette |
| --- | --- | --- |
| **Projet Web** | `iamina-review`, ID `prj_AYaUi32KTDHak8I7dmdQpDrqd8SI` ; `ssoProtection.enabled=true`, `deploymentType=preview`. | Projet Preview protégé. Root `frontend/` a été précédemment attestée dans Vercel UI ; la réponse `get_project` de cette lecture ne montre **pas** `rootDirectory` : ne pas la déclarer revalidée ici. |
| **Projet API** | `iamina-certified`, ID `prj_Pn9FnyconF3h2w9gOU74iV98kJoU` ; `ssoProtection.enabled=true`, `deploymentType=all_except_custom_domains`. | SSO protégé sur Preview ; la surface de domaines personnalisés mérite une revue distincte. Root `backend/` attestée historiquement, non affichée dans `get_project` actuel. |
| **Couple Preview courant inventorié** | Web `dpl_5rsqzp4s35VXNmPBrP6ZpGXhBPeL` / API `dpl_3ZK13h6n214Y46pwVPJJDSGM8ePw` ; tous deux `READY`, target `null` (Preview), branch W01, **même SHA `042f28df29a2c8ed0e3ddb56aabcf3520dbde269`**. | **Ce n'est pas le HEAD GitHub W01 le plus récent**, donc le nouveau plan/source n'a pas été déployé et le couple ne prouve pas la qualification de la candidate finale G4. Aucun déploiement lancé lors du contrôle. |
| **Variables Web** | 4 déclarations non secrètes `IAMINA_REVIEW_PREVIEW_API_BASE_URL` limitées aux Preview, dont une sur branche W01 ; aucun `IAMINA_ENV` côté Web affiché. | Ne pas afficher/propager leur valeur URL si l'identité réelle de l'API n'a pas été corrélée au déploiement. |
| **Variables API** | `IAMINA_ENV` **plain = development**, une déclaration ciblant **Preview + Production**. `DATABASE_URL` distincte par cible ; `IAMINA_EXPECTED_DB_HOST/NAME` séparés par cible, rôle limité en Preview. | **G3 Production BLOQUANT** : mode applicatif Production non activé. Les clés SMTP/récupération n'apparaissent pas dans les 17 déclarations listées ; ne pas changer `IAMINA_ENV` directement sans plan de mail/TLS/rollback. Les valeurs secrètes n'ont pas été déchiffrées. |
| **Variable de nettoyage historique** | `IAMINA_W01_G5_CLEANUP_ENABLED` toujours déclarée pour Preview branche W01. | À réexaminer et retirer **sous autorisation** ; sa présence ne prouve **pas** que la route API historique est encore servie. Les logs de la nouvelle API l'ont montrée 404. |
| **Anciennes URLs/aliases** | Alias listés : **60** Web et **19** API ; plusieurs correspondent à d'anciens déploiements, parfois sur branches différentes. | Inventaire d'aliases seulement : pas une preuve que chaque route est active. Stratégie de retrait/revocation ciblée à approuver, aucune suppression spontanée. |
| **Garde anti-deploy** | `frontend/vercel.json` et `backend/vercel.json` contiennent tous deux `"git":{"deploymentEnabled":false}` dans le repo. | **Preuve source seulement** ; l'effectivité de l'auto-deploy Git/Vercel n'a pas été requalifiée par un évènement de déploiement. |
| **Neon Production** | Projet `square-sun-82359137`, branche `br-fragrant-frost-b1lbdfzs`, name `production`, `current_state=archived`, `primary=true`, **`protected=false`**. | **G2 BLOQUANT** ; toute protection/modification nécessite un human gate Production. Aucune écriture réalisée. |
| **Neon synthétique** | Projet `noisy-truth-00115950` : branches `synthetic-only`, `w01-restore-proof-20261021`, `w01-endpoint-swap-holding-20261021`. Snapshot `snap-orange-mode-b9tjsdd1` existant. | Existence d'un snapshot et d'une branche restaurée **ne prouve pas** récupération d'un jeu de données synthétique non vide ; G6 toujours PARTIEL. |

### 3.1 Verdict par gate à ce pointage

- **G1 PARTIEL :** projects distincts, SSO et source anti-deploy prouvés ; réglages serveur Root/auto-deploy finaux et exposition des alias encore à vérifier.
- **G2 PARTIEL/BLOQUANT :** sandbox Preview isolée mais Production `protected=false` directement observée.
- **G3 PARTIEL/BLOQUANT :** `IAMINA_ENV=development` effectivement partagé avec Production ; SMTP et certificat TLS prod non requalifiés.
- **G4 PARTIEL (hébergé PASS limité) :** le couple immuable Preview partage le SHA `042f28df`, sans certifier le HEAD W01 actuel.
- **G5 PARTIEL/BLOQUANT :** parcours A→B→A et cleanup exceptionnel historiques probants, **suppression normale dépend toujours de Redis** ; ne pas effacer le hook.
- **G6 PARTIEL/BLOQUANT :** snapshots/branches existent ; restore synthétique **non vide** et SQL comparatifs manquent.
- **G7 OUVERT :** décision d'architecture C1 non ratifiée, G1–G6 incomplets, PR W01 encore Draft ; CI exacte et postmerge nécessaires.

## 3.2 Mise à jour de sécurité du spike #1151 (25 octobre 2026)

Le commit [`3851f4082a35f7fd08c210be96912330559abbfa`](https://github.com/hraaaaf/IAMINA-MVP/commit/3851f4082a35f7fd08c210be96912330559abbfa) étend le garde du stockage SQL temporaire aux cibles Vercel, même `DEBUG=True`, et exige un contexte de tests locaux pytest. La route refuse désormais le flag expérimental avant lecture du fichier ou extraction. Les tests de refus runtime/egress et la contention PostgreSQL deux connexions sont étendus. [Nouvelle CI générale #40242157736](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/40242157736) à vérifier sur ce SHA ; **ne pas transférer 20/20 de `62ca7aad`**. La confidentialité WAL/PITR, le risque de faux contenu « synthétique », et l'interdiction patient demeurent inchangés. Prototype toujours Draft, non fusionné, non déployé.

## 3.3 Vérification GitHub finale et pré-revue C1 (25/10/2026)

À la lecture GitHub, **PR W01 #1128 HEAD `e1763530` et PR Pulper #1151 HEAD `ed0714f3` : 20/20 workflows COMPLETED/SUCCESS chacune**. Le rouge de l'ancien SHA `3851f408` n'est pas transféré à la candidate corrigée ; l'assertion du test a été alignée sur l'erreur attendue sans désactiver les gardes. La PR temporaire #1150 (base `main`) a été **fermée sans merge** ; la PR #1151 reste ouverte et Draft.

Une [matrice de pré-revue sécurité C1](2026-10-25-w01-c1-pulper-safety-gate.md) précise les scénarios d'échec et preuves nécessaires avant de sélectionner une architecture de stockage documentaire. Il ne s'agit **ni** d'une revue indépendante **ni** d'une certification privacy de l'option AEAD. **Statut inchangé W01 NO-GO**, G1–G7 non fermés, W02 gelé.

## 4. Next exact / gate humain

**Next immédiat exécutable sans permission :** revue source/tests du mécanisme proposé Option A, préparation des oracles négatifs et de concurrence, comparaison documentaire des providers d'enveloppe chiffrée ; conserver le staging SQL #1151 isolé, sans activation clinique. Pour C2, cartographier seulement les aliases et métadonnées sans casser de déploiement.

**Human gates réellement nécessaires :** (a) validation sécurité/privacy pour tout mécanisme stockant/transférant temporairement des données médicales, (b) autorisation spécifique de nouvelles Previews Vercel E2E, (c) tests d'écriture/restauration **sur Neon exclusivement synthétique isolé**, (d) modifications de variables/protection Neon Production et nettoyage d'anciennes URLs. **Ne jamais déployer Vercel sans GO explicite.**

**Chemin restant :** C1 design + revues → correction/choix du staging → G5 E2E hébergé avec autorisation → G6 restore non vide sur sandbox avec autorisation → G2/G3 Production sous contrôle humain → G7 revue + CI SHA final + merge/postmerge + Notion → ouverture W02. **Aucun % inventé**.
