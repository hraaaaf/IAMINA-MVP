# IAMINA — W01+D2 synthetic Flutter Web erasure QA — 28 October 2026

## Goal / observable success / proof

Goal: run real authenticated Flutter Web synthetic signup, consent + D2 inbox and A→B→A, then erase accounts through **application endpoints**, independently confirming Neon auth_user, profiles, logs, notices, and D2 receipts = 0. Nothing clinical is real. This goal is **NOT YET ACHIEVED**.

## BEFORE / reference / proposed change

**BEFORE** (source code at Preview HEAD `90bcf7a4`): Profile → Compte → Zone de danger shows Sign out and Withdraw consent; no account deletion action. An authenticated Profile screenshot is unavailable; pixel baseline **NOT VERIFIED**.

**Goal UX:** one unmistakable 48px-high, Preview-only destructive action inside the existing account card, after Sign out, without reorganizing other controls. Keep the same typography/card/borders as neighboring actions. Require typing the server's precise phrase before an irreversible action.

**Reference/mockup** (same responsive account expansion, no invented decorative UI):

```text
Profil → Compte
  [Déconnexion]
  [Supprimer le compte de test]  ← only exact IAMINA protected Preview
  [Retirer le consentement]     ← only if consent active

Confirmation modal
  Preview synthétique uniquement. Supprime le compte et purge le coffre local.
  [DELETE MY ACCOUNT __________]
  [Annuler]  [Supprimer]
```

## Implementation in isolated QA branch

Branch `test/w01-d2-safe-flutter-erasure-20261028`, rooted at Preview HEAD `90bcf7a4`. The client-side UI is gated by compile-time **same-origin Preview**, **remote enrollment**, verified native Django credential, HTTPS immutable `iamina-review-…-achraf-benmoussa-s-projects.vercel.app` host; the BFF independently restricts exact Vercel branch/SHA and `@example.invalid` registration. No Production-facing button. The application DELETE uses current bearer and body `{"confirm":"DELETE MY ACCOUNT"}`, requires HTTP 200, performs zero blind retries, purges five bound local clinical tables before credential retirement; non-200 or uncertain state never claims success.

## AFTER proof — not yet available

No Preview deployment of QA branch has been authorized. Compare authenticated Profile screenshots **at identical 390×844 and 1280×900 viewports** after explicit Preview deployment GO; test modal overflow, labels in FR/EN/AR, keyboard focus, cancellation and failure/no-erase states. Visual score **NOT MEASURED**. The existing production website and approved Preview SHA `90bcf7a4` remain untouched.

## Tests and real gate

Run isolated `flutter analyze`, negative scope tests, Flutter Web build via QA-only GitHub Action. If GREEN, integrate vetted changes into the existing DRAFT PR as a controlled batch. A **new Vercel Preview deployment on changed SHA requires an explicit separate GO**, and the exact branch/SHA-scoped synthetic auth env will need repinning. Only then create actual Flutter users, test D2, delete both and verify Neon independently. Never use direct SQL DELETE or weaken SSO.
