# 00 — Analisi dello stato attuale (crm-mm)

> Parte del [Progetto GHL-Parity](./README.md). Analisi condotta sul branch `develop`
> di questo fork di [frappe/crm](https://github.com/frappe/crm).

## Cos'è oggi questo repository

`crm-mm` è un fork di **Frappe CRM** (Vue 3 + frappe-ui sul frontend, app Frappe in
Python sul backend, licenza AGPL-3.0) con lavoro custom già avviato (vedi `.pi/PLAN.md`):
un motore di **Form Scripting** evoluto (`frontend/src/data/script.js`,
`frontend/src/data/document.js`), `formDialog()`, FieldLayout standalone e altri
miglioramenti architetturali al rendering dei campi.

## Cosa c'è GIÀ — e conta molto per il progetto

La percezione che "manca tutto" va corretta: diversi mattoni GHL-like esistono già
in questo repo o nel framework sottostante.

### 1. Telefonia: base solida, non da zero

- **Twilio Voice** integrato nativamente (`crm/integrations/twilio/`):
  - chiamate **dal browser** tramite Twilio Voice JS SDK (access token generato in
    `api.py::generate_access_token`);
  - webhook TwiML per chiamate in ingresso/uscita, con validazione della firma;
  - **registrazione chiamate** e **CRM Call Log** (`crm_call_log`) collegato a
    lead/deal tramite numero (`get_contact_lead_or_deal_from_number`);
  - anagrafica agenti telefonici: `CRM Telephony Agent`, `CRM Telephony Phone`.
- **Exotel** come secondo provider (`crm/integrations/exotel/handler.py`).
- Cosa manca rispetto a GHL: **Power Dialer** (coda di chiamate sequenziali su una
  lista), **SMS bidirezionali** con inbox, voicemail drop, esiti chiamata strutturati.

### 2. WhatsApp: API già presente

- `crm/api/whatsapp.py` gestisce messaggi WhatsApp in/out agganciati a lead e deal
  (integrazione con l'app `frappe_whatsapp` via `doc_events`), con controllo ruoli
  (`Sales Manager`, `Sales User`) e notifiche (`CRM Notification`).
- Cosa manca: uso di WhatsApp **dentro le automazioni** (sequenze, template in massa)
  e inbox unificata multi-canale.

### 3. Email: comunicazioni sì, campagne no

- Timeline email per lead/deal, **Email Template**, invio via Frappe `sendmail`.
- Cosa manca: campagne massive, sequenze drip, tracking aperture/click a livello
  campagna, gestione liste/segmenti.

### 4. Automazioni: motore presente, orchestrazione assente

Il framework Frappe fornisce già i mattoni server-side:

- `doc_events` (hook su create/update di qualsiasi DocType) — già usati in `hooks.py`;
- **Scheduler** (`scheduler_events`, cron) e **Background Jobs** (`frappe.enqueue`);
- **Notification** (regole evento→email/SMS) e **Workflow** (stati/transizioni);
- **Webhook** nativi in/out;
- **Assignment Rule** (round-robin / load balancing sulle assegnazioni!) — nativo.

Cosa manca: il **builder visuale di workflow multi-step temporizzati** (trigger →
wait 2 giorni → email → if/else → SMS → goal), cioè il cuore dei "Workflows" GHL.
È il pezzo con il più alto rapporto valore/sforzo dell'intero progetto.

### 5. UI e piattaforma

- Frontend Vue 3 SPA con pagine: Leads, Deals, Contacts, Organizations, **Calendar**,
  CallLogs, Tasks, Notes, Dashboard, DataImport.
- Sistema di **CRM Form Script** (server-defined, eseguiti nel browser) — punto di
  estensione potentissimo e già rafforzato in questo fork.
- `website_route_rules` già espone `/crm-form/<route>` (form pubblici).
- **SLA** (service level agreement su lead/deal), **CRM Products**, gerarchia vendite
  (`crm_sales_hierarchy`, territorio, holiday list).
- Integrazione **ERPNext** (preventivi/ordini da deal) — leva unica che GHL non ha:
  contabilità, magazzino, HR reali a valle del CRM.

## La matrice dei gap (verso GoHighLevel)

| # | Area GHL | Stato in crm-mm | Gap reale |
|---|---|---|---|
| 1 | Funnel & landing page builder | ❌ assente nel CRM (ma esiste **Frappe Builder** come app affiancabile) | Integrazione, non sviluppo da zero |
| 2 | Marketing automation omnicanale | ⚠️ mattoni presenti (hooks, scheduler, notification, whatsapp, twilio) | Manca il **workflow engine visuale** con wait/branch |
| 3 | Telefonia & SMS | ⚠️ chiamate browser Twilio già presenti | Power dialer, SMS 2-way, inbox unificata |
| 4 | Corsi & membership | ❌ assente (ma esiste **Frappe LMS** come app affiancabile) | Integrazione + paywall + collegamento CRM |
| 5 | White-label / SaaS mode | ⚠️ multi-sito nativo di bench; branding hard-coded "Frappe CRM" | Provisioning automatico, branding per-tenant, billing |
| 6 | Calendari & booking | ⚠️ pagina Calendar + Google Calendar sync del framework + Assignment Rule round-robin | Pagina di prenotazione pubblica stile Calendly |
| 7 | Reputation management | ❌ assente | Modulo nuovo (Google Business Profile API) |

## Vincoli e decisioni architetturali di partenza

1. **Non forkare di più: estendere.** Tutto il nuovo codice va in una **nuova app
   Frappe separata** (proposta: `crm_suite`) installata sullo stesso sito accanto a
   `crm`. Motivi: mantenere la possibilità di fare pull da upstream `frappe/crm`,
   isolare la manutenzione, poter distribuire/riusare i moduli.
2. **Riusare le app ufficiali Frappe** dove esistono (Builder, LMS, Payments,
   Frappe Whatsapp): il costo è integrazione, non sviluppo.
3. **AGPL-3.0**: il fork e ogni app che importa `crm` restano AGPL; il modello di
   business white-label è compatibile (vendi hosting/servizio, non licenze), ma il
   codice va reso disponibile agli utenti del servizio se modificato (dettagli nel
   [modulo 06](./06-white-label-saas.md)).
4. **Il frontend nuovo** segue lo stack esistente: Vue 3 + frappe-ui, pagine montate
   nella SPA `/crm` oppure SPA separate per moduli grandi (pattern già usato da
   Builder/LMS/Helpdesk).
