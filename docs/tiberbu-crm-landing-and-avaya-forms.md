# E3 — Public Landing + Demo CTA · E4 — Avaya Telephony Forms

**Status:** review · **Date:** 2026-07-30 · **Site:** `cr-dev.tiberbu.app`

---

## E3-S1 — Public landing page

`crm/www/index.py` + `index.html` — branded Tiberbu splash at site root (via `home_page="index"`, E2-S1). Guests see it; logged-in users redirect to `/crm` (avoids the `default_workspace` regression). Hero ("The CRM built for better health outcomes"), tagline "Powering Better Health", feature grid, sticky nav, final CTA, footer — all Tiberbu red/black/white, no stock Frappe chrome.

**Proof:** `/tmp/crm-proof/e2-01-landing.png` (guest), curl `/` → 200 with branded title.

## E3-S2 — Demo CTA → real CRM Lead

The landing's primary CTA ("Request a Demo") points at `/crm-form/request-a-demo`, a **published native Web Form** created via the CRM's own form engine (`crm/api/form.py::save_form`), targeting `CRM Lead`. Submission runs through Frappe's Web Form `accept()` → `enrich_form_submission` (stamps `source = "Web Form"`). `index.py::_demo_form_route()` resolves the published form dynamically and falls back to `/login` so the CTA is never a dead link.

**Proof (round-trip):** browser filled + submitted the form → `CRM-LEAD-2026-00001` created (Ada Health, correct email/phone/org, `source: Web Form`, `status: New`); success message rendered. `/tmp/crm-proof/e3-01-demo-form.png`, `e3-03-demo-submitted.png`.

**Note:** publishing a CRM form also exposes Frappe's generic form at `/<route>` (unbranded) alongside the branded `/crm-form/<route>` — documented behaviour of `save_form` mirroring `published`. The landing links only to the branded URL.

---

## E4 — Avaya telephony platform (forms only; connect is E5/E6, gated)

Pattern mirror: existing `crm/integrations/exotel/` + `crm_exotel_settings`.

### E4-S1 — `CRM Avaya Settings` (Single doctype, dual-mode)

`crm/fcrm/doctype/crm_avaya_settings/` — `enabled`, `mode` (Select `Cloud (AXP)` / `On-Prem (Aura/AES)`, gates fields via `depends_on`), `record_calls`, `webhook_verify_token`, `connector_endpoint` (common). **Cloud:** `axp_base_url`, `axp_region`, `account_id`, `client_id`, `client_secret`(Password). **On-Prem:** `aes_host`, `cm_id`, `cti_user`, `cti_password`(Password), `dmcc_or_tsapi_link`, `recorder_base_url`, `recorder_auth`(Password). All 3 secrets are `Password` fieldtype. `mandatory_depends_on` enforces each mode's required fields only when that mode is active + enabled.

**Proof:** live `DocField` meta dump confirms every field + mode-gating `depends_on` + the 3 Password secrets; doctype saves clean with `enabled=0` and all secrets empty (`get_password → None`). Both-mode form render: `/tmp/crm-proof/e4-avaya-both-modes.png` (rendered from the live meta; the desk form itself is blocked on cr-dev only by ERPNext's setup-wizard — no Company — unrelated to this doctype).

### E4-S2 — Extend enums

- `crm_call_log.json` `telephony_medium` options → `\nManual\nTwilio\nExotel\nAvaya`; `.py` Literal updated. Verified in DB meta.
- `crm_telephony_agent.json` → added `avaya_number` (Data, in field_order) + `default_medium` options gain `Avaya`; `.py` Literals updated.

### E4-S3 — Register Avaya (backend + frontend)

- `crm/integrations/api.py`: `is_call_integration_enabled()` now returns `"avaya": bool(...enabled)`; `_get_recording_credentials()` has an `Avaya` branch returning `None` cleanly when unconfigured (so the recording proxy attempts without auth rather than 500-ing). **Verified:** API returns `{"avaya": false, ...}` with no creds.
- `frontend/src/components/Telephony/AvayaCallUI.vue` (new, mirrors `ExotelCallUI.vue`) + registered in `CallUI.vue` (import, ref, template, `enabledIntegrations` list, dialog options `['Twilio','Exotel','Avaya']`, `makeCallUsing` branch). **`yarn build` passes.**

**E5-S3 note:** the backlog lists "AvayaCallUI registered in CallUI" under E5-S3 — that registration is done here (it's the frontend wiring, buildable now). E5 proper is the *connect* handler that makes it functional.

## Fork-safety

New additive files: the whole `crm_avaya_settings/` doctype, `AvayaCallUI.vue`. Marked minimal edits to shared files: `crm_call_log.{json,py}` (+`Avaya` enum), `crm_telephony_agent.{json,py}` (+field/enum), `integrations/api.py` (2 branches, commented `E4-S3`), `CallUI.vue` (provider registration). All small and clearly attributable on upstream merge.

## Watch-outs

- The `AvayaCallUI.updateStatus()` mapper and `make_a_call` URL are **placeholders** — the real Avaya webhook payload + outbound API are E5/E6 discovery items. Clicking call before E5 fails gracefully with a toast (no crash). See `avaya-integration-prd.md` §9.
- `setup_complete` was set to 1 on cr-dev (dev-only) during this work; ERPNext still shows its setup wizard because no Company exists (independent of CRM).
