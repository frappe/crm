# Frappe CRM — Product Overview

## What Is Frappe CRM?

Frappe CRM is a simple, open-source Customer Relationship Management tool built for modern sales teams. It is designed to be affordable, unlimited in users, and highly customizable — without the complexity or steep pricing of mainstream CRM products. Built on the [Frappe Framework](https://github.com/frappe/frappe), it prioritizes a clean user experience while remaining deeply extensible.

> **Live Demo:** [frappecrm-demo.frappe.cloud](https://frappecrm-demo.frappe.cloud/api/method/crm.api.live_demo.login)  
> **Website:** [frappe.io/crm](https://frappe.io/crm)  
> **Documentation:** [docs.frappe.io/crm](https://docs.frappe.io/crm)

---

## Core Features

### Lead & Deal Management
- Unified Lead/Deal page consolidating activities, comments, notes, tasks, emails, calls, and attachments into a single view.
- Full lifecycle tracking from lead capture through to closed deal.

### Kanban View
- Drag-and-drop Kanban board for leads and deals.
- Visual pipeline management across custom stages.

### Custom Views
- Personalized list views with custom filters, column selection, and sorting.
- Saved views per user or team.

### Activity Timeline
- Chronological log of all interactions: emails sent, calls made, notes added, tasks completed.

### Email Integration
- Send and receive emails directly from a lead or deal page.
- Email templates for consistent, repeatable outreach.

### Call Integration
- **Twilio** (built-in): Make and receive calls; optional call recording.
- **Exotel** (built-in): Route calls through agents' mobile phones; optional call recording.
- Call log automatically linked to the relevant lead or deal.

### WhatsApp Integration
- Send and receive WhatsApp messages via [Frappe WhatsApp](https://github.com/shridarpatil/frappe_whatsapp).

### ERPNext Integration
- Extend CRM data into invoicing, accounting, and operations via [ERPNext](https://erpnext.com).

### Form Scripting
- Write JavaScript classes per DocType (`CRMLead`, `CRMDeal`, `Contact`, `CRMOrganization`) to customize form behaviour without modifying source code.
- Lifecycle hooks: `onLoad`, `onRender`, `onValidate`, `onSave`, and more.
- Field change hooks, `setFieldProperty` API (hide, require, relabel fields), and `formDialog` for custom multi-step flows.
- Third-party apps can contribute scripts via `CRM Form Script` records — no core modification needed.

---

## Target Users

| Persona | Why Frappe CRM |
|---|---|
| **Small to mid-size sales teams** | Unlimited users, no per-seat pricing |
| **Teams on Frappe/ERPNext** | Native integration, shared user/permission model |
| **Technical teams needing customization** | Form scripting, open source, self-hostable |
| **Organizations with compliance requirements** | Self-hosted option, AGPL licensed |

---

## Hosting Options

### Managed (Frappe Cloud)
Get a production instance in minutes at [frappecloud.com/crm](https://frappecloud.com/crm/signup). Managed updates, backups, and monitoring included.

### Self-Hosted
Deploy on your own infrastructure using the one-command easy-install script:

```bash
python3 ./easy-install.py deploy \
    --project=crm_prod_setup \
    --email=your@email.com \
    --image=ghcr.io/frappe/crm \
    --version=stable \
    --app=crm \
    --sitename subdomain.domain.tld
```

### Docker (Development / Evaluation)
A `docker-compose.yml` is provided for quick local evaluation. See the [README](./README.md#docker) for setup steps.

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python, [Frappe Framework](https://github.com/frappe/frappe) |
| **Frontend** | Vue 3, [Frappe UI](https://github.com/frappe/frappe-ui) |
| **Database** | MariaDB (via Frappe) |
| **Realtime** | Socket.io |
| **Build** | Vite, Yarn |
| **Testing** | Vitest (frontend unit tests) |

---

## Release Branches & Compatibility

| Branch | Stability | Frappe | ERPNext |
|---|---|---|---|
| `main` (v1.x) | Stable | v15.x & v16.x | v15.x & v16.x |
| `develop` (future v2.x) | Unstable | develop / future v17 | develop / future v17 |

---

## Roadmap Highlights

The active development roadmap (tracked in [`.pi/PLAN.md`](./.pi/PLAN.md)) is focused on the following areas:

| Phase | Focus | Status |
|---|---|---|
| **Phase 3B** | Decouple Grid from FieldLayout — make form components independently composable | 🔜 Next |
| **Phase 4** | `getMeta` as single source of truth for field resolution and transforms | Planned |
| **Phase 6A** | Programmatic layout manipulation from form scripts (virtual fields, sections) | Planned |
| **Phase 6B** | Client-side permission level enforcement via `usePermLevel` composable | Planned |
| **Phase 5** | Scripting DX rethink — chainable/declarative API for form scripts | Last |

### Backlog
- List view scripting (column visibility, bulk action hooks, custom cell renderers)
- Inter-script event communication (`this.emit` / `this.on`)
- Conditional field injection from scripts

---

## Design Principles

1. **Generic-first** — No CRM-specific assumptions baked into the core layout or scripting engine. CRM behaviour lives in Form Script records.
2. **Extensibility via records** — Third-party apps extend via database records, not code patches.
3. **Incremental delivery** — Each development phase ships independently and is usable on its own.
4. **Test pure logic** — Business logic is extracted to utility files and covered by unit tests before being wired into components.
5. **Ask before deciding** — Major API or architecture decisions are documented with options and resolved with maintainers before implementation.

---

## Community & Support

| Channel | Link |
|---|---|
| Telegram Group | [t.me/frappecrm](https://t.me/frappecrm) |
| Discuss Forum | [discuss.frappe.io/c/frappe-crm](https://discuss.frappe.io/c/frappe-crm) |
| Documentation | [docs.frappe.io/crm](https://docs.frappe.io/crm) |
| YouTube | [@frappetech](https://www.youtube.com/@frappetech) |
| X / Twitter | [@frappetech](https://x.com/frappetech) |

---

## License

Frappe CRM is released under the [GNU Affero General Public License v3.0](./LICENSE).
