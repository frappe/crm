# Staging & Operations Readiness Checklist

Use this checklist to clear the remaining non-code production blockers after PR #2253 workflows are approved and running.

Related:
- PR workflow approval: `docs/pr-2253-workflow-run-approval-guide.md`
- Master plan: `docs/production-readiness-plan.md`

---

## 1. Owner + Schedule (fill before execution)

| Item | Primary Owner | Backup Owner | Scheduled Window | Status |
|---|---|---|---|---|
| Staging deploy | @joefoxing | TBD | TBD | Not started |
| Smoke test execution | @joefoxing | TBD | TBD | Not started |
| Backup drill | TBD | TBD | TBD | Not started |
| Restore drill | TBD | TBD | TBD | Not started |
| Rollback drill | TBD | TBD | TBD | Not started |
| Final sign-off | @joefoxing | TBD | TBD | Not started |

---

## 2. Staging Deployment Gate

## Preconditions
1. PR #2253 checks include `Frontend`, `Linters`, `Server` and all are green.
2. Target commit SHA is finalized.
3. Deployment window and rollback owner are assigned.

## Execution
1. Deploy target SHA to staging from the same artifact path intended for production.
2. Capture deployment metadata:
   - commit SHA
   - container/image/tag
   - migration output
   - timestamp
3. Confirm application boots and endpoint health checks pass.

## Evidence to record
- Deployment log URL/path
- Exact SHA/tag deployed
- Health-check output

---

## 3. Smoke Test Gate

Run these on staging after deploy:

1. Auth/session flow: login, authenticated API call, logout.
2. CRM core flow: create/update/view Lead and Deal.
3. Activity flow: add comment/note/task and verify persistence.
4. Notification/socket flow: trigger event and confirm client refresh path.
5. Form script critical path (if enabled in tenant): load + save without error.

## Pass criteria
- No P0/P1 failures.
- No blocker regressions in browser console/network.

## Evidence to record
- Test checklist with pass/fail per case
- Screenshots (where relevant)
- Error logs for any failed step

---

## 4. Backup + Restore Gate

## Backup drill
1. Trigger database backup using production-equivalent process.
2. Record backup identifier, size, and completion timestamp.
3. Validate backup artifact integrity (checksum or platform validation).

## Restore drill
1. Restore backup into isolated verification target.
2. Run minimal integrity checks:
   - login works
   - key doctypes readable
   - sample records present
3. Record restore duration and any manual intervention.

## Pass criteria
- Backup and restore complete successfully within expected RTO/RPO boundaries.

---

## 5. Rollback Gate

## Predefine rollback trigger criteria
1. P0 functional regression in core CRM flows.
2. Error rate threshold breached post-deploy.
3. Migration/app startup failure.

## Drill
1. Perform controlled rollback in staging to prior known-good SHA/tag.
2. Re-run a subset of smoke tests.
3. Confirm service health is restored.

## Pass criteria
- Rollback executes cleanly and restores service within target time.

---

## 6. Final Sign-off Template

| Gate | Result | Evidence Link |
|---|---|---|
| Build | Pass/Fail | |
| Security (high/critical) | Pass/Fail | |
| Quality (Frontend/Linters/Server) | Pass/Fail | |
| Staging deploy | Pass/Fail | |
| Smoke tests | Pass/Fail | |
| Backup/restore drill | Pass/Fail | |
| Rollback drill | Pass/Fail | |

**Go/No-Go Decision:** GO / NO-GO  
**Decision Owner:**  
**Timestamp:**  

