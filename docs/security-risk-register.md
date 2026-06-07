# Security Risk Register (Production Readiness)

This register tracks remaining moderate dependency findings after high/critical remediation.

Reference command:

```bash
cd frontend
corepack yarn audit --level high
corepack yarn audit --json
```

Current state:
- High/Critical: **0**
- Moderate: **present** (tracked below)

---

## 1. Findings and Decision Log

| Advisory ID | Package | Severity | Title | Patched In | Current Path | Decision | Owner | Due Date | Status |
|---|---|---|---|---|---|---|---|---|---|
| 1102341 | `esbuild` | Moderate | Dev server request/response exposure | `>=0.25.0` | `vite > esbuild` | Accept temporarily (dev-surface) | @joefoxing | 2026-06-14 | Open |
| 1116229 | `vite` | Moderate | Path traversal in optimized deps map handling | `>=6.4.2` | `vite` | Plan upgrade in compatibility window | @joefoxing | 2026-06-14 | Open |
| 1117015 | `postcss` | Moderate | XSS in CSS stringify output | `>=8.5.10` | `postcss` | Upgrade dependency chain | @joefoxing | 2026-06-14 | Open |
| 1119108 | `ws` | Moderate | Uninitialized memory disclosure | `>=8.20.1` | `happy-dom > ws` | Accept temporarily (test/dev dependency path) | @joefoxing | 2026-06-14 | Open |

---

## 2. Risk Acceptance Rules

Use temporary acceptance only when all are true:

1. Severity is not high/critical.
2. Vulnerability is limited to dev/test tooling path, not runtime production request path.
3. Compensating control exists (restricted environment, no untrusted input path, no public exposure).
4. Owner and due date are assigned.

If any condition fails, remediation is required before release.

---

## 3. Exit Criteria for Closing Security Gate

1. `corepack yarn audit --level high` returns no high/critical (already true).
2. Each moderate finding is either:
   - fixed and verified, or
   - explicitly accepted with owner, due date, and rationale.
3. Register status updated to `Closed` for all items or carries formal accepted risk sign-off.

