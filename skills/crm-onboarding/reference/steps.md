# Steps

Each step has a key, a title to rewrite in their words, when it applies, what you do, what they do, and a **Done when** check. A check is a read on the site's data. Never mark a step done on someone's word alone, except where the step says so.

"Setup users" and "agreed" values come from the plan (`plan.md`). "After setup" means after the date the last setup step was marked done.

Always in the plan: `company`, `deal-stages`, `lost-reasons`, `sources`, `team`, `first-prospect`, `first-close`, `regular-use`, `weekly-use`. Add the rest when the interview turns them on.

## Set up

### `company`: Your company basics are in

- **Do:** set `FCRM Settings` `brand_name`, `brand_logo` (a file they give you) and `currency`. Set `System Settings` `currency` to the same value when it differs. `currency` is a one-way door.
- **Done when:** `FCRM Settings` `currency` is the agreed currency, and `brand_name` is set.

### `deal-stages`: Your deal stages follow how you sell

- **Agree:** their stages in their words, in order, and which one means won and which lost.
- **Do:** read `CRM Deal Status`. Rename the defaults that match a stage of theirs, create the missing ones, and remove the defaults no deal uses. Set `type` (Open, Ongoing, On Hold, Won, Lost), `position` and, if they want it, `probability`.
- **Done when:** the `CRM Deal Status` names equal the agreed list, with at least one of type Won and one of type Lost.

### `lead-stages`: New enquiries land as leads first

- **When:** they qualify an enquiry before it becomes a real deal, or get many enquiries. Otherwise leave it out and say they will work in deals only.
- **Do:** the same as `deal-stages`, on `CRM Lead Status`. Keep a status named `Qualified`, or tell them converted leads will keep their old status.
- **Done when:** the `CRM Lead Status` names equal the agreed list.

### `lost-reasons`: When you lose a deal, you pick why

- **Agree:** their three to six real reasons. Keep `Other`.
- **Do:** rename, create and remove `CRM Lost Reason` records (`lost_reason`, `description`).
- **Done when:** the `CRM Lost Reason` names equal the agreed list.

### `sources`: You can see where each prospect came from

- **Do:** create and remove `CRM Lead Source` records (`source_name`). One source is fine.
- **Done when:** the `CRM Lead Source` names include every agreed source.

### `products`: Your offerings are in CRM

- **When:** they sell set products, plans or packages, priced or not.
- **Do:** create `CRM Product` records: `product_code` (required), `product_name`, `standard_rate`.
- **Done when:** a `CRM Product` with `disabled` 0 exists for each agreed offering.

### `currencies`: Deals in more than one currency still add up

- **When:** they quote in more than one currency.
- **Do:** set `FCRM Settings` `service_provider` (`frankfurter.app` needs no key; another provider needs `access_key`, which they type in the settings form themselves).
- **They do:** create one deal in a second currency.
- **Done when:** `service_provider` is set, and a `CRM Deal` whose `currency` differs from the CRM currency has `exchange_rate` other than 1.

### `forecasting`: You can see what is likely to close, and when

- **When:** they said they cannot see what will close, or someone reviews the pipeline.
- **Do:** first count open deals without `expected_deal_value` or `expected_closure_date`, and have them filled. Then set `FCRM Settings` `enable_forecasting` to 1. It is a one-way door.
- **Done when:** `enable_forecasting` is 1, and no open deal lacks `expected_deal_value` or `expected_closure_date`.

### `team`: Everyone who sells can sign in

- **Agree:** names, work emails, and who is a manager.
- **Do:** show the list, then call `crm.api.invite_by_email` with `emails` (comma-separated) and `role` (`Sales User`, `Sales Manager` or `System Manager`), once per role. People who already have a user: `crm.api.user.add_existing_users` with `users` and `role`. Set `User` `language` when they work in another language. An invitation expires after 3 days.
- **They do:** each person accepts the email and signs in.
- **Done when:** each agreed person is in `crm.api.session.get_users` with the agreed `role`, and their `User` has a `last_login`. A `CRM Invitation` still `Pending` or `Expired` means they have not accepted.

### `manager`: Your manager sees the whole pipeline

- **When:** someone reviews other people's deals.
- **Do:** `crm.api.user.update_user_role` with `user` and `new_role` `Sales Manager`. Needs System Manager.
- **Done when:** the agreed manager has the Sales Manager role.

### `assignment`: New prospects go to the right person

