---
name: frappe-crm
description: Work with sales data and the sales team in Frappe CRM on a Frappe site. Use for any question about agents, sales reps, salespeople or the sales team, their performance or workload, revenue, the pipeline, follow-ups or replies waiting, and to find, create or update leads, deals, contacts and organizations, convert a lead to a deal, read a lead's or deal's timeline, add notes, tasks or comments, send email from a lead or deal, or assign owners, when the site runs the CRM app.
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
- Send an email: call `frappe.core.doctype.communication.email.make` through `run_action`, with `doctype`, `name`, `recipients`, `subject`, `content` and `send_email: 1` in `args`. See section 4 first.
- Assign an owner: set `lead_owner` or `deal_owner`. CRM then shares the document with that user and assigns it to them.
- Create a lead from a call: call `crm.fcrm.doctype.crm_call_log.crm_call_log.create_lead_from_call_log` with `call_log` and `lead_details`.

## 3. Traps

- **Do not make a deal from a lead's data yourself.** Use `convert_to_deal`, or the lead stays unconverted and loses its link to the deal.
- **A lead with a `Lost` status cannot be converted.**
- **A `Lost` status needs `lost_reason`.** When `lost_reason` is `Other`, `lost_notes` is also required.
- **Forecasting can make deal fields mandatory.** When it is on in `FCRM Settings`, every deal save needs `expected_deal_value` and `expected_closure_date`.
- **Statuses are site data.** Do not assume `New`, `Qualified` or `Won` exist. Read the status doctypes.

## 4. Questions about work to do

- **Who is waiting on a reply.** `awaiting_reply_since` is set on `CRM Lead` and `CRM Deal`. Leave out leads with `converted = 1` and records whose status type is not `Open` or `Ongoing`. One record is one count, so two records for one person count twice.
- **Reading a conversation.** `get_activities` does not list WhatsApp. On sites with the WhatsApp app, also read `WA Message` by `reference_doctype` and `reference_docname`.
- **Listing records.** Call `read_records` or `run_report`, so the user gets a table. Do not write the records out as text.
- **Sending email.** `send_email: 1` sends at once. Show the draft in your reply first. When the user agrees, send it through `run_action`, so the approval shows the recipients, subject and content. Do not send from `execute`, because its approval shows only your description.
- **Facts with no field.** "Renewal", "at risk" and contract dates have no field. They can come only from a message or a note, so say which one you read. Do not infer them.
- **Follow-ups.** `CRM Task` keeps no completion date and no old due dates, so "missed" cannot be worked out. Say "due and still open". All-day tasks are overdue after their day ends.
- **Team questions.** Count a record for its owner, or its first assignee if it has no owner, and never for both. A manager in the Sales Hierarchy sees only their subtree, and does not see leads with no owner or assignee.
- **Response time.** `first_response_time` and `first_responded_on` are wrong for WhatsApp and calls, and mix working hours with wall-clock time. To find records nobody answered in time, use `response_by` in the past with `first_responded_on` and `last_outbound_at` both empty.
- **Pipeline.** `status_change_log` on a deal holds each move with `from`, `to` and `to_date`. Order stages by `CRM Deal Status.position`. Treat `Lost` and `On Hold` as exits, not steps. The open row, with no `to_date`, gives the time in the current stage.

## 5. Questions about people and performance

- **"Agent", "rep", "salesperson", "my team" and "my organization".** On a site with CRM these mean CRM sales users: enabled users with the Sales User or Sales Manager role, not Administrator. Do not ask whether the user means AI agents, telephony agents or employees.
- **"Best", "top" or "performing" with no measure.** Rank by the value of deals won: deals whose status type is `Won`, by `deal_owner`, with `closed_date` in the period, summing `deal_value` × `exchange_rate` for the site's base currency. Show the number of deals won beside it. With no period given, use the last 30 days.
- **Answer first, then offer other measures.** Give the ranking with one line on what it used, for example "By value of deals won in the last 30 days". Then offer other measures: deals won by count, open pipeline (`expected_deal_value`), replies waiting, overdue follow-ups, or calls made. Ask a question instead only when no measure fits.
- **Win rate.** Only won deals get a `closed_date`. For lost deals in a period, use the `status_change_log` row whose `to` status has type `Lost`, with its `to_date`.
- **Whose people.** Read records as the user, so the Sales Hierarchy applies: a manager in the hierarchy sees their subtree only. Say so when the answer covers only part of the team.

## 6. Links

Each time an answer names a lead, deal, contact or organization, link it to its page in the CRM app, so the user can open it. Use the document `name` in the path and the person or company as the link text, for example `[Asha Rao](/crm/leads/CRM-LEAD-2026-00042)`.

- Lead: `/crm/leads/<name>`
- Deal: `/crm/deals/<name>`
- Contact: `/crm/contacts/<name>`
- Organization: `/crm/organizations/<name>`

Do not link to `/app/...`. Sales users often cannot open desk pages.
