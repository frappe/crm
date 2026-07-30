# cr-dev.tiberbu.app — Performance Root-Cause Investigation

**Date:** 2026-07-30 · **Investigator:** perf review · **Site:** cr-dev.tiberbu.app
**Symptom reported:** login / page loads take >40 s on cr-dev; other sites on the same VM are fine.

---

## TL;DR

The **origin server is not the bottleneck.** Every layer measurable from the VM —
nginx, gunicorn, MariaDB, Redis, egress, the `crm` app hooks, and the authenticated
CRM API — responds in **tens of milliseconds** for cr-dev, using the **exact same web
tier and database** as the healthy sites. The VM is near-idle (load 0.42 on 16 cores,
50 GB RAM free).

The slowness is therefore on a path the server cannot self-measure: the
**client → Cloudflare edge → first-load of a heavy SPA + a socket.io reconnect loop.**
cr-dev is the *only* site that ships a large single-page app and opens a realtime socket,
which is why it alone is affected.

---

## Evidence (all collected 2026-07-30)

### Environment — healthy, not capacity-bound
| Metric | Value |
|---|---|
| Load average | 0.42 / 0.43 / 0.42 on **16 cores** |
| Memory | 61 GB total, **50 GB available** |
| Disk | 15 % used |
| Swap | 0 B used |
| OOM / kernel kills | none in 45 days |
| MariaDB restarts | none |

### Routing — cr-dev shares the healthy tier
- nginx (`/home/ubuntu/frappe-bench/config/nginx.conf`) proxies **all** sites —
  `desk`, `cr-dev`, `devsecops`, `afyangu` — to the same upstream
  `frappe-bench-frappe → 127.0.0.1:8000`.
- That upstream is **gunicorn with 9 sync workers** (`-w 9 -t 120`), shared by every site.
- `default_site = cr-dev.tiberbu.app` + `serve_default_site: true`, so unmatched-Host /
  bare-IP / bot traffic lands on cr-dev. Volume seen is low; not currently a factor.

### Origin latency — fast (measured over real HTTPS through Cloudflare)
| Request | Latency |
|---|---|
| `/api/method/ping` | 2–44 ms |
| `/login` page | 37–65 ms |
| `/crm` shell | 94 ms |
| bad-cred `POST /api/method/login` | 65 ms |
| **30× sampled `/login`** | min 37 ms / p50 47 ms / **max 61 ms** — no spikes |
| **20 concurrent `/login`** | p90 73 ms — **no worker-pool starvation** |
| Authenticated CRM endpoints (real API key): `get_list_data`, `get_views`, `get_form_script`, `get_data`, `get_notifications` | all **< 100 ms** on warm cache |

### Database — trivial
- `_cr_dev`: 48 MB, 779 tables, **12 CRM Leads / 7 CRM Deals**.
- Slow-query log OFF; processlist idle; 1 connection; `max_connections=151`.
- Custom permission hooks (`crm.permissions.org_hierarchy`) return `""` (no-op) for
  Administrator / System Manager and are trivially cheap at this data scale.

### App code — no blocking call in the hot path
- `crm/api/route_guard.py` `before_request` hooks: two string comparisons, early-exit
  for non-desk paths. Negligible.
- `crm/www/crm.py get_boot()`: `is_fc_site()` is **local** (no network);
  `capture()` telemetry **early-returns** because `enable_telemetry = 0` on cr-dev.
- `domain_enrichment` runs **async** (`frappe.enqueue`, `enqueue_after_commit`) — not inline.
- Outbound `requests.get` calls (exchange-rate, call-recording proxy) are bounded
  (timeout 5–30 s) and only fire on **specific user actions**, never on page load.

### The cr-dev-only anomaly — realtime socket
- nginx access log shows cr-dev emitting a continuous stream of
  `GET/POST /socket.io/?EIO=4&transport=polling` from `/crm/leads/view/list`, each with a
  **new session id**, ~3 % ending in **499** (client disconnected).
- desk/devsecops show **almost no** socket.io traffic (they are not realtime SPAs).
- socket.io handshake itself succeeds and advertises a websocket upgrade, but the
  repeating fresh-sid pattern indicates the connection is **not stabilising** —
  consistent with the websocket **upgrade being blocked/reset at the Cloudflare edge**
  while long-polling limps along.

### SPA payload — heavy, cr-dev-only
| Asset (eager, first load) | Raw | Gzip/wire |
|---|---|---|
| `useActiveTabManager-*.js` | **6.18 MB** | — |
| `index-*.js` | 2.67 MB | **732 KB** |
| `index-*.css` | — | 446 KB |
| Total `frontend/` | **18 MB** | — |

On a cold cache over a constrained client link this is a first-paint cost desk simply
does not have.

### Comparison caveat
`/etc/hosts` on the VM contains `127.0.0.1 desk.tiberbu.app`, so **from this box** desk
bypasses Cloudflare and hits nginx directly, while cr-dev goes through Cloudflare.
Publicly, all sites resolve to the same Cloudflare IPs (104.26.x / 172.67.68.120), so end
users hit the same edge — but the "desk is fine" observation from the VM is not a clean
comparison.

---

## Additional proof added after deeper testing (2026-07-30, round 2)

- **Websocket upgrade works BOTH direct and through Cloudflare** — a raw socket.io v4
  handshake returned `HTTP/1.1 101 Switching Protocols` on `127.0.0.1:443` (origin) AND on
  the Cloudflare edge IP. **Cloudflare is NOT blocking realtime.** (Earlier suspicion #1
  is disproven.)
