# E5 / E6 — Avaya Connect (GATED / BLOCKED)

**Status:** blocked (external dependency) · **Date:** 2026-07-30

---

## Why these are not built

E5 (Avaya Cloud/AXP connect) and E6 (On-Prem Aura/AES connect) are **gated on Tiberbu
providing:**

1. **Confirmed Avaya edition** (BRD R1) — Cloud AXP vs on-prem Aura/AES determines the
   integration mechanism.
2. **Live credentials** — AXP `client_id`/`client_secret`/`account_id`/base URL, or
   AES host/CTI user+password/DMCC-TSAPI link/recorder auth.
3. **Confirmed API contracts** — the real inbound webhook payload shape and the outbound
   `make_a_call` REST/CTI contract. Per the handoff and `avaya-integration-prd.md` §9,
   these are **discovery items**; the rule is **do NOT invent Avaya payloads as real**.

Building handler logic against guessed payloads would produce code that must be rewritten
once the real contract lands — wasted effort and a correctness risk. So the connect layer
waits; everything that does NOT depend on live Avaya is already done (E4).

## What IS ready (so credential handoff is turnkey)

- **`CRM Avaya Settings`** (E4-S1) — dual-mode config doctype, all secrets as Password.
- **Enums** (E4-S2) — `Avaya` in `CRM Call Log.telephony_medium` and
  `CRM Telephony Agent.default_medium` + `avaya_number`.
- **API registration** (E4-S3) — `is_call_integration_enabled()` reports `avaya`;
  `_get_recording_credentials()` has an Avaya branch (returns None cleanly when unconfigured).
- **`AvayaCallUI.vue`** (E4-S3 / satisfies **E5-S3**) — mirrors `ExotelCallUI`, registered
  in `CallUI.vue`; listens on the `avaya_call` realtime event; outbound calls
  `crm.integrations.avaya.handler.make_a_call`. Fails gracefully with a toast until the
  handler exists.

## What E5/E6 will add (when unblocked)

Mirror `crm/integrations/exotel/handler.py` (reference mapped in the E4 research):

- **E5-S1 (Cloud/AXP):** `crm/integrations/avaya/handler.py` —
  `@frappe.whitelist(allow_guest=True) handle_request` (validate `?key=` against
  `webhook_verify_token`, `frappe.publish_realtime("avaya_call", payload)`, create/update
  `CRM Call Log` with `telephony_medium="Avaya"`, `get_contact_by_phone_number` screen-pop).
- **E5-S2:** `make_a_call` (AXP REST outbound, must return a dict with a call-id key the UI
  reads); recording URL stored on the call log, played via the existing
  `get_recording_url` proxy (already Avaya-aware from E4-S3).
- **E6-S1 (On-Prem):** same handler with `mode == "On-Prem"` — a server-side CTI connector
  bridging AES (TSAPI/DMCC) events → the same `handle_request` webhook path.

Finalize `AvayaCallUI.updateStatus()` against the confirmed payload at that point.

## Action to unblock

Send `docs/avaya-integration-prd.md` (discovery questionnaire) to the Tiberbu Avaya team;
resume E5 once edition + credentials + payload contracts are confirmed.

## Compliance gate (before recording go-live, BRD R2)

Call-recording consent/retention + Kenya DPA 2019 review must complete before enabling
`record_calls` in production — independent of the technical connect work.
