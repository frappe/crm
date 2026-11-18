# The setup plan on the site

Keep the plan as one `Note`, so any later session, in any assistant, can read where the setup stands. A Note exists on every Frappe site and needs nothing installed.

- `title`: `CRM setup plan`. One plan per site. Find it with `{"title": ["like", "CRM setup plan%"]}`.
- `public`: 1. A Note that is not public is visible only to its owner, so nobody else, and no other session signed in as someone else, could read the plan.
- `content`: HTML, in the shape below. Write it in the person's language and words.

Read the whole Note before you change it, and write it back whole: `content` is one field. Show the edit and wait for a yes, as with every write.

## Shape

```html
<h3>About</h3>
<p><b>Business:</b> what they sell, to whom, in one line.<br>
<b>Started:</b> 2026-11-16<br>
<b>Live means:</b> "Every new enquiry is in CRM within a day" (their words).<br>
<b>Live check:</b> every CRM Lead created in the last 7 days has a lead_owner, and leads were created on 4 of the last 5 weekdays.<br>
<b>Set up by:</b> partner@example.com (setup users; leave empty when the business set itself up)</p>

<h3>Agreed</h3>
<ul>
<li>Deal stages: Enquiry, Site visit, Quote sent, Won, Lost</li>
<li>Lost reasons: Price, Timing, Went with a local builder, Other</li>
<li>Sources: Website, Referral, Walk-in</li>
<li>Sellers: 4 (names in the Team step)</li>
</ul>

<h3>Steps</h3>
<table>
<tr><th>#</th><th>Step</th><th>Why</th><th>Who</th><th>Status</th></tr>
<tr><td>1</td><td>Your deal stages follow how you sell</td><td>You said every job starts with a site visit</td><td>Setup</td><td>Done 2026-11-16</td></tr>
<tr><td>2</td><td>Your four sellers can sign in</td><td>Asha and Ravi follow up on web leads</td><td>You invite, they sign in</td><td>To do</td></tr>
<tr><td>9</td><td>Your team adds a real new enquiry</td><td>The first sign CRM replaced the notebook</td><td>Your team</td><td>To do</td></tr>
</table>

<h3>Asked for, not in this setup</h3>
<ul><li>2026-11-16: "Can enquiries come from our WhatsApp number?"</li></ul>

<h3>Log</h3>
<p>Newest first. 2026-11-16: stages and reasons done. Email waits for the Google admin. Next: invite the team.</p>
```

## Rules

- **Status** is `To do`, `Done <date>` or `Not needed: <reason>`. Mark a step done only after its Done when check passed on the data.
- **Who** is one of: Setup (you, or whoever sets up), You invite and they sign in, You and they (they send, you import), Your team.
- Put the agreed values under "Agreed". The checks in `steps.md` compare the site against them.
- Never put a password, key or personal data beyond names and work emails in the Note. Every desk user can read it.
- When the plan changes after a session, change the steps and add a log line saying why.
