# E7 — Support-Journey Automation

**Status:** review · **Date:** 2026-07-30 · **Site:** `cr-dev.tiberbu.app`

Composes EXISTING CRM primitives (CRM Task, ToDo assignment, CRM Notification, SLA) — no new engine. New additive module: `crm/automation/support_journey.py`, wired via `hooks.py` `doc_events`.

---

## E7-S1 — Onboarding journey (Deal Won → staged tasks + assignment + notify)

Handler: `on_deal_update` (CRM Deal `on_update`). Per project rules this is an **explicit,
named** handler that detects the trigger itself — `_has_transitioned_to_won()` fires the
journey **only on the transition into a Won status** (checks `has_value_changed("status")`
+ previous status was non-Won), not as a blind `on_update` side-effect and not on every save.

Seeds 4 staged `CRM Task`s (due-date offset from today), assigned to the deal owner:
- Welcome call — day +1, High
- Send onboarding pack & credentials — day +2, Medium
- Schedule kickoff/implementation — day +5, Medium
- Day-30 check-in — day +30, Low

Then a CRM Notification to the owner. **Idempotent** — a marker-task existence check
prevents re-seeding on subsequent saves (incl. Won A → Won B).

**Proof:** Deal `Qualification → Won` created exactly 4 tasks with correct priorities/offsets
assigned to Administrator; re-save kept the count at 4 (idempotent). Console test output
recorded.

## E7-S2 — Missed-call recovery (missed Avaya call → callback task + notify)

Handler: `on_call_log_update` (CRM Call Log `after_insert` + `on_update`). Fires only for
`telephony_medium == "Avaya"` + `type == "Incoming"` + status in
{No Answer, Missed, Failed, Busy}. Creates a High-priority callback `CRM Task` for the
receiving agent (`receiver`), linked to the call log, + a notification. Idempotent per call log.

**Proof:** a missed inbound Avaya call log created 1 High-priority task "Call back missed
call from +254700999888" assigned to the receiver. Console test output recorded.

## Dependency note

E7-S2 depends on real Avaya call events, which arrive only once E5/E6 (Avaya connect) is
live. The handler is complete and proven against a synthetic call log today; it will
trigger automatically on real missed calls once the E5 webhook writes Avaya call logs.

## Fork-safety

New additive module `crm/automation/`. Marked minimal edit to `hooks.py`: appended the
handler to `CRM Deal.after_insert` + `on_update` and a new `CRM Call Log` doc_events entry,
all commented `E7`.

## Second-pass review fixes (applied)

- **Background execution**: the journey bodies (`run_onboarding_journey`,
  `run_missed_call_recovery`) now run via `frappe.enqueue(..., enqueue_after_commit=True)`,
  not inline on the user's save — this keeps `ignore_permissions=True` on a legitimate
  (non-request) path per project rules and adds zero latency to the Deal/Call-Log write.
  The doc_event handlers only detect the trigger and enqueue.
- **Create-as-Won** (#6): `on_deal_update` is now on `after_insert` too, and `_entered_won`
  treats a new deal saved directly with a Won status as an entry. Verified: create-as-Won → 4 tasks.
- **Missed-call fallback assignee** (#4): when `receiver` is empty (nobody answered), the
  callback task falls back to the call log `owner` instead of being orphaned. Verified.
- **Notification from_user** (#5): `_notify` uses a distinct `from_user` (triggering user /
  call owner, else Administrator) so `notify_user` doesn't early-return on `owner==assignee`.
  Verified: notifications fire.
- **NIT**: dropped the invalid `"Missed"` status (not a real CRM Call Log option); removed
  the unused `import frappe` from the Avaya settings controller.

## Ops note

Schema/hook change → requires `bench --site <site> migrate` (none needed for E7 itself, no
new fields) + `bench restart` (new `crm/automation/` module + `hooks.py` doc_events). Both
were run on cr-dev before the proofs above.
