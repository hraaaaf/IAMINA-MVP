# IAmina — Flutter Frontend

Flutter client for the IAmina MENA diabetes companion.

For product strategy, safety rules, and current priorities, start at the repository root:

- `../README.md`
- `../docs/ROADMAP.md`
- `../docs/architecture/ARCHITECTURE.md`
- `../docs/CONTRIBUTING.md`

## Stack

- Flutter — pinned by `.tool-versions`
- GoRouter — navigation
- Drift — offline-first local persistence
- Provider — state management

Firebase-related client code may still exist as **legacy current-state** while the Django-native auth migration is designed and executed. Do not treat Firebase as the target architecture.

## Run locally

From `frontend/`:

```bash
flutter pub get
flutter run -d chrome
```

Run the backend through the repository's Docker-first workflow.

## Build-time configuration

Use environment/build-time variables for non-secret runtime configuration such as the backend base URL.

Never embed real provider keys, service-account credentials, or secrets in Dart defines or committed source.

## Product constraints that affect frontend work

- Flutter is the only product frontend.
- Locale is more than one language code: country, UI language, response language, dialect, script/transliteration, units, time zone, and emergency jurisdiction must remain separable.
- Location may suggest locale choices; it must not silently determine them.
- RTL and Arabic-script behavior must be tested for enabled pilot locales.
- Safety-critical rules must not exist only in the client.
- Offline-first sync must preserve `client_uuid` idempotency.
- AI/provider errors require explicit, safe UX; do not leave indefinite loading states.

## Validation

```bash
flutter analyze
flutter test
```

Use Flutter widget/integration tests for product UI behavior. Do not assume Flutter web widgets are ordinary DOM nodes that can always be tested with CSS/text selectors.
