# 07 — Reputation Management (recensioni)

> Parte del [Progetto GHL-Parity](./README.md). Obiettivo: richiesta automatica di
> recensioni via SMS/email, dashboard recensioni aggregate, risposta dalla dashboard.

## Cosa fa GHL (spec di parità)

Flusso GHL ([riferimento](https://supplygem.com/gohighlevel-reputation-management/)):
appuntamento/transazione completata → trigger di workflow → SMS/email con **deep link
diretto al form di recensione** → dashboard che aggrega recensioni Google/Facebook →
risposta dalla dashboard (solo Google, via API) → suggerimenti AI per le risposte.

## Fatti verificati (2025/26) che determinano il design

### Google Business Profile (GBP) API — l'unico canale completo ufficiale

- [Review data API](https://developers.google.com/my-business/content/review-data):
  lettura di **tutte** le recensioni per location (paginata), **creazione/modifica/
  cancellazione delle risposte**, batch multi-location. Tutto attivo.
- **Accesso gated**: ogni progetto GCP parte con **quota 0**. Serve l'"Application
  for Basic API Access": business case legittimo, profilo GBP verificato attivo da
  60+ giorni, dominio del sito che combacia col dominio email di contatto.
  Approvazione manuale (giorni–settimane). **→ La domanda va presentata SUBITO,
  all'avvio del progetto.**
- Quote post-approvazione: ~300 richieste/minuto; modifiche max 10/min per profilo.
- OAuth: l'app agisce per conto del **proprietario/gestore** del profilo (il cliente
  concede accesso via Google OAuth) — perfetto per il modello agenzia.
- **Places API non è un sostituto**: massimo 5 recensioni, senza risposte
  ([issue storica](https://issuetracker.google.com/issues/35825957)).

### Facebook — di fatto morto via API

- Da **Graph API v22.0 (gennaio 2025)** l'endpoint `/{page}/ratings` è deprecato:
  le letture restituiscono errore e i webhook ratings non vengono più inviati
  ([changelog v22](https://developers.facebook.com/docs/graph-api/changelog/version22.0/)).
- Anche GHL e i concorrenti sono colpiti allo stesso modo. **Decisione: Facebook solo
  come link-out alla tab Recensioni della pagina; programmatico solo Google.**

### Il deep link di recensione è banale

```
https://search.google.com/local/writereview?placeid=<PLACE_ID>
```
apre direttamente il form di recensione (Place ID dal GBP dashboard o Places API).

### Open-source esistente: nulla

Il settore (Birdeye, Podium, GHL, NiceJob…) è tutto SaaS commerciale; nessun progetto
open-source mantenuto trovato. **Il modulo è un build from scratch**, ma il cuore è
modesto: OAuth Google + ~4 endpoint GBP.

## Design del modulo (`crm_suite.reputation`)

### DocType

- `Review Location` — location GBP collegata (place_id, account/location GBP, token OAuth)
- `Review` — recensione sincronizzata (rating, testo, autore, data, replied?)
- `Review Request` — richiesta inviata (contatto CRM, canale SMS/email, stato, click)
- `Reputation Settings` — credenziali OAuth, template messaggi, soglie

### Meccanica

1. **Sync**: job scheduler che effettua polling delle recensioni (l'API base non ha
   webhook affidabili per nuove recensioni; il polling entro 300 QPM è il design
   sicuro — Pub/Sub Notifications API da verificare in fase di build).
2. **Richieste**: azione "Richiedi recensione" su deal vinto / appuntamento completato
   + **azione nativa nel workflow engine** (modulo 02): invia SMS/email col deep link.
3. **Dashboard**: pagina Vue nella SPA CRM — media rating, trend, ultime recensioni,
   risposta inline (via API GBP), filtro per location.
4. **Notifiche**: recensione ≤3 stelle → notifica/assegnazione immediata a un utente.
5. (Fase 2) Risposte suggerite via AI.

### Dipendenze incrociate

- Richiede il **workflow engine** (modulo 02) per l'automazione delle richieste e il
  **canale SMS** (modulo 03) per l'invio.
- Nel modello SaaS (modulo 06): OAuth GBP **per tenant** (ogni cliente collega il
  proprio profilo).

## Deliverable e ordine

1. Presentare domanda di accesso GBP API (giorno 1 — lead time lungo).
2. DocType + OAuth flow + sync recensioni.
3. Dashboard recensioni nella SPA.
4. Review request manuale, poi come azione di workflow.
5. Risposta dalla dashboard.
