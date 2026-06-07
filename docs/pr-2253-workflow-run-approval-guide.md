# PR #2253 — Workflow Run & Approval Guide

PR: https://github.com/frappe/crm/pull/2253  
Branch: `joefoxing/production-readiness-unblock`

This guide explains exactly how to approve and run CI workflows for this PR, and what to do if workflows do not start.

---

## 1. Permissions required

You need one of the following on `frappe/crm`:

1. **Write/Admin/Maintain access** to approve and run workflows from forked PRs.
2. **Actions permissions enabled** in repo settings (already enabled in `frappe/crm`).

If you only have read access, you can view status but cannot approve/start blocked runs.

---

## 2. Approve workflow execution from the PR UI (most important)

For fork PRs, GitHub may block workflow execution until a maintainer approves it.

1. Open PR #2253.
2. Go to the **Checks** tab (or scroll to the checks section).
3. Look for a banner/button like:
   - **"Approve and run workflows"**
   - or **"Workflows awaiting approval"**
4. Click **Approve and run workflows**.
5. Wait 30–90 seconds and refresh checks.

If this step is skipped, workflows may remain pending indefinitely.

---

## 3. Confirm which workflows should run for this PR

Expected PR-triggered workflows for this repo:

1. `Frontend` (`.github/workflows/frontend-tests.yml`)
2. `Linters` (`.github/workflows/linters.yml`)
3. `Server` (`.github/workflows/server-tests.yml`) — runs on `pull_request` unless all changed files match ignored patterns.

Check changed files quickly:

```bash
gh pr view 2253 --repo frappe/crm --json files --jq '.files[].path'
```

If server tests are skipped unexpectedly, verify file paths against `paths-ignore` in `server-tests.yml`.

---

## 4. Monitor runs with GitHub CLI

Use these from any terminal authenticated with `gh`:

```bash
gh pr checks 2253 --repo frappe/crm --watch
```

```bash
gh run list --repo frappe/crm --event pull_request --branch joefoxing/production-readiness-unblock --limit 20
```

View detailed logs for a run:

```bash
gh run view <run-id> --repo frappe/crm --log
```

---

## 5. Re-run failed jobs/runs

If a workflow run exists but failed:

1. PR → **Checks** → open failing run.
2. Click **Re-run failed jobs** (preferred) or **Re-run all jobs**.

CLI equivalent:

```bash
gh run rerun <run-id> --repo frappe/crm --failed
```

or:

```bash
gh run rerun <run-id> --repo frappe/crm
```

---

## 6. If no PR workflows start after approval

Use this escalation order:

1. **Re-open checks page** and verify approval actually applied.
2. **Push a no-op commit** to retrigger `pull_request` workflows:
   ```bash
   git checkout joefoxing/production-readiness-unblock
   git commit --allow-empty -m "chore: retrigger pr workflows"
   git push
   ```
3. If still blocked, ask a repo maintainer to:
   - confirm Actions policy allows fork PR runs,
   - re-approve workflow execution on PR #2253,
   - check org-level Actions restrictions.

Note: `server-tests.yml` does **not** define `workflow_dispatch`, so the reliable trigger is PR activity (new commit/synchronize event).

---

## 7. What “workflow gate cleared” means for this PR

Treat workflow gating as cleared when:

1. Required workflow runs are visible for PR #2253.
2. `Frontend`, `Linters`, and `Server` checks are `success` (or an explicit maintainer-approved skip with reason).
3. No required check is left `pending`.

Then you can mark the **server CI blocker** in `docs/production-readiness-plan.md` as resolved.

