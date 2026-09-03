# 12 — WhatsApp Business, connesso dal cliente in un click

> ✅ **FASE 1 IMPLEMENTATA (03/09/2026)** — onboarding completo. Verificato
> sulle guide Meta di settembre 2026. Resta un **prerequisito bloccante lato
> Meta** (programma Tech Provider) prima di poterlo provare davvero: vedi sotto.

## L'obiettivo

Come per Facebook: il cliente apre Settings → WhatsApp, preme **Connetti**,
**scansiona un QR code col telefono**, e da quel momento le chat WhatsApp
stanno **sia nel CRM sia nell'app WhatsApp Business sul telefono**, sincronizzate.
Una sola app Meta dell'agenzia per tutti i clienti.

## Il QR code: quale dei due

Esistono due strade che passano per un QR, e vanno distinte bene.

| | **Coexistence (ufficiale)** | **Ponte WhatsApp Web (non ufficiale)** |
|---|---|---|
| Cos'è | Funzione Meta: l'app WhatsApp Business del cliente viene collegata alla Cloud API | Librerie tipo Baileys / whatsapp-web.js / Evolution API che pilotano WhatsApp Web |
| QR | Sì, si scansiona **dall'app WhatsApp Business** | Sì, si scansiona come "dispositivo collegato" |
| Il cliente continua a usare il telefono | **Sì**, è il punto della funzione | Sì, ma la sessione è fragile |
| Storico chat | **Sincronizza 6 mesi di conversazioni 1:1** e 2 settimane di media | Solo da quel momento |
| Termini di servizio | Conforme | **Violazione**: numeri bannati, rottura a ogni aggiornamento di WhatsApp |
| Costo | Tariffe Meta per conversazione | "Gratis" finché non ti bannano il numero del cliente |

**Andiamo di Coexistence.** Dà esattamente l'esperienza che hai in mente — QR,
telefono che continua a funzionare, chat in entrambi i posti — restando una cosa
vendibile. La strada non ufficiale, su numeri di clienti paganti, è un rischio
che non vale la pena correre.

## Architettura (stesso schema del Facebook già fatto)

L'onboarding di Coexistence si fa con **Embedded Signup**, che gira nel browser
col **JS SDK di Facebook**: la pagina che lo ospita deve stare nella whitelist
dell'app. Con N siti cliente varrebbe lo stesso problema dei redirect URI —
e la soluzione è la stessa: **la pagina di connessione la ospita l'hub**.

```
cliente.it → Settings → WhatsApp → "Connetti"
           → si apre l'hub:  https://hub/whatsapp-connect?site=<firmato>
HUB        → FB.login() con il config_id dell'Embedded Signup v4
             il cliente sceglie/crea la WABA, il numero, e SCANSIONA IL QR
             dall'app WhatsApp Business (schermata gestita da Meta)
           → l'evento WA_EMBEDDED_SIGNUP restituisce waba_id + phone_number_id
           → callback FB.login restituisce un code con TTL di SOLI 30 SECONDI
HUB        → scambia SUBITO il code per il business token (server-side)
           → POST firmato (relay secret) al site del cliente: token + id
cliente.it → salva l'account WhatsApp, si iscrive ai webhook, pronto
```

Il code dura 30 secondi: per questo l'hub **scambia lui** e passa il token al
site via server-to-server, invece di rimbalzare il code nel browser come
facciamo per Facebook.

### Webhook: i flussi sono simmetrici

Come per i lead, la sottoscrizione è **a livello di app**: tutti i messaggi di
tutti i clienti arrivano all'hub, che li smista per WABA (o `phone_number_id`).

Ma la Coexistence aggiunge tre campi che una normale integrazione Cloud API non
vede mai — ed è qui che sta la sincronizzazione bidirezionale:

| Campo | Cosa porta | Chi lo capisce |
|---|---|---|
| `messages` | messaggi in arrivo dai clienti + stati di consegna | **frappe_whatsapp** |
| `smb_message_echoes` | i messaggi che l'azienda scrive **dal telefono** | **nostro** |
| `history` | fino a 6 mesi di conversazioni passate, a chunk | **nostro** |
| `smb_app_state_sync` | la rubrica dell'azienda | **nostro** |
| `account_update` | esito dell'Embedded Signup, stato dell'account | **nostro** |

`frappe_whatsapp` conosce solo `messages`: senza gestire gli altri, **quello che
il cliente scrive dal telefono non comparirebbe nel CRM** — cioè verrebbe a
mancare metà della promessa. Perciò l'hub **spacchetta ogni entry per campo**:
`messages` va all'endpoint di frappe_whatsapp (rifirmato con l'app secret, così
lo valida come una consegna Meta normale), il resto al nostro
(`receive_events`, firmato col relay secret) che li trasforma in
`WhatsApp Message`.

