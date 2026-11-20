---
name: crm-onboarding
description: Set up Frappe CRM for a business and see it through to daily use. Ask how they sell, agree a setup plan in their words, set up stages, lost reasons, sources, products, currency, forecasting, the team, assignment and email, then check every step on the site's data. Use when someone wants to set up, implement or start using CRM, asks what to do next in their CRM setup, or asks whether their team is really using it, when the site runs the CRM app.
---

# Setting up Frappe CRM

This skill takes a business from a fresh CRM site to a team that sells in it every week. It does not repeat the data rules: read the `frappe-crm` skill that ships with CRM (`skills/frappe-crm/`, in the site's assistant `crm/frappe-crm`) before you write a lead, deal or status.

Every step here is a document read or write, or a whitelisted method, so it works the same from the site's assistant, MCP or frappectl. You act as the connected user. Setting up needs System Manager or Sales Manager. Inviting a Sales Manager or System Manager needs System Manager.

The work has four parts, in this order: **agree the plan**, **set up**, **start using**, **check**. Setting up is your job. Using is theirs: their people add the leads and move the deals, and you check that they did.

## Before you start

1. Call `frappe.auth.get_logged_user`, then `crm.api.session.get_users`: it returns every CRM user with their `role`. Find yourself in it. Without Sales Manager or System Manager, stop and say who can do the setup.
2. Look for a plan. List `Note` with `{"title": ["like", "CRM setup plan%"]}`. If one exists, read it and go to "Check where it stands". Do not start a second plan.
3. Read what is already there: `CRM Lead Status`, `CRM Deal Status` (fields `name`, `type`, `position`), `CRM Lost Reason`, `CRM Lead Source`, `FCRM Settings`, and counts of `CRM Lead` and `CRM Deal`. A site with real leads and deals is not a fresh site. Every change to a status or setting then touches records people use.

## 1. Agree the plan

Ask the questions in `reference/interview.md`. Ask one or two at a time. When the person gives you call notes, take every answer you can from them and ask only for what is missing.

Start with the fit question. When what they lose track of is orders, stock or payments, not prospects, say so: CRM will not fix that, and ERPNext should come first.

Then build the plan from `reference/steps.md`. Every step there says when it applies. Keep the steps that apply, drop the rest, and for each one write:

- the title in their words: "Your stages are Enquiry, Site visit, Quote, Won, Lost", not "Configure CRM Deal Status"
- one line on why, tied to what they said
- who does it: you, them, or their team
- what "done" means on the site's data, from the step's **Done when**

Ask what "CRM is working" looks like for them in a month, and turn the answer into a check you can run on their data, such as "every new enquiry is a lead within a day". If you cannot check it from data, rewrite it with them until you can. This is their live condition.

What they ask for that this skill does not set up goes in the plan under "Asked for, not in this setup", in their words. See "Scope".

**Stop here.** Post the plan, end your turn and wait for their reply. Agree it with them, not with yourself. On a yes, save it as a Note (`reference/plan.md`) so the next session starts where this one ended.

## 2. Set up, one step at a time

Work the setup steps of the plan in order. For each one:

1. Read the records the step touches.
2. Show the change list: for each record, the doctype, the name, each field with its old and new value. Write "new" for a record you will create.
3. Wait for a yes. Ask even when the chat approves writes on its own: the person must see each change to their CRM before it is made.
4. Write, ten records or fewer at a time.
5. Run the step's **Done when** check. Say whether it passed, and what the data showed.
6. On a pass, mark the step done in the plan (show that edit too), and name the next step.

Warn before a change that is hard to undo. These are listed in "One-way doors".

To bring in their existing leads or deals: under about 50 rows, create them in batches of ten after one test row. Above that, prepare the file with them, and have them import it with Data Import from the list view. Then check the counts against their file.

## 3. Start using

From here the steps belong to their team: the first real lead, the first deal won or lost, follow-ups as tasks. **Never create their leads, deals, notes, tasks or calls for them**, even when asked. A record you made proves nothing about whether they use CRM. Explain how to do it in the app, then check that it happened.

A record counts for a use step when it was made after setup by someone who is not a setup user. The plan lists the setup users: an implementer or partner who set up the site for them. When the business set itself up, the list is empty and every record after setup counts.

## 4. Check where it stands

When they ask "where are we", "what's next" or "is it working", run the **Done when** check of every step in the plan. Reads only. Then answer in three lines: what is done, what is next, the one thing to do now. Under that, a short table: step, done or not, what the data shows.

They are **live** when their live condition holds and their own people used CRM in the last 7 days. Check it again 30 and 90 days after the plan's start date. Live at day 90 is the goal; setup is not.

Offer, at the end of every session, to add three lines to the plan's log: what was done, what failed, what is next.

## Scope

This skill sets up standard CRM: statuses, lost reasons, sources, products, currency and exchange rates, forecasting, users and roles, assignment rules, an email account and email templates, organizations and contacts, and importing open leads and deals.

It does not set up custom fields, form layouts, form scripts, automations, SLAs, the sales hierarchy, telephony, WhatsApp, web forms, Facebook or other lead capture, or the ERPNext link. Note each ask in the plan and say it is not part of this setup.

## One-way doors

Ask before each of these, and say what will happen:

1. **CRM currency.** `FCRM Settings` `currency` becomes read-only once saved. Confirm it twice.
2. **Forecasting.** Turning on `enable_forecasting` makes every deal save fail, old deals too, until `expected_deal_value` and `expected_closure_date` are set. Count the open deals without them first.
3. **Changing a status that records use.** Rename it (a rename keeps every lead or deal on it) rather than create a new one and delete the old one. Never delete a status, reason or source that records use.
4. **Inviting people.** Each invite sends an email. Show the list first.
5. **Imports.** A wrong import makes hundreds of records to clean up. Test with one row first.

Everything else can be changed back, so do it after the change list and a yes.

## When a call fails

An error that names its cause has a fix in the traps below or in `frappe-crm`. For an error with no cause:

1. Run the call once more. Change only what could matter.
2. Make it smaller until you find the smallest call that still fails.
3. Stop and give the person the exact call and the exact error.

Never work around a permission error. Say which role the step needs.

## Traps

- **Statuses are site data, and their `type` carries the meaning.** Every site starts with 7 lead statuses, 7 deal statuses and 9 lost reasons. Rename or remove these to match the plan, and give each new status a `type` and a `position`. Keep at least one Won and one Lost deal status.
- **Converting a lead sets its status to `Qualified`**, but only when a lead status with that exact name exists. Rename it away and converted leads keep their old status. Keep it, or tell the person.
- **A deal gets its `closed_date` when it moves to a status of type Won.**
- **A Lost status needs a lost reason**, and `Other` also needs `lost_notes`. Set up the reasons before anyone loses a deal.
- **New email templates are hidden.** An `Email Template` shows in CRM only with `enabled` 1 and `reference_doctype` set to `CRM Lead` or `CRM Deal`.
- **`CRM Organization` has no type field.** Partners, agents and banks are organizations like customers. A type field is a custom field: note the ask.
- **An owner is `lead_owner` or `deal_owner`,** not the record's creator. An assignment rule sets it.
- **Never take a password in chat.** The person connects their mailbox in CRM's settings, under Email Accounts. You check the result.
- **Read in pages.** Ask for 100 rows or fewer at a time. For counts, count; do not list.

## Reference

- `reference/interview.md`: the questions, in order, and what each answer decides.
- `reference/steps.md`: every step, when it applies, what you do, what they do, and its Done when check.
- `reference/plan.md`: how to write the plan as a Note on the site.
