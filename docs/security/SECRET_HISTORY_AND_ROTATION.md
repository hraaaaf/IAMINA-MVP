# Secret history and provenance certification

**Status:** pre-remediation tooling prepared; pilot gate remains blocked by issue #30 until the historical blob is purged and a fresh full-history scan passes.

## 1. Scope

The pilot requires proof that no covered credential pattern remains in either:

- the current tracked tree; or
- any blob reachable from Git refs.

Scanning only current files is insufficient because deleted credential-like material remains retrievable from repository history and old clones.

## 2. Current known result

A full non-shallow scan performed on 2026-08-02 found:

- current tracked tree: **pass**;
- reachable history: **fail**;
- one forbidden historical path: `.claude/settings.local.json`;
- six generic `sk-` service-token findings in one reachable blob;
- referenced service host in the deleted configuration: `aiapiv2.pekpik.com`.

The scheduled full-history preflight on 2026-08-10 reconfirmed the tracked-tree pass and reachable-history failure. SECURITY-30A removed unrelated classifier noise without allow-listing the historical PekPik blob.

### Provenance correction — 2026-08-11

Repository history shows that the PekPik material was already present in the **initial IAMINA snapshot** inside `.claude/settings.local.json`, a local Claude/agent permission file. The later cleanup commit describes the file as `local agent settings containing secrets`.

The project owner reports no knowledge of, or intentional account relationship with, PekPik. A connected-mailbox search found no PekPik registration, billing or account correspondence.

Current public PekPik documentation states that developers can copy **public test keys** and test the gateway **without registration**. Therefore the repository does **not** have evidence that these six historical values were user-owned PekPik account credentials.

This changes the incident classification from **assumed user-owned credential rotation** to **public/test-key provenance plus historical secret-like material purge**.

It does **not** change the scanner result: `.claude/settings.local.json` remains a forbidden historical path and the blob must still be removed from all reachable refs.

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
7. never prints the matched value.

Covered categories include generic service tokens, provider API-key patterns, AWS/GitHub/Slack tokens, private-key material and forbidden local credential paths.

Known safe classifier exceptions remain narrow and exact. The historical PekPik blob is not allow-listed.

The scanner is high-signal rather than mathematically exhaustive. A pass proves that no covered non-exempt pattern exists in reachable blobs; it does not prove that every unknown credential format has been detected.

## 4. Two-phase rollout

### Phase A — pre-remediation

The preflight provides:

- the scanner;
- synthetic regression tests;
- weekly/manual full-history execution;
- this runbook.

`.github/workflows/secret-history-preflight.yml` intentionally remains scheduled/manual while the historical blob is reachable. Its full-history step is expected to fail until issue #30 is remediated.

### Phase B — final certification

After the history rewrite passes locally and from a fresh clone, the workflow may become a mandatory push/pull-request gate without changing scanner logic or adding an exception for the affected blob.

## 5. Required order of operations

1. Preserve the provenance evidence: initial-snapshot location, local-agent file classification, no demonstrated user-owned PekPik account, and PekPik's public-test-key model.
2. Confirm current tracked code and configured deployment surfaces do not reference PekPik.
3. Coordinate a repository history rewrite with maintainers.
4. Remove `.claude/settings.local.json` from every affected branch and tag, not only `main`.
5. Verify the rewritten mirror locally with the unchanged scanner and `git fsck --full`.
6. Force-update rewritten refs only after branch/tag impact is reviewed.
7. Require fresh clones; old clones must not push pre-rewrite history back.
8. Invalidate or archive old deployment sources/caches where applicable.
9. Run tracked-tree and full-history scanners from a fresh non-shallow clone.
10. Activate the blocking push/pull-request history workflow.
11. Obtain Security Reviewer and Release Certifier approval on the exact rewritten head.
12. Close issue #30 only after the fresh-clone scans and blocking gate pass.

### What is no longer a prerequisite

Do **not** require the project owner to rotate or revoke a PekPik account credential unless independent evidence establishes that a user-owned PekPik account/credential actually existed.

No such account ownership is currently demonstrated.

If later evidence establishes a private/user-owned credential, provider-side revocation and activity review become mandatory before closure.

## 6. Safe history rewrite procedure

Prefer `git filter-repo` from a fresh isolated mirror clone:

```bash
git clone --mirror <REPOSITORY_URL> IAMINA-MVP-clean.git
cd IAMINA-MVP-clean.git

git filter-repo --path .claude/settings.local.json --invert-paths

python /trusted/path/audit_git_history_secrets.py --repo .
git fsck --full
```

Do not force-push until:

- the rewritten mirror passes;
- branch/tag impact is reviewed;
- collaborators receive fresh-clone instructions;
- rollback/deployment implications are understood.

Do not paste or search credential values in shell history. Use path/blob metadata only.

## 7. Evidence ledger

The restricted or operational evidence record should include, without credential values:

- incident reference: issue #30;
- provenance classification;
- evidence that no user-owned PekPik account is demonstrated;
- current-tree/current-runtime PekPik search result;
- history-rewrite change reference;
- affected refs reviewed;
- fresh-clone scanner run reference;
- blocking-gate activation reference;
- Security Reviewer verdict;
- Release Certifier verdict.

If future evidence proves private credential ownership, additionally record provider revocation, provider activity review and affected-environment verification.

## 8. Fresh-clone certification

After the rewrite:

```bash
git clone <REPOSITORY_URL> IAMINA-MVP-fresh
cd IAMINA-MVP-fresh
test "$(git rev-parse --is-shallow-repository)" = "false"
python scripts/check_secrets.py
python scripts/audit_git_history_secrets.py
```

Certification is invalid if:

- the checkout is shallow;
- any branch/tag still makes the forbidden blob reachable;
- the tracked-tree scan fails;
- the history scanner fails;
- evidence refers to a clone created before the rewrite.

## 9. Pilot closure criteria

The roadmap gate remains open until all are true:

- [x] provenance investigated; no user-owned PekPik account is currently demonstrated;
- [x] current tracked tree contains no PekPik integration reference;
- [ ] historical `.claude/settings.local.json` blob removed from all reachable refs;
- [ ] rewritten mirror passes unchanged history scanner and `git fsck --full`;
- [ ] force-updated refs are coordinated;
- [ ] fresh non-shallow clone passes tracked-tree and full-history scanners;
- [ ] blocking push/pull-request history certification is enabled;
- [ ] stale clones/deployment caches are handled as applicable;
- [ ] Security Reviewer approves the exact rewritten state;
- [ ] Release Certifier approves closure.

The current-tree secret-hygiene pass alone is not sufficient.
