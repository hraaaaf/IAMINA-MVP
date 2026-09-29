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


## Runtime shadow implementation

Status: **IMPLEMENTED IN SHADOW — NO NETWORK / NO PATIENT OUTPUT CHANGE**

The live companion path now exercises the protected-body seam for
`CLINICIAN_PREP` after the deterministic reply has already passed its normal
domain verifier.

Runtime behavior:
1. build a fresh envelope-scoped opaque body token;
2. use that token as the local shadow provider candidate;
3. reinsert the exact deterministic body locally;
4. pass the reinjected reply through the existing active module verifier again;
5. keep the original deterministic patient reply unchanged.

This runtime shadow performs no external provider call and does not change provider
policy, consent state, patient output, or clinical authority. Its purpose is to
prove that the protected seam survives the actual companion control flow before any
future provider-backed shadow is considered.


## Protected verifier module hook

The chassis now exposes a condition-agnostic protected narration verifier port.

Contract:
- `BaseEngine.verify_protected_advice_reply()` defaults to the existing exact-copy verifier;
- the companion runtime calls the protected port only for the protected shadow seam;
- the diabetes module explicitly opts in `CLINICIAN_PREP` to its protected wrapper verifier;
- all other diabetes families retain their existing strict verifier behavior.

This keeps condition semantics inside the module while allowing a future provider-backed
wrapper candidate to be verified without weakening the chassis contract.


## Provider-backed shadow generator

Status: **IMPLEMENTED — OFF BY DEFAULT**

Feature flag:
`NARRATION_PROTECTED_PROVIDER_SHADOW=False` by default.

Provider payload is deliberately minimal:
- locale;
- script;
- envelope-scoped opaque protected body token.

It excludes:
- patient message;
- deterministic clinical body;
- exact clinical values;
- facts/history;
- AdviceDecision/rule identifiers.

Execution order:
1. feature flag must be ON;
2. processor policy must authorize Groq for `companion_chat/text`;
3. only then may the provider adapter be constructed;
4. returned candidate passes protected-body reinjection;
5. active module protected verifier validates the reinjected candidate;
6. patient-visible reply remains the original deterministic governed reply.

An accidental flag flip therefore cannot create provider traffic while the processor
policy gate is not approved. This stage remains shadow-only and non-authoritative.
