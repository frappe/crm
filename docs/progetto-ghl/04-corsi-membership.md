# 04 — Corsi, Membership e Aree Riservate

> ⚠️ **FUORI SCOPE** dal 31/08/2026 (vedi [decisioni di scope](./README.md#%EF%B8%8F-decisioni-di-scope-31082026)). Conservato come riferimento.

> Parte del [Progetto GHL-Parity](./README.md). Obiettivo: vendere corsi online e
> membership (stile Teachable/Kajabi, come il modulo Memberships di GHL).

## Verdetto della ricerca: **si adotta, non si costruisce**

[**Frappe LMS**](https://github.com/frappe/lms) (AGPL-3.0, ~3.2k stelle, release
**settimanali/mensili** — v2.62.1 del 28/08/2026) copre ~90% della parità GHL:

- Corsi → capitoli → lezioni: testo, video, PDF, **quiz** (chiuse/aperte),
  **SCORM**, assignment con consegne.
- **Certificati** al completamento (template personalizzabile), directory dei
  certificati.
- **Batch (coorti)** con **classi live Zoom** schedulate dall'app, pricing per batch.
- **Corsi a pagamento**: flag `Is Paid Course` → gateway di pagamento →
  auto-enrollment al pagamento. Usa [frappe/payments](https://github.com/frappe/payments)
  (MIT: Stripe, Razorpay, PayPal, Paytm, Braintree, M-Pesa, GoCardless).
- Progress tracking per lezione/corso, statistiche, discussioni con moderazione.
- Frontend **Vue 3 + frappe-ui** (SPA su `/lms`) — lo stesso stack del CRM.

### Convivenza con il CRM: verificata

`bench install-app crm && bench install-app lms` sullo stesso sito: CRM su `/crm`,
LMS su `/lms`, **stessi utenti/auth/database**. Unico vincolo: tenere allineate le
versioni Frappe richieste dalle due app (entrambe tracciano v15/develop; LMS
richiede anche `payments`).

## I gap reali da costruire (`crm_suite.membership`)

Confermato dalla ricerca (docs+issues LMS): mancano **drip content, abbonamenti
ricorrenti, bundle/offerte, community feed**.

1. **Drip content**: DocType `Lesson Schedule` / regola "sblocca lezione N giorni
   dopo l'enrollment" via `scheduler_events`.
2. **Membership a abbonamento**: `Access Pass` (tier) + Stripe Billing
   (subscription webhook → grant/revoke ruolo e enrollment). Pattern di
   riferimento: il vecchio modulo Membership di ERPNext Non Profit (deprecato,
   solo come prior art).
3. **Bundle/offerte**: un acquisto → N corsi/pass (si aggancia al checkout funnel
   del modulo 01, che ha già Stripe con metodo salvato).
4. **Ponte CRM ↔ LMS** (il vero valore rispetto a usare Kajabi separato):
   - acquisto/enrollment ⇒ evento per il **workflow engine** (modulo 02): tag
     "studente", sequenze di onboarding, upsell;
   - progresso stagnante ⇒ trigger "re-engagement";
   - lead del CRM ⇒ vista dei corsi/membership attive del contatto.
5. (Fase 2) Community feed stile GHL Communities — valutare se davvero serve.

## Licenze

LMS è AGPL-3.0 (come il CRM): stesso regime già accettato per il fork — nessun
vincolo nuovo. `payments` è MIT.

## Deliverable e ordine

1. Installare LMS+payments sul bench di sviluppo, corso demo a pagamento end-to-end.
2. Ponte eventi LMS→workflow engine (enrollment, completamento, pagamento).
3. Drip content + Access Pass a abbonamento (Stripe Billing).
4. Bundle nel checkout funnel.
5. White-label del portale LMS per la SaaS mode (modulo 06).
