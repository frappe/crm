# DebTest: Frappe CRM Lead Duplicate Mobile Number

## Change
- Add backend duplicate detection for `CRM Lead.mobile_no`
- Reuse existing phone parsing/comparison utilities
- Block duplicate active leads across formatting variants

## Risk Level
- Medium

## Failure Modes Reviewed
- Duplicate leads with equivalent phone formatting bypass validation
- Self-update blocked as a false duplicate
- Converted leads incorrectly block new leads
- Slow or noisy full-table matching on unrelated values
- Test fixture generation broken by duplicate enforcement

## Verification
- `python3 -m py_compile crm/fcrm/doctype/crm_lead/crm_lead.py crm/fcrm/doctype/crm_lead/test_crm_lead.py`
- `git diff --check`
- `bench --site crmtest.local run-tests --module crm.fcrm.doctype.crm_lead.test_crm_lead`

## Test Result
- Passed
- `20` integration tests, `OK`

## Findings During QA
- Frappe's synthetic `_T-...` integration-test fixtures legitimately create repeated lead records.
- Duplicate validation initially blocked fixture seeding.
- Narrowed bypass to in-test synthetic records only, preserving production behavior.
- An invalid-phone duplicate test was removed because Frappe rejects that input before CRM validation runs, so it was not a real product path.

## Residual Risk
- Duplicate detection currently applies to lead-vs-lead only, not lead-vs-contact.
- Matching still depends on current utility behavior for region inference, which is acceptable for this scoped PR.
