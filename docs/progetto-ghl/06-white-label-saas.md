# 06 — White-Label / SaaS Mode (multi-tenant)

> ⚠️ **SCOPE RIDOTTO** dal 31/08/2026: di questo modulo restano solo gli script di **provisioning + snapshot** (§6.3, golden site) come strumento interno. Signup, billing, rebilling e white-label aggiuntivo sono fuori scope (vedi [decisioni](./README.md#%EF%B8%8F-decisioni-di-scope-31082026)).

> Parte del [Progetto GHL-Parity](./README.md). Obiettivo: replicare la "SaaS Mode"
> di GoHighLevel — sub-account per cliente, snapshot, rebilling con markup, brand
> proprio — sull'infrastruttura Frappe.

## Cosa fa GHL (spec di parità)

Fonte: [documentazione ufficiale GHL SaaS Mode](https://help.gohighlevel.com/support/solutions/articles/48001177740-activate-saas-mode-request-payment-and-configure-phone-rebilling).

1. **Sub-account ("locations")** — un workspace per ogni cliente dell'agenzia.
2. **Snapshot** — un account-template preconfigurato (pipeline, workflow, template
   email, custom field) clonato automaticamente in ogni nuovo sub-account.
3. **Rebilling con markup** — l'agenzia paga Twilio/Mailgun a prezzo wholesale e
   rifattura al cliente con ricarico; wallet con ricarica automatica.
4. **White-label per agenzia** — dominio custom (CNAME), logo, nome app; sul piano
   $497 anche app mobile brandizzata (a pagamento extra).

## Come lo replichiamo su Frappe

### 6.1 Multi-tenancy: un sito per cliente (già nativo)

Frappe/bench è multi-tenant by design: un bench serve N siti, ogni sito = database
MariaDB separato + directory `sites/<nome>/` separata. **Isolamento più forte del
modello row-level di GHL.**

- `bench config dns_multitenant on` → routing per Host header.
- `bench new-site cliente1.tuobrand.com --install-app crm crm_suite` → **completamente
  scriptabile** (admin password, db root, ecc.): il provisioning è un background job.
- DNS wildcard `*.tuobrand.com` + certificato wildcard Let's Encrypt (DNS-01).
- Dominio custom del cliente: `bench setup add-domain --site cliente1 dominiocliente.com`.

Riferimenti: [docs multitenancy](https://docs.frappe.io/framework/user/en/bench/guides/setup-multitenancy),
[bench wiki](https://github.com/frappe/bench/wiki/Multitenant-Setup).

Vincolo da conoscere: tutti i siti di un bench condividono le versioni delle app
(upgrade = tutti i tenant insieme). Per una SaaS è più pregio che difetto; scalare =
più bench/server.

### 6.2 Stack di deployment (decisione)

| Opzione | Cosa è | Verdetto |
|---|---|---|
| [frappe_docker](https://github.com/frappe/frappe_docker) | Setup Docker/Compose ufficiale, multi-sito | ✅ **Base MVP** |
| [rtCamp/Frappe-Manager](https://github.com/rtCamp/Frappe-Manager) | CLI production: TLS automatico, bench isolati, migrazioni | ✅ Alternativa credibile all'MVP |
| [frappe/press](https://github.com/frappe/press) (AGPL) | La piattaforma dietro Frappe Cloud: provisioning multi-server, billing, marketplace, backup | ⚠️ Production-grade ma pesantissima da self-hostare (agent per server, Ansible, topologia multi-server, doc scarsa). **Solo oltre ~50 tenant** |
| [frappe/pilot](https://github.com/frappe/pilot) | "Frappe Server Manager" nuovo: UI+CLI per app/siti/backup/domini | 🟡 Giovane, da rivalutare |

**Decisione MVP:** frappe_docker + un bench + DNS multitenancy + wildcard TLS +
provisioning scriptato. Press rimandata.

### 6.3 Motore "Snapshot" (da costruire — nessuna app esistente)

L'equivalente Frappe dello snapshot GHL è il **restore di un "golden site"**:

- Si mantiene un sito-template configurato (pipeline, workflow, template, campi).
- Alla firma di un nuovo cliente: `bench new-site` + `bench --site nuovo restore golden.sql.gz`
  (oppure fixtures/data-import da app custom per snapshot più granulari).
- DocType da creare nell'app `crm_suite` (modulo `saas`):
  - `SaaS Plan` (prezzo, limiti, app incluse)
  - `SaaS Tenant` (sito, dominio, stato, piano, snapshot usato)
  - `SaaS Snapshot` (riferimento al backup/fixture-set del golden site)
  - `SaaS Provisioning Job` (coda + log del provisioning)
- Signup flow pubblico (web form + Stripe Checkout) → job in coda → sito pronto in
  minuti → email di benvenuto con credenziali.

### 6.4 Rebilling con markup (da costruire)

Nessuna scorciatoia open-source esistente. Design:

- **Metering**: ogni sito tenant registra uso (SMS inviati, minuti voce, email) in un
  DocType locale `Usage Record`; un job giornaliero lo spinge via API al sito "agency"
  centrale.
- **Pricing**: `SaaS Plan` definisce prezzo unitario con markup configurabile per
  tenant (es. SMS wholesale Twilio ~$0.0079 → rivenduto a $0.015).
- **Billing**: Stripe usage-based billing (metered prices) + wallet/credito opzionale.
- Press ha primitive di billing ma **non** il rebilling con markup: si costruisce.

### 6.5 White-label del CRM

- Pattern collaudato nell'ecosistema: piccola app "whitelabel" che sovrascrive logo,
  favicon, nome app, navbar (es. [routeget/erpnext15-whitelabel](https://github.com/routeget/erpnext15-whitelabel)).
- Per la SPA di Frappe CRM: patch dei riferimenti "Frappe CRM"/logo negli asset del
  frontend (siamo già un fork: banale) + logo per-tenant da `SaaS Tenant`.
- App mobile brandizzata: fuori scope iniziale (GHL la fa pagare ~$497/mese extra);
  la PWA del CRM copre il caso d'uso a costo zero.

### 6.6 Licenze e obblighi (sintesi fattuale, non parere legale)

- Frappe Framework: **MIT**. Frappe CRM: **AGPL-3.0**
  ([license & trademark](https://docs.frappe.io/legal/others/license-and-trademark.md)).
- **AGPL §13 (network clause)**: se modifichiamo Frappe CRM (lo stiamo facendo: fork)
  e lo offriamo come servizio in rete, dobbiamo mettere a disposizione degli utenti
  del servizio il sorgente modificato sotto AGPL. Il reselling hosted è **permesso e
  senza royalty**; ciò che si vende è il servizio, non la licenza.
- App proprie separate che non modificano/linkano il codice CRM: zona grigia dibattuta;
  tutto ciò che patcha il CRM è chiaramente coperto da AGPL. Strategia: tenere
  `crm_suite` pubblicabile, o negoziare la licenza commerciale Frappe
  (legal@frappe.io — termini non pubblici).
- **Trademark**: vietato usare i marchi "Frappe"/"ERPNext" nel nome di prodotto/dominio
  senza consenso scritto — il rebranding è quindi la direzione *conforme*.

### 6.7 Confronto TCO con GHL

Prezzi GHL 2025/26 (cross-check su 3+ fonti; riconfermare su gohighlevel.com):

| Piano GHL | Prezzo | Note |
|---|---|---|
| Starter | $97/mese | max 3 sub-account, no API |
| Unlimited | $297/mese | sub-account illimitati, white-label base |
| Agency SaaS Pro | $497/mese | SaaS mode completa, rebilling, snapshot |

Più costi d'uso (SMS ~$0.0079–0.012/segmento, email ~$0.68–0.90/1000, numeri,
azioni workflow premium, app mobile white-label extra).

Self-hosted Frappe: VPS multi-tenant ~$40–100/mese a piccola scala + costi d'uso
identici (Twilio/SMTP diretti, wholesale) + **tempo di sviluppo** (il vero costo).
Il markup sul rivenduto resta al 100% nostro, senza fee per sub-account.

## Deliverable del modulo

1. Stack Docker multi-tenant con wildcard DNS/TLS (settimana 1–2).
2. App `crm_suite.saas`: DocType tenant/plan/snapshot + provisioning job.
3. Signup pubblico + Stripe Checkout + golden-site restore.
4. App whitelabel (logo/nome per-tenant).
5. Metering + rebilling Stripe usage-based (fase 2).
