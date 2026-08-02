# Secret History and Rotation Certification

## Scope

The pilot requires proof that no known credential pattern remains in either the
current tracked tree or any blob reachable from Git refs. Scanning the current tree
alone is insufficient because a deleted credential remains retrievable from Git
history.

## Permanent controls

The `Secret history certification` workflow:

1. checks out the complete repository with `fetch-depth: 0`;
2. verifies the checkout is not shallow;
3. runs the existing tracked-file scanner;
4. enumerates every object reachable through `git rev-list --objects --all`;
5. inspects text blobs up to five MiB;
6. reports only blob prefixes, paths, line numbers and credential categories;
7. never prints a detected credential value.

The workflow runs on relevant pushes and pull requests, weekly, and on manual
dispatch.

## Covered categories

- generic `sk-` service tokens;
- Anthropic-style API keys;
- Google API keys, except the deliberately public Firebase client identifier at
  its exact generated-client path;
- AWS access keys;
- GitHub tokens;
- Slack tokens;
- private-key material;
- forbidden tracked or historical `.env`, service-account and local-credential
  paths.

The scanner is high-signal rather than exhaustive. A pass means no covered pattern
was found; it is not proof that an unknown credential format has never existed.

## Finding response

When a finding appears:

1. treat the credential as compromised;
2. rotate or revoke it before rewriting history;
3. identify affected commits with `git log --all --find-object=<BLOB_ID>`;
4. assess logs and provider activity for misuse;
5. remove the secret from active configuration and Git history;
6. coordinate the history rewrite with every clone and deployment source;
7. rerun tracked and history scans from a fresh full clone;
8. record only provider/category, rotation time, owner and evidence reference —
   never the credential itself.

## Rotation evidence ledger

Rotation evidence remains outside source control because it may reveal account and
provider details. The restricted ledger must contain:

- credential category and provider;
- affected environment;
- detection or precautionary-rotation reason;
- revoked-at and replacement-activated-at timestamps;
- responsible owner role;
- opaque provider audit reference;
- confirmation that deployments no longer reference the old credential;
- confirmation that a fresh-clone history scan passes.

## Pilot gate

The repository gate closes only after:

- tracked-file secret hygiene passes;
- the full reachable-history workflow passes from a non-shallow checkout;
- any detected live credential is rotated or revoked;
- deployment secrets are verified in the approved secret manager;
- external rotation evidence is approved by the security owner.
