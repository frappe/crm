# 01 — Funnel & Landing Page Builder

> Parte del [Progetto GHL-Parity](./README.md). Obiettivo: costruzione visuale di
> landing page e funnel multi-step con A/B test, form di cattura lead e checkout.

## Cosa fa GHL (spec di parità)

- **Funnel = sequenza ordinata di step** (opt-in → sales page → order form →
  upsell/downsell → thank-you), ogni step con un path sotto lo stesso dominio;
  tracking per step di visite/opt-in/vendite.
- **A/B split test**: duplica uno step come variante B, split % del traffico,
  assegnazione sticky del visitatore, statistiche di conversione per variante.
- **Checkout**: prodotti one-time, abbonamenti, piani di pagamento, **order bump**
  (checkbox sull'order form), **one-click upsell** (riaddebito sul metodo di
  pagamento tokenizzato senza reinserire la carta).
- Gateway: Stripe, PayPal, Authorize.net, NMI, Square.

## Fatti verificati sull'ecosistema (agosto 2026)

### Frappe Builder — il page builder c'è già, ed è MIT

[frappe/builder](https://github.com/frappe/builder) — sviluppo attivissimo
(release quindicinali, v1.33 ad agosto 2026), ~2.3k stelle.

- **Licenza: MIT dalla v1.31 (luglio 2026)** — prima era AGPL. Per uso commerciale
  costruire su ≥1.31.
- Editor visuale drag-drop stile Figma (flexbox/grid), breakpoint responsive,
  dark mode, blocchi predefiniti, CSS custom.
- **CMS integrato**: dati dinamici dai DocType, data script per blocco, client
  script, publishing one-click servito dal web server del sito Frappe (frappe.io
  stesso gira su Builder). Analytics di pagina integrate.
- **Agente AI "Bob"** (v1.33): costruzione/modifica conversazionale delle pagine,
  wiring dei form a data source reali.
- Form → lead: pattern attuale = client script con `fetch()` verso API whitelisted
  che inserisce in `CRM Lead`; il supporto form nativo sta atterrando ora (v1.33)
  ma è nuovo e poco documentato. Poiché Builder gira **sullo stesso sito** del CRM,
  l'inserimento è diretto, senza webhook.
- **Cosa Builder NON è**: un funnel builder. Niente sequenze di step, A/B test,
  checkout/order-bump/upsell. Niente mapping dominio→singolo funnel (i domini
  custom sono a livello sito: `bench setup add-domain`).

### Alternative valutate

- [GrapesJS](https://github.com/GrapesJS/grapesjs) (BSD-3, ~25k stelle, attivo):
  giusto solo se serve l'editor **dentro** la nostra SPA; ha anche preset
  newsletter → utile come **editor di template email** nel modulo 02.
  (Esiste [libracore/PageMaster](https://github.com/libracore/PageMaster) come
  PoC GrapesJS-in-Frappe, non una base.)
- **Frappe Web Forms** (nativi, MIT): form→DocType con submission guest, multi-step
  (page break), campi condizionali, **pagamenti via frappe/payments**. Production-
  grade ma esteticamente basici → motore form dietro pagine Builder.

### Pagamenti

- [frappe/payments](https://github.com/frappe/payments) (MIT, usato da ERPNext):
  gateway Stripe, Razorpay, PayPal, Braintree, PayTM (Mollie in arrivo). Modello
  "Payment Request" hosted-checkout. **API in ridisegno: pinnare le versioni.**
- **Gap per parità GHL**: niente carta salvata / one-click charge / order bump /
  checkout abbonamenti. → Per il checkout dei funnel si parla **direttamente con
  Stripe** (PaymentIntents + SetupIntents con metodo di pagamento salvato: è la
  via realistica per l'upsell one-click), incapsulato come gateway aggiuntivo.

## Decisione architetturale

**Frappe Builder (≥1.31) per le pagine + layer funnel custom in `crm_suite.funnels`.**
Non si costruisce un page builder: si costruisce solo ciò che manca — la logica
funnel sopra le pagine.

### DocType (`crm_suite.funnels`)

- `Funnel` — nome, dominio/route base, stato, statistiche aggregate
- `Funnel Step` — ordine, tipo (optin/sales/order/upsell/thankyou), pagina Builder
  collegata, path
- `Funnel Step Variant` — variante A/B, % split, contatore conversioni
- `Funnel Visitor` — visitor id (cookie), variante assegnata (sticky), eventi
- `Funnel Conversion Event` — step, tipo (view/optin/purchase), valore, lead creato
- `Funnel Order` — checkout: prodotti, bump accettato?, upsell, PaymentIntent id

### Meccanica

1. **Routing**: website route handler `/{funnel}/{step}` che risolve la pagina
   Builder della variante assegnata (cookie sticky, split % random alla prima
   visita) e logga l'evento view.
2. **Form**: Web Form o form Builder che POSTa su API whitelisted → crea
   `CRM Lead` (con source = funnel/step/variante) → può **iscrivere il lead a un
   workflow** (modulo 02).
3. **Checkout**: pagina order con Stripe Elements; PaymentIntent + salvataggio del
   payment method; order bump = line item condizionale; pagina upsell post-acquisto
   che riaddebita il metodo salvato (one-click).
4. **Stats**: dashboard per funnel (visite, opt-in rate, conversion rate, revenue
   per step/variante).

## Deliverable e ordine

1. Installazione Frappe Builder sul bench + prova pubblicazione pagina con form → `CRM Lead`.
2. DocType funnel + routing multi-step + tracking eventi.
3. A/B variant assignment sticky + statistiche.
4. Checkout Stripe (one-time) → order bump → upsell one-click (fase 2).
5. Collegamento ai workflow (trigger "Form Submitted", "Order Placed") — modulo 02.
