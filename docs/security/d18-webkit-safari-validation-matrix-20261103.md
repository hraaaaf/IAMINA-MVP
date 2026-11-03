# IAMINA D18 Web — Safari / WebKit qualification matrix (2026-11-03)

**Décision :** D18/5 — compatibilité du coffre SQLite chiffré, **PRE-CUTOVER**. Cette matrice n'est PAS un résultat de test. Ne jamais conclure « Safari certifié » à partir de WebKit Linux.

## Goal, succès, preuve

- **Goal :** sauvegarde, restauration, isolation des sessions et tenue du stockage chiffré à l'arrêt/reprise sur IAMINA **Web** en environnement Safari.
- **Succès navigateur de CI :** vrai Playwright WebKit Linux et Chromium exécutent **tous les mêmes 10 tests** (exports A, mauvaise archive, crash partiel, refus écrasement, refus lecture partielle, restauration B, deuxième import refusé, mauvaise DEK refusée, réouverture B, source A intouchée).
- **Preuve externe matérielle :** Safari physique iPhone, appareil/version et iOS notés, scénario reproductible et résultats par assertion avec captures anonymes et absence de donnée réelle ; non disponible dans le runner Linux.

## Automatisation sur PR #1239 (SYNTHÉTIQUE)

| Contrôle | Chrome CI | WebKit CI | Safari physique |
|---|---|---|---|
| Worker Dedicated + MessageChannel + transfert clé ArrayBuffer | prouvé sur #1235 | CI à observer | non exécuté |
| Web Locks, absence de lock = refus sans fallback | prouvé sur #1235 | CI à observer | non exécuté |
| IndexedDB VFS xWrite → flush → fermeture → redémarrage | prouvé sur #1235 | CI à observer | non exécuté |
| AES-GCM archive scellée, mauvais mot de passe refusé | prouvé sur #1235 | CI à observer | non exécuté |
| Crash après bloc partiel, quarantaine, sans remplacement | prouvé sur #1235 | CI à observer | non exécuté |
| FKs, tables, index, trigger, view, BLOB, NULL, sqlite_sequence, PRAGMA integrity_check | prouvé sur #1235 | CI à observer | non exécuté |
| Déconnexion A → B → A et AuthEpoch | prouvé Chrome sur #1233 | NON inclus dans ce test WebKit | non exécuté |
| Données de taille > 16 Mio et éviction/quotas | NON prouvé | NON prouvé | non exécuté |

## Checklist iPhone Safari réel (gates humains ultérieurs)

- [ ] Tester uniquement sur **preview explicitement autorisée** avec deux identités et données synthétiques, jamais des patients.
- [ ] Enregistrer modèle iPhone, version iOS/Safari, état stockage disponible, locale FR puis AR (RTL), et mode normal / privé.
- [ ] À largeur 390 puis 430 px, contrôler lisibilité et scroll des messages : verrouillage, erreur mauvaise phrase/code, coffre manquant, restauration interrompue, refus écrasement, copie de recovery code ; capturer le BEFORE/AFTER si des composants visuels sont changés.
- [ ] A→logout→B→logout→A : aucun accès croisé, ancienne clé inutilisable, refus de worker toujours actif, Web Locks libéré.
- [ ] Force-quit Safari puis rouvrir après écriture validée : BLOB, FK, triggers, vues, séquences, marqueurs chiffrés restaurés ; inspection des octets / absence en-tête SQLite en clair.
- [ ] Simuler perte IndexedDB sur **profil/test synthétique** avec archive hors navigateur réellement enregistrée ; vérifier restauration sur un autre appareil/profil après authentification et refus mauvais passphrase, wrong-scope et fichier corrompu.
- [ ] Tester annulation du sélecteur, fichier hors limite, manque de quota, fermeture pendant import, fichier déjà existant, autorisation de téléchargement / restauration hors-ligne, navigation background / foreground.
- [ ] Refuser certification si des données restent accessibles après logout, si le fichier partiel est remplacé sans approbation ou si une entrée plaintext est créée.

**Risque principal restant :** même un scénario WebKit 10/10 vert n'élimine ni l'éviction de stockage mobile, ni le seuil pilote d'archive 16 Mio (format JSON base64 mémoire), ni les risques XSS et de coordination des writers historiques.

**No-go permanent :** `AppDatabase.forPatientVault` ne doit pas être activé, aucune migration réelle, merge ou déploiement Vercel sans autorisation explicite et revue indépendante sécurité/clinique.
