# IAMINA — First Live Narration Family Gate

## Family retenue

`CLINICIAN_PREP`.

## Pourquoi

Le verifier actuel V1 est volontairement maximalement strict :
- seul le `fallback` déterministe exact est accepté ;
- toute copie altérée retombe sur le fallback ;
- aucune invention de fait patient ou conclusion clinique n'est tolérée.

C'est une meilleure première surface live que `MONITORING_INTERPRETATION`, dont le verifier accepte davantage de formulations et exigerait donc un semantic verifier plus large avant exposition.

## Contrat live proposé

Le corps clinique reste exactement le `resolution.reply` certifié.

Provider :
- reçoit un body token opaque one-shot ;
- ne reçoit jamais le body clinique ;
- doit conserver exactement une occurrence du token ;
- peut générer uniquement un wrapper relationnel court.

Local :
1. vérifie token/body ;
2. réinjecte exactement `resolution.reply` ;
3. vérifie que le body est présent exactement une fois ;
4. vérifie le wrapper séparément ;
5. exécute les guards safety/output/dialect ;
6. sinon fallback exact.

## Wrapper gate

Le wrapper sera refusé si :
- il contient un chiffre clinique ;
- il contient une instruction thérapeutique ;
- il ajoute un diagnostic, une causalité ou un degré d'urgence ;
- il contient un fait patient absent ;
- il dépasse la longueur autorisée ;
- il viole le script/locale ;
- il modifie, fragmente ou duplique le body exact.

Le wrapper n'a aucune autorité clinique.

## Compatibilité verifier

Le verifier V1 existant ne sera pas affaibli.

Une fonction dédiée vérifiera :
- extraction exacte du body déterministe ;
- wrapper non-clinique ;
- puis le body lui-même continue à passer le verifier V1 exact-copy.

## Rollout

1. shadow candidate : appel provider mais réponse patient déterministe inchangée ;
2. comparer candidate wrapper vs réponse actuelle ;
3. machine gate + adversarial;
4. activation opt-in interne uniquement ;
5. aucune activation multi-family simultanée.

## Stop conditions

Retour immédiat au déterministe si :
- mismatch body ;
- token replay ;
- wrapper clinique ;
- erreur provider ;
- erreur privacy/egress ;
- family verifier fail ;
- output guard fail.

## Hors scope

- autres rule families ;
- L2/L3 supplémentaires ;
- streaming token-by-token patient ;
- changement d'autorité clinique ;
- Vercel.
