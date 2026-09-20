# FoodPicker B30 — International basics I: Italy

## Goal
Append a small, high-frequency international batch after certified B29 without disturbing the 389-item prefix.

## Baseline / target
- baseline: 389 concepts
- target: 392 concepts
- branch: `feat/foodpicker-b30-international-italy-1`

## Accepted concepts
1. `pizza_margherita` — FR: Pizza Margherita — EN: Margherita pizza — AR: بيتزا مارغريتا
2. `spaghetti_carbonara` — FR: Spaghetti carbonara — EN: Spaghetti carbonara — AR: سباغيتي كاربونارا
3. `lasagne_bolognese` — FR: Lasagnes à la bolognaise — EN: Bolognese lasagna — AR: لازانيا بولونيز

All three use `MealFoodRegion.universal` and native B30 painters.

## Provenance evidence
### Pizza Margherita
- Italian Ministry of Culture: https://cultura.gov.it/comunicato/pizza-a-capodimonte-ancora-attivo-il-forno-dove-fu-cotta-la-prima-margherita — records the 1889 Capodimonte/Queen Margherita tradition and the tomato-mozzarella-basil version.
- Italia.it: https://www.italia.it/en/campania/naples/things-to-do/pizza — identifies Margherita as the best-known Neapolitan pizza and ties it to Naples/Queen Margherita.
- EU Pizza Napoletana TSG specification: https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A52016XC0518%2804%29 — documents the Margherita within the Neapolitan tradition and its classic ingredients.

### Spaghetti carbonara
- Italia.it Rome/Lazio cuisine: https://www.italia.it/en/lazio/rome/things-to-do/traditional-roman-food-districts-of-rome — treats spaghetti alla carbonara as Roman cuisine and specifies spaghetti, eggs, pecorino romano and guanciale.
- Accademia Italiana della Cucina: https://www.accademiaitalianadellacucina.it/sites/default/files/notizie_files/2009_03_06_4_ricette.pdf — codifies “Spaghetti alla Carbonara” as a classic Italian recipe.

### Lasagne alla bolognese
- Italia.it Bologna guide: https://www.italia.it/en/emilia-romagna/bologna/guide-history-facts — explicitly lists Bolognese lasagna among Bologna foods.
- Accademia Italiana della Cucina, Emilia-Romagna: https://www.accademiaitalianadellacucina.it/en/regionistati/emilia-romagna — documents “Lasagne verdi alla bolognese”.
- Italia.it pasta guide: https://www.italia.it/it/italia/cosa-fare/tipi-di-pasta-italiana-formati-e-ricette — describes classic lasagne alla bolognese with ragù, béchamel and grated cheese.

## Rejected / deferred
- Croissant: rejected for this cycle because serious sources describe its origin story as materially ambiguous (Viennese inspiration vs later French transformation). The catalog may still add a generic croissant later under a non-origin claim, but it does not pass this lot's provenance gate.
- Spaghetti bolognese: deferred in favor of the culturally clearer `lasagne_bolognese`.

## UI proof contract
BEFORE: B29 fixture `Mansaf jordanien` at 390x844, 768x1024, 1280x900.
Goal: expose B30 international artwork without geometry/category regression.
AFTER fixture: `Pizza Margherita` at the same three viewports.

## Required gates
- CI
- P5-5 End-to-End Pilot Rehearsal
- UI geometry golden audit
- UI browser screenshot certification
- exact-head artifact SHA256 verification and manual inspection of all three FoodPicker captures

## Merge / deployment
No automatic merge. Human approval is required after certified visual proof. No Vercel deployment.
