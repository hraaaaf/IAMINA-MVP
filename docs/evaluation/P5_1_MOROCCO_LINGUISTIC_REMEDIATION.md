# P5-1 Morocco linguistic remediation

## Trigger
Exact-main v3 run #34654142883 on `db7531d8ee862eb9a3b0249fbee8abecd31ea27c` was machine-green but produced Morocco-lane wording unsuitable for final retained human certification. v4 remained too permissive. v5 correctly rejected `بسهولة / b sahla` and exposed ambiguous “simple/easy” semantics in the synthetic prompts. v6 corrected those prompts and made 4/5 Morocco lanes pass, but the MSA lane still reintroduced `بسهولة` despite a no-pressure/no-blame request.

## Retained evidence
- v3 artifact #10284573280, digest `sha256:811b99c22216b49a727e81c38d792bc86bfd1bf32928c5d5e382c2a01ae6ad88`
- v4 artifact #10285243803, digest `sha256:91a56923bdc0f4f26c4305176c000a6004e657c5668fd3a223657531ed6870a3`
- v5 failed artifact #10285505607, digest `sha256:1643808915ef56cd482e6649973a861547adaaced0199402538e4dd288998ab6`
- v6 failed run #34655996828, artifact #10285670650, digest `sha256:d954b4aa262528ef52bccee0f2b5f39afa9043608b0f5be5fcebb337b16e271d`
- all synthetic only, no patient data

## v7 targeted policy
Before native/competent human review:
- retain the v6 Morocco prompts using “sans pression / بلا ضغط / bla daght” instead of ambiguous “simple/easy” semantics;
- retain gender-neutral/non-patronizing current-Morocco checks;
- retain Moroccan register checks for Darija Arabic/Latin and phrase-level FR↔Darija;
- add an explicit MSA requirement preserving “without pressure or blame” semantics and forbidding `سهل/سهلة/سهولة/بسهولة` or equivalent easy/easily wording;
- Gulf lanes remain deferred expansion lanes and do not inherit current-Morocco tone gates;
- exact-SHA binding, one bounded provider call, and retained human review remain mandatory.

This document records engineering rationale only. It is not linguistic, clinical, CNDP, legal, provider, deployment, or real-patient approval.
