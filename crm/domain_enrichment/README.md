# Domain Enrichment

Auto-enrich a CRM Lead, Deal or Organization from its **website** — no paid data
providers. Given a domain, the engine crawls the public site, runs **admin-tunable,
rule-based** extractors (company name, description, logo, industry,
emails, phones, social links), records everything with full provenance, and fills
the mapped CRM fields according to configurable write policies.

The guiding principle: **config is data, the engine is code.** Everything a
sales-ops admin would tune — keywords, social patterns,
field mappings, crawl limits, enabled sources, the SSRF allow/block lists — lives
in **doctypes you edit in the desk**, never in Python. The engine knows no keywords
itself; it loads rules and executes them.

---

## What & why

- **Domain-based.** The only input is a website URL. No API keys, no per-record
  cost, no third-party enrichment vendor.
- **Rule-based / public-data.** Industry and social profiles
  are all matched by **rules an admin owns** (`CRM Enrichment Rule`).
  The mechanics (crawling, HTML parsing, the favicon scorer, JSON-LD parsing,
  readability diagnosis, email/phone regexes) are pure code because they are
  algorithms, not tunable knowledge.
- **Provenance preserved.** Every extracted value records `{value, source, method}`
  — which page it came from and how it was found — so a reviewer can judge how much
  to trust it. The full provenance JSON is stored on each run.
- **Self-contained.** The only outbound traffic is fetching the target site itself —
  no third-party APIs.
- **Framework-native.** Outbound HTTP uses `frappe.utils.get_request_session`;
  background work uses `frappe.enqueue`; progress streams over
  `frappe.publish_realtime`.

---

## Architecture

```
DESK ADMIN (data)                         ENGINE (code, rule-agnostic)        RESULT (data)
 CRM Enrichment Settings (Single) ─┐       crm/domain_enrichment/
 CRM Enrichment Rule (+Pattern) ───┼─►get_config()──► config.py              CRM Enrichment Run
 CRM Enrichment Field Mapping ─────┘      http.py (session+SSRF+cap)           (Dynamic Link to
                                          crawler.py (BFS; caps from cfg)       Lead/Deal/Org)
        │                                 extractors.py (rule executors)              ▲
        ▼                                 pipeline.py → EnrichmentResult              │
   bench migrate syncs                    api.py (@whitelist) / tasks.py        mapper.py writes
   native fields onto                     (enqueue + realtime)                  mapped fields onto
   Lead/Deal/Organization                                                      the record (policy)
```

### Module map (`crm/domain_enrichment/`)

| File | Responsibility |
|---|---|
| `config.py` | `get_config()` → `EnrichmentConfig` (settings + `Rule`/`Mapping` objects), built on demand (not cached). `get_settings()` / `auto_enrich_enabled_for()` are the cheap Settings-only reads for hot paths. |
| `http.py` | `fetch(url, cfg)` on the framework session; the **SSRF guard** (`validate_url`); byte cap; HTML-only filter; never-raise `(status, html, error, final_url)` contract. |
| `crawler.py` | Same-domain, depth-limited BFS. Caps / link-priority order / skip patterns from config. |
| `extractors.py` | **Generic rule executor** (`apply_keyword_rules`) + the pure mechanics. No literal keyword tables. |
| `result.py` | `EnrichmentResult` and its `{value, source, method}` provenance schema. Pure dataclasses, no framework import. |
| `pipeline.py` | `run(website, cfg, progress)` orchestrates crawl → extract → assemble `EnrichmentResult`. Never writes to the DB. |
| `mapper.py` | `apply_to_document(doc, result, cfg)` — the **single** result→CRM-field authority, driven by Field Mapping records + write policies. |
| `tasks.py` | `run_enrichment` (enqueued worker) + `write_run` (the **single** run-history writer). Streams realtime progress; never raises. |
| `api.py` | Whitelisted `enrich` (enqueue) + `enrich_preview` (bounded sync prefill). Type-annotated; permission- and rate-limited. |
| `cross_record.py` | `copy_enrichment_from_organization` — the one link-time Org→Lead/Deal copy. |
| `install.py` | Idempotent seeder: translates the original constant tables into Rule + Field Mapping records. |

---

## Configuration guide

Three doctypes hold all the tunable knowledge. `get_config()` reads them on demand
(no cache), so an edit takes effect on the very next enrichment without a restart.

### 1. CRM Enrichment Settings (Single)

