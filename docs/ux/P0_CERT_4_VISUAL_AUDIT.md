# P0-CERT-4 — Audit visuel initial et registre canonique

## Statut

- **LOT** : P0-CERT-4.0
- **Type** : audit et arbitrages UX
- **État** : prêt pour revue
- **Branche** : `cert/p0-cert-4-visual-audit`
- **Base auditée** : `main` au commit `1e00938efd12b742e15c21840f3faf58f4de1973`
- **Source de preuve** : `docs/ux/P0_CERT_3_CAPTURE_MATRIX.md`
- **Périmètre** : 25 captures, cinq parcours, français/arabe, desktop, tablette, mobile et petit écran
- **Code produit modifié** : aucun

## Objectif

Transformer l'audit visuel issu de P0-CERT-3 en référence technique et produit vérifiable avant toute correction. Le présent document fixe :

1. le score initial ;
2. les défauts observés ;
3. leur priorité ;
4. les décisions produit approuvées ;
5. l'ordre d'exécution ;
6. les critères d'acceptation et de recertification.

Aucune correction UX ne doit être intégrée à ce LOT.

---

## 1. Verdict initial

IAmina possède déjà une identité visuelle cohérente, propre et crédible. L'expérience mobile est actuellement plus convaincante que l'expérience desktop et tablette.

La certification UX finale n'est pas encore accordée. Le défaut bloquant principal est la localisation arabe incomplète : la structure RTL fonctionne, mais plusieurs écrans, actions et états restent partiellement en français.

## 2. Score de référence

| Axe | Score initial |
|---|---:|
| Cohérence visuelle | 8,2 / 10 |
| Simplicité | 7,8 / 10 |
| Lisibilité mobile | 8,1 / 10 |
| Adaptation desktop/tablette | 6,7 / 10 |
| Navigation | 7,5 / 10 |
| Localisation arabe / RTL | 6,2 / 10 |
| Confiance médicale et clarté | 7,6 / 10 |
| **Score UX global provisoire** | **7,4 / 10** |

Ces scores sont des indicateurs de suivi. La certification ne peut pas être obtenue par moyenne si un défaut P0 reste ouvert.

## 3. Registre canonique des défauts

| ID | Priorité | Famille | Constat | Risque utilisateur | LOT correctif |
|---|---|---|---|---|---|
| UX-A01 | P0 | Arabe / RTL | Des textes français restent visibles en mode arabe | Perte immédiate de confiance et expérience MENA incohérente | P0-UX-6 |
| UX-A02 | P1 | Desktop / tablette | Contenu trop étroit, espace vide important, interface mobile centrée | Sous-exploitation de l'écran et hiérarchie faible | P0-UX-7 |
| UX-A03 | P1 | Navigation mobile | Plusieurs icônes principales n'ont pas de libellé permanent | Destinations ambiguës et charge d'apprentissage | P0-UX-8 |
| UX-A04 | P1 | Petit écran | Actions flottantes susceptibles de se superposer à 360×560 | Actions cachées ou difficiles à atteindre | P0-UX-9 |
| UX-A05 | P1 | Import | Chevauchement conceptuel apparent entre « Importer » et « Pulper » | Choix incompréhensible et parcours fragmenté | P0-UX-10 |
| UX-A06 | P1 | Premier usage | Dashboard trop vide sans guidage initial suffisant | L'utilisateur ne sait pas quoi faire ensuite | P0-UX-11 |
| UX-A07 | P2 | Profil | Page très longue avec hiérarchie et regroupement progressif insuffisants | Recherche d'information lente et surcharge cognitive | P1-UX-12 |
| UX-A08 | P2 | Terminologie | Termes techniques ou internes : Pulper, CGM, AGP, traitement externe contrôlé | Compréhension réduite hors public expert | P1-UX-13 |
| UX-A09 | P2 | Densité | Certains écrans manquent de densité ou de structure sur grand format | Impression d'inachèvement | P2-UX-14 |
| UX-A10 | P2 | Polish | Espacements, alignements et états visuels à harmoniser | Cohérence perçue inférieure au niveau clinique attendu | P2-UX-14 |

## 4. Décisions produit approuvées

### D1 — Arabe intégral avant certification

**Décision : A — approuvée.**

La certification finale exige :

- aucun texte français visible en mode arabe, hors marques ou noms propres explicitement autorisés ;
- traduction des boutons, menus, badges, états vides, erreurs, aides, confirmations, placeholders et infobulles ;
- maintien possible des marques `IAmina`, `Dexcom` et `LibreLink` ;
- explication arabe des acronymes médicaux lorsque nécessaire ;
- test RTL réel sur les cinq parcours ;
- gate automatisé pour les clés manquantes, fallbacks, chaînes codées en dur et résidus français.

### D2 — Responsive desktop et tablette

**Décision : A — approuvée.**

Adopter une vraie composition responsive : contenu principal plus large, grille à deux colonnes lorsque pertinente, panneau secondaire utile, largeur de lecture maîtrisée et aucune simple extension artificielle des cartes mobiles.

### D3 — Navigation mobile explicite

**Décision : A — approuvée.**

Les destinations principales doivent afficher une icône et un libellé permanent, avec un état actif explicite.

### D4 — Importer et Pulper

**Décision : A — approuvée.**

Inspecter les comportements réels avant de modifier l'interface :

- fusionner les fonctions si elles se chevauchent ;
- sinon renommer « Pulper » par un terme décrivant son résultat ;
- conserver un seul point d'entrée principal.

### D5 — Dashboard vide

**Décision : A — approuvée.**

Créer un premier usage guidé avec une explication courte, une action principale, une action secondaire facultative, aucune donnée fictive et une distinction explicite entre état vide, chargement et erreur.

### D6 — Profil progressif

**Décision : A — approuvée.**

Regrouper le profil en sections thématiques et appliquer une divulgation progressive : informations personnelles, données médicales, appareils et intégrations, confidentialité, préférences et actions sensibles.

### D7 — Terminologie compréhensible

**Décision : A — approuvée.**

Présenter le libellé compréhensible en premier et le terme médical ou l'acronyme en complément. Aucune simplification ne doit altérer le sens clinique.

### D8 — Ordre d'exécution

**Décision : A — approuvée.**

1. arabe et RTL ;
2. desktop et tablette ;
3. navigation mobile ;
4. petit écran ;
5. Importer / Pulper ;
6. dashboard premier utilisateur ;
7. profil ;
8. wording et polish ;
9. recertification finale.

---

## 5. Lots correctifs et critères d'acceptation

### P0-UX-6 — Arabe intégral et RTL

Critères de sortie :

- zéro chaîne française non autorisée dans les parcours arabes certifiés ;
- zéro clé i18n manquante visible ;
- aucun fallback involontaire vers le français ou l'anglais ;
- ordre RTL, alignements, marges et icônes directionnelles vérifiés ;
- états vides, erreurs, chargements, confirmations et aides traduits ;
- gate automatisé vert ;
- preuves visuelles FR/AR sur les formats requis.

### P0-UX-7 — Desktop et tablette

Critères de sortie :

- mise en page réellement responsive ;
- utilisation utile de la largeur disponible ;
- formulaires et contenus longs limités à une largeur lisible ;
- absence de grand vide structurel injustifié ;
- aucun débordement aux formats desktop et tablette certifiés.

### P0-UX-8 — Navigation mobile

Critères de sortie :

- chaque destination principale est compréhensible sans mémoriser son icône ;
- libellés permanents et état actif explicite ;
- cohérence FR/AR ;
- zones tactiles et lecteur d'écran vérifiés.

### P0-UX-9 — Petit écran 360×560

Critères de sortie :

- aucune superposition entre contenu, navigation et actions flottantes ;
- aucune action inaccessible ;
- clavier, modal, snackbar, menu et textes arabes longs vérifiés ;
- scroll final complet et zones tactiles utilisables.

### P0-UX-10 — Importer / Pulper

Critères de sortie :

- comportement réel des deux parcours documenté ;
- responsabilités et résultats utilisateur comparés ;
- décision de fusion, déplacement ou renommage fondée sur le code réel ;
- un point d'entrée principal clairement identifiable ;
- aucune promesse d'import ou de traitement non réalisée.

### P0-UX-11 — Dashboard premier utilisateur

Critères de sortie :

- distinction véridique entre vide, chargement, erreur et hors connexion ;
- prochaine action évidente ;
- aucune métrique ou donnée fictive présentée comme réelle ;
- rendu utile sur mobile, desktop et RTL.

### P1-UX-12 — Profil progressif

Critères de sortie :

- sections thématiques explicites ;
- éléments secondaires regroupés ou repliables sans cacher les informations critiques ;
- actions sensibles distinguées ;
- ordre de lecture, clavier et RTL cohérents.

### P1-UX-13 — Wording médical et produit

Critères de sortie :

- vocabulaire compréhensible en premier ;
- acronymes expliqués lorsque nécessaire ;
- cohérence terminologique FR/AR ;
- validation que la simplification ne modifie pas le sens clinique.

### P2-UX-14 — Densité et polish

Critères de sortie :

- espacements, alignements, rayons, ombres et états harmonisés ;
- aucune correction cosmétique ne masque un problème fonctionnel ;
- comparaison avant/après documentée.

---

## 6. Matrice minimale de recertification

Les cinq parcours de référence doivent être contrôlés en français et en arabe sur :

| Format | Résolution de référence | FR | AR |
|---|---:|:---:|:---:|
| Desktop | résolution P0-CERT-3 ou équivalent documenté | requis | requis |
| Tablette | résolution P0-CERT-3 ou équivalent documenté | requis | requis |
| Mobile | 390×844 | requis | requis |
| Petit écran | 360×560 | requis | requis |

Minimum : **5 parcours × 2 langues × 4 formats = 40 combinaisons**.

Les captures statiques doivent être complétées par les états pertinents :

- premier usage ;
- données existantes ;
- chargement ;
- erreur ;
- hors connexion ;
- synchronisation ;
- import ;
- confirmation ;
- contenu long ;
- clavier ouvert ;
- RTL.

## 7. Gates obligatoires des lots applicatifs

Selon le périmètre réellement modifié :

- Flutter analyze ;
- tests Flutter ciblés et suite pertinente ;
- backend SQLite ;
- backend PostgreSQL ;
- migration drift ;
- Ruff ;
- import-linter / architecture ;
- anti-bypass ;
- Bandit ;
- OpenAPI ;
- contrôle des secrets ;
- vérification du diff ;
- captures avant/après ;
- preuve du comportement réel.

Un lot documentaire comme P0-CERT-4.0 ne prétend pas valider les suites applicatives qu'il ne modifie pas.

## 8. Cibles de certification

| Axe | Initial | Cible minimale |
|---|---:|---:|
| Cohérence visuelle | 8,2 | 8,5 |
| Simplicité | 7,8 | 8,3 |
| Lisibilité mobile | 8,1 | 8,5 |
| Desktop/tablette | 6,7 | 8,0 |
| Navigation | 7,5 | 8,2 |
| Arabe/RTL | 6,2 | 8,5 |
| Confiance médicale | 7,6 | 8,3 |
| **UX globale** | **7,4** | **≥ 8,2** |

Conditions supplémentaires :

- aucun défaut P0 ouvert ;
- aucune action principale trompeuse ou inaccessible ;
- aucune donnée clinique fabriquée ;
- preuves visuelles et tests associés disponibles ;
- recertification P0-CERT-5 validée.

## 9. Définition de terminé — P0-CERT-4.0

Le LOT est terminé lorsque :

- le registre des défauts est versionné ;
- les huit décisions sont enregistrées ;
- chaque famille de défaut possède un LOT correctif et un critère d'acceptation ;
- la matrice de recertification est définie ;
- aucune correction applicative n'est mélangée au LOT ;
- le diff documentaire est relu ;
- la PR est approuvée et mergée.

## 10. Prochain LOT

`P0-UX-6 — Arabe intégral et RTL certifiable`.

Avant modification, ce LOT devra inventorier le système i18n réel, les chaînes codées en dur, les fallbacks, les composants partagés et les tests existants. Il ne devra pas créer de mécanisme parallèle si l'infrastructure actuelle peut être étendue.
