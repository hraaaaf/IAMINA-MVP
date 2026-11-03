# IAMINA — D3 Web : Mes rappels sur Accueil

Date : 2026-11-02. Base vérifiée : `main@9570e4c695844aa7dd5e79d9da0e80d4b8c7dc5c`.
Branche : `feat/d3-web-my-reminders-20261102`.
État : **CANDIDAT — tests et preuve navigateur à certifier**. Aucune Preview/Production déployée dans ce lot.

## Décision / Goal / Succès / Preuve
**Décision D3 (registre du 08/10, option A)** : remplacer `Your next step` sur l'Accueil par **Mes rappels**, 2 à 3 prochaines échéances réelles et ordonnées, **Voir tout** ouvrant la liste, **Aucun rappel configuré** → **Créer un rappel**. Rappels planifiés distincts des notifications proactives/cloche (D2).

**Goal** : un bloc réellement branché au coffre local sélectionné, sur Home à la place de l'ancien bloc de prochaine action, sans décaler la Tendance initiale, ni données démo ou réseau.

**Succès attendu** :
- Home avec mesures : Tendance → Insights → Mes rappels (mobile) ; Tendance → Insights + Mes rappels côte à côte (desktop). Home sans mesure : carte après la première mesure CTA, sans faux patient.
- Vrais rappels **activés** et de date future (limite 3) par `dueAt` croissant, puis `id` ; titre et échéance lisibles en FR/EN/AR et RTL.
- Si aucun enregistré : état vide et **Créer un rappel**, avec bouton **Voir tout**. Si uniquement passés/inactifs : aucun « à venir » inventé.
- Navigation réelle vers `/reminders`, accessible au clavier, touch, focus. La source est `AppDatabase.watchReminders()`, et le `StreamBuilder` est réinitialisé par `ObjectKey(database)` lors d'un changement de coffre A→B→A.

**Preuve exigée** : Flutter analyze/tests/build PWA SHA exact ; tests A→B→A, filtrage/tri/limite3, état vide/navigation, FR/EN/AR ; capture BEFORE→AFTER Chrome vraie Home aux mêmes 390×844 / 768×1024 / 1280×900 FR/AR ; contrôle visuel et accessibilité, recette Preview autorisée par le propriétaire ; puis merge, postmerge, Production sur autorisation distincte.

## BEFORE / référence / AFTER
**BEFORE réel code** : `dashboard_responsive_sections.dart` contient `DashboardTrendSection`, `DashboardInsightSection`, `DashboardNextActionSection` ; dernier propose `Your next step` sous forme d'action évaluée. L'ancienne PR D3 #1137 introduit *seulement* un compteur de rappels **après** les sections, donc ne remplace pas `Your next step` ni ne montre 2–3 échéances ; elle n'est pas fusionnée.

**Mockup approuvé / cible** : garder Tendance inchangée, puis dans l'emplacement de l'ancien bloc `Your next step`, une carte sobre **Mes rappels** (icône agenda, bouton **Voir tout** en haut à droite), lignes « Titre du rappel — date + heure », maximum trois. Carte vide « Aucun rappel configuré » + « Créer un rappel ». En largeur ≥760, carte adjacente à Insights ; sous 760, carte sous Insights. Sur Home vierge, carte indépendante placée sous la CTA première mesure.

**AFTER code candidat** :
- `dashboard_my_reminders_card.dart` : cartes réelle/locale, 0/1/2/3 prochaines échéances, state loading/error, action gestion, FR/EN/AR/RTL, adaptation patient.
- `dashboard_responsive_sections.dart` : remplacement de `DashboardNextActionSection` en conservant Tendance/Insight ;
- `dashboard_premium_screen.dart` : accès aux rappels même sans relevé glycémique ;
- tests ciblés `dashboard_my_reminders_card_test.dart`.

## Limites / sécurité
Le schéma `ReminderData` actuel contient `title`, `dueAt`, `enabled`, `createdAt` uniquement. **Aucun champ d'accomplissement ni règle de récurrence** : l'application ne peut pas marquer une occurrence accomplie ni calculer la suivante sans une évolution de schéma et décision dédiée ; ne rien inventer. Échéances affichées à l'heure locale du navigateur avec `toLocal()`. Les titres sont visibles sur l'Accueil à la demande explicite du propriétaire ; aucun push, écran verrouillé, démo, backend ni API externe ajoutés. Un futur audit de confidentialité doit considérer le partage d'écran/appareil et le verrou local, hors du périmètre du présent écran.