| Field | Meaning |
|---|---|
| `enabled` | Master on/off for the whole feature. |
| `enable_lead` / `enable_deal` / `enable_organization` | Which doctypes can be enriched. |
| `auto_enrich` | When `1`, a newly-created CRM **Lead, Deal or Organization** that has a website is enriched automatically in a background job (`after_insert`). A new Deal with a new Organization enriches both (each crawls and writes its own fields). Default `0` — enrichment is otherwise manual via the Enrich button. Gated per doctype by `enable_lead` / `enable_deal` / `enable_organization`. |
| `max_pages` / `max_depth` | Crawl breadth/depth caps (BFS). |
| `request_timeout` | Per-request timeout (seconds). |
| `max_download_bytes` | Hard cap on bytes read per page (streamed). |
| `retry_count` | Transient-error retries on the session. |
| `user_agent` | Crawler User-Agent header. |
| `preview_max_pages` / `preview_timeout` | Bounds for the fast `enrich_preview` (create-modal) path. |
| `allowed_domains` / `blocked_domains` (child) | SSRF allow/block lists (subdomain-aware). A blocked host is always rejected; if an allow list exists, only listed hosts pass. |
| `link_priority_order` (child) | `keyword` + `weight`: a crawl-ordering hint — links whose URL/anchor contain these are fetched first (higher weight = sooner). Defaults are seeded on install. |
| `skip_patterns` (child) | URL substrings/regexes to never crawl. |

If the Single has never been saved, the engine falls back to sane defaults
(`config.DEFAULT_SETTINGS`).

### 2. CRM Enrichment Rule (+ CRM Enrichment Rule Pattern)

The heart of the knowledge base. One record = one rule.

