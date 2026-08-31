# 10 — Meta Lead Ads (Facebook + Instagram) production-grade

> ✅ **IMPLEMENTATO (31/08/2026)**. Ricostruita l'integrazione lead sync sulla base
> delle guide ufficiali Meta (developers.facebook.com, verificate ad agosto 2026).
> Sostituisce il flusso "incolla access token" (che si rompeva in ore: i token
> utente scadono) con OAuth completo + webhook real-time + riconciliazione.

## Architettura implementata

```
Settings modal → "Meta Lead Ads"
  1. App ID/Secret (+ webhook URL e verify token da copiare nell'app Meta)
  2. "Connect with Facebook" → OAuth code flow (state firmato HMAC)
       code → user token → LONG-LIVED user token (~60gg)
       → /me/accounts → PAGE TOKEN per pagina (non scade) cifrati (Password)
       → pagine + form (paginati) upsert, con mapping domande preservato
  3. Selezione pagine: toggle per pagina → POST /{page}/subscribed_apps
       (subscribed_fields=leadgen, col page token) → webhook real-time
  4. Mapping campi: per form, domande (per KEY, non label) → campi CRM Lead,
       con default automatici (FULL_NAME→nome, EMAIL, PHONE, ...)
```

**Ingestione** (`crm/integrations/meta/leads.py`), condivisa da webhook e polling:
- webhook `crm.integrations.meta.webhook.handle`: GET = handshake hub.challenge;
  POST = verifica **X-Hub-Signature-256** (HMAC-SHA256 del body col app secret),
  risposta 200 immediata + coda (Meta ritenta per sole 36h) — il payload NON
  contiene i dati: fetch di /{leadgen_id} col page token;
- **dedup per `facebook_lead_id`** (id globale univoco ⇒ webhook+polling idempotenti);
- FULL_NAME splittato in nome/cognome, telefoni normalizzati (`p:+39...`),
  source Facebook/Instagram (campo `platform` con fallback se non disponibile);
- **riconciliazione oraria** sugli ultimi 2 giorni dei form delle pagine attive
  (retry webhook = 36h; la dedup la rende economica);
- **backfill 90 giorni** on-demand (Meta CANCELLA i lead dopo 90 giorni: mai
  trattare Meta come system of record);
- failure log (`Failed Lead Sync Log`) su ogni lead non importabile;
- **token health giornaliero** via /debug_token, flag sulla pagina + error log;
- ogni chiamata Graph porta **appsecret_proof** (si può attivare "Require App
  Secret" sull'app);
- trigger automazioni: i lead creati emettono `Lead Created` con payload
  `{facebook_form_id, source}` ⇒ le automazioni possono filtrare per form
  (equivalente del trigger GHL "Facebook Lead Form Submitted").
- **Data Deletion Callback** (`.../webhook.data_deletion`, signed_request
  verificato) — richiesto dall'App Review.
- Instagram: i lead IG appartengono alla stessa pagina Facebook (conferma docs) —
  un'unica integrazione copre entrambi.

## Checklist di produzione (dalle guide ufficiali)

### App Meta (developers.facebook.com)
1. Prodotto **Facebook Login**: Valid OAuth redirect URI =
   `https://<site>/api/method/crm.integrations.meta.oauth.callback` (HTTPS).
   (Non esiste API pubblica per questa whitelist: è l'unico passo davvero
   manuale, insieme alla creazione dell'app.)
2. **Webhook (Page → leadgen): CONFIGURATO AUTOMATICAMENTE** al salvataggio di
   App ID/Secret (o col bottone "Configure automatically") via
   `POST /{app_id}/subscriptions` con l'app token — Meta verifica il callback
   in modo sincrono, quindi il sito deve essere raggiungibile in HTTPS. La
   configurazione manuale resta documentata in Settings come fallback.
3. **Data Deletion Request URL** =
   `https://<site>/api/method/crm.integrations.meta.webhook.data_deletion`.

### App Review (per usare l'app con utenti esterni al team)
- **Advanced Access** per: `pages_show_list`, `pages_read_engagement`,
  `pages_manage_metadata`, `pages_manage_ads`, `leads_retrieval`,
  `ads_management` (+ `business_management`; per il Social Planner anche
  `pages_manage_posts`, `instagram_basic`, `instagram_content_publish`) —
  con **Business Verification**
  dell'azienda e screencast del flusso completo (login → scelta pagina → sync).
- **Data Use Checkup** annuale.
- In development mode i webhook reali non arrivano: usare il
  [Lead Ads Testing tool](https://developers.facebook.com/tools/lead-ads-testing)
  o il bottone **"Test lead"** in Settings (`POST /{form}/test_leads`, 1 per form).

### Il tranello n°1: Leads Access Manager
Se il Business ha attivato la personalizzazione dell'accesso ai lead, le API
rispondono vuoto/permission error **anche con token validi**: in
**Business Settings → Integrations → Leads Access** va assegnato questo CRM.
L'hint è mostrato anche nella pagina Settings.

### Rate limit
Leadgen: ~4800 × lead generati (90gg) chiamate/24h per pagina; usare i page token
(bucket separati); backoff sui codici 4/17/32/613/80001.

## Compatibilità

Il vecchio flusso `Lead Sync Source` (token manuale + polling) resta funzionante:
se la pagina del form è collegata via OAuth usa automaticamente il nuovo motore
paginato; altrimenti ricade sul token incollato (legacy).

## Test

`crm/tests/test_meta_leads.py`: mapping/split nome, idempotenza, source IG,
failure log, normalizzazione telefono, merge domande senza perdere mapping,
verifica firma webhook.