- **When:** more than one seller, and follow-ups slip or they named who handles what.
- **Agree:** the rule in their words, such as "web leads go to Asha and Ravi in turn".
- **Do:** create an `Assignment Rule` with `document_type` `CRM Lead` (or `CRM Deal`), a `description`, `rule` (`Round Robin`, `Load Balancing` or `Based on Field`), `users`, `assignment_days`, and the condition in both `assign_condition` (Python, such as `source == 'Website'`) and `assign_condition_json` (`[["source","==","Website"]]`), so CRM's own settings can show and edit it. An assignment sets `lead_owner` or `deal_owner`.
- **Done when:** an `Assignment Rule` on that doctype with `disabled` 0, the agreed users and the agreed condition. After setup, a new lead that matches has an owner.

### `email`: Your inbox is connected, so emails show on the deal

- **When:** they sell over email.
- **They do:** add the mailbox in CRM, under Settings, Email Accounts. They type the password or sign in there. Never take it in chat.
- **Do:** check the result, and say which settings to pick.
- **Done when:** an `Email Account` with `enable_outgoing` 1 and `enable_incoming` 1. After a test, a `Communication` linked to a `CRM Lead` or `CRM Deal` (`reference_doctype`, `reference_name`).

### `templates`: Your common emails are one click away

- **When:** they send the same emails again and again.
- **Agree:** which emails, and their own wording or a sample.
- **Do:** draft each `Email Template` (`name`, `subject`, `response` in HTML) in their voice, with `enabled` 1 and `reference_doctype` `CRM Lead` or `CRM Deal`. Use only their facts.
- **Done when:** an `Email Template` with `enabled` 1 and `reference_doctype` set, for each agreed name.

### `import`: Your open prospects and deals are in

- **When:** they have open leads or deals anywhere: a sheet, a notebook, another CRM.
- **Agree:** the file, what to drop, and who owns which rows.
- **Do:** see "Set up" in `SKILL.md` for the size rule. Map their columns to `CRM Lead` or `CRM Deal` fields with them, and owners to users. Statuses must exist first.
- **Done when:** the open `CRM Lead` and `CRM Deal` counts equal their file minus the dropped rows, and every open deal has a `deal_owner` and a `status`.

### `network`: Your partners and agents are in CRM

- **When:** third parties that are not customers matter to deals.
- **Do:** create `CRM Organization` records and their `Contact` records. There is no type field; see the traps.
- **Done when:** a `CRM Organization` for each agreed name.

## Start using

Their team does these. You explain how, then check.

### `first-prospect`: Your team adds a real new prospect

- **Done when:** a `CRM Lead` or `CRM Deal` created after setup, by someone who is not a setup user, with an owner and a status.

### `first-conversion`: Your first lead becomes a deal

- **When:** `lead-stages` is on.
- **Done when:** a `CRM Lead` with `converted` 1, changed after setup by someone who is not a setup user, and a `CRM Deal` whose `lead` is that lead.

### `first-email`: Your first email sent from CRM

- **When:** `email` is on.
- **Done when:** a sent `Communication` on a lead or deal, sent by someone who is not a setup user, with a reply on the same record.

### `first-close`: Your first deal is won or lost in CRM

- **Done when:** a `CRM Deal` whose status has type Won, or type Lost with a `lost_reason`, changed after setup by someone who is not a setup user. Expect it after one of their usual deal lengths, not sooner.

### `follow-ups`: Your follow-ups live in CRM

- **When:** follow-ups slip today.
- **Done when:** five or more `CRM Task` records with a `due_date`, made by people who are not setup users. Five is a starting guess; agree the number with them.

### `calls`: Your calls are logged

- **When:** they sell by phone. This is logging by hand; telephony is not part of this setup.
- **Done when:** five or more `CRM Call Log` records made by people who are not setup users.

## Habit and live

### `regular-use`: Your team logs its work

- **Done when:** notes (`FCRM Note`), tasks, calls, emails and status changes on leads and deals, made by people who are not setup users since setup, add up to the agreed number. Start at 25 from two or more people; a team of one, 25 from one; under ten new prospects a month, 10. These are guesses: agree the number.

### `weekly-use`: CRM is part of your week

- **Done when:** people who are not setup users changed leads or deals in three different calendar weeks.

### `pipeline-review`: Your pipeline review happens in CRM

- **When:** they named who reviews the pipeline and how often.
- **Done when:** the reviewer changed five or more deals on one day, in two different weeks. A rough sign, not proof: say so.

### `live`: CRM is working, in your words

- **Done when:** their live condition passes on the data, and people who are not setup users changed a lead or deal in the last 7 days. Check at 30 and 90 days from the start date.
