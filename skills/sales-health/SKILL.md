---
name: sales-health
starter: How are my sales doing?
prompts:
  - "How did this month compare to last?"
  - "Which deals are closing soon?"
description: Give a short, plain-English update on how sales are going in the CRM, such as the open pipeline by stage, this month against last month, deals won and lost, and deals that have gone quiet. Use when someone asks about their sales health, pipeline, numbers, performance or how the month is going.
---

# How are my sales doing

The person asking may be a salesperson or a manager, and isn't technical. Answer in simple, plain English, like a colleague summing up the month. Never mention record IDs, field names, tools, code or technical terms, and don't use tables or code blocks.

1. Call `sales_health`. It needs no approval and only reads, so never write code for this.
2. Open with one sentence on how things are going, comparing this month with last month, such as "A busier month than last: 36 deals won so far, against 65 in all of last month."
3. Then a few short lines:
   - **Pipeline**: how many open deals and their total value, and the stage with the most in it. Skip stages with nothing in them.
   - **This month**: new leads, leads that became deals, deals won (with their value) and lost.
   - **Needs attention**: deals gone quiet and overdue tasks, if any.
4. Write amounts in the CRM's currency with thousands separators, such as ₹18,42,600 or $1,842,600. If `currency` is empty, leave the symbol out.
5. End with one or two options they can click, such as "What's on my plate today?" or "Show me the quiet deals". Link to [Deals](/crm/deals) or the [Deals board](/crm/deals/view/kanban) when they want to look for themselves.

When they ask about one thing, answer just that, still from `sales_health`:

- **"How did this month compare to last?"**: only the month against last month: new leads, leads that became deals, deals won (with their value) and lost. Say that this month isn't over yet.
- **"Which deals are closing soon?"**: the deals in `closing_soon`, soonest first, each as a link with its close date and value, such as [Acme Corp](/crm/deals/...), closing Thursday, $12,000. If there are none, say no open deals are due to close in the next 30 days.

It covers everything they're allowed to see. If a number is missing because they can't see those records, leave it out without explaining why.
