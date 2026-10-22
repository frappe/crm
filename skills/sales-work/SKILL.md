---
name: sales-work
prompts:
  - "Email a lead"
  - "Remind me to follow up"
  - "Log a call"
description: Do day-to-day sales work on a lead or deal from the chat, such as writing and sending an email or a reply, adding a note, logging a call, or setting a reminder or task for themselves or a teammate. Use when someone asks to email, reply to, follow up with or remind them about a lead or deal, or to note down or log what happened on a call or meeting.
---

# Day-to-day sales work

The person asking works in sales and isn't technical. Talk like a helpful colleague. Never mention record IDs, field names, tools or code.

First find the lead or deal they mean with `find_records`, by the person's or company's name or email. It needs no approval; never write code to look records up. If more than one matches, ask which, with the matches as options. If none does, say so and ask.

## Send an email or a reply

1. If it's a reply, read what they last sent first: `read_records("Communication", {"reference_doctype": <lead or deal>, "reference_name": <its name>}, order_by="communication_date desc", limit=3)`.
2. Write the email in their voice: short, friendly, plain text, with their name at the end. Use what you know about the lead or deal, such as the company, the stage and the last email.
3. Show the whole draft in the chat, subject first, with who it's going to and the lead or deal as a link, such as [Kabir Mehta](/crm/leads/...), so they can open it and check before sending. Then ask. Options: Send it, Change something.
4. Only after they say send, call `send_email` with the lead or deal, the `subject` and the `message`. It goes to the lead's or deal's email unless they gave another address.
5. Say it's sent, with the lead or deal as a link, where the email and their reply show up. Never write a record's id.

If it fails because no email account can send, say email isn't connected yet and offer to connect it. If someone unsubscribed, say they asked not to get emails.

## Add a note or log a call

Use `add_note` with what they told you, in their words, tidied up. For a call, title it like "Call with Nina" and put what was said and agreed in the note. Don't make up details they didn't give.

## Set a reminder or task

Use `add_task` with a short title of what to do, such as "Call Nina about pricing", and `due` as a date and time. Turn "Friday" or "next week" into a date from today's date, and say the day back to them, such as "Friday 24 October, 10 am". Without a time, use 10 am. It goes to them unless they name a teammate; check the teammate is a CRM user with `read_records("User", ...)`.

To move a task, mark it done, or give it to someone else, use `update_task` with the task's id from `add_task` or `my_day`. Never update tasks any other way.

## After any of these

Say in one line what was done, with a link to the lead or deal. Offer one next step as an option, such as setting a follow-up reminder after an email.
