# IAMINA — Intent Envelope V1 Runtime Integration

Status: **IN PROGRESS — DEFAULT OFF — NO PRODUCTION ACTIVATION**

Base frozen contract: `docs/COMPANION_INTENT_ENVELOPE_PIPELINE_V1.md`
Frozen source baseline: `50c9671098bd92531a524a6114addc5e44bb9c2e`

## Goal

Wire the frozen Intent Envelope V1 into the authenticated Companion runtime without changing any frozen invariant and without authorizing production patient-data egress.

## Success

- local safety remains before any intent classifier;
- existing deterministic fast paths remain before classification;
- runtime integration is default-off and cannot create a network classifier implicitly;
- when explicitly enabled with an injected governed classifier provider, unresolved turns pass through the frozen V1 envelope;
- deterministic-local, patient-data, conversational and clarify decisions are handled without granting external egress authority;
- patient-data decisions resolve only through canonical patient-scoped read-only sources;
- classifier failure / invalid output / missing provider fails closed;
- chat and stream paths have parity;
- legacy behavior is unchanged with the runtime gate disabled;
- targeted unit/Django tests and exact-head CI are green;
- no Vercel deployment or production activation in this lot.

## Proof required

1. Code inspection of call ordering.
2. Default-off regression tests.
3. No-implicit-provider tests.
4. Route-specific runtime tests.
5. Patient-scope/adversarial tests.
6. Chat/stream parity.
7. Exact-head CI.
8. Human gate before any production activation.

## Constraints

- V1 schema/invariants are frozen.
- Groq patient-data egress remains unauthorized while processor/legal-basis gates are pending.
- The intent decision never authorizes narrator egress.
- No merge to production and no Vercel deployment without explicit owner authorization.