**D2** : la cloche de l'ancien header route encore vers `/reminders` ; c'est une dette distincte D2 (l'utilisateur a décidé de réserver la cloche aux notifications). Ne pas affirmer D2 corrigée. Ne pas modifier les décisions D12, D13, D18 ni D22.

## Gates / Next
- Vérifier CI sur le commit exact, diagnostiquer et corriger tout échec sans supprimer une assertion.
- Capturer BEFORE/AFTER avec la vraie **carte** NextAction (baseline) vs la vraie **carte** Mes rappels (candidate) dans un harnais navigateur isolé, FR/AR et mêmes viewports ; **ne pas présenter ces images comme une comparaison de Home complet**. La présence/position dans Home est vérifiée séparément par les tests Dashboard/P7. Attribuer score seulement après lecture réelle des 12 images.
- Exiger autorisation explicite **Preview** avant tout Vercel et recette utilisateur ; aucune production par défaut.
- Traiter les PR D3 antérieures #1085 et #1137 comme candidates historiques / supplantées seulement après validation du nouveau candidat.

## Suivi CI et preuve Chrome — 02/11/2026 23:44 UTC
- Premier run Chrome [#41546944191](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41546944191) sur `744c037130d577b64558a77085d51d8cecfc90f4` : **FAILURE** après compilation Web BEFORE+AFTER réussie. 11 captures ont passé les contrôles de taille, la 12e (`after-ar-1280x900.png`) mesure 1280×900 mais seulement **5 289 octets**, sous le seuil strict de 10 000 ; la capture est donc **refusée**, sans score ni certification. Les 12 fichiers ont été archivés par `if: always()` (artifact `13189263384`), mais ils doivent encore être réellement examinés avant toute conclusion visuelle.
- Correction ciblée du harnais dans `549abcb68f5a0796a6065ac99b602ef2b19d8a7f` : quatre tentatives bornées par viewport avec rechargement Chrome entre captures invalides ; **maintien** de l'exigence dimensions exactes + PNG ≥10 000 octets, et contrôle supplémentaire de diversité de couleurs (≥24 couleurs distinctes). Aucun relâchement des assertions produit ; si la capture reste blanche ou incomplète, le gate échoue encore. Le diagnostic « rasterisation transitoire » est une hypothèse à vérifier sur le nouveau run, pas une cause démontrée.
- Sur l'ancien HEAD, P7 [#41546944133](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41546944133) et P5-5 [#41546944119](https://github.com/hraaaaf/IAMINA-MVP/actions/runs/41546944119) ont abouti **SUCCESS** après les corrections `ce1aa465` / `d34d14b9`. Les autres workflows et la preuve du HEAD corrigé restent à certifier.
- Aucune Preview/Production Vercel ni merge. Récurrence et statut accompli absents du schéma `ReminderData`.

## 03/11/2026 — D3 bug de production : deuxième rappel inaccessible via le raccourci d'ajout

**Signalement utilisateur sur le vrai site Production** : après la création d'un premier rappel, le bouton d'ajout (création d'un autre rappel), **pas le bouton de validation « Ajouter le rappel »**, ne fonctionne plus.

**Constat déterministe dans le code de production** `main@578250e21e798c6f1b9ea52a23678f2ed8c03be8` : `DashboardMyRemindersCard` ne rend `Créer un rappel` **que si** `upcoming.isEmpty`. Au premier rappel futur, `upcoming.isNotEmpty`, le CTA disparaît de l'Accueil. Le lien `Voir tout` continue de mener à `/reminders`, où un formulaire d'ajout existe. C'est une faille UX reproductible par inspection du code ; aucun problème d'écriture Drift ni dysfonctionnement du bouton de validation n'est encore démontré.

**Goal du correctif** : rendre **+ Ajouter un rappel** accessible en permanence dans l'en-tête de la carte Accueil, y compris après 1, 2, 3+ rappels. Garder « Voir tout » et, si vide, le bouton explicite « Créer un rappel ». L'action + doit ouvrir `/reminders` avec le formulaire visible. Ne toucher ni aux traitements cliniques, ni à la DB, ni à la notification OS.

**BEFORE** : carte « Mes rappels » avec seulement « Voir tout » après le premier événement ; l'appel à l'ajout est absent. **Référence / mockup cible** : `[icône] Mes rappels              [+]  Voir tout`, puis les échéances ; + icône 44×44, tooltip et nom accessibles localisés FR/EN/AR, logique RTL par la Row Flutter. **AFTER candidat** : `dashboard_my_reminders_card.dart` rend le + au niveau du header indépendamment du nombre de rappels et renvoie à la même route `/reminders` ; le CTA vide reste intact.

**Test de non-régression ajouté** : vrai `RemindersScreen` dans un GoRouter widget à largeur iPhone 390×844, FR/AR/EN, avec AppDatabase Drift en mémoire : carte vide → créer premier → retour Accueil → + encore activé → créer deuxième → les deux titres sauvegardés et affichés, absence d'exception. Les tests précédents filtrage/ordre/limite3/vault A→B→A sont maintenus. La preuve réelle de ce comportement dépend de l'exécution Flutter CI sur le nouveau SHA, **pas encore validée** à ce stade.

**Source historique D3** : PR #1229 fusionnée, propriétaire avait validé visuel initial, Vercel Frontend Production READY `dpl_4r1pYYKJZZFNUV8HmdvuqAnMH4jD` sur `578250e`. **Le nouveau fix n'est pas encore en Production** et requiert certification + revue visuelle FR/AR mêmes viewports + autorisation explicite de redéploiement Vercel avant une nouvelle release. Aucune nouvelle Preview demandée ni déployée. Clôture D3 suspendue tant que le raccourci d'ajout n'est pas réparé et confirmé sur iPhone.

**Next exact** : ouvrir PR de correctif → CI exact SHA / tests create1→create2 et visual Chrome FR/AR x 390/768/1280 → score fondé sur captures → GO Vercel Production dédié si nécessaire → deploy + vraie recette iPhone → closeout Notion et doc.
