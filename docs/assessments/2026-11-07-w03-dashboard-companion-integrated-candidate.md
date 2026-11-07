# IAMINA — W03 Dashboard compagnon intégré — candidature 07/11/2026

## Décision (remplace le choix visuel D27 sur Home)
L'audit de Chrome instrumenté 390×844 sur `main@fba8e36a3ea08aae55a737ad12e8d75632b3f781` a démontré une surcouche ChatBrain qui masque « Tendance » (mesures synthétiques) et le lien « Mes rappels » (état vierge). Jugement initial : flottant 3/10, Dashboard sans lui 7/10. Le propriétaire reprend explicitement ce lot le 07/11/2026. Cette modification retire volontairement le déplacement D27 du launcher Home ; la page de conversation est hors périmètre.

## GOAL / SUCCESS / PROOF
- **GOAL** : un compagnon identifié par son nom et son utilité, sans bouton flottant ni masquage du suivi.
- **SUCCESS** : Dashboard avec mesure : une unique CTA intégrée sous « À retenir aujourd’hui » ; sans mesure : CTA secondaire après les rappels, « Ajouter ma première mesure » demeure l'action primaire ; toutes redirigent vers `/companion/chat` ; libellés FR/EN/AR, RTL, clavier et touch ; 0 superposition sur 390×844, 768×1024, 1280×900.
- **PROOF requise** : captures BEFORE (workflow de l'audit), AFTER sur même état/vue, test des deux CTA, 100 % FUE Web FR/AR aux trois viewports, CI et revue adversariale sur SHA exact, scores selon `docs/QUALITY_SCORING_POLICY.md`.
- **Non-scope** : aucune logique glycémique, auth, serveur, consentement, moteur IA, conversation, règle médicale ou déploiement.
- **Limite clinique** : le texte de CTA ne présume aucun accès ni analyse de données absentes.
- **Retrait historique** : le localStorage `iamina.d27.fab.position.v1` peut subsister chez d'anciens utilisateurs ; il n'est plus lu, écrit ni utilisé dans le Dashboard, et il n'est pas effacé pour éviter une mutation implicite.
- **Statut initial** : CANDIDATE / NOT_VERIFIED / NOT_DEPLOYED. La preuve AFTER, CI et FUE exact HEAD restent à collecter avant tout verdict, merge et closeout.

## FUE — matrice à compléter
| Cas | État | Viewports | Locale | Action | Preuve |
|---|---|---|---|---|---|
| A | 1+ mesures synthétiques | 390×844,768×1024,1280×900 | FR,AR | CTA « Poser une question », retour/navigation | NOT_RUN |
| B | 0 mesure | idem | FR,AR | première mesure prioritaire, rappel et CTA secondaire cliquables | NOT_RUN |
| C | A+B | idem | FR,AR | absence de recouvrement, scroll, keyboard, RTL, accessible focus | NOT_RUN |
| D | chargement/erreur données | pertinent | FR,AR | aucune action mensongère / fuite de données | NOT_RUN |

Aucun résultat non exécuté n'est compté PASS. Captures originales détaillées dans le hub Notion « Audit UX visuel ChatBrain / Dashboard » (07/11/2026).
