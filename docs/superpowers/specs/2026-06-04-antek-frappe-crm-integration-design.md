# AnTek Materials Frappe CRM Integration Design

## 1. Objective

Integrate the architecture from `AnTek-Materials---Frappe-CRM-Integration-Custom-App-Architecture.md` into this repository by implementing:

- Tripartite credit-contract modeling
- Credit ledger accounting events
- Automatic debt-limit lock control
- Signed outbound synchronization to FastAPI (`/api/v1/logistics/credit-sync`)
- Deployment and CI-oriented documentation for operational rollout

This implementation targets the existing `crm` Frappe app (same repository), not a separate external app package.

## 2. Scope

### In scope

1. New business DocTypes:
   - `Tripartite Contract`
   - `Credit Ledger Entry`
2. Business logic for debt aggregation, remaining credit computation, and lock flag transitions.
3. Hook wiring on ledger submit to recompute contract state.
4. FastAPI sync client with signature support and idempotency metadata.
5. Config surface for integration settings.
6. Tests for core computation and hook behavior.
7. Deployment/operations docs mapped to current repo workflow.

### Out of scope

1. Changes in FastAPI service implementation itself.
2. Mobile client UX changes in C-Logs.
3. Re-architecture of existing CRM core DocTypes.

## 3. Domain Model

## 3.1 Tripartite Contract (DocType)

Represents one three-party credit arrangement linked to an originating deal.

Required fields:

- `contract_id` (Data, unique, human-readable)
- `deal_link` (Link -> `CRM Deal`)
- `contractor` (Link -> `CRM Organization`)
- `owner` (Link -> `Contact` or `CRM Contact`, implementation aligned to existing doctype names)
- `credit_limit` (Currency, default `200000000.00`)
- `current_debt` (Currency, read-only)
- `remaining_credit` (Currency or derived read-only field)
- `is_locked` (Check, read-only)

Operational fields (for sync observability):

- `sync_status` (Select: `Pending`, `Synced`, `Failed`)
- `sync_error` (Small Text)
- `last_synced_at` (Datetime)
- `last_sync_event_id` (Data)

## 3.2 Credit Ledger Entry (DocType)

Represents a debt-changing transaction tied to one contract.

Required fields:

- `entry_id` (Data, autoname/series or UUID)
- `tripartite_contract` (Link -> `Tripartite Contract`)
- `transaction_type` (Select: `Delivered`, `Owner Payment`)
- `reference_doc` (Data)
- `amount` (Currency; positive for delivery debt increase, negative for owner payment debt decrease)
- `posting_datetime` (Datetime, default now)

Constraints:

- Submitted (`docstatus=1`) entries are source of truth for debt computation.
- Cancellations/re-submissions must be reflected by recomputation from submitted entries.

## 4. Processing Flow

## 4.1 Ledger Submit Flow

1. User submits `Credit Ledger Entry`.
2. Hook validates semantic correctness:
   - Contract exists and is active.
   - Amount sign aligns with transaction type policy.
3. System recomputes contract debt as sum of submitted ledger entries for that contract.
4. System updates contract:
   - `current_debt`
   - `remaining_credit = credit_limit - current_debt`
   - `is_locked = 1` when `current_debt >= credit_limit`, else `0`
   - `sync_status = Pending`
5. Post-commit sync dispatch sends signed webhook payload to FastAPI.
6. Delivery result updates sync status fields.

## 4.2 Outbound Sync Payload

Canonical payload:

- `event`: `credit_status_changed`
- `event_id`: deterministic/idempotent identifier
- `contract_id`
- `contractor_id`
- `current_debt`
- `credit_limit`
- `remaining_credit`
- `is_locked`
- `updated_at`

Headers:

- `X-AnTek-Signature`: HMAC signature generated from payload and configured secret.

## 5. Error Handling

1. Validation errors block submission with explicit user feedback.
2. Sync transport failures do not silently succeed:
   - Log structured error
   - Mark contract sync status as `Failed`
   - Persist error text and timestamp
3. Retry policy is bounded and configurable.
4. Duplicate submit/sync handling uses `event_id` to support idempotent downstream processing.

## 6. Repository Integration Plan (Implementation Targets)

Expected target areas:

- `crm/fcrm/doctype/` for new DocType JSON/Python assets
- `crm/hooks.py` for `doc_events` registration
- New integration module under `crm/integrations/` or `crm/antek_materials/` for sync client/service logic
- Tests under existing Python test structure near new modules
- Ops docs under repository docs path

Exact file placement will follow prevailing local patterns discovered during implementation.

## 7. Testing Strategy

1. Unit tests:
   - Debt aggregation function
   - Lock-state transition logic
   - Signature generation
2. DocType behavior tests:
   - Ledger submit updates contract snapshot correctly
   - Lock toggle at threshold crossing
3. Integration-facing tests:
   - Payload schema and fields
   - Failure-path state updates

## 8. Deployment & Operations

This integration will be deployable through existing bench/app migration flow for this repository:

1. Apply migrations for new DocTypes and fields.
2. Configure integration settings (endpoint, secret, timeouts).
3. Validate end-to-end with a non-production contract and ledger sequence.
4. Enable production synchronization and monitor sync status fields/logs.

CI guidance will include running relevant Python tests and migration validation steps required by this repository conventions.

## 9. Success Criteria

Integration is complete when:

1. Submitting a ledger entry updates contract debt and lock state deterministically.
2. Contract lock state reflects credit-limit policy exactly.
3. Webhook payloads are signed, idempotent, and operationally observable.
4. Failures are visible and actionable without breaking accounting workflows.
5. Tests cover core computation, hook behavior, and outbound payload behavior.
