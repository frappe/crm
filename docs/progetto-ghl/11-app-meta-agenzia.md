# 11 — Una sola app Meta per tutti i clienti

> ✅ **IMPLEMENTATO (03/09/2026)**. Il cliente preme "Connetti con Facebook" e
> vede il popup di Meta. Non crea app, non vede App ID/Secret, non tocca
> developers.facebook.com. L'app è **una sola, dell'agenzia**, come fa GHL.

## Il problema

Ogni cliente ha un site Frappe separato. Con un'app Meta per cliente servirebbe,
per ognuno: creare l'app, business verification, App Review (settimane). Non sta
in piedi. Ma un'app condivisa incontra due vincoli tecnici:

1. **Redirect URI**: Meta pretende una corrispondenza **esatta** con la
   whitelist dell'app e **non supporta wildcard**
   ([Login Security](https://developers.facebook.com/docs/facebook-login/security)) —
   non si possono whitelistare N domini cliente che crescono nel tempo.
2. **Webhook**: la sottoscrizione è **a livello di app**, non di pagina. Un'app
   sola = **un solo URL di callback** per tutti i lead di tutti i clienti.

## La soluzione: un site "hub"

Un site (es. `hub.miaagenzia.it`, anche esso un CRM di questa stessa codebase)
è l'unico indirizzo registrato sull'app Meta. Fa da centralino.

### OAuth — è il pattern che Meta stessa raccomanda

> *"For apps with dynamic redirect URIs, use the `state` parameter to pass back
> the dynamic information to a limited number of redirect URIs."*

```
cliente.it  → "Connetti con Facebook"
            → dialog Meta con redirect_uri = HUB, state firmato {site: cliente.it}
utente autorizza (popup Meta standard)
            → Meta redirige all'HUB
HUB         → verifica la firma dello state, rilancia il code a cliente.it
cliente.it  → scambia il code (redirect_uri = HUB, come richiede Meta) con
              l'app secret condiviso → token → sync pagine/form
```

Il code è monouso e inutile senza l'app secret, che hanno solo i nostri site.
La destinazione arriva dallo **state firmato in HMAC**: non è un open redirect.

### Webhook — l'hub smista

```
Meta → HUB /webhook.handle  (verifica X-Hub-Signature-256)
HUB  → per ogni notifica legge page_id nella tabella "Meta Page Route"
     → inoltra al site proprietario, firmando con X-CRM-Relay-Signature
cliente.it → accetta la firma del relay ed elabora il lead come sempre
```

La tabella si popola da sola: quando un cliente attiva "Sync leads" su una
pagina, il suo site chiama l'hub (`register_page_route`, firmato) e rivendica
quella pagina.

## Creazione dell'app, passo per passo

1. **developers.facebook.com → My Apps → Create app.**
   - *App name*: **lo vedono i clienti nel popup di login** — mettere il nome
     commerciale dell'agenzia, non "test".
   - *Use case*: **Other** → tipo **Business**. Attenzione: gli use case
     **non si possono più rimuovere** dopo la creazione.
   - *Business portfolio*: collegare il Business Manager dell'agenzia (serve
     poi per la Business Verification).
2. **App settings → Basic**: copiare **App ID** e **App Secret**. Compilare
   Privacy Policy URL e Terms of Service (obbligatori per l'App Review).
3. **Prodotti → Facebook Login → Settings → Valid OAuth Redirect URIs**:
   incollare il callback dell'**hub** (una riga; se ne possono aggiungere
   altre in seguito, es. quando nasce un hub definitivo):
   `https://<hub>/api/method/crm.integrations.meta.oauth.callback`
4. **Config del site** (sotto): App ID, secret, relay secret, hub URL.
5. **Webhook**: nel CRM **dell'hub**, Settings → Meta → "Configure
   automatically". Il CRM registra `Page → leadgen` da solo; il site deve
   essere raggiungibile in HTTPS perché Meta verifica il callback sul momento.
6. **App settings → Advanced → Data Deletion Request URL**:
   `https://<hub>/api/method/crm.integrations.meta.webhook.data_deletion`
7. **Prova end-to-end**: Settings → Meta → "Connetti con Facebook" → attivare
   "Sync leads" su una pagina → bottone **"Test lead"** sul form.
   In development mode funziona solo con gli account del team dell'app
   (App roles → Add people), ed è normale.
8. **App Review**: avviarla subito, è la parte lunga (settimane).

## Configurazione (una volta sola, sul bench)

`common_site_config.json` — vale per **tutti** i site:

```json
{
  "meta_app_id": "1234567890",
  "meta_app_secret": "…",
  "meta_relay_secret": "…stringa lunga a caso, condivisa…",
  "meta_hub_url": "https://hub.miaagenzia.it"
}
```

Sul **site hub** stesso: stesse chiavi ma **senza** `meta_hub_url` (o con il
proprio URL), così processa invece di rilanciare.

Sull'app Meta (developers.facebook.com), una volta sola:
- **Facebook Login → Valid OAuth Redirect URI**:
  `https://hub.miaagenzia.it/api/method/crm.integrations.meta.oauth.callback`
- **Webhooks → Page → leadgen**:
  `https://hub.miaagenzia.it/api/method/crm.integrations.meta.webhook.handle`
  (configurabile dal bottone in Settings → Meta **sull'hub**)
- **Data Deletion**: `…/webhook.data_deletion` sull'hub.

Quando le chiavi sono nel config, la pagina Settings → Meta del cliente
**nasconde** App ID/Secret e webhook e mostra solo "Connetti con Facebook".

## Cosa resta da fare all'agenzia (una volta)

**App Review con Advanced Access** sull'app unica, con Business Verification:
`pages_show_list`, `pages_read_engagement`, `pages_manage_metadata`,
`pages_manage_ads`, `leads_retrieval`, `ads_management`, `business_management`
+ per il Social Planner `pages_manage_posts`, `instagram_basic`,
`instagram_content_publish`. Serve uno screencast del flusso completo
(login → scelta pagina → arrivo lead). Finché l'app è in development mode
funziona solo con gli account del team dell'app.

Valutare la designazione **Meta Tech Provider** (app usata da altre aziende):
dà supporto dedicato e sblocca l'onboarding di business terzi con la propria app.

## Senza hub (fallback)

Se `meta_hub_url` non è impostato, tutto funziona come prima: ogni site è il
proprio callback e va whitelistato singolarmente sull'app. Con app condivisa ma
senza hub i webhook arrivano a un solo site: gli altri prendono comunque i lead
dalla **riconciliazione oraria** + backfill (ritardo fino a un'ora invece del
tempo reale).

## Test

`crm/tests/test_meta_leads.py::TestMetaSharedApp`: firma/manomissione/scadenza
dello state, firma del relay, risoluzione della rotta per pagina.
