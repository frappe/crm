# Story Definition Rules — Tiberbu CRM
**Owner:** Salim
**Version:** 1.0 — 2026-08-01

These rules exist because bad story definition is the #1 cause of wasted worker turns, cancelled tasks, and incomplete sprints.

---

## Rule 1 — One file, one story (the primary rule)

Every story must have a **primary file** — the single file the worker opens first and edits most. If a story touches more than 3 files, split it.

❌ Bad: "Add SES inbound + provision UI + DocType fields + Vue component"
✅ Good: Story A — `crm/email/ses_inbound.py`. Story B — `SESSettings.vue` (depends on A).

---

## Rule 2 — Explicit file list, no exploration

Every story must include an explicit **File List** section with full paths:

```
## Files to modify
- crm/api/ses.py  (primary)

## Files to create
- crm/email/ses_inbound_provision.py
```

A worker that has to spend turns finding files is wasting turns.

---

## Rule 3 — Quick wins first, blockers last

Order stories so:
1. Schema / DocType changes go first (no UI, no dependencies)
2. Python backend logic goes second
3. Vue frontend goes third (depends on backend types)
4. Integration / wiring goes last (depends on all of the above)

---

## Rule 4 — Explicit dependencies, no implicit assumptions

Every story must declare:
```
## Depends on
- Story 1.1 (ses_runtime.py exists and exports AwsSesRuntimeConfig)

## Blocks
- Story 2.1 (webhook handler imports provision module)
```

If a story has no dependencies, say "None". Never leave it blank.

---

## Rule 5 — Size cap: S/M/L with turn budget

| Size | Max files | Max new lines | Turn budget |
|------|-----------|---------------|-------------|
| S    | 1         | ~100          | 10          |
| M    | 2–3       | ~300          | 20          |
| L    | 3–5       | ~500          | 30          |

If a story is XL, split it before it enters Studio. No XL stories.

---

## Rule 6 — Acceptance criteria must be testable in 1 command

Every AC must be verifiable by running one command or checking one thing:

❌ Bad: "The SES inbound flow works correctly"
✅ Good: "bench execute crm.email.ses_inbound_provision.provision exits 0 and prints a dict with sns_topic_arn"
✅ Good: "POST to /api/method/crm.api.ses_inbound.receive with tampered signature → HTTP 403"

---

## Rule 7 — No story may touch the same file as an in-progress story

Check the active story list before writing a new story. Concurrent edits to the same file = merge conflicts = wasted turns.

---

## Rule 8 — Backend stories must include the expected function signature

```python
# Expected final signature:
def provision(aws_region_inbound: str, recipient_domain: str, ...) -> dict:
```

---

## Rule 9 — Frontend stories must include the component interface

```typescript
// Expected emits / props:
const provisionResource = createResource({ url: 'crm.api.ses_inbound_provision_api.provision', ... })
```

---

## Rule 10 — Every sprint must start with a dependency graph

Before any story enters Studio, draw the dependency graph. Stories with no incoming arrows go first.

---

## Rule 11 — context7 validation is mandatory before any framework decision

Before writing any Vue component, Frappe controller, hook registration, whitelist method,
DocType field, or API call pattern:

1. `mcp__context7__resolve-library-id` — map the library name to a context7 ID
2. `mcp__context7__query-docs` — fetch current upstream documentation

This applies to: Vue 3, frappe-ui, Vite, Frappe v15 Python, TanStack Query, Tailwind.
It applies even to patterns you believe you know — training data lags real releases.

If context7 is unreachable → surface it as a blocker. Do NOT fall back to memory.

---

## Rule 12 — Frappe-specific rules (mandatory)

- `bench restart` after every Python change — no exceptions.
- `bench migrate` after every DocType JSON change.
- Never use `frappe.get_all()` — use `frappe.get_list()` for user-facing reads.
- `ignore_permissions=True` only on scheduler/webhook paths — add `# SYSTEM-INTERNAL` comment.
- Never use f-strings in log/error messages — use `%`-formatting or string concat (Amazon Inspector flags f-strings as XSS).
- `override_email_send` must never rely on a configured Email Account existing.

---

## Checklist before submitting any story to Studio

- [ ] Single primary file identified
- [ ] Full file list included (modify + create)
- [ ] Dependencies explicitly declared
- [ ] Blocks explicitly declared
- [ ] Size is S, M, or L (no XL)
- [ ] All ACs are testable with 1 command
- [ ] Function/component interface included
- [ ] No other active story is touching the same files
- [ ] `bench restart` / `bench migrate` steps noted where needed
