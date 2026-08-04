# Secret history and credential-rotation certification

**Status:** pre-remediation tooling prepared; pilot gate remains blocked by issue #30.

## 1. Scope

The pilot requires proof that no covered credential pattern remains in either:

- the current tracked tree; or
- any blob reachable from Git refs.

Scanning only current files is insufficient because deleted credentials remain retrievable from repository history and old clones.

## 2. Current known result

A full non-shallow scan performed on 2026-08-02 found:

- current tracked tree: **pass**;
- reachable history: **fail**;
- one forbidden historical path: `.claude/settings.local.json`;
- six generic service-token findings in one reachable blob;
- referenced service host in the deleted configuration: `aiapiv2.pekpik.com`.

Credential values are intentionally absent from this document, issues, PRs and logs.

The remediation tracker is issue #30.

## 3. Scanner behavior

`scripts/audit_git_history_secrets.py`:

1. requires a full non-shallow Git checkout;
2. enumerates all objects reachable through `git rev-list --objects --all`;
3. identifies text blobs up to five MiB;
4. checks forbidden historical paths;
5. scans covered credential categories;
6. reports only blob prefix, path, line and category;
7. never prints the matched credential value.

Covered categories include:

- generic `sk-` service tokens;
- Anthropic-style API keys;
- Google API keys, except the deliberately public Firebase client identifier at its exact generated-client path;
- AWS access keys;
- GitHub tokens;
- Slack tokens;
- private-key material;
- forbidden `.env`, service-account and local-credential paths.

The scanner is high-signal rather than mathematically exhaustive. A pass proves that no covered pattern exists in reachable blobs; it does not prove that every unknown credential format has been detected.

## 4. Two-phase rollout

### Phase A — pre-remediation

The mergeable preflight provides:

- the scanner;
- synthetic regression tests;
- weekly and manual full-history execution;
- this response runbook.

`.github/workflows/secret-history-preflight.yml` intentionally has only scheduled and manual triggers. Its full-history step is expected to fail until issue #30 is remediated. The historical blob is **not allow-listed**, and the scanner is not weakened.

### Phase B — final certification

Only after provider-side rotation/revocation and history rewrite may the workflow become a mandatory push/pull-request gate.

Final activation must add blocking triggers without changing scanner logic or adding exceptions for the compromised blob.

## 5. Required order of operations

1. Treat every discovered credential as compromised.
2. Revoke or rotate all potentially affected PekPik credentials.
3. Review provider activity logs for unauthorized use.
4. Confirm all deployments and developer environments use replacement credentials from the approved secret manager.
5. Record restricted evidence using opaque references only.
6. Coordinate a repository history rewrite with all maintainers.
7. Remove the affected blob from all branches and tags, not only `main`.
8. Force-update rewritten refs using the approved maintenance window.
9. Invalidate or archive old deployment sources and caches.
10. Require fresh clones; old clones must not push rewritten history back.
11. Run the scanner from a fresh full non-shallow clone.
12. Activate the blocking push/pull-request history workflow.
13. Obtain security-owner approval.

Rotation/revocation must happen **before** history rewrite. Rewriting Git does not invalidate an already exposed credential.

## 6. Safe history rewrite procedure

The exact rewrite command must be chosen and reviewed during the maintenance window. Prefer `git filter-repo` from a fresh mirror clone.

Illustrative procedure, to be adapted after rotation confirmation:

```bash
# Fresh isolated mirror clone
git clone --mirror <REPOSITORY_URL> IAMINA-MVP-clean.git
cd IAMINA-MVP-clean.git

# Remove the forbidden historical path from all refs.
# Review the installed git-filter-repo version and command before execution.
git filter-repo --path .claude/settings.local.json --invert-paths

# Verify locally before any force push.
python /trusted/path/audit_git_history_secrets.py --repo .
git fsck --full
```

Do not execute the force push until:

- rotation evidence is approved;
- the local rewritten mirror passes;
- branch/tag impact is reviewed;
- all collaborators receive the fresh-clone instruction;
- deployment rollback is prepared.

Do not paste or search for credential values in shell history. Use blob/path metadata only.

## 7. Restricted rotation evidence ledger

The restricted evidence record must include, without credential values:

- incident reference: issue #30;
- provider and credential category;
- affected environments;
- revoked/rotated timestamp;
- replacement activation timestamp;
- accountable owner role;
- opaque provider audit-log reference;
- conclusion of unauthorized-use review;
- confirmation that deployed environments no longer reference old credentials;
- history-rewrite change reference;
- fresh-clone scanner run reference;
- security-owner approval reference.

Signed provider records and internal identities remain outside source control.

## 8. Fresh-clone certification

After the rewrite:

```bash
git clone <REPOSITORY_URL> IAMINA-MVP-fresh
cd IAMINA-MVP-fresh
test "$(git rev-parse --is-shallow-repository)" = "false"
python scripts/check_secrets.py
python scripts/audit_git_history_secrets.py
```

The certification is invalid if:

- the checkout is shallow;
- any branch or tag containing the blob remains reachable;
- the tracked-tree scan fails;
- the history scanner fails;
- evidence refers to a clone created before the rewrite.

## 9. Pilot closure criteria

The roadmap gate remains open until all are true:

- [ ] six potentially affected credentials are revoked or rotated;
- [ ] provider activity review is complete;
- [ ] all deployments use replacement credentials;
- [ ] restricted rotation evidence is approved;
- [ ] the historical blob is removed from all reachable refs;
- [ ] a fresh non-shallow clone passes both scanners;
- [ ] blocking push/pull-request history certification is enabled;
- [ ] old clones and deployment caches are handled;
- [ ] security owner approves closure.

The current-tree secret-hygiene pass alone is not sufficient.
