# Domain Enrichment — Extraction Context

The vocabulary for extracting the `domain_enrichment` feature out of Frappe CRM
into standalone, independently-installable app(s). This glossary is being built
during a design/grilling session; it records only terms whose meaning has been
deliberately fixed.

## Language

**Enrichment Engine** (a.k.a. "generic core"):
The reusable, CRM-agnostic part: HTTP fetch + SSRF guard, crawler, extractors,
mapper, pipeline, run history, and the config doctypes — targeting _any_ DocType,
with no hard dependency on Frappe CRM.
_Avoid_: "the module", "website intelligence", "enricher".

**CRM Adapter** (a.k.a. "glue"):
The CRM-specific integration on top of the Engine. It is NOT a separate app — it
stays inside the CRM repo, which takes on the adapter role: enrichment fields on
Lead/Deal/Org, the domain/website source field per doctype, the Organization→Lead/Deal
copy, seeded field mappings, triggers, and the CRM SPA/desk UI. CRM declares a
dependency on the Engine. (Decision: only ONE new app — the Engine — is created.)
_Avoid_: "the integration", "plugin", "the second app".

**Enrichment Target**:
An Engine config record `{target_doctype, url_fieldname, enabled, auto_enrich}` naming
a doctype the Engine may enrich and which field holds its domain. The Engine's generic
`doc_events['*'] after_insert` consults the cached set of these; adapters integrate by
seeding rows (data), not code. In CRM the adapter seeds Lead/Deal/Organization → `website`.
_Avoid_: "reference doctype" (reserved for a Run's origin), "enable flag" (the old
hardcoded `enable_lead/deal/org` Settings this replaces).

**Field Mapping**:
A data record saying "enrichment result key X → fieldname Y on doctype Z, under
write-policy P". The single source of result→field truth.

**Run**:
A history record of one enrichment execution against one origin document, holding
status, summary, and full provenance JSON.

## Deferred cleanups (from code review)

Known but intentionally out of scope for now — revisit later:

- **TLS fingerprinting (deferred to the engine extraction).** The fetcher uses
  `requests`, so the TLS ClientHello is standard OpenSSL and is trivially
  fingerprinted (JA3/JA4) as a non-browser client — bot walls (Cloudflare, Akamai,
  DataDome) that fingerprint TLS will still block it even though we now send
  browser-like headers (`http.build_session`). Real evasion needs a TLS-impersonating
  client (e.g. `curl_cffi`) or a headless browser, both of which carry weight the
  in-CRM feature deliberately avoids. Revisit when the engine is pulled into its own
  app, where a heavier optional fetch backend is a reasonable dependency to own.

- **Frontend `isExternalUrl` / `openExternalUrl` duplication.** These two helpers are
  byte-identical in `frontend/src/components/FieldLayout/Field.vue` and
  `frontend/src/components/SidePanelLayout.vue` (the POC, `bba9a77c`, added the second
  copy). Per `AGENTS.md` ("add tests in `tests/unit/` when adding pure logic to
  `src/utils/`") they should be extracted to `frontend/src/utils/externalUrl.js` with a
  unit test, and imported in both components. Deferred as a frontend-general cleanup,
  not part of the enrichment backend work.
