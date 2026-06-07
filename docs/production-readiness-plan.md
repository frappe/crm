# Production Readiness Plan

## Status

**Current assessment:** Not production-ready (**closer, but blocked on server/staging gates**).

**Execution update (2026-06-06):**
1. ✅ Frontend build is now reproducible on Windows and Linux-compatible tooling (`yarn build` succeeds).
2. ✅ High-severity frontend dependency vulnerabilities are removed (`yarn audit --level high` reports no high/critical).
3. ⛔ Backend CI-equivalent validation is still pending because Bench server tests require Linux Bench + MariaDB workflow.
4. ⛔ Staging deployment, smoke, backup/restore drill, and rollback drill are still pending.

**Current production blockers:**
1. Server test gate (`.github/workflows/server-tests.yml`) not yet executed in CI-like environment.
2. Staging and operational readiness gates not yet completed.

---

## Scope and Objectives

This plan defines the work required to reach a **go-live decision** for this repository with:
- Reproducible, successful production build.
- No unresolved high/critical dependency vulnerabilities.
- Passing frontend and backend test gates in CI-like environment.
- Clear release sign-off checklist and rollback readiness.

---

## Phase 1 — Stabilize Build Pipeline

### Goal
Resolve the hanging frontend build and make production artifacts deterministic.

### Tasks
1. Reproduce the build hang in a controlled environment (local and CI runner parity).
2. Isolate the stall point (Vite config/plugin loading, PWA plugin, asset generation, or copy step).
3. Add temporary diagnostic logging/timing around plugin initialization and build hooks.
4. Test mitigation paths:
   - Pin/adjust `vite`, `vite-plugin-pwa`, and related transitive deps.
   - Temporarily disable PWA plugin to confirm root-cause surface.
   - Validate `copy-html-entry` behavior on target OS/runtime.
5. Implement fix and remove temporary diagnostics.
6. Document root cause and permanent remediation in project docs/changelog.

### Exit Criteria
- `corepack yarn build` completes successfully twice in a row on a clean install.
- Build artifacts are generated at expected paths.
- No manual post-processing required.

### Phase Status
✅ **Completed**

### Implemented changes
- Disabled proxy plugin in production build path (`frappeProxy: isDev`) to avoid Windows path traversal loop in upstream plugin utilities.
- Removed `vite-plugin-pwa` integration from frontend build config.
- Replaced shell `cp` build step with cross-platform Node copy command.
- Removed hard dependency on `sites/common_site_config.json` import in `src/socket.js`; now resolves socket port from boot globals with fallback.

---

## Phase 2 — Remediate Security Vulnerabilities

### Goal
Eliminate high-severity dependency findings and reduce overall risk.

### Tasks
1. Generate and triage vulnerability report with dependency tree ownership.
2. Upgrade or override vulnerable transitive packages (starting with `serialize-javascript`, `fast-uri`, and related chain under `vite-plugin-pwa/workbox-build`).
3. Verify compatibility with frontend runtime and build output.
4. Re-run audit and capture before/after results.
5. Open explicit risk-acceptance record only if a finding is not patchable immediately (time-boxed, owner assigned, mitigation documented).

### Exit Criteria
- `yarn audit --level high` returns no high/critical vulnerabilities.
- Any remaining moderate findings are documented with owner and due date.

### Phase Status
🟡 **Partially completed**

### Implemented changes
- Removed `vite-plugin-pwa` dependency chain that introduced prior high-severity advisories.
- Verified no high/critical advisories remain at `--level high`.

### Remaining actions
- Triage and assign owners/dates for remaining moderate advisories (currently 9).

---

## Phase 3 — Backend and Integration Validation

### Goal
Validate server-side behavior in production-like test conditions.

### Tasks
1. Run server test workflow equivalent (Bench + site + MariaDB service) using project CI definitions.
2. Ensure Python checks/linting/test commands pass in the same dependency versions used by CI.
3. Validate key CRM flows end-to-end against a fresh site:
   - Authentication/session flows
   - Lead/deal CRUD paths
   - Activity/comment/event workflows
   - Integration touchpoints (if enabled in target deployment)
4. Confirm migration/install path for new environment setup.

### Exit Criteria
- Server tests pass in CI and at least one reproducible staging run.
- No unresolved P0/P1 defects in core CRM workflows.

### Phase Status
🟡 **Partially completed**

### Completed checks
- Python syntax compilation check across `crm/**/*.py` passes.

### Remaining actions
- Execute full Bench + MariaDB server workflow in Linux CI/staging.
- Run end-to-end CRM flow validation on a fresh site.

---

## Phase 4 — Release Hardening and Operational Readiness

### Goal
Confirm deployability, observability, and rollback preparedness.

### Tasks
1. Create/verify staging deployment from the same release artifact.
2. Execute smoke tests post-deploy.
3. Confirm monitoring/alerting coverage for app health, error rates, and job failures.
4. Validate backup and restore process (database + required assets).
5. Prepare rollback runbook with trigger criteria and ownership.
6. Freeze dependency versions and create release notes.

### Exit Criteria
- Successful staging deployment with smoke suite pass.
- Rollback drill completed and documented.
- Release checklist approved by engineering owner.

### Phase Status
⛔ **Not started**

---

## Release Gates (Go/No-Go)

A production release is allowed only if all gates are green:

1. **Build Gate:** Frontend production build succeeds in clean environment and CI.
2. **Security Gate:** No high/critical dependency vulnerabilities.
3. **Quality Gate:** Frontend tests and backend server tests pass.
4. **Staging Gate:** Deployment and smoke tests pass in staging.
5. **Operations Gate:** Monitoring, backup/restore, and rollback runbook verified.

Any failed gate is an automatic **No-Go**.

---

## Suggested Execution Order (Fastest Risk Reduction)

1. Fix build hang (Phase 1).
2. Patch high vulnerabilities (Phase 2).
3. Run full backend/integration validation (Phase 3).
4. Complete release hardening and go/no-go review (Phase 4).
