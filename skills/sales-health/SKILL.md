---
name: sales-health
starter: How are my sales doing?
prompts:
  - "How did this month compare to last?"
  - "Which deals are closing soon?"
  - "Why are we losing deals?"
  - "What's the forecast this quarter?"
  - "Who's closing the most this quarter?"
description: Give a short, plain-English update on how sales are going in the CRM, such as the open pipeline by stage, this month against last month, deals won and lost, and deals that have gone quiet. Use when someone asks about their sales health, pipeline, numbers, performance or how the month is going.
---

# How are my sales doing

The person asking may be a salesperson or a manager, and isn't technical. Answer in simple, plain English, like a colleague summing up the month. Never mention record IDs, field names, tools, code or technical terms, and don't use tables or code blocks.

1. Call `sales_health`. It needs no approval and only reads, so never write code for this.
2. Open with one sentence on how things are going, comparing this month with last month, such as "A busier month than last: 36 deals won so far, against 65 in all of last month."
3. Then a few short lines:
   - **Pipeline**: how many open deals and their total value, and the stage with the most in it. Skip stages with nothing in them.
   - **This month**: new leads, leads that became deals, deals won (with their value) and lost.
   - **Needs attention**: deals gone quiet (no email, call, note or other activity in 2 weeks) and overdue tasks, if any.
4. Write amounts in the CRM's currency with thousands separators, such as ₹18,42,600 or $1,842,600. If `currency` is empty, leave the symbol out.
5. End with one or two options they can click, such as "What's on my plate today?" or "Show me the quiet deals". Link to [Deals](/crm/deals) or the [Deals board](/crm/deals/view/kanban) when they want to look for themselves.

When they ask about one thing, answer just that, still from `sales_health`:

- **"How did this month compare to last?"**: only the month against last month: new leads, leads that became deals, deals won (with their value) and lost. Say that this month isn't over yet.
- **"Why are we losing deals?"**: the reasons in `lost_reasons_last_90_days`, the most common first, each with how many deals and their value, such as "Pricing: 3 deals, ₹2,10,000". Name the top reason in one line first. If none were lost, say so. Suggest one thing that fits the top reason, such as reviewing prices or following up sooner.
- **"Who's closing the most?"**, a leaderboard, or "What's our win rate?": from `this_quarter_by_owner`, each person with deals won, their value, deals lost and win rate, the most won value first, then the team's win rate. Say it's this quarter so far. Leave out win rates that are empty because nothing closed yet.
- **"What's the forecast?"** for this month or quarter: from `forecast`, what's won so far, then the open deals due to close and their value, then the likely total: won so far plus the open deals weighted by how likely each is to close. Say the weighted figure is an estimate. Name the period's dates, such as "October to December".
- **"Which lead sources work best?"** or conversion by source: from `lead_sources_last_90_days`, each source with its leads, how many became deals and the rate, the best rate first among sources with a few leads. Point out a source with many leads and few deals. If it's empty because they can't see leads, say so in one line.
- **"Which deals are closing soon?"**: the deals in `closing_soon`, soonest first, each as a link with its close date and value, such as [Acme Corp](/crm/deals/...), closing Thursday, $12,000. If there are none, say no open deals are due to close in the next 30 days.

It covers everything they're allowed to see. If a number is missing because they can't see those records, leave it out without explaining why.
