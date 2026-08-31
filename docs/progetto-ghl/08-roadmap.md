# 08 — Roadmap, dipendenze e stime

> Parte del [Progetto GHL-Parity](./README.md). Stime in settimane-persona (sp)
> per uno sviluppatore senior full-stack Frappe (Python + Vue). Team di 2 ⇒
> calendario ≈ metà.

## Grafo delle dipendenze

```
Fase 0 (fondamenta) ──▶ Fase 1 (motore + canali) ──▶ Fase 2 (acquisizione) ──▶ Fase 3 (monetizzazione) ──▶ Fase 4 (SaaS)

02 Workflow engine  ◀── dipende da: channel adapter (03-SMS, whatsapp, email)
01 Funnel           ◀── Builder installato; trigger verso 02
05 Booking          ◀── 02 per i promemoria; 03 per SMS
07 Reputation       ◀── 02 per le richieste; 03 per SMS; pratica GBP avviata in Fase 0
04 Membership       ◀── LMS installato; 01 per checkout; 02 per onboarding
06 SaaS             ◀── tutto il resto stabile su singolo sito
```

## Fase 0 — Fondamenta (2–3 sp)

- Scaffold app **`crm_suite`** (moduli vuoti, CI, convenzioni), installazione sul
  bench di sviluppo accanto a `crm`.
- Installare e provare: **Frappe Builder**, **Frappe LMS + payments**,
  **frappe_whatsapp**.
- **Avviare le pratiche a lead time lungo**: accesso GBP API, Meta Business
  Verification, numeri/compliance Twilio, dominio + wildcard DNS.
- Setup SMTP transazionale/marketing (SES/Mailgun) + SPF/DKIM/DMARC.

## Fase 1 — Motore e canali (8–11 sp) → *già qui si supera un CRM normale*

| Item | Modulo | Stima |
|---|---|---|
| SMS two-way Twilio (webhook, thread, UI base) | 03 | 2 sp |
| Workflow engine MVP (enrollment, wait, email/tag, tick scheduler, JSON) | 02 | 3–4 sp |
| Canvas visuale Vue Flow + pannelli proprietà | 02 | 2–3 sp |
| If/Else, Goal, Split, Trigger Link con tracking | 02 | 1–2 sp |

**Milestone M1**: "lead creato → sequenza email+SMS+WhatsApp con branch e goal,
costruita visualmente".

## Fase 2 — Acquisizione (7–10 sp)

| Item | Modulo | Stima |
|---|---|---|
| Layer funnel su Builder (step, routing, tracking) | 01 | 2–3 sp |
| A/B split test sticky + statistiche | 01 | 1–2 sp |
| Booking 1:1 pubblico + GCal busy-block + reschedule/cancel | 05 | 2–3 sp |
| Round-robin/collective + trigger workflow appuntamenti | 05 | 1 sp |
| Inbox unificata UI (email+SMS+WhatsApp+voce) | 03 | 1–2 sp |

**Milestone M2**: "funnel pubblicato → lead → sequenza → prenotazione con
promemoria automatici, tutto nel thread del contatto".

## Fase 3 — Monetizzazione e retention (6–9 sp)

| Item | Modulo | Stima |
|---|---|---|
| Checkout Stripe funnel (one-time, bump, upsell one-click) | 01 | 2–3 sp |
| Ponte CRM↔LMS + drip content + Access Pass abbonamento | 04 | 2–3 sp |
| Reputation: sync GBP, dashboard, review request via workflow | 07 | 1–2 sp |
| Power dialer + disposition + voicemail drop (AMD) | 03 | 1–2 sp* |

*\* il dialer può anticiparsi in Fase 2 se la priorità commerciale è outbound.*

**Milestone M3**: "vendita corso dal funnel con upsell; studenti nel CRM;
richieste recensione automatiche post-vendita".

## Fase 4 — SaaS Mode (6–9 sp + infra continua)

| Item | Modulo | Stima |
|---|---|---|
| Stack Docker multi-tenant, wildcard DNS/TLS | 06 | 1–2 sp |
| Provisioning automatico (signup → new-site + golden restore) | 06 | 2–3 sp |
| App whitelabel per-tenant | 06 | 1 sp |
| Metering + rebilling Stripe usage-based | 06 | 2–3 sp |
| Messenger/IG DM nell'inbox (post App Review Meta) | 03 | 2 sp (quando sbloccato) |

**Milestone M4**: "un cliente si iscrive, paga, e in minuti ha il suo CRM
brandizzato con snapshot preconfigurato; l'uso di SMS/email gli viene rifatturato
con markup".

## Totale

**29–42 settimane-persona** (≈ 7–10 mesi per 1 senior, ≈ 4–5 mesi per un team di 2)
per la parità sostanziale. Il valore però arriva incrementale: **M1 in ~2 mesi**
già elimina la dipendenza da GHL per automazioni e nurturing.

## Rischi principali

| Rischio | Mitigazione |
|---|---|
| App Review Meta lenta/respinta (IG/Messenger) | Canali Meta ultimi; WhatsApp (già ok) copre il caso d'uso principale in EU |
| Accesso GBP API negato/lento | Domanda al giorno 1; il resto del modulo 07 non ne dipende (deep link funziona comunque) |
| API frappe/payments in ridisegno | Pin delle versioni; checkout funnel parla direttamente con Stripe |
| Deliverability email su volumi | SMTP dedicato per tenant + warm-up + DMARC dalla Fase 0 |
| Scope creep sul workflow engine | MVP verticale a JSON prima del canvas; lista azioni chiusa per milestone |
| Manutenzione upstream (fork CRM) | Codice in `crm_suite`, fork minimo, rebase periodico da frappe/crm |