⚠️ Gli echo vengono scritti con `db_insert()`, **non** con `insert()`: un
messaggio Outgoing inserito normalmente farebbe partire l'invio via API a
frappe_whatsapp, e il messaggio — già partito dal telefono — verrebbe recapitato
due volte.

### Session logging

Meta richiede che l'Embedded Signup sia implementato **con session logging**.
La pagina dell'hub riporta ogni passo (`WA_EMBEDDED_SIGNUP`, avvii, annulli con
`current_step`, errori) a `log_session_event`, che li registra nel doctype
**`WhatsApp Signup Session`**: un onboarding che si pianta diventa assistibile
invece che un mistero.

## Cosa serve lato Meta (da fare in quest'ordine)

1. **Programma Tech Provider** — *il prerequisito bloccante*: la documentazione
   dell'Embedded Signup dice "You must already be a Solution Partner or Tech
   Provider". Va richiesto a Meta ed è un processo di verifica. **È la cosa più
   lunga: va avviata subito**, in parallelo con l'App Review dei lead.
2. Prodotto **WhatsApp** aggiunto all'app, con `whatsapp_business_management` e
   `whatsapp_business_messaging`.
3. **Configurazione Facebook Login for Business** per **Embedded Signup v4**
   (variante di login "WhatsApp Embedded Signup"; prodotti: WhatsApp Cloud API
   e Marketing Messages API). ⚠️ Le configurazioni fatte per la v2 **non
   valgono**: la v2 va in pensione il **15 ottobre 2026**.
4. Dominio dell'**hub** in *Allowed domains* e *Valid OAuth redirect URIs*;
   attivi: Client OAuth login, Web OAuth login, Enforce HTTPS, Embedded Browser
   OAuth Login, Strict Mode, **JavaScript SDK login**.
5. Webhook `messages` + `account_update` sull'URL dell'hub.

## Cosa c'è già nel CRM

Il fork parla già con l'app **`frappe_whatsapp`** (di Frappe): doctype
`WhatsApp Message`, `WhatsApp Templates`, `WhatsApp Account`, `WhatsApp Settings`.
`crm/api/whatsapp.py` legge e scrive quei documenti, l'interfaccia chat su
Lead/Deal esiste già (`WhatsAppArea.vue`, `WhatsAppBox.vue`, selettore di
template), e le automazioni hanno già il trigger `on_whatsapp_received`.

Manca **solo l'onboarding**: oggi un `WhatsApp Account` va configurato a mano,
incollando token e phone number id — esattamente la cosa da cui vogliamo
scappare.

## Piano di lavoro

**Fase 1 — onboarding ✅ fatta**
- `crm/www/whatsapp_connect.*` — pagina `/whatsapp-connect` sull'hub con
  l'Embedded Signup v4 (JS SDK, `featureType: whatsapp_business_app_onboarding`
  per la Coexistence), raggiunta con uno state firmato;
- `crm/integrations/whatsapp/signup.py` — scambio del code entro i 30 secondi,
  lettura del numero, sottoscrizione della WABA, consegna firmata al site;
- `crm/integrations/whatsapp/api.py` — il site riceve le credenziali e crea da
  sé il `WhatsApp Account` di frappe_whatsapp (scrivendo **solo i campi che
  quella versione ha davvero**, per non rompersi con release diverse) e lo
  imposta come account di invio;
- `crm/integrations/whatsapp/webhook.py` — l'hub spacchetta il payload per
  account e lo **rifirma con l'app secret**: il site di destinazione lo valida
  come una consegna Meta normale, quindi frappe_whatsapp lo elabora senza
  sapere che esiste un hub;
- doctype `Meta WhatsApp Route` (WABA → site), con le stesse difese delle
  pagine: elenco chiuso dei site e nessuna riassegnazione silenziosa;
- Settings → WhatsApp: stato, numeri, scelta del numero di invio, disconnessione;
- test: `crm/tests/test_whatsapp_connect.py`.

**Config aggiuntiva** (oltre a quelle di `11-app-meta-agenzia.md`):
`whatsapp_signup_config_id` = l'id della configurazione Embedded Signup v4.

**Fase 2 — rifiniture**
- gestione template dal CRM (creazione e stato di approvazione);
- finestra 24h: avviso in chat quando serve un template per riaprire;
- azione "Invia WhatsApp" nelle automazioni (oggi c'è solo il trigger).

## Nota sui costi

WhatsApp non è gratis: Meta fattura **per conversazione** e le regole cambiano
spesso. Fuori dalla finestra di 24 ore dall'ultimo messaggio del cliente si può
scrivere **solo con template approvati**. Va deciso presto se il costo lo
assorbi tu o lo ribalti sul cliente, perché cambia cosa mostrare nell'interfaccia.
