# IAMINA — Native Voice Live Benchmark Preflight

Base : `main@58fe3f030975901da3873d23ad3a1b0e0bf9c86b`.

## Goal

Préparer l'exécution synthétique réelle du benchmark Native Voice sur Groq GPT-OSS 120B, avec coût borné, zéro donnée patient et autorisation réseau fail-closed.

## Prix vérifié le 2026-09-26

Sources officielles Groq :
- `https://console.groq.com/docs/model/openai/gpt-oss-120b`
- `https://console.groq.com/docs/models`

Prix contrôlé :
- input : $0.15 / 1M tokens ;
- cached input : $0.075 / 1M tokens ;
- output : $0.60 / 1M tokens.

La fixture repo a été rafraîchie avec `verified_on=2026-09-26` et `review_due_on=2026-10-26`.

## Run contract

- provider : Groq ;
- model : `openai/gpt-oss-120b` ;
- dataset : `iamina-native-voice-live-v1` ;
- patient_data : false ;
- 70 appels synthétiques maximum ;
- max output : 120 tokens / tour ;
- plafond financier dur : **50,000 microUSD = $0.05** ;
- le run est bloqué tant que `NATIVE_VOICE_NETWORK_AUTHORIZED=true` n'est pas explicitement fourni ;
- clé API référencée uniquement par `env:GROQ_API_KEY` ;
- aucun secret stocké.

## Output

Le runner produit :
- réponses provider ;
- usage tokens par appel ;
- coût réel worst-case à partir de l'usage reporté ;
- checks machine préliminaires ;
- packet destiné à la double revue native.

Il ne peut pas déclarer `Native Voice Certified` : la revue humaine native reste obligatoire.

## Hard machine preflight

- script demandé ;
- réponse non vide ;
- longueur bornée ;
- aucun nouveau chiffre clinique avec unité ;
- aucune instruction explicite de traitement/dose.

## Human gate restant

Le code peut être mergé et certifié sans coût externe.

**L'exécution réseau réelle est un gate séparé** car elle entraîne une dépense, même très faible. Elle ne doit être lancée qu'après autorisation explicite du plafond $0.05.