- **Real login transaction timed phase-by-phase on cr-dev:** LoginManager 92 ms,
  `_get_unseen_notes` 9 ms, `login_feed` 128 ms, **`get_bootinfo` 746 ms** → total well
  under 1 s. Compared across sites, cr-dev `get_bootinfo` = **611 ms**, desk = **2401 ms**,
  devsecops = **961 ms** — cr-dev is the **fastest** of the three.
- **Real end-user (Sales User `sales.tester@tiberbu.test`, perm conditions ACTIVE):**
  `permission_query_conditions` 0.1 ms, `_in_hierarchy` 11 ms, perm-scoped
  `get_list CRM Lead/Deal` 3–4 ms, `get_bootinfo` 740 ms. (Administrator bypasses the
  custom perm hooks; this run exercises them — still fast.)
- **2FA is OFF on cr-dev** (`enable_two_factor_auth = 0`) — same as the healthy sites; not
  a factor. No outgoing Email Account is configured on any site; login sends no mail.
- **Assets cache correctly at Cloudflare** (`cf-cache-status: MISS`→`HIT`), compress from
  6.2 MB raw to ~594 KB on the wire, and nginx sets `max-age=31536000`. No hardcoded
  dev/localhost URL in the production bundle. `window.site_name` and `socketio_port` are
  injected correctly.
- **Eager first-load is ~1.2 MB gzipped** (index.js 732 KB + index.css 446 KB). The 6.1 MB
  `useActiveTabManager` and 1.2 MB `Dashboard` chunks are **lazy** route chunks, not first
  paint. So even the bundle-weight theory does not explain a 40 s stall on a normal link.

**Net:** the origin is fast at every server-measurable layer for both Administrator and a
real Sales User. The 40 s is not reproducible from the VM.

## Root cause (ranked)

**The origin is exonerated.** Every server-side path (routing, DB, gunicorn, login
transaction, boot, permission hooks, realtime handshake, asset delivery) is fast for both
Administrator and a real Sales User, and Cloudflare passes websockets and caches assets.
The 40 s therefore originates **client-side / in-transit** and cannot be reproduced from
the VM. Most-likely remaining causes, in order — each verifiable only with a real browser
session:

1. **The specific client's network path to Cloudflare** (a bad CF PoP, ISP routing, or
   local network). `cf-ray` shows the `CDG` (Paris) PoP from the VM; the affected user may
   hit a degraded PoP. A 40 s that reproduces for one user/location but not from the server
   points here.
2. **Browser-side stall** — a specific extension, a corrupt service-worker
   (`registerSW.js` / PWA) cached in that browser, or a device on a slow link doing the
   cold 1.2 MB (gzipped) first paint + lazy chunk fetches. A stale service worker in
   particular can make an SPA appear to hang for tens of seconds.
3. **An intermittent origin event not present during testing** — e.g. a gunicorn sync
   worker briefly tied up by a slow outbound `requests.get` (call-recording proxy,
   timeout 30 s) or a burst that momentarily exhausts the 9-worker pool. Low probability
   given the idle VM, but it is the only origin path that could spike transiently.

---

## Fix / next actions

### A. Confirm it's the edge/client (5 min, do this first)
- Open cr-dev in the browser with **DevTools → Network** and **sort by Time**. The 40 s
  will be on a `socket.io` request or a large `.js`/`.css` asset — not on `/api/method/*`.
- In Cloudflare dashboard for `tiberbu.app`: enable **WebSockets** (Network tab) and, if on
  a plan that supports it, verify no rule is stripping the `Upgrade` header for
  `/socket.io/*`. Frappe realtime **requires** websockets end-to-end.
- Temporarily test cr-dev **grey-cloud** (DNS-only, bypass Cloudflare) or add a
  `hosts`-file entry to the VM IP `35.181.234.75` and re-measure. If it's fast direct, the
  edge is confirmed as the cause.

### B. Fix the socket path
- Ensure nginx forwards the upgrade for cr-dev (the `location /socket.io` block already
  sets `Upgrade`/`Connection` — verify Cloudflare isn't the blocker).
- Confirm `socketio_port: 9000` is reachable through the full public path (Cloudflare
  proxies `/socket.io/` over 443 to nginx → node `:9000`; port 9000 must **not** be exposed
  directly to the client).

### C. Trim first-load weight (frontend)
- The 6.1 MB `useActiveTabManager` chunk is oversized. Re-check the Vite chunking
  (`frontend/vite.config.js` was recently edited to drop source maps and `manualChunks` —
  good) and lazy-load ProseMirror/editor and dashboard code so they are not in the eager
  entry.

### D. Housekeeping (unrelated to the 40 s, but found during review)
- **Stray dev server:** `bench serve --port 8005` (PID chain parented by a Claude Code
  session) is running and burning ~8 % CPU idle. It is **not** in the request path
  (nginx → :8000). Kill it: `kill <pid>`.
- **43 leaked `frappe-mcp-server` processes** from `claude-code-studio-v2` accumulating
  since Jul 1. Clean them up to reclaim RAM.

### E. Enable capture so the next real 40 s is recorded
- Add request timing to nginx `log_format main` (append
  `rt=$request_time uct=$upstream_connect_time urt=$upstream_response_time`). If `urt`
  stays small during a 40 s user stall, the origin is exonerated definitively and the edge
  is proven.
- Optionally enable MariaDB slow-query log (`long_query_time=2`) to rule in/out DB tails.

---

## What was ruled OUT (do not re-investigate)
VM capacity · gunicorn worker count / starvation · MariaDB size or slow queries · Redis
queue backlog · `crm` `before_request` hooks · `route_guard` · `org_hierarchy` permission
queries · telemetry/frappecloud phone-home · outbound egress/DNS from the VM ·
`domain_enrichment` (async).
