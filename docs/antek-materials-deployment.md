# AnTek Materials deployment

## Prerequisites

- Frappe Bench v15+ with Python 3.12+
- MariaDB 10.6+
- CRM app on `develop` branch (requires Frappe v17-dev or later)

---

## Migrate

Run migrations on the production site to create the new DocTypes and apply the partner role custom fields patch:

```bash
bench --site production.antekmaterials.vn migrate
```

This will:
- Create tables for `Tripartite Contract`, `Credit Ledger Entry`, and `AnTek Integration Settings`
- Apply the `create_antek_partner_role_fields` patch (adds `partner_role` Select field to `CRM Organization` and `Contact`)

---

## Configure AnTek Integration Settings

1. In the Frappe desk, navigate to **AnTek Integration Settings** (Settings > AnTek Integration Settings)
2. Fill in:
   - **FastAPI Webhook URL**: full URL of the FastAPI `/webhook/credit-status` endpoint (e.g. `https://api.antekmaterials.vn/webhook/credit-status`)
   - **Signature Secret**: shared HMAC-SHA256 secret (32+ bytes recommended, stored as Password)
   - **Request Timeout (Seconds)**: default `5`; increase if FastAPI is on a slow network
   - **Max Retries**: default `3` (informational; retry logic is added in a later phase)
   - **Sync Enabled**: check to activate outbound sync; uncheck to pause without code changes
3. Save the settings.

---

## Operational verification

After deploying and configuring, run this smoke test:

```bash
# 1. Create a test contract (or use an existing one)
bench --site production.antekmaterials.vn execute crm.fcrm.doctype.tripartite_contract.tripartite_contract --args '{"contract_id":"SMOKE-001","credit_limit":1000000}'

# 2. Run the full AnTek test suite
bench --site test_site run-tests --app crm --module crm.fcrm.doctype.antek_integration_settings.test_antek_integration_settings
bench --site test_site run-tests --app crm --module crm.fcrm.doctype.tripartite_contract.test_tripartite_contract
bench --site test_site run-tests --app crm --module crm.fcrm.doctype.credit_ledger_entry.test_credit_ledger_entry
bench --site test_site run-tests --app crm --module crm.tests.test_fastapi_credit_sync
```

### Manual end-to-end check

1. Open a `Tripartite Contract` with `credit_limit = 200,000,000`
2. Create and Submit a `Credit Ledger Entry` with `transaction_type = Delivered`, `amount = 10,000,000`
3. Reload the contract — verify:
   - `current_debt = 10,000,000`
   - `remaining_credit = 190,000,000`
   - `credit_locked = 0`
   - `sync_status = Synced` (if FastAPI is reachable) or `Failed` (if not configured)
4. Check the FastAPI server logs to confirm the signed webhook arrived with the correct `X-AnTek-Signature` header

---

## Rollback criteria

If migration fails or the sync produces incorrect data:

1. **Rollback migration**: `bench --site production.antekmaterials.vn rollback`
2. **Disable sync**: Set `sync_enabled = 0` in **AnTek Integration Settings** to stop outbound calls without reverting code
3. **Remove patch**: If `create_antek_partner_role_fields` needs to be undone, delete the `partner_role` Custom Fields from the CRM Organization and Contact DocTypes in the desk

---

## CI integration

Add to your bench CI pipeline:

```yaml
- name: Run AnTek integration tests
  run: |
    bench --site test_site run-tests --app crm --module crm.fcrm.doctype.antek_integration_settings.test_antek_integration_settings
    bench --site test_site run-tests --app crm --module crm.fcrm.doctype.tripartite_contract.test_tripartite_contract
    bench --site test_site run-tests --app crm --module crm.fcrm.doctype.credit_ledger_entry.test_credit_ledger_entry
    bench --site test_site run-tests --app crm --module crm.tests.test_fastapi_credit_sync
```
