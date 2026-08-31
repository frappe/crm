# 09 — Social Planner (agenda social stile GHL)

> ✅ **MVP IMPLEMENTATO (31/08/2026)**, aggiunto allo scope su richiesta.
> Basato su ricerca dalle guide GHL e dalle API di publishing (agosto 2026).

## Cosa fa GHL (spec di parità)

Social Planner: composer multi-network con personalizzazione per piattaforma,
calendario (mese/settimana/lista), stati bozza/approvazione/programmato,
post ricorrenti, bulk CSV (90 post), RSS-to-post, gestione commenti, analytics
per post. Reti 2026: FB, IG, Threads, LinkedIn, GBP, TikTok, YouTube, Pinterest,
Bluesky. **X/Twitter NON è supportato da GHL** (abbandonato nel 2023).

## Fatti chiave della ricerca (determinano l'architettura)

- **Le app review sono il vero costo**, non il codice: Meta (business
  verification + advanced access, settimane), **LinkedIn Community Management
  API 1–4 mesi e solo entità legali**, TikTok audit (senza audit i post escono
  SELF_ONLY), YouTube upload forzati privati senza audit + quota 6 upload/dì,
  GBP localPosts vive ancora sull'endpoint legacy v4 (rischio sunset).
- **[Postiz](https://github.com/gitroomhq/postiz-app)** (AGPL, ~35k stelle,
  attivissimo) è self-hostabile con **API REST pubblica**
  ([docs](https://docs.postiz.com/public-api)): può fare da **motore di
  pubblicazione headless** — le app dei network le crei tu una volta a livello
  agenzia, gli OAuth/retry/media pipeline li gestisce Postiz.
- **[Ayrshare](https://www.ayrshare.com)** (aggregatore a pagamento, da
  ~$149/mese): usa le SUE app già approvate → **zero app review, live in un
  giorno**. Perfetto come ponte iniziale.
- Mixpost Pro ($299 una tantum) è l'alternativa a Postiz; Lite (MIT) troppo
  limitato.

## Architettura implementata

**Frontend e dati in Frappe, pubblicazione via adapter pluggabili** (scelta in
`CRM Social Settings`):

| Adapter | Stato | Note |
|---|---|---|
| **Meta (built-in)** | ✅ | pubblica DIRETTAMENTE su Facebook Page e Instagram Business con la Graph API, riusando i page token dell'OAuth Meta Lead Ads (nessun servizio terzo). FB: `/feed`, `/photos`, `/videos`; IG: container `/media` (+polling status) → `/media_publish`; IG richiede un media, video = REELS. Scope aggiunti: `pages_manage_posts`, `instagram_basic`, `instagram_content_publish`. |
| **Manual** | ✅ | nessuna chiamata esterna: il planner traccia e "pubblica" (per test e flussi manuali) |
| **Postiz** | ✅ | `POST {url}/public/v1/posts` con API key; `provider_account_id` = integration id |
| **Ayrshare** | ✅ | `POST /api/post` con Bearer key; mapping piattaforme incluso |

### Collegamento profili in un click (`crm/social/accounts.py`)

Niente più id incollati a mano: in Settings → Social Planner il bottone
**"Import connected profiles"** interroga il provider e fa upsert dei
`CRM Social Account` (match per piattaforma+id):

- **Meta**: pagine Facebook già connesse (+ account Instagram Business
  collegati, letti da `instagram_business_account` in `/me/accounts`); ogni
  account porta il link alla `Facebook Page` per il token di pubblicazione.
- **Postiz**: `GET {url}/public/v1/integrations` (i profili si collegano
  nella UI di Postiz, poi si importano).
- **Ayrshare**: `GET /api/user` → `displayNames` (profilo default; i
  profileKey multi-profilo restano manuali).

### Componenti

- DocType: `CRM Social Settings` (single: provider+credenziali),
  `CRM Social Account` (piattaforma + id provider), `CRM Social Post`
  (contenuto, media, stato, schedule, ricorrenza, approvazioni) +
  child `CRM Social Post Target` (account, override per network, esito).
- Scheduler ogni 2 minuti (`crm.social.publisher.process_due_posts`):
  pubblica i post Scheduled scaduti, aggiorna esiti per target, gestisce le
  **ricorrenze** (clona alla prossima occorrenza) e notifica via realtime.
- **Flusso approvazioni**: Sales User → bozza / "Request approval";
  Sales Manager → Approva/Programma/Pubblica subito.
- Pagina **`/social`** (redesign 31/08): calendario mensile Espresso con
  header giorni, cella "oggi" evidenziata, chip con pallini colorati per
  piattaforma + bordo colorato per stato, overflow "+N" con dialog del
  giorno, legenda stati, CTA "Connect profiles" se non ci sono account;
  composer con chip profilo colorati, contatore caratteri, anteprima
  immagine, errori per-target visibili sui post falliti.
- Test: `crm/tests/test_social.py` (incl. sync account da pagine FB/IG).

## Setup operativo

1. **Percorso consigliato**: provider **Meta** → App ID/Secret in
   Meta Lead Ads (webhook auto-configurato), "Connect with Facebook",
   poi "Import connected profiles": FB+IG pubblicano nativamente.
2. Per le altre reti: **Postiz self-hosted** (Docker) + avviare SUBITO le
   pratiche (LinkedIn è il collo di bottiglia) oppure ponte **Ayrshare**
   (zero review, `profileKey` per cliente).
3. **Manual** resta utile per test e flussi solo-pianificazione.

## Non incluso (fase 2)

Bulk CSV, RSS-to-post, gestione commenti, analytics per post (Postiz/Ayrshare
le espongono via API), viste settimana/lista.
