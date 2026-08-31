# Progetto GHL-Parity — Frappe CRM come piattaforma all-in-one

> **Obiettivo**: portare questo fork di Frappe CRM (`crm-mm`) alla parità funzionale
> con GoHighLevel — funnel, marketing automation omnicanale, telefonia/SMS/inbox
> unificata, corsi & membership, calendari di prenotazione, white-label SaaS e
> reputation management — riusando al massimo l'ecosistema open-source Frappe.
>
> Ricerca condotta online ad **agosto 2026** (repo, docs ufficiali, changelog API);
> ogni modulo cita le fonti.

## Indice dei documenti

| Doc | Modulo | Verdetto sintetico |
|---|---|---|
| [00](./00-analisi-stato-attuale.md) | Analisi stato attuale del repo | Non si parte da zero: Twilio Voice browser, WhatsApp, scheduler, round-robin nativi |
| [01](./01-funnel-landing-builder.md) | Funnel & Landing Page | **Adottare Frappe Builder (MIT da v1.31)** + layer funnel custom (step, A/B, checkout Stripe) |
| [02](./02-marketing-automation.md) | Marketing Automation | **Il cuore del progetto: da costruire** (motore enrollment Python + canvas Vue Flow); i canali esistono già |
| [03](./03-telefonia-sms-inbox.md) | Telefonia, SMS, Inbox | SMS two-way + inbox unificata + power dialer da costruire su Twilio già integrato; Meta (FB/IG) per ultimi (App Review) |
| [04](./04-corsi-membership.md) | Corsi & Membership | **Adottare Frappe LMS** (release-attivo, stesso stack); costruire solo drip, abbonamenti, ponte CRM |
| [05](./05-calendari-prenotazioni.md) | Calendari & Booking | Estendere rtCamp frappe-appointment + Google Calendar sync nativo; round-robin/buffer da aggiungere |
| [06](./06-white-label-saas.md) | White-Label / SaaS | Multi-sito bench nativo + provisioning scriptato + golden-site "snapshot"; rebilling custom; AGPL ok per reselling hosted |
| [07](./07-reputazione-recensioni.md) | Reputation | Solo Google (GBP API, **domanda di accesso da presentare subito**); Facebook API morta (v22) → link-out |
| [08](./08-roadmap.md) | Roadmap & effort | Fasi, dipendenze, stime |

## Architettura complessiva

```
                       ┌────────────────────────────────────────────────┐
                       │                UN SITO FRAPPE (per tenant)     │
                       │                                                │
  Frappe Builder ──────│──  pagine/funnel pubblici, form → CRM Lead     │
  (app ufficiale, MIT) │                                                │
                       │  ┌──────────────┐   ┌───────────────────────┐  │
  Frappe LMS ──────────│─▶│  crm (fork)  │◀──│  crm_suite (NUOVA app)│  │
  (app ufficiale)      │  │  lead/deal   │   │  ├─ automation  (02)  │  │
                       │  │  twilio voice│   │  ├─ funnels     (01)  │  │
  frappe_whatsapp ─────│─▶│  whatsapp api│   │  ├─ inbox/sms   (03)  │  │
  (community, MIT)     │  │  email       │   │  ├─ dialer      (03)  │  │
                       │  └──────────────┘   │  ├─ membership  (04)  │  │
  frappe/payments ─────│──  gateway          │  ├─ booking     (05)  │  │
  (app ufficiale, MIT) │                     │  ├─ reputation  (07)  │  │
                       │                     │  └─ saas        (06)* │  │
                       └─────────────────────┴───────────────────────┴──┘
                              * il modulo saas vive sul sito "agency" centrale

  Infrastruttura: frappe_docker + bench multi-sito + DNS wildcard + TLS wildcard
  Provisioning nuovi tenant: bench new-site + restore del golden site ("snapshot")
```

### Principi decisi

1. **Estendere, non forkare oltre**: tutto il codice nuovo va nella nuova app
   `crm_suite`, installata accanto a `crm`. Il fork del CRM resta minimo
   (branding + hook points) per poter continuare a fare pull da upstream.
2. **Adottare le app ufficiali dove esistono** (Builder, LMS, payments,
   frappe_whatsapp): il costo diventa integrazione, non sviluppo.
3. **Un solo channel-adapter layer** (`send(channel, recipient, payload)`)
   condiviso da workflow engine, inbox, booking e reputation.
4. **Il workflow engine (modulo 02) è la spina dorsale**: quasi ogni altro modulo
   vi si aggancia come trigger o come azione. Va costruito per primo.
5. Stack invariato: Python/Frappe backend, Vue 3 + frappe-ui frontend, MariaDB,
   Redis/scheduler per i job.

### Licenze (sintesi)

- Frappe Framework, Builder ≥1.31, payments, frappe_whatsapp, Vue Flow: **MIT/BSD**.
- CRM (questo fork), LMS, telephony, frappe-appointment: **AGPL-3.0** → l'app
  `crm_suite` va considerata AGPL; il modello di business (vendere il servizio
  hosted, non licenze) è pienamente compatibile, con obbligo di rendere
  disponibile il sorgente modificato agli utenti del servizio (dettagli nel
  [modulo 06](./06-white-label-saas.md), inclusa la questione trademark).

## Azioni con lead time lungo — da avviare SUBITO

Queste pratiche burocratiche durano settimane/mesi e non dipendono dal codice:

1. **Google Business Profile API**: domanda di Basic API Access (quota 0 di
   default; serve profilo GBP verificato da 60+ giorni e dominio email coerente).
2. **Meta Business Verification + App Review** per Messenger/Instagram DM
   (modello tech provider) e per i template WhatsApp.
3. **Twilio**: upgrade account, numeri, e A2P 10DLC se si punta al mercato USA.
4. Registrazione dominio brand + wildcard DNS/TLS per l'infrastruttura SaaS.
