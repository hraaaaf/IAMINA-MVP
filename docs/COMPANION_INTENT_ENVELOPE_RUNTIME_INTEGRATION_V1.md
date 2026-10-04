# IAMINA — Intent Envelope V1 Runtime Integration

Status: **CERTIFIED — DEFAULT OFF — ACTIVATION GATED**

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


## Certified integration shape

The runtime seam is intentionally inert by default:

- `IAMINA_INTENT_ENVELOPE_RUNTIME_ENABLED` is opt-in and defaults off;
- `IAmina` accepts an explicitly injected intent provider but never constructs one implicitly;
- current authenticated chat endpoints instantiate `IAmina(user, language)` without an intent provider, so this lot does not activate external classification;
- local input safety and existing deterministic fast paths execute before the frozen intent pipeline;
- an enabled classifier proposal is still untrusted and is routed only through the frozen V1 policy decision;
- deterministic patient-data routes resolve a semantic target through the condition-agnostic chassis port and active-module canonical read-only resolver;
- conversational routes do not gain structured patient clinical-context authority;
- external intent classification requires all of: an explicitly injected provider, an APPROVED processor policy for `intent_classification`, a valid patient-scoped AI-egress context/current consent, and text-payload DLP authorization immediately before provider invocation;
- Groq remains PENDING and is denied before network use;
- classifier failure, missing provider, invalid output, processor denial or egress denial fails closed to local clarification;
- chat and stream use the same runtime route adapter;
- Darija Latin classified recall keeps Latin script.

Frozen files `companion/intent_envelope.py`, `companion/intent_model.py` and `companion/intent_pipeline.py` were not modified by this runtime-integration lot.

## Certification evidence — 2026-10-04

Certified code HEAD: `481a35d9d693456a8fa8cb2da70db1f1f7552e7a`.

Targeted runtime integration run `37234311665`: **SUCCESS**.

- Ruff: green;
- architecture boundaries/import-linter: 2 contracts kept, 0 broken;
- LLM gateway anti-bypass: passed;
- AI egress authorization anti-bypass: passed;
- targeted pytest: **111 passed + 51 subtests passed**;
- coverage includes default-off behavior, no implicit provider, pending-processor denial before network use, external patient-scope/consent/payload seam, deterministic meta/recall, canonical patient target routing, chat/stream parity, and all 12 frozen patient targets.

Authenticated real-chat E2E run `37234315671`: **SUCCESS** on the same code HEAD.

- Flutter chat validation: green;
- local authenticated backend startup: green;
- synthetic IAMINA identity registration: green;
- browser build: green;
- real Chrome exchange/capture: green;
- proof artifact: `iamina-companion-real-chat-e2e`, artifact ID `11315411126`;
- artifact digest: `sha256:5004edc826bd6f89a3f3ac85005bc206bcc52925ad5555e255a8fed4602641a8`.

An earlier targeted run exposed only two stale mock-call expectations after the new explicit patient-context keyword; those tests were corrected without weakening behavior. A later newly added Darija-Latin recall test initially used the wrong helper fixture type; that test fixture was corrected. Both final exact code-head suites are green.

## Activation gate

This certification proves the **default-off runtime integration**, not production activation.

Production activation still requires an explicit owner decision plus a separately approved classifier provider/processor path. Groq patient-data egress remains unauthorized while its processor/legal/transfer/consent conditions are pending. No Vercel deployment is authorized by this certification.
