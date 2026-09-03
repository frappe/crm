# 13 — Google Calendar, connesso in un click

> ✅ **IMPLEMENTATO (03/09/2026)**. Stesso schema del Meta: un solo progetto
> Google Cloud dell'agenzia, il cliente preme un bottone e autorizza. Nessun
> Client ID da incollare, nessun progetto da creare per cliente.

## Come funziona

Google, come Meta, pretende che il redirect URI combaci **esattamente** e non
ammette wildcard: stesso problema, stessa soluzione. Il redirect punta all'hub,
che rilancia il code al site del cliente con lo state firmato; il site scambia
il code e salva il refresh token.

```
cliente.it → Settings → Google Calendar → "Connetti"
           → schermata Google (scelta account + consenso)
           → Google redirige all'HUB
HUB        → verifica la firma, rilancia il code a cliente.it
cliente.it → scambia il code → refresh token salvato sul suo Google Calendar
```

Il token finisce nel doctype **`Google Calendar` del framework**, quindi la
sincronizzazione degli appuntamenti e il controllo "quando sono occupato" del
booking continuano a funzionare senza modifiche. `Google Settings` viene
compilato da solo con le credenziali del bench: senza, il framework non
riuscirebbe a rinnovare il token.

Il codice chiede `access_type=offline` **e** `prompt=consent`: senza entrambi
Google non restituisce il refresh token alla seconda autorizzazione, e il
collegamento morirebbe alla prima scadenza.

## Configurazione (una volta sola)

`common_site_config.json`, accanto alle chiavi Meta:

```json
{
  "google_client_id": "....apps.googleusercontent.com",
  "google_client_secret": "..."
}
```

`meta_hub_url` e `meta_relay_secret` sono riusati: **un hub solo per tutto**.

Su console.cloud.google.com, una volta:
1. Progetto + **API Google Calendar** abilitata.
2. **Schermata consenso OAuth**: tipo *Esterno*, nome e logo dell'agenzia
   (li vede il cliente), email di supporto, dominio autorizzato.
3. **Credenziali → ID client OAuth → Applicazione web**, con un solo
   *URI di reindirizzamento autorizzato*:
   `https://<hub>/api/method/crm.integrations.google.oauth.callback`

## La verifica Google (più leggera di Meta)

Lo scope Calendar è **sensibile**, non *restricted*: serve la verifica OAuth
ma **non** il security assessment CASA (quello vale per Gmail e Drive). Servono
nome/logo coerenti con la schermata di consenso, la proprietà del dominio
verificata in Search Console e un video dimostrativo del flusso. Tempi
dichiarati: circa 10 giorni dalla domanda completa.

⚠️ **Prima della verifica** l'app mostra la schermata "app non verificata" ed è
limitata a **100 utenti per la vita del progetto**. E soprattutto: in modalità
*Testing* Google **invalida i refresh token dopo 7 giorni** — il calendario si
scollegherebbe ogni settimana. Quindi il progetto va messo in **Produzione**
(anche non ancora verificato) prima di darlo ai clienti.

## Dove si connette

Settings → **Booking → Google Calendar**, non sotto Meta: è una connessione
**per utente**, non per sito — ogni commerciale collega il proprio calendario.
Per questo la voce è visibile a tutti, non solo ai manager, e il banner nelle
impostazioni del Booking porta allo stesso flusso.
