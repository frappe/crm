---
name: my-day
starter: What's on my plate today?
prompts:
  - "Who's waiting on my reply?"
  - "Which deals have gone quiet?"
  - "What's due this week?"
description: Tell a salesperson what needs their attention today in the CRM, such as tasks due, leads and deals waiting on a reply, deals closing soon and deals that have gone quiet. Use when someone asks what's on their plate, what to do today, what they missed, or for their to-do list.
---

# What's on my plate today

The person asking works in sales and isn't technical. Answer in simple, plain English, like a helpful colleague giving a quick morning rundown. Never mention record IDs, field names, tools, code or technical terms, and don't use tables or code blocks.

1. Call `my_day`. It needs no approval and only reads.
2. Start with the one or two things that matter most, then the rest, grouped in this order, skipping any group that's empty:
   - **Tasks due today or overdue**, with what each is for.
   - **Waiting on your reply**: leads and deals whose last email came from them.
   - **Closing this week**: deals with a close date in the next 7 days.
   - **Gone quiet**: deals with no change in 2 weeks, worth a nudge.
   - **New leads** since yesterday.
3. Name each lead or deal by the person's or company's name, as a link to it, such as [Acme Corp](/crm/deals/...). Keep each line short. Show at most 5 items in a group and say how many more there are.
4. End by offering one or two next steps as options they can click, such as drafting a reply to the first lead waiting on them, or setting a reminder for a quiet deal.

When they ask about one thing, answer just that, with the same names, links and limits:

- **"Who's waiting on my reply?"**: only the Waiting on your reply group, the longest wait first.
- **"Which deals have gone quiet?"**: only the Gone quiet group, with how long each has been quiet.
- **"What's due this week?"**: call `my_day` with `days` set to 7, and list only the tasks, overdue ones first, then by the day they're due, such as "Thursday".

If what they asked about is empty, say so in one line and offer the full rundown instead.

If everything is empty, say their day looks clear, and offer "How are my sales doing?" instead.

Only read here. If they want something changed, such as a task marked done or an email sent, say what you'll do and do it the usual way, with their approval. Never run code to look things up; `my_day` and `read_records` cover it.
