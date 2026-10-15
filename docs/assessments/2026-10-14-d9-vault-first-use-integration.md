# D9 — Intégration first-use dans le coffre patient

**État : DRAFT, non déployé, non fusionné.** Branche D9 issue de la base D7, isolée des autres chantiers.

## Goal et preuve requise

**Goal :** sur un nouvel appareil, ne pas répéter l'onboarding d'un compte natif ayant une **preuve serveur explicite** de première utilisation terminée. Une réponse d'un autre patient, une réponse périmée après changement de compte/verrouillage ou une absence d'accès réseau ne peut ni accorder le consentement IA ni inventer un profil clinique.

**Succès observable** : connecté au compte A et après déverrouillage, l'app demande la preuve first-use au serveur et vérifie `owner_user_id == activeScope.nativeDjangoUserId`, l'époque auth, la génération du coffre et le nonce de verrouillage. Seul `completed=true` pour A retire l'obligation de refaire l'onboarding. `completed=false` autorise l'onboarding standard ; la sauvegarde locale explicite est suivie d'un POST minimal et idempotent; si cet ACK échoue, aucune confirmation distante n'est affichée. L'IA reste soumise à son consentement séparé.

## Avant → cible → implémentation → après / UI

**BEFORE (constat code D7) :** `seedInitialProfile(null)` fait considérer le premier usage incomplet et déclenche `/onboarding` avant de consulter la preuve serveur ; ancien compte + coffre vierge reçoit les questions à nouveau. **Aucune capture BEFORE certifiée**.

**Cible / mockup textuel** : avant contenu patient, écran sobre de progression « Vérification sécurisée du compte… ». Si preuve inconnue/réseau indisponible, écran neutre avec « Réessayer » et « Se déconnecter » ; pas d'écran clinique ni de saut d'onboarding. Conserver l'app-lock existant en premier.

**Implémentation D9 isolée** : dans `PatientVaultAppHost`, après ouverture du bon coffre et déverrouillage, transport first-use propriétaire et écran neutre ; `ConsentService` reçoit uniquement une preuve d'onboarding (pas une ligne PatientProfiles). `OnboardingChatScreen` tente l'ACK après sauvegarde locale et n'annonce jamais de synchronisation distante sans succès. Verrouillage/compte A→B→A rend toute ancienne réponse caduque.

**AFTER / preuve en attente** : tests unitaires Flutter de la preuve et contrat de branchement ; CI Flutter PWA + tests de navigation et captures **mêmes viewports 320×640 et 1280×800**. Aucun score visuel tant que la comparaison réelle n'est pas disponible.

## Garde-fous

- Serveur indépendant [#995](https://github.com/hraaaaf/IAMINA-MVP/pull/995), transport indépendant [#996](https://github.com/hraaaaf/IAMINA-MVP/pull/996) : DRAFT non fusionnés. D9 intégration ne les déploie pas.
- Dépendance coffre D7 [#986](https://github.com/hraaaaf/IAMINA-MVP/pull/986) : l'intégration D9 utilise ses abstractions et doit être retestée contre le dernier HEAD D7, pas mergée directement vers `main`.
- **Nouveaux comptes** : si la réponse GET est `completed=false`, montrer l'onboarding ; 401/403/404, échec/timeout, owner absent ou discordant => inconnue, pas d'autorisation.
- **Anciens comptes** : sans preuve serveur D9, rien n'est inféré automatiquement à partir d'un profil médical ou d'un consentement. La stratégie de migration depuis une installation déjà authentifiée exige une décision explicite et une revue sécurité/identité.
- **Off-line** : le coffre déjà localement complété conserve son état local ; un coffre distant vierge et une réponse inconnue restent dans l'écran de vérification, sans données du précédent patient.
- Contrôler également le transport des écritures médicales au moment de la future intégration avec les protections cliniques existantes ; aucune modification D7/D30 effectuée dans ce lot.

**Human gate réel** : revue indépendante sécurité/privacy du flux de compte + preuve sur appareil neuf, vérification CI exacte au HEAD, test A→B→A et conformité visuelle avant fusion. Aucun Vercel sans autorisation.

**Next** : CI de cette branche de validation D9 → corriger si rouge → tests de navigation et scénarios concrets → revue indépendante → rapprochement aux PRs #995/#996/D7 → fusion et postmerge exclusivement après preuves, sinon maintenir DRAFT. Issue D9 #966 reste ouverte.
