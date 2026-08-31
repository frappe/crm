# 02 — Marketing Automation Omnicanale (Workflow Engine)

> Parte del [Progetto GHL-Parity](./README.md). **È il modulo cuore del progetto**:
> il builder visuale di automazioni multi-step temporizzate (trigger → wait →
> email/SMS/WhatsApp → if/else → goal) che replica i "Workflows" di GHL.

## Verdetto della ricerca: va costruito

Nell'ecosistema Frappe **non esiste un'app matura di marketing automation**:

- **ERPNext Email Campaign**: drip lineare solo-email con offset in giorni; niente
  branch, niente altri canali, bug noti (unsubscribe di un membro uccide la campagna
  [#52448](https://github.com/frappe/erpnext/issues/52448), email in plain text
  [#39176](https://github.com/frappe/erpnext/issues/39176)). Vive in ERPNext, non
  nel CRM. → prior art, non base.
- **Notification** (nativo): messaggi singoli evento-driven — niente sequenze/wait.
- **Workflow** (nativo): macchina a stati di approvazione documenti — non adatta.
- [Frappe-FlowAgent](https://github.com/MirzaAreebBaig/Frappe-FlowAgent) (MIT):
  builder visuale di workflow per Frappe con 27 tipi di nodo — lo spirito giusto,
  ma beta giovane con singolo maintainer. → ispirazione, non fondamenta.
- Fallback non-Frappe: Mautic (GPL-3) via API — scartato: rompe l'esperienza nativa.

**I canali però esistono già** e si riusano come adapter:
Email Queue nativa, [frappe_whatsapp](https://github.com/shridarpatil/frappe_whatsapp)
(MIT, production-ready, Meta Cloud API diretta: template, flows, bulk, webhook di
stato), SMS Settings/Twilio REST (modulo 03).

## Spec di parità: i Workflows GHL

Dalla [lista azioni ufficiale](https://help.gohighlevel.com/support/solutions/articles/155000002294-what-are-workflow-actions-complete-list-)
e correlate:

**Trigger** (categorie): contatto creato/modificato, tag aggiunto, compleanno/data
custom, form inviato, survey, trigger link cliccato, cliente ha risposto,
appuntamento prenotato / cambio stato (confirmed/showed/no-show), opportunità
creata / cambio stage / stale, eventi chiamata, eventi email (open/click/bounce),
fattura pagata, abbonamento, Facebook Lead Form, ordini e-commerce. Ogni trigger
con filtri (quale form, quale pipeline…).

**Azioni**: contatto (create/update, add/remove tag, assign user, note, task, DND),
comunicazione (email, SMS, WhatsApp, voice, voicemail drop, Messenger/IG DM,
notifica interna, review request), dati (webhook, Google Sheets), opportunità
(create/update/remove), pagamenti (Stripe charge, invia fattura), AI prompt.

**Control-flow — la semantica da replicare esattamente:**

- **Wait**: durata fissa / fino a orario-data specifica / fino a evento (es.
  risposta) / relativo alla data appuntamento.
- **If/Else**: N branch + branch "None" obbligatorio; gruppi di condizioni AND/OR
  su campi contatto (anche custom), tag, engagement email, output di step precedenti.
- **Goal Event**: checkpoint — quando un contatto in qualunque punto del workflow
  soddisfa il goal (link cliccato, tag, appuntamento, pagamento) **salta avanti**
  allo step goal o esce, skippando gli step in coda.
- **Split**: ripartizione random % (A/B sulle automazioni).
- Enrollment per-contatto con regole di ri-ingresso: **il record di enrollment è
  la struttura dati centrale.**

## Architettura (`crm_suite.automation`)

### DocType

- `CRM Workflow` *(nome def.: Automation Workflow)* — grafo JSON (nodi+archi),
  stato (draft/attivo/paused), regole di ri-ingresso, statistiche
- `Workflow Trigger` — tipo evento + filtri (child table o campo JSON del grafo)
- `Workflow Enrollment` — contatto/lead/deal + workflow + **step corrente** +
  `wait_until` + stato (active/waiting/completed/exited/goal_met)
- `Workflow Execution Log` — audit per step (inviato, skippato, errore)
- `Trigger Link` — short link tracciato (click ⇒ evento per trigger/goal)

### Motore di esecuzione (Python)

1. **Ingresso**: `doc_events` in `hooks.py` su `CRM Lead`, `CRM Deal`,
   `Communication`, `WhatsApp Message`, `CRM Call Log`, eventi funnel (modulo 01),
   booking (modulo 05), pagamenti → matching dei trigger → crea `Workflow Enrollment`.
2. **Avanzamento**: esecutore idempotente che processa l'enrollment step-by-step;
   i **Wait** impostano `wait_until` (o listener su evento); un **tick dello
   scheduler ogni minuto** (+ `frappe.enqueue` con ETA) riprende gli enrollment
   scaduti.
3. **If/Else**: valutazione condizioni su campi del documento/contatto (safe eval
   in stile filtri Frappe, non Jinja arbitrario).
4. **Goal**: ogni evento in ingresso controlla anche i goal-listener degli
   enrollment attivi → jump forward.
5. **Channel adapter** (interfaccia unica `send(channel, recipient, payload)`):
   - Email → Email Queue nativa + template (tracking open/click con pixel e
     redirect `Trigger Link`);
   - WhatsApp → API di frappe_whatsapp (template Meta approvati fuori dalle 24h);
   - SMS → adapter Twilio (modulo 03);
   - Interno → `CRM Notification`, assegnazione, task.
6. **Throttling/Drip**: batch con rate limit per non bruciare quote provider.

### Frontend: canvas visuale

- **[Vue Flow](https://github.com/bcakmakoglu/vue-flow)** (MIT, ~6.8k stelle,
  attivo, Vue 3 + TS): port di React Flow, nodi/archi come componenti SFC.
  Scelto su Drawflow (dormiente da fine 2024) e Rete.js (overkill: l'esecuzione
  è server-side).
- Pagina `Automations` nella SPA CRM: lista workflow + canvas editor con palette
  nodi (trigger/azioni/control-flow), pannello proprietà per nodo (riuso di
  FieldLayout standalone / formDialog già presenti in questo fork), test-run e
  log per enrollment.
- Editor template email: GrapesJS preset newsletter (fase 2; all'inizio bastano
  gli Email Template esistenti).

## Ordine di build (MVP → parità)

1. **MVP verticale**: trigger "Lead creato" + azioni Email/Wait/Tag + enrollment
   + tick scheduler. Senza canvas: definizione JSON. *(prova del motore)*
2. Canvas Vue Flow + pannelli proprietà + attivazione/pausa.
3. If/Else + Goal + Split + Trigger Link con tracking click.
4. Canali WhatsApp e SMS; trigger da funnel/booking/pagamenti.
5. Statistiche per step, test A/B, template di workflow pronti ("ricette").

## Rischi

- **Deliverability email**: campagne massive richiedono SMTP dedicato
  (SES/Mailgun/Postmark) + SPF/DKIM/DMARC per tenant — da includere nel setup SaaS.
- **Quote Meta/Twilio**: gestione errori e retry nel channel adapter fin dall'MVP.
- Idempotenza dell'esecutore (no doppio invio su retry): chiave univoca
  enrollment+step nel log.