| Field | Meaning |
|---|---|
| `rule_name` | Unique name (the record's id). |
| `rule_type` | `Industry` / `Social`. |
| `enabled` | Disabled rules are skipped by the config builder. |
| `target_value` | The label a match emits (tech name, network). Ignored for `Industry`. |
| `industry` | (Industry rules only) the linked `CRM Industry` a match classifies to. |
| `weight` | Multiplier on the hit count (industry scoring). |
| `match_scope` | `Headline` / `Full Text` / `HTML` / `Headers` / `URL` — which slice of the page the rule matches. |
| `patterns` (child) | One or more `pattern` strings; `is_regex` toggles substring vs. regex. Substrings are matched case-insensitively. |

### 3. CRM Enrichment Field Mapping

The single source of result→field truth. One record = one field written.

| Field | Meaning |
|---|---|
| `enabled` | Disabled mappings are skipped. |
| `source_key` | One of the 13 frozen result keys (below). |
| `target_doctype` | `CRM Lead` / `CRM Deal` / `CRM Organization`. |
| `target_fieldname` | The field on that doctype to fill (validated to exist). |
| `write_policy` | `Fill if empty` / `Always refresh` / `Override defaults` (below). |
| `default_values` | (Override defaults) newline-separated values treated as "unset". |
| `create_missing_link` | (Link fields) auto-create the linked master if missing (e.g. a new `CRM Industry`). |

**The 13 `source_key`s:** `company_name`, `description`, `logo`, `industry`,
`primary_email`, `primary_phone`, `secondary_phone`, `linkedin`,
`twitter`, `github`, `facebook`, `instagram`, `youtube`.

**Write policies:**
- **Fill if empty** — write only when the target field is currently empty.
- **Always refresh** — overwrite (or clear) with the fresh value, even if the field
  had a previous value. Used for fully engine-derived fields that should always
  reflect the latest crawl.
- **Override defaults** — treat the listed `default_values` (plus empty) as "unset"
  and fill over them, but respect any real user value. Useful for a field that ships
  with a meaningless placeholder default that enrichment should replace.

### Worked examples

**Add a new industry.** Create a `CRM Industry` (or let `create_missing_link` do it),
then a `CRM Enrichment Rule`: `rule_type = Industry`, `industry = <your industry>`,
`match_scope = Headline`, and add patterns (e.g. `biotech`, `genomics`). Save — the
classifier picks it up on the next run.

**Add a social network.** New `CRM Enrichment Rule`: `rule_type = Social`,
`target_value = "mastodon"`, `match_scope = HTML`, and a regex pattern
(`is_regex = 1`) such as `@[A-Za-z0-9_]+@mastodon\.social`.

**Remap a result field / change a write policy.** Edit the relevant
`CRM Enrichment Field Mapping` — change `target_fieldname`, or flip `write_policy`
from `Fill if empty` to `Always refresh`. To stop a field being written, untick
`enabled` on its mapping.

**Tune crawl limits / SSRF.** Raise `max_pages`/`max_depth` for deeper crawls; add a
`skip_patterns` row (e.g. `/blog/`) to skip noisy sections; add a `blocked_domains`
row to hard-block a host, or `allowed_domains` rows to restrict crawling to an
allow-list only.

---

## How a run works (end to end)

1. **Trigger** — the SPA `EnrichFromWebsite` button (or the desk form button) calls
   the whitelisted `api.enrich(reference_doctype, reference_name)`.
2. **Validate + enqueue** — `enrich` checks the doctype is enabled, the user has
   `write` permission, and the record has a `website`, then `frappe.enqueue`s
   `tasks.run_enrichment` on the `long` queue with a per-doc `job_id` and
   `deduplicate=True` (a second click while one is in-flight is a no-op).
3. **Crawl** — `pipeline.run` builds the session, runs the BFS crawler (SSRF-guarded
   `http.fetch` per page), and emits progress callbacks.
4. **Rule execution** — the extractors run the config rules: industry classification,
   social profiles, plus the mechanics (company info, emails, phones).
5. **Map** — `mapper.apply_to_document` writes the mapped fields onto the origin doc
   per each mapping's write policy; the doc is saved (normal, permission-respecting).
6. **Run record** — `tasks.write_run` persists exactly one `CRM Enrichment Run` with
   the summary fields + full `raw_json` provenance.
7. **Realtime** — progress and the terminal result stream to the triggering user over
   the `domain_enrichment_progress` event.

Progress event payload (mirrors `crm/api/whatsapp.py`):

```json
{"reference_doctype": "...", "reference_name": "...", "step": 3, "total": 9,
 "message": "...", "status": "running|completed|error", "payload": {}}
```

The terminal `completed` event's `payload` carries `{filled_fields, notes, **result.flat()}`.

### Run lifecycle (state machine)

```
        enqueue (dedupe)      worker start          all steps ok
 [Queued] ───────────► [Running] ─────────────────────────────► [Completed]
                           │
                           │  exception / blocked / unreachable
                           ▼
                       [Failed]   (reason in notes; frappe.log_error)
```

`tasks.run_enrichment` never raises to the worker: on any exception the Run is
written as `Failed` (with the traceback truncated into `notes`), the error is logged
via `frappe.log_error`, and an `error` event is published.

---

## Cross-record behavior

There is exactly **one** cross-record copy:
`cross_record.copy_enrichment_from_organization(target_doc)`. When a **Lead** or
**Deal** links an already-enriched **Organization**, the Organization's stored
enriched fields are copied onto the **empty** fields of the Lead/Deal
(fill-empty semantics, even for mappings normally configured "Always refresh"), so
user-entered data is never touched.

- **Lead seam:** `CRMLead.create_organization` (existing-org branch).
- **Deal seam:** `CRMDeal.validate` when `organization` is set/changed.
- An Organization is "enriched" if it has a **completed** `CRM Enrichment Run`, or
  (fallback) any populated native enriched field.

**No background fan-out.** The copy is synchronous, in-request, Organization →
Lead/Deal only. There is no job, no propagation to other linked records, and no
write back to the Organization. The field-writing reuses `mapper.apply_to_document`
(the single authority) — no second copy implementation exists.

---

## SSRF Guard

- **SSRF guard (`http.validate_url`).** Mandatory and not provided by the framework.
  It rejects non-`http(s)` schemes, resolves the hostname, and rejects any URL that
  resolves to a loopback / private / link-local / reserved / multicast / unspecified
  address — including the cloud-metadata endpoint `169.254.169.254`. It honors the
  `blocked_domains` / `allowed_domains` lists and **re-validates after every
  redirect** (redirects are followed manually). The private-network rejection is
  **unconditional** — there is deliberately no setting to disable it (a crawler that
  fetches user-supplied URLs must never be turnable into an internal-network probe).
- **DNS-rebinding TOCTOU — closed by IP pinning.** The guard validates the resolved
  addresses and the connection is then made to one of those exact addresses
  (`http._pinned_get`): the URL netloc is rewritten to the validated IP while the
  Host header, TLS SNI and certificate verification stay on the original hostname
  (urllib3 `server_hostname`). A host that alternates DNS answers (short TTL) can no
  longer pass validation with a public IP and serve the request from a private one.
  Each redirect hop is re-validated and re-pinned.
- **Permissions.** `api.enrich` enforces the Settings allow-list and
  `doc.check_permission("write")` — a user who cannot edit the record cannot enrich
  it. The worker save is a normal permission-respecting save. `create_missing_link`
  auto-creation is permission-respecting too: `_ensure_link_target` only creates a
  master (`CRM Industry`) when the enriching user has create rights on it, so a
  scraped value can never escalate into an insert the user couldn't do by hand. The
  only `ignore_permissions` write is the engine-owned `CRM Enrichment Run` audit log
  — never a cross-record write to data the user can't edit.
- **Rate limiting.** Every entry point that triggers a fetch — `enrich`, `retry`,
  and `enrich_preview` — is decorated with `rate_limit(limit=ENRICH_RATE_LIMIT,
  seconds=60)` (per user, per route). `enrich`/`retry` only enqueue a per-doc-
  deduplicated job; `enrich_preview` does one synchronous crawl.

---

## Extending in code

- **Add an extractor mechanic** (e.g. a new heuristic): add a pure function to
  `extractors.py`, call it from `pipeline.run`, and surface its output on
  `EnrichmentResult` (`result.py`). Keep tunable knowledge in rules, not constants.
- **Add a new `rule_type`:** add the option to the `CRM Enrichment Rule` Select, add
  a generic executor (or reuse `apply_keyword_rules`) in
  `extractors.py`, and wire it into `pipeline.run` via `cfg.rules("<Type>")`. Keep the
  rule vocabulary small (substring/regex + scope + weight) — do **not** grow a DSL.
- **Add a new `source_key`:** extend `mapper.get_value_for_source_key`, add the option
  to the Field Mapping Select, and (if it needs new data) populate it on
  `EnrichmentResult`.

---

## Limitations & future

- **JS-rendered sites.** Enrichment reads server-delivered HTML only (`requests` +
  BeautifulSoup), so a fully client-rendered site yields only `<head>` metadata; the
  run records the "main content is JavaScript-rendered" note (`READABILITY_MESSAGES["empty"]`)
  and fields may be blank. A headless-Chromium render fallback was prototyped but
  **intentionally removed** — the per-worker Chromium memory footprint isn't worth it
  for a fallback. (The implementation is preserved locally in the gitignored
  `CHROMIUM_FALLBACK.local.md` if it ever needs to be reintroduced.)
- **Logo vs image.** The `logo` is the company's **link icon** (`extract_logo`): the
  best declared `<link rel=icon>` — scalable SVG > largest raster / apple-touch — with
  `/favicon.ico` as the fallback. It's the crisp, square brand mark suited to an avatar.
  The larger social/brand image (`extract_image`: JSON-LD `Organization.logo` →
  `og:image`/`twitter:image`) is captured separately as `image` in the run JSON — it is
  **not** used as the logo (`og:image` is usually a wide banner) and isn't mapped to a
  record field by default.
- **Scheduled re-enrichment — _future feature, not implemented._** Triggering is
  either manual (Enrich button) or automatic on Lead/Deal/Organization creation (`auto_enrich`);
  there is no *scheduled* re-enrichment of existing records. A future version could enqueue periodic re-enrichment of
  stale records (e.g. via a scheduled job that re-runs `tasks.run_enrichment` for
  records whose last `CRM Enrichment Run` is older than N days).
- **TLS fingerprinting.** The fetcher uses `requests`, so its TLS ClientHello
  fingerprints (JA3/JA4) as a non-browser client. Bot walls that fingerprint TLS
  (Cloudflare, Akamai, DataDome) can still block it even though `http.build_session`
  sends browser-like headers. Real evasion needs a TLS-impersonating client
  (`curl_cffi`) or a headless browser — deliberately out of scope here.

---

## Tests

Framework-native tests live in `crm/domain_enrichment/tests/` and are discoverable by
`bench run-tests --app crm`:

- **Pure unit (`frappe.tests.UnitTestCase`, no DB, offline fixtures):**
  `test_crawler.py`, `test_extractors.py`, `test_pipeline.py`, `test_ssrf.py`. The
  rule executors are exercised with in-memory `Rule` objects (`tests/fixtures.py`);
  the SSRF guard mocks `socket.getaddrinfo` so DNS is deterministic and offline.
- **Integration (`frappe.tests.IntegrationTestCase`, real test DB):**
  `test_integration.py` — seeder idempotency, mapper write-policies, the Run writer,
  API permission/allow-list enforcement, and the link-time Org→Lead/Deal copy. The
  crawl is monkeypatched to a canned `EnrichmentResult`, so the suite is network-free.

```bash
bench --site <site> run-tests --app crm --module crm.domain_enrichment.tests.test_extractors
bench --site <site> run-tests --app crm --module crm.domain_enrichment.tests.test_integration
```
