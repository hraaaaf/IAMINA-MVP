# GitHub Actions — default concurrency policy

All workflows in this directory must define top-level `concurrency.group` and `concurrency.cancel-in-progress`. The test `scripts/tests/check_workflow_concurrency.mjs` is enforced by `CI` before path-based jobs.

The default group is per workflow and PR number or Git ref:

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: ${{ github.event_name == 'pull_request' || github.event_name == 'pull_request_target' || (github.event_name == 'push' && github.ref != 'refs/heads/main') }}
```

- New commits on the same PR cancel superseded runs of that workflow.
- Non-main branch pushes likewise cancel superseded runs.
- `main` pushes and `workflow_dispatch` are serialized within the same group but **not automatically cancelled**: protect releases, manually requested benchmarks and human approvals.
- Existing workflow-specific groups or explicit safety exceptions may remain, but MUST have a top-level group and cancellation setting.
- Job-level concurrency alone does not meet this requirement.
- This policy cannot retroactively cancel old queued workflow runs launched before it existed. Those runs must be safely cancelled separately; never cancel current PR HEAD or `main`.

Before introducing a new YAML workflow, run `node scripts/tests/check_workflow_concurrency.mjs`.
