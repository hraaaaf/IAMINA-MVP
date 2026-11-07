# IAMINA — W03 Web : bouton compagnon flottant premium — candidature 07/11/2026

## Décision propriétaire / périmètre
La première proposition « CTA intégré uniquement » a été abandonnée après itérations visuelles. Le propriétaire a **validé explicitement** le mockup créé sur les pixels réels de Chrome 390×844 : `/mnt/data/IAMINA_MOCK_FAB_SATINE_VRAI_DASHBOARD_390x844.png`. Cette référence est uniquement un visuel, pas une capture d'implémentation. Le bouton cible est **58 px**, émeraude satiné et bulle crème à trois points ; sans feuille, cerveau ni dorure marquée. Garder les cartes, données, rappels et navigation existants.

## GOAL / SUCCESS / PROOF
- **GOAL :** un seul bouton flottant compagnon reconnaissable et premium, sans doublon dans Dashboard.
- **SUCCESS :** route `/companion/chat` ; bouton visible en FR/EN/AR et côté logique RTL ; action touch/keyboard/semantics, diamètre 58 dp. **Zéro interception ou masquage des cartes même quand on fait défiler**.
- **Mécanique candidate :** FAB dans une petite zone inférieure réservée et non scrollable au-dessus de MainShell.bottomNavigationBar ; le viewport des cartes s'arrête au-dessus (pas de Positioned overlay). Le rendu devra être confronté au mockup ; contrôler qu'il ne crée pas de rupture visuelle et qu'il ne réduit pas excessivement l'espace utile.
- **PROOF :** CI/flutter test & analyze au commit exact, screenshots Chrome avant/après sur même viewport/locale/état, FUE browser FR/AR 390×844/768×1024/1280×900, avec/sans mesures, keyboard et scroll, revue adversariale, scores selon QUALITY_SCORING_POLICY.
- **Non-scope :** aucune logique médicale, auth, API, persistance, conversation ou déploiement.
- **Statut actuel :** DESIGN_VALIDATED / CODE_CANDIDATE / NOT_VERIFIED / NOT_DEPLOYED. **Pas de merge ni Vercel sans réussite des gates appropriés**.

## Matrice FUE non certifiée
| Cas | État | Formats | Locales | Preuve |
|---|---|---|---|---|
| A | avec mesures synthétiques | 390/768/1280 | FR/AR | NOT_RUN |
| B | sans mesures | 390/768/1280 | FR/AR | NOT_RUN |
| C | scroll + focus + route | 390/768/1280 | FR/AR | NOT_RUN |
| D | chargement et données indisponibles | utile | FR/AR | NOT_RUN |

Le localStorage historique D27 n'est pas lu/écrit, et n'est pas effacé.

## Complément FUE navigateur — lancé après validation du design
Instrumentation ajoutée dans l'entrée de certification isolée `ui_dashboard_backend_cert_main.dart` : test possible des locales FR/AR réelles avec route de destination *strictement factice pour CI* (ne modifie pas la page de chat produit). `dashboard_capture.js` doit désormais tester dans Chrome les **3 viewports × FR/AR** sur une identité synthétique sans données, capture AR, position avant/après scroll, cible accessible ≥44px, et activation du FAB par clavier Entrée. Le widget test dédié doit vérifier tap, Tab+Entrée, RTL, et géométrie stable pendant le scroll. **Ne compter que les CI/artefacts SUCCESS au nouveau SHA, pas les anciens.** Vérifier particulièrement la capture arabe : glyphes/RTL, disparition de CTA doublon et navigation non interceptée. Aucun déploiement Vercel.
