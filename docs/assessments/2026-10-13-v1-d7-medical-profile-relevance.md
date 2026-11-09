# IAMINA D7 — Présentation des traitements selon le profil déclaré

## Décision originale et Goal
Registre Notion 8 octobre 2026, option A : profil progressif et modifiable, types type1/type2/gestationnel/prédiabète/autre/inconnu, traitements multiples, personnalisation pédagogique mais aucun ajustement clinique non vérifié.

## BEFORE → Mockup cible
BEFORE main a6284c4... : les deux surfaces (onboarding et profil) proposent la même rangée de choix unique Insuline / Comprimés / Hygiène de vie, quel que soit le type déclaré. Un prédiabète voit l'insuline sans contexte.
CIBLE : garder le style IAMINA et le parcours 5 étapes. Quand type=pre :
- sous « Quel traitement suivez-vous actuellement ? », note « Indiquez uniquement ce que vous suivez réellement. »
- catégorie apparente « Habitudes de vie »
- action discrète « Je suis un autre traitement / Je préfère répondre plus tard »
- uniquement après clic de l'utilisateur, dévoiler médicaments, insuline, autre, inconnu, pour enregistrer un fait réellement déclaré.
Pour type1 insuline en première vue, pour type2 habitudes de vie et médicaments déclarés, pour gestationnel habitudes de vie et insuline ; inconnu et autre : aucune suggestion primaire, saisie manuelle. Aucun traitement pré-rempli. Jamais de recommandation de dose, de modification de traitement, de cible, de diagnostic ou d'alerte.

## Sources cliniques (information non prescriptive)
ADA Standards 2026 prévention https://doi.org/10.2337/dc26-s003
ADA Standards 2026 pharmacologie https://doi.org/10.2337/dc26-s009
ADA Standards 2026 grossesse https://doi.org/10.2337/dc26-S015
NICE PH38 prévention https://www.nice.org.uk/guidance/ph38/chapter/recommendations
NICE NG28 médecine adulte (2026) https://www.nice.org.uk/guidance/NG28/chapter/initial-medicines

## Modifications / limites réelles
La politique Dart `medical_profile_choice_policy.dart` classe uniquement les options de *déclaration*, et `MedicalTreatmentSelector` sert aux deux écrans. Les traitements secondaires, y compris une déclaration inhabituelle, restent accessibles. Test unitaire + widget doivent prouver pre vue initiale sans insuline, extension explicite possible et non-régression type1/type2/gestationnel FR/AR.

**Pas complet :** la table Drift actuelle `PatientProfiles.treatment` ne stocke qu'une valeur, et `ConsentService` considère onboarding complet uniquement avec diabète+traitement. On ne peut certifier les traitements combinés et le vrai « plus tard » tant que schéma+cache/backend+gate identité ne sont pas refaits/testés. Le PR #963 de garde d'identité avec hash Firebase et aucune vraie identité native reste bloqué. Ne pas merger D7 comme une livraison complète du produit. Conserver la décision originale et user gate visuel. Aucun Vercel.

## Tests et validation attendus
Flutter analyze/tests, parcours Chrome réel à 390x844, 768x1024, 1280x900, écran pre BEFORE et AFTER comparable, note du menu déroulé ; contrôle état mobile/profile et accessibilité. Sécurité intercomptes : tests A→B natif avec SQLite et auth liée au profil avant persistance. Traitements multiples : conception du stockage explicite + compatibilité des lecteurs + migrations + sécurité + tests. Adaptation clinique soumise à audit indépendant D19. Le sous-lot courant est la *pertinence des options*, pas D7 totale.
