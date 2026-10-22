---
name: frappe-crm
description: Work with sales data in Frappe CRM on a Frappe site. Use to find, create or update leads, deals, contacts and organizations, convert a lead to a deal, read a lead's or deal's timeline, add notes, tasks or comments, send email from a lead or deal, or assign owners, when the site runs the CRM app.
---

# Frappe CRM

CRM tracks sales in two documents. A `CRM Lead` is a prospect that is not yet qualified. A `CRM Deal` is a qualified opportunity, usually made by converting a lead. Every step here is a document read or write, or a whitelisted method, so it works the same from the site's assistant, MCP or frappectl. Each user sees the leads and deals that their roles and the sales hierarchy allow.

## 1. Data model

- `CRM Lead`: a person (`first_name` is required) and an `organization` name as text. Also `email`, `mobile_no`, `status`, `lead_owner`, `source`, and `converted` (1 after conversion).
- `CRM Deal`: `organization` links to a `CRM Organization`. The `contacts` table links `Contact` records, with one marked `is_primary`. Also `status`, `deal_owner`, `deal_value`, `expected_deal_value`, `expected_closure_date`, `probability`, and `lead` (the source lead).
- `CRM Lead Status` and `CRM Deal Status`: each site defines its own statuses. Read them first. The `type` field gives the meaning: `Open`, `Ongoing`, `On Hold`, `Won` or `Lost`.
- `CRM Organization` holds companies. `Contact` holds people, with emails in `email_ids` and phones in `phone_nos`.
- `FCRM Note` (`title`, `content`) and `CRM Task` (`title`, `status`, `priority`, `assigned_to`, `due_date`) link to a lead or deal through `reference_doctype` and `reference_docname`.
- `CRM Call Log` records calls. Its `reference_doctype` and `reference_docname` point to the lead or deal.

## 2. Operations

- Convert a lead: call `crm.fcrm.doctype.crm_lead.crm_lead.convert_to_deal` with `lead`. It makes the deal, contact and organization and marks the lead converted. It returns the deal name. Pass `if_converted: "Return Existing"` to get the existing deal on a retry instead of a second deal.
- Read a timeline: call `crm.api.activities.get_activities` with `name` (a lead or deal). It returns field changes, emails, comments, calls, notes, tasks and attachments.
- Change deal contacts: call `add_contact`, `remove_contact` or `set_primary_contact` in `crm.fcrm.doctype.crm_deal.crm_deal`, each with `deal` and `contact`.
- Add a comment: call `crm.api.comment.add_comment` with `reference_doctype`, `reference_name` and `content` (HTML).
- Send an email: call `frappe.core.doctype.communication.email.make` with `doctype`, `name`, `recipients`, `subject`, `content` and `send_email: 1`.
- Assign an owner: set `lead_owner` or `deal_owner`. CRM then shares the document with that user and assigns it to them.
- Create a lead from a call: call `crm.fcrm.doctype.crm_call_log.crm_call_log.create_lead_from_call_log` with `call_log` and `lead_details`.

## 3. Traps

- **Do not make a deal from a lead's data yourself.** Use `convert_to_deal`, or the lead stays unconverted and loses its link to the deal.
- **A lead with a `Lost` status cannot be converted.**
- **A `Lost` status needs `lost_reason`.** When `lost_reason` is `Other`, `lost_notes` is also required.
- **Forecasting can make deal fields mandatory.** When it is on in `FCRM Settings`, every deal save needs `expected_deal_value` and `expected_closure_date`.
- **Statuses are site data.** Do not assume `New`, `Qualified` or `Won` exist. Read the status doctypes.
