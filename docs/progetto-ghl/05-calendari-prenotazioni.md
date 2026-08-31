# 05 — Calendari e Prenotazioni (booking stile Calendly)

> ✅ **MVP IMPLEMENTATO** (31/08/2026) direttamente in questo fork (modulo FCRM):
>
> - DocType `CRM Booking Calendar` (durata, buffer pre/post, preavviso minimo,
>   orizzonte, timezone, membri, orari settimanali via `CRM Service Day`,
>   holiday list) — `crm/fcrm/doctype/crm_booking_calendar/`
> - DocType `CRM Booking` (invitato, agente, stato, token di gestione) +
>   `CRM Booking Calendar Member`
> - Calcolo slot server-side timezone-aware (UTC) con busy-block dai booking
>   esistenti di tutti i calendari, buffer e round-robin least-booked
> - API guest rate-limited: `get_calendar`, `get_slots`, `book`,
>   `get_booking`, `cancel_booking`, `reschedule_booking` (`crm/api/booking.py`)
> - Pagina pubblica `/book/<route>` (slot nella timezone del visitatore,
>   form, gestione via `?token=` per reschedule/cancel) — `crm/www/book.*`
> - Email di conferma con allegato .ics + notifica all'agente; ogni booking
>   crea/aggancia un `CRM Lead` (source "Booking")
> - Test: `crm/tests/test_booking.py`
>
> **Non ancora incluso** (prossimi passi del modulo): busy-block da Google
> Calendar, vista di gestione nella SPA (per ora si usa il Desk), promemoria
> SMS/sequenze (arrivano con i moduli 03/02), pagamenti alla prenotazione.

> Parte del [Progetto GHL-Parity](./README.md). Obiettivo: pagine di prenotazione
> pubbliche con disponibilità reale, round-robin di team, promemoria e sync
> calendario esterno.

## Cosa fa GHL (spec di parità)

- **Tipi di calendario**: personale, **round robin** (distribuzione al membro con
  meno booking o a rotazione, con priorità), **collective** (intersezione delle
  disponibilità, tutti prenotati insieme), classe/evento (1-a-molti con posti),
  service menu.
- Disponibilità: orari settimanali ricorrenti per membro + override per data +
  festività; durata slot, preavviso minimo, orizzonte massimo, cap giornaliero,
  **buffer pre/post**.
- Booking flow: form di intake custom, pagamento Stripe alla prenotazione,
  **timezone auto-rilevata dell'invitato**.
- Post-booking: conferma email/SMS con **link self-service di reschedule/cancel**,
  sequenze di promemoria multiple, workflow no-show, link meeting auto (Zoom/Meet).
- **Sync 2-way** con Google Calendar, Outlook/O365, iCloud (eventi esterni
  bloccano gli slot).

## Cosa esiste già

### In questo repo / nel framework

- Pagina **Calendar** nella SPA CRM (vista appuntamenti interni).
- **Google Calendar sync 2-way nativo del framework** (DocType Google Calendar ↔
  Event, OAuth per utente). Limiti: sync periodico da scheduler (non push) — va
  bene per il busy-block, non per invalidazione slot istantanea. **Outlook/M365:
  nessun sync nativo → lavoro greenfield (MS Graph `calendarView` + subscriptions).**
- **Assignment Rule** nativa (round-robin/load-balancing sulle assegnazioni
  documenti) — logica riusabile.

### App esistenti valutate

| App | Verdetto |
|---|---|
| [rtCamp/frappe-appointment](https://github.com/rtCamp/frappe-appointment) (AGPL, branch version-16, su Frappe Cloud marketplace) | ✅ **Miglior punto di partenza**: link di scheduling personali 1:1 + group link, sync Google Calendar per conflitti, link Zoom/Meet automatici, reschedule dell'invitato, integrazione ferie ERPNext. **Non documentati** (verificare nel codice): round-robin, collective, buffer, reminder, cancel link, Outlook |
| ERPNext `Appointment` + Booking Settings (GPL-3) | Minimale: slot fissi, assegnazione least-loaded, verifica email. Richiede tutto ERPNext → prior art |
| pibico/appointment_booking, booking_mgmt | Nicchia / resource-booking, non Calendly-style |

Non esiste un clone Calendly completo open-source su Frappe.

## Decisione architetturale

**Fork/estensione di rtCamp frappe-appointment** (o riscrittura ispirata, decisione
dopo code-review del repo) dentro `crm_suite.booking`, con questi add-on:

### Da aggiungere

1. **Tipi di calendario**: `Booking Calendar` (tipo: personal/round-robin/
   collective/class) + membri con peso/priorità. Round-robin: riuso della logica
   Assignment Rule o contatore "meno booking".
2. **Buffer pre/post, preavviso minimo, orizzonte, cap giornaliero** sul calcolo
   slot.
3. **Timezone dell'invitato**: rendering slot lato client nella TZ rilevata
   (il calcolo resta server-side in UTC).
4. **Reschedule/cancel link** firmati (token) nella conferma.
5. **Promemoria** email/SMS a offset multipli → **azioni del workflow engine**
   (modulo 02), non un sistema di reminder separato; trigger: booked / rescheduled
   / cancelled / no-show / completed.
6. **Pagamento alla prenotazione** (Stripe, riuso checkout modulo 01) — fase 2.
7. **Outlook 2-way** — fase 2 (greenfield MS Graph).

### Integrazione CRM (il differenziale)

- Booking pubblico ⇒ crea/aggiorna `CRM Lead` + evento sul thread del contatto
  (inbox modulo 03) ⇒ enrollment in workflow ("promemoria 24h/1h", "no-show →
  sequenza di recupero").
- Pagina di booking incorporabile nelle pagine Builder dei funnel (embed/iframe
  o blocco dedicato) — chiude il cerchio funnel → appuntamento.

## Deliverable e ordine

1. Code-review di frappe-appointment (verificare buffer/round-robin/reminder reali)
   → decisione fork vs. rebuild ispirato.
2. Booking page pubblica 1:1 con Google Calendar busy-block + conferma con
   reschedule/cancel link.
3. Round-robin e collective; buffer e limiti.
4. Trigger di workflow per l'intero ciclo di vita dell'appuntamento.
5. Pagamenti alla prenotazione + Outlook sync (fase 2).
