# 08 — Roadmap, dipendenze e stime (scope ridotto, rev. 31/08/2026)

> ✅ **STATO (31/08/2026, sera): MVP di TUTTE le fasi implementato e pushato.**
>
> - Fase 1 Booking: DocType, slot engine, pagina pubblica `/book/<route>`, email+ICS, lead auto ✅
> - Fase 2 SMS/Inbox: `CRM SMS Message`, webhook Twilio 2-way, tab SMS su Lead/Deal, pagina `/inbox` ✅
> - Fase 3 Automazioni: motore enrollment (`crm/automation/engine.py`), trigger/azioni/wait/stop_if/
>   exit-on-reply, scheduler, builder visuale `/automations` (frappe-ui espresso) ✅
> - Fase 4 Dialer: `CRM Dial Session`, coda sequenziale, esiti (disposition) loggati sul record,
>   pagina `/dialer` che riusa la chiamata browser Twilio ✅ (voicemail drop con AMD: rimandato,
>   richiede chiamate REST invece del Voice SDK browser)
> - Fase 5 Provisioning: `scripts/provisioning/` (golden snapshot + provision_tenant) ✅
>
> Verifiche: build Vite ok, 150/150 test vitest ok, ruff pulito, test integrazione Python
> scritti (da eseguire con `bench run-tests --app crm` su un bench reale, qui non disponibile).
> Restano da fare sul campo: `bench migrate`, configurazione Twilio/numeri e prova end-to-end.

> Parte del [Progetto GHL-Parity](./README.md). Ricalibrata sulle
> [decisioni di scope](./README.md#-decisioni-di-scope-31082026): **Booking (05)
> per primo**, poi SMS/inbox (03), workflow engine (02), dialer, e script di
> provisioning/snapshot. Stime in settimane-persona (sp) per un senior full-stack
> Frappe.

## Grafo delle dipendenze

```
Fase 1: Booking (05)  ──────────────┐
Fase 2: SMS 2-way (03) ─────────────┼──▶ Fase 3: Workflow engine (02)
        Inbox unificata (03)        │        (usa booking-trigger e canale SMS)
                                    │
Fase 4: Power dialer (03) ──────────┘   Fase 5: provisioning + snapshot (06-lite)
```

Nota d'ordine: il booking parte per primo su decisione del committente; i
promemoria automatici arriveranno quando esisteranno il canale SMS (Fase 2) e il
workflow engine (Fase 3) — nell'MVP booking le conferme/notifiche sono email
dirette.

## Fase 1 — Booking MVP (2–3 sp) ← **si parte da qui**

- DocType: calendario di booking (durata, buffer pre/post, preavviso minimo,
  orizzonte, disponibilità settimanale per membro), prenotazione (invitato,
  stato, token).
- Calcolo slot server-side in UTC, rendering nella timezone dell'invitato.
- Pagina pubblica di prenotazione (guest) + conferma email con link firmati di
  **reschedule/cancel**.
- Ogni booking crea/aggancia un `CRM Lead` e appare nella timeline.
- Round-robin sui membri del calendario (assegnazione al meno carico).
- Fase 1b: busy-block da Google Calendar (sync nativo del framework).

## Fase 2 — SMS 2-way + Inbox unificata (3–4 sp)

- Webhook inbound Twilio (firma validata) + invio REST con status callback.
- DocType `SMS Message` threaded + adapter `send()` riusabile.
- Inbox UI nella SPA: thread per contatto con email+SMS+WhatsApp+chiamate.
- Promemoria booking via SMS (primo aggancio 05→03).

## Fase 3 — Workflow engine (6–8 sp)

- MVP a JSON: enrollment, trigger (lead creato, booking, SMS ricevuto), azioni
  (email, SMS, WhatsApp, tag, task, assegnazione), Wait, tick scheduler.
- Canvas Vue Flow + pannelli proprietà.
- If/Else, Goal, Split, Trigger Link con tracking.
- Sequenze promemoria/no-show per il booking (sostituiscono le email dirette
  della Fase 1).

## Fase 4 — Power dialer (1–2 sp)

- `Dial Session`/coda da vista CRM filtrata, riuso della sessione Twilio Voice
  browser esistente, esiti chiamata (disposition) → trigger workflow.
- Voicemail drop con Answering Machine Detection.

## Fase 5 — Provisioning + snapshot (1–2 sp, strumento interno)

- Script `bench new-site` + restore del golden site preconfigurato per creare il
  site di un nuovo cliente in minuti. Niente signup pubblico, niente billing.

## Totale scope ridotto

**13–19 settimane-persona** (≈ 3–4,5 mesi per 1 senior; ~metà calendario in 2).
Era 29–42 sp a scope pieno: il taglio di funnel/LMS/reputation/Meta/rebilling
dimezza l'effort.

## Rischi principali (rivisti)

| Rischio | Mitigazione |
|---|---|
| Timezone/DST nel calcolo slot | Tutto in UTC server-side, conversione solo in rendering; test su cambi ora |
| Sync Google Calendar è polling, non push | Buffer di sicurezza + ricontrollo disponibilità al momento della conferma |
| Scope creep sul workflow engine | MVP a JSON prima del canvas; lista azioni chiusa per milestone |
| Deliverability email (conferme/promemoria) | SMTP transazionale con SPF/DKIM per site |
| Manutenzione upstream (fork CRM) | Codice nuovo in modulo separato dell'app, rebase periodico da frappe/crm |
