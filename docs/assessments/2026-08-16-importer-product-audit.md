# Importer product audit — 2026-08-16

Status: SMART audit complete; two truthfulness corrections identified; runtime correction pending.

## Product contract

Importer is the acquisition hub. Its primary real action is Document Import. Direct CGM connectors may be shown only as unavailable/future capabilities and must never look connected. Existing local-data status must describe what is actually stored, without inventing urgency.

## SMART section audit

| Section | Product interest | Score | Decision / status |
|---|---|---:|---|
| Canonical header | Establishes acquisition context consistently | 9.5/10 | KEEP |
| Local-data status banner | Reassures the user that readings exist locally and gives useful recency context | 6.5/10 baseline | IMPROVE — current “latest” lookup is ordered by `createdAt`, not actual reading time |
| Three-day stale warning | Attempts to flag old local data | 4.5/10 | REMOVE — arbitrary 3-day urgency with no actionable connector path; retain factual last-reading time instead |
| First-use Document Import CTA | Gives a real productive action when no readings exist | 9.5/10 | KEEP |
| Returning-user Document Import card | Keeps the only production acquisition path visually primary | 9.5/10 | KEEP |
| Document-type chips | Clarify accepted acquisition use cases | 9.0/10 | KEEP; actual file-format details belong to Document Import |
| “Direct connections” section | Separates future device integrations from the working document path | 8.5/10 | KEEP if unavailable state stays unmistakable |
| Dexcom G6/G7 card | Communicates roadmap capability without fake connection | 8.5/10 | KEEP as unavailable / soon only |
| Abbott LibreLink card | Same | 8.5/10 | KEEP as unavailable / soon only |
| Unavailable connector action | Prevents dead controls masquerading as working integrations | 9.5/10 | KEEP |
| Demo-data control | Useful development aid only | 9.5/10 debug / N/A production | KEEP behind `kDebugMode`; never surface in production |
| Desktop two-column connector layout | Uses space efficiently without changing semantics | 9.0/10 | KEEP |
| Mobile single-column layout | Keeps acquisition cards readable and touch-safe | 9.0/10 | KEEP |

## Verified findings

- `_loadStats()` orders `LogEntries` by `createdAt DESC` and takes one row, then displays `loggedAt ?? createdAt` as the “latest reading”. An older measurement imported or created later can therefore be presented as the latest reading.
- `_isDataStale` turns the status into a warning after exactly three days. No clinical or connector contract establishes three days as an authoritative freshness threshold.
- The stale warning is particularly low-value while both direct CGM connectors are explicitly unavailable.
- First use routes to the real `/pulper` Document Import path.
- Dexcom and Libre cards use `_UnavailableAction` and a localized “soon” badge rather than fake callbacks.
- Demo seeding is protected by `kDebugMode`.
- The page correctly makes Document Import primary over future direct connections.

## Recommended runtime correction

- Compute latest local reading from the maximum effective event time `loggedAt ?? createdAt`, not maximum row creation time.
- Remove the three-day stale warning branch and always keep the local-data banner factual/neutral: count + actual latest stored reading time.
- Do not add connection buttons or notifications for Dexcom/Libre until a real connector contract exists.

## Certification gate

No final page score or CLOSED status before runtime correction, exact-head gates, real Chrome 390×844 inspection, merge/post-merge recertification and canonical closeout.

MENA roadmap numerator remains unchanged by this page audit.
