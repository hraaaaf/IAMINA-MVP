# IAMINA D18 Web — Étape 5/6 : matrice Safari / WebKit, 03/11/2026

**Décision et Goal.** Avant tout cutover clinique, vérifier la compatibilité du connecteur chiffré et de la restauration du coffre entier sur les navigateurs Web pris en charge, en distinguant le moteur WebKit Linux de l'iPhone Safari réel. **Zéro donnée patient réelle.**

## Preuves automatiques attendues

- **Chromium** : benchmark de référence PR #1235, 10/10 phases source A → archive chiffrée hors navigateur → cible B vierge, crash/quarantaine, clés et scopes invalides, aucun overwrite, redémarrage, parité octets/schéma. Dernière preuve valide sur CODE SHA `baf25129`, run #41635184362 SUCCESS ; run documentaire #41635800820 SUCCESS.
- **WebKit mobile simulé** : GitHub Actions avec véritable moteur WebKit Playwright 1.55, viewport 390 × 844, DPR 3, tactile simulé. Les mêmes 10 assertions doivent passer, sous `D18_RESTORE_BROWSER=webkit`, sans retries, fallback sqlite3.wasm ou downgrade des garanties de lock/crypto. L'échec des primitives `navigator.locks`, IndexedDB ou WebAssembly doit rester **NO-GO**, non contourné par un test en mémoire.
- **Restauration** : worker CI dédié sous verrou exclusif ; mauvais fichier/passphrase/scope et mauvaise DEK refusés ; octets persistés comparés, source préservée ; un import interrompu conserve un fichier partiel inaccessible et ne doit jamais être automatiquement ré-enrôlé.

## Gate humain séparé — iPhone Safari physique

À réaliser uniquement avec un compte et une base *synthétiques*. Une émulation WebKit Linux ne valide ni iOS Safari, ni les restrictions d'onglet arrière-plan, ni l'éviction de stockage d'iOS.

- [ ] Sur un véritable iPhone Safari, utiliser une URL Preview **uniquement après autorisation explicite** de déploiement, en environnement de test séparé du coffre clinique non chiffré.
- [ ] Noter version iOS/Safari, taille écran, état connexion/réseau, paramètres stockage, mode normal/privé.
- [ ] Créer le coffre synthétique A, verrouiller et déconnecter ; ouvrir B ; revenir à A sans voir de données B.
- [ ] Refuser mauvais mot de passe/code recovery ; vérifier absence de repli en SQLite en clair.
- [ ] Exporter un vrai **fichier externe** de sauvegarde chiffrée complète ; vérifier ouverture de la sauvegarde depuis Fichiers iOS et refus de fichier modifié ou de mauvais scope.
- [ ] Quitter Safari complètement puis revenir ; vérifier réouverture avec clé locale, intégrité et enregistrements synthétiques.
- [ ] Restaurer dans un profil/environnement effectivement neuf avec une procédure validée ; vérifier source inchangée et refus d'écraser une destination.
- [ ] Répéter en Wi-Fi et mode hors ligne ; vérifier panne, interruption pendant écriture, verrouillage iOS et retour depuis arrière-plan.
- [ ] Tester stockage presque plein, éviction contrôlée, quotas et sauvegarde indépendante ; aucune promesse de récupération sans fichier sauvegardé.
- [ ] Capturer écrans et observations FR/AR RTL sur largeurs 390 et 768 si pertinentes ; comparer au baseline des profils (pas d'affirmation visuelle sans BEFORE/AFTER).
- [ ] Revue indépendante sécurité/crypto/XSS/CSP, politique de suppression d'un fichier partiel et code review de chaque import/backup.

## Bloqueurs explicites avant release

1. `AppDatabase.forPatientVault` continue d'utiliser `sqlite3.wasm` non chiffré ; les preuves ci-dessus sont **CI synthétiques et non branchées**.
2. Import interrompu = quarantaine fail-closed ; **reprise idempotente avec UX sans effacement clinique non implémentée**.
3. Le codec d'archive actuel borne à 16 Mio ; les coffres cliniques de taille réelle exigent un chemin streaming, quotas et tests de restauration sur plusieurs tailles.
4. Pas de déploiement Vercel, promotion, merge ou activation sans autorisation explicite du responsable.

**Critère de sortie de 5/6 :** test WebKit avec résultat exact et preuves archivées **ET** contrôle réel iPhone validé par humain. Un résultat WebKit vert seul est **partiel**.