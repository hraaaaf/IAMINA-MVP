# P0-UX-6 — Audit technique i18n / arabe / RTL

## Statut

- LOT : P0-UX-6.0
- Type : audit technique préalable
- Base auditée : `main` au commit `9218ef153ea713b9c60dff273df8f80a45362d4e`
- Code produit modifié : aucun

## Verdict

L'infrastructure Flutter de localisation existe, avec ARB `fr`, `en`, `ar`, `AppLocalizations`, les delegates Flutter et une locale pilotée par `LocalePreferenceService`.

Cependant, l'application n'est pas certifiable en arabe dans son état actuel. Le système est fragmenté entre :

1. les fichiers ARB générés ;
2. une couche parallèle manuelle `AuditedPageCopy` ;
3. de nombreuses chaînes visibles codées en dur ;
4. un onboarding entièrement français qui force la langue `fr` ;
5. un fallback runtime explicite vers le français.

Le défaut P0 est donc confirmé par le code, pas seulement par les captures.

## Constats canoniques

| ID | Priorité | Constat | Preuve code | Conséquence |
|---|---|---|---|---|
| I18N-01 | P0 | Fallback runtime vers le français | `LocalePreferenceService` initialise et échoue vers `Locale('fr')` | Résidu français garanti si API indisponible |
| I18N-02 | P0 | Onboarding entièrement codé en français | `onboarding_chat_screen.dart` | Signup arabe impossible |
| I18N-03 | P0 | Onboarding force `preferredLanguage: 'fr'` | `_finish()` | Préférence choisie ignorée |
| I18N-04 | P0 | Aucun choix distinct langue/pays/ton local dans l'onboarding | modèle `_userData` actuel | Décisions produit 2–4 non implémentées |
| I18N-05 | P0 | Couche i18n parallèle `AuditedPageCopy` | `l10n/audited_page_copy.dart` | Deux sources de vérité, gate incomplet |
| I18N-06 | P0 | Erreur de rendu principale en français avec détail technique visible | `main.dart` | Violation décisions 17 et 22 |
| I18N-07 | P1 | Locales régionales absentes | seuls `app_ar.arb`, `app_fr.arb`, `app_en.arb` | pas de `ar-MA`, `ar-EG`, `ar-SA` |
| I18N-08 | P1 | Persistance locale avant connexion non démontrée | service dépend de l'API profil | décision 10 non couverte |
| I18N-09 | P1 | Modification immédiate langue/pays/ton non démontrée | service lecture seule (`refresh`) | décision 9 non couverte |
| I18N-10 | P1 | Gate CI spécifique i18n/RTL non identifié | CI actuelle générique | régressions possibles |
| I18N-11 | P1 | Tests RTL/accessibilité/golden non identifiés | audit repo | certification non prouvée |
| I18N-12 | P2 | Textes médicaux mélangés avec acronymes sans politique structurée | ARB + copie manuelle | cohérence clinique fragile |

## Architecture existante à conserver

- `frontend/l10n.yaml`
- `frontend/lib/l10n/app_fr.arb`
- `frontend/lib/l10n/app_en.arb`
- `frontend/lib/l10n/app_ar.arb`
- `AppLocalizations`
- delegates Flutter officiels
- `LocalePreferenceService`, à étendre plutôt qu'à remplacer
- API `/api/v1/profile/locale`, si son contrat reste compatible avec les décisions approuvées

## Architecture à supprimer progressivement

`AuditedPageCopy` ne doit pas devenir une deuxième infrastructure permanente. Son contenu utile doit être migré vers les ARB, puis tous les consommateurs doivent utiliser `AppLocalizations`.

## Découpage recommandé du LOT

### P0-UX-6.1 — Source de vérité unique

- migrer la copie auditée vers ARB ;
- remplacer les appels `AuditedPageCopy` ;
- interdire les nouvelles chaînes visibles codées en dur ;
- conserver une seule infrastructure i18n.

### P0-UX-6.2 — Onboarding localisation

- demander séparément langue, pays/région et ton local facultatif ;
- proposer une valeur par défaut selon la région ;
- ne plus forcer `fr` ;
- persister avant connexion puis synchroniser après connexion ;
- séparer textes cliniques standards et microcopies locales.

### P0-UX-6.3 — Fallback et contrat backend

- remplacer le fallback français par la chaîne stricte `ar-MA → ar → erreur de test` ;
- conserver des codes backend structurés, sans texte utilisateur brut ;
- ajouter des méthodes d'écriture et résolution de conflit dans le service de préférences.

### P0-UX-6.4 — RTL et composants techniques

- RTL structurel ;
- LTR explicite pour valeurs, e-mails, URLs, codes et axes temporels ;
- textes longs, taille agrandie et 360×560 ;
- accessibilité et ordre de lecture.

### P0-UX-6.5 — Gate CI et recertification

- parité de clés ARB ;
- détection des chaînes visibles codées en dur ;
- détection des fallbacks interdits ;
- widgets en arabe ;
- golden tests des cinq parcours ;
- captures FR/AR sur quatre formats ;
- double revue linguistique et clinique documentée.

## Ordre d'exécution

1. source de vérité unique ;
2. onboarding et persistance ;
3. fallback/contrat backend ;
4. RTL/accessibilité ;
5. gate CI et preuves.

## Critère de sortie

P0-UX-6 reste ouvert tant que les cinq parcours ne sont pas intégralement traduits, sans résidu français, avec RTL, accessibilité, textes longs, gate CI, captures et double revue documentés.
