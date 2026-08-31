# 03 — Telefonia, SMS, Power Dialer e Inbox Unificata

> Parte del [Progetto GHL-Parity](./README.md). Obiettivo: SMS bidirezionali,
> power dialer con voicemail drop, e la "Conversations" GHL — un thread unico per
> contatto che unifica email, SMS, WhatsApp, voce e (poi) Messenger/IG DM.

## Punto di partenza: cosa c'è già in questo repo

- **Twilio Voice nativo** con chiamate **nel browser** (`@twilio/voice-sdk` nel
  frontend, WebRTC): popup di chiamata, mute, note in chiamata, registrazione
  attivabile, `CRM Call Log` con recording URL e collegamento a lead/deal.
  Webhook TwiML in `crm/integrations/twilio/api.py` con validazione firma.
- **Exotel** (click-to-call via telefono agente, mercato India).
- **WhatsApp** two-way via `frappe_whatsapp` (tab WhatsApp su lead/deal).
- **Email** two-way in timeline (Communication).
- **Manca del tutto: SMS** (l'integrazione Twilio del CRM è solo voce; l'SMS
  Settings del framework è solo outbound generico).

Repo correlati: [frappe/telephony](https://github.com/frappe/telephony) (AGPL,
estrae Twilio+Exotel per riuso; la [issue #7](https://github.com/frappe/telephony/issues/7)
propone un layer provider-agnostico con SMS — direzione con cui allinearsi).

## 3.1 SMS bidirezionali (build, priorità alta)

Meccanica Twilio verificata:

- **Inbound**: webhook per numero (o Messaging Service) che POSTa `From`, `To`,
  `Body`, `MessageSid`; risposta TwiML o invio via REST. Endpoint Frappe
  `allow_guest` con validazione `X-Twilio-Signature` (stesso pattern già usato per
  la voce).
- **Outbound**: REST API + status callback (queued/sent/delivered/failed).
- Opzione di livello superiore: **Twilio Conversations API** (autocreation di
  conversazione su inbound orfano, webhook `onMessageAdded`) — buon backend per il
  modello a thread; da valutare in fase di design dettagliato.
- ⚠️ Regolamentare: per traffico USA serve registrazione **A2P 10DLC**; per l'Italia
  registrazione mittente alfanumerico dove applicabile.

Implementazione: DocType `SMS Message` threaded per contatto/lead + push realtime
(socketio) nella UI + adapter `send()` riusato dal workflow engine (modulo 02).

## 3.2 Inbox unificata ("Conversations")

GHL unifica in un thread per contatto: email, SMS, WhatsApp, FB Messenger, IG DM,
web chat, voce/voicemail.

### Architettura (`crm_suite.inbox`)

- `Conversation` — contatto/lead/deal, ultimo messaggio, unread count, assegnatario
- `Conversation Message` — canale, direzione, corpo, stato consegna, riferimento
  al record nativo (Communication / WhatsApp Message / SMS Message / CRM Call Log)
- **Channel adapter** condiviso col workflow engine: email, SMS, WhatsApp subito;
  la UI è una pagina "Inbox" nella SPA con thread, composer multi-canale (che
  mostra il canale disponibile in base alla finestra: es. WhatsApp fuori 24h ⇒
  solo template) e filtri (non letti, assegnati a me).

### Meta (Messenger + Instagram DM): per ultimi, sono il "long pole"

Fatti verificati:
- Messenger: webhook `messages`, permessi `pages_messaging`; **finestra 24h**,
  tag `HUMAN_AGENT` (risposte umane fino a 7 giorni) **dietro App Review**.
  Segnalata deprecazione di altri message tag (~feb 2026) — riverificare sul
  changelog Meta in fase di build.
- Instagram DM: solo user-initiated, finestra 24h; produzione richiede
  **Advanced Access → Meta App Review + Business Verification** (review 2025/26
  molto severe). Modello praticabile: diventare **tech provider** (una review
  nostra, poi onboarding clienti via OAuth) — indispensabile per la SaaS mode.
- Nessuna app Frappe esistente implementa questi canali: build custom.

## 3.3 Power Dialer (build — nessun prior art nell'ecosistema)

Spec di parità (GHL + add-on tipo Kixie):
- coda di chiamate sequenziale da una lista/vista filtrata del CRM: a fine
  chiamata parte la successiva; pausa/skip;
- **esiti chiamata (disposition)** per chiamata, che scrivono sul record e possono
  triggerare workflow/cambio stage;
- **voicemail drop**: un click deposita un messaggio preregistrato quando risponde
  la segreteria e passa alla successiva;
- registrazioni auto-allegate, SMS di follow-up templated, missed-call text-back,
  analytics (connect rate, talk time).

Implementazione su ciò che esiste già:
1. `Dial Session` + `Dial Queue Entry` (fed da una CRM view/filtri) — la sessione
   browser Twilio Voice **già presente** viene riusata in loop.
2. Voicemail drop con **Twilio Answering Machine Detection**
   (`MachineDetection=DetectMessageEnd` + `<Play>` del file; callback AMD async
   così l'agente passa alla chiamata successiva mentre il drop viene riprodotto).
3. `Call Disposition` (child su `CRM Call Log`) + hook → trigger di workflow.
4. UI: pannello dialer nella SPA (lista, progress, esiti rapidi, note).

## Ordine di build

1. SMS two-way + DocType inbox + adapter (sblocca anche moduli 02 e 07).
2. Inbox unificata UI (email+SMS+WhatsApp+chiamate nel thread).
3. Power dialer con disposition; voicemail drop (AMD) subito dopo.
4. Missed-call text-back (automazione pronta: trigger "chiamata persa" → SMS).
5. Messenger/IG DM: avviare Business Verification e App Review Meta **in anticipo**
   (lead time lungo), implementare per ultimi.
