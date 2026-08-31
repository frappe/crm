# Provisioning tenant + snapshot (modulo 06-lite)

Strumenti interni per creare in minuti il site di un nuovo cliente, già
preconfigurato — l'equivalente dello "snapshot" di GoHighLevel. Vedi
[docs/progetto-ghl/06-white-label-saas.md](../../docs/progetto-ghl/06-white-label-saas.md).

## Setup una tantum del bench

```bash
bench config dns_multitenant on
# DNS: *.tuobrand.com → IP del server; certificato wildcard (Let's Encrypt DNS-01)
```

## 1. Preparare il golden site

Un site normale (es. `golden.internal`) configurato a mano una volta sola:
pipeline e status, template email, **automazioni** (CRM Automation), calendari
di **booking**, layout campi, ruoli. Niente dati reali di clienti.

## 2. Creare lo snapshot

```bash
./apps/crm/scripts/provisioning/make_golden_snapshot.sh golden.internal ./snapshots
```

Produce `./snapshots/golden-latest.sql.gz` (+ archivi file se presenti).
Rilanciarlo dopo ogni modifica al golden site.

## 3. Provisioning di un nuovo cliente

```bash
export ADMIN_PASSWORD='...'
export MYSQL_ROOT_PASSWORD='...'
./apps/crm/scripts/provisioning/provision_tenant.sh cliente1.tuobrand.com \
    ./snapshots/golden-latest.sql.gz www.cliente1.it   # dominio custom opzionale
```

Lo script: crea il site, ripristina lo snapshot, reimposta la password admin,
migra, aggiunge il dominio custom e abilita lo scheduler.

## Post-provisioning (manuale, per cliente)

- `CRM Twilio Settings`: credenziali e numeri del cliente
- Email Account (SMTP/IMAP) + SPF/DKIM/DMARC sul dominio del cliente
- WhatsApp Settings (app frappe_whatsapp) se usato
- Logo/branding

## Note

- Tutti i site di un bench condividono le versioni delle app: `bench update`
  aggiorna tutti i tenant insieme.
- Backup: `bench --site all backup --with-files` in cron è il minimo sindacale.
- Signup pubblico, billing e rebilling sono fuori scope per decisione del
  31/08/2026 (gestione manuale dei clienti).
