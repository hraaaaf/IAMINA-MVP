# Proactive Intelligence — Trigger Map & Freshness Remediation

Date: 2026-09-24

## Goal

Keep the governed Clinical Twin fresh after authoritative Journal writes so the existing read-only proactive Dashboard preview reflects newly synchronized evidence without requiring an explicit proactive evaluation.

## Success criteria

- A successful non-demo Journal create refreshes the deterministic Clinical Twin.
- A batch containing new authoritative Journal rows refreshes the Clinical Twin once after the batch.
- The refresh does not create or consume `ProactiveInsightState`, delivery signatures, surfacing timestamps or the 24-hour attention budget.
- Existing PATCH/DELETE/source-replacement reconciliation remains authoritative.
- A failure in derived refresh does not roll back or misreport a successfully committed authoritative Journal source row.
- No LLM, diagnosis, causality, treatment, dose or new clinical threshold is introduced.

## Current trigger map

| Source/event | Clinical Twin refresh | Proactive delivery state | Patient surface | Status |
| --- | --- | --- | --- | --- |
| Journal single create | refresh after successful authoritative write | not consumed | Dashboard read-only preview can reflect the new governed state | covered by this remediation |
| Journal batch insert | one refresh after batch | not consumed | Dashboard read-only preview can reflect the new governed state | covered by this remediation |
| Journal PATCH of clinically contributive fields | purge/rebuild via source-erasure reconciliation | subordinate state follows source truth | later reads use rebuilt state | existing |
| Journal DELETE | purge/rebuild via source-erasure reconciliation | subordinate state follows source truth | later reads use rebuilt state | existing |
| Batch replacement of an existing clinical source row | purge/rebuild once in batch transaction | subordinate state follows source truth | later reads use rebuilt state | existing |
| GET personal-response | canonical Clinical Twin refresh | not consumed | personal-response result | existing |
| POST proactive-insights/evaluate | refresh + prioritization | may consume one non-urgent delivery item / 24h | proactive feed | existing explicit command |
| GET proactive-insights/preview | no mutation | not consumed | Dashboard Insight | existing read-only projection |
| GET companion/overview | no mutation | not consumed | Dashboard Today / Companion | existing read-only projection |
| Dashboard Insight load | calls proactive preview | not consumed | passive read-only insight | existing |
| Dashboard Next Action button | explicit POST smart-suggestion evaluation | may consume non-urgent attention budget | bounded next action | existing explicit action |
| CGM sync | stores normalized CGM rows | no proactive delivery | CGM surfaces | gap: current personal-response Clinical Twin does not consume CGMReadingRecord directly |
| Local-only Drift write before server sync | server Clinical Twin cannot see it yet | none server-side | local UI only | expected local-first boundary |
| Background scheduler / worker | none identified in current proactive path | none | none | gap |
| OS push / unsolicited notification | none | none | none | intentionally not claimed |

## V1 → V2 interpretation

The existing proactive engine is already deterministic and governed. The main missing behavior is not a new clinical authority layer; it is trigger completeness and freshness.

### V2-A — Source-write freshness

Event-driven Clinical Twin refresh after authoritative Journal writes. This remediation implements the smallest safe version of this layer.

### V2-B — Multi-source longitudinal inputs

Future work may add additional already-qualified source families such as verified CGM observations, but only through explicit eligibility/provenance rules. CGM transport rows must not be silently treated as the same evidence population as sparse Journal rows.

### V2-C — Background trigger orchestration

A future scheduler/outbox may evaluate whether material governed state changed without requiring a foreground user action. It must preserve:
- deterministic emergency routing upstream;
- explicit attention-budget state;
- suppression of unchanged material state;
- patient-scoped idempotency;
- no LLM-derived urgency or clinical truth.

### V2-D — Notification delivery

Push/OS notification semantics are not part of this remediation. Any future unsolicited patient interruption requires explicit notification preferences, delivery infrastructure, privacy review, locale/safety parity and separate certification.

## Non-scope

- no new detector or threshold;
- no new suggestion class;
- no notification or push delivery;
- no CGM-to-Clinical-Twin promotion;
- no UI change;
- no Vercel deployment;
- no database migration;
- no generative-model authority.

## Safety rationale

The authoritative source row remains primary. Clinical Twin refresh is a recomputable deterministic derivation. If refresh fails after a committed source write, the source write remains successful and the failure is logged; derived-state failure must not masquerade as source-data loss.

The read-only proactive preview remains non-mutating and does not consume the patient's attention budget. Only explicit delivery/evaluation commands may mutate proactive delivery bookkeeping under the existing contract.
