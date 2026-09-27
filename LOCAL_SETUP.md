# Local Setup — Frappe CRM (backend + frontend)

Run the whole stack on this Mac: Frappe/MariaDB/Redis in Docker, the Vue app
natively with hot reload.

Every step says what it does and how to tell it worked. Run them in order.

> ### ⚠️ Read this before running any `bench` command
>
> When `bench init` fails it asks **`Do you want to rollback these changes? [y/N]`**.
> That rollback is `shutil.rmtree()` on the whole bench directory. If your repo is
> bind-mounted inside the bench, the rollback **deletes your working tree** — it
> recurses straight through the mount.
>
> This guide avoids that by keeping the repo outside the bench until the bench
> exists (step 11). If a bench command ever offers a rollback, **answer `N`**.

---

## Part 0 — How the frontend and backend actually connect

Worth reading first, because the setup only makes sense once you know what talks
to what.

### The frontend is not served by Vite in production

`frontend/` is a standalone Vue 3 + Vite app that gets **compiled into the
Frappe app**. From `frontend/package.json`:

```
build: vite build --base=/assets/crm/frontend/ && yarn copy-html-entry
copy-html-entry: cp ../crm/public/frontend/index.html ../crm/www/crm.html
```

A build writes JS/CSS to `crm/public/frontend/` (served by Frappe at
`/assets/crm/frontend/`) and drops the HTML entry at `crm/www/crm.html`.
Anything in a Frappe app's `www/` folder becomes a route — that is why the app
lives at **`/crm`**.

`crm/www/crm.py` is that route's controller. Its `get_context()` calls
`get_boot()`, and the `jinjaBootData` Vite plugin has already injected a loop
into the built HTML that turns every boot key into a `window` global:

```html
<script>
  {% for key in boot %}
  window["{{ key }}"] = {{ boot[key] | tojson }};
  {% endfor %}
</script>
```

`get_boot()` returns `csrf_token`, `site_name`, `socketio_port`,
`frappe_version`, `sysdefaults`, `translated_messages`, timezone and more.

### In dev there is no Jinja, so boot is fetched over HTTP

`frontend/src/main.js` branches on `import.meta.env.DEV`:

```js
if (import.meta.env.DEV) {
  frappeRequest({ url: '/api/method/crm.www.crm.get_context_for_dev' })
    .then((values) => {
      for (let key in values) window[key] = values[key]
      socket = initSocket()
      app.mount('#app')
    })
}
```

Same payload, fetched instead of templated. **`get_context_for_dev` throws
unless `developer_mode` is on**, which is why step 10 sets it.

### Vite proxies API calls to Frappe

`vite.config.js` passes `frappeProxy: true` to the frappe-ui plugin
(`frontend/node_modules/frappe-ui/vite/frappeProxy.js`), which proxies

```
^/(desk|app|login|api|assets|files|private)   ->   http://<host>:8000
```

and picks the Vite port as `8080 + (webserver_port - 8000)` — so **8080**.

Two details that matter:

- The proxy's `router` rewrites the target from the **Host header**:
  `` `http://${req.headers.host.split(':')[0]}:8000` ``. Browse to
  `crm.test:8080` and it forwards to `crm.test:8000`, which is how Frappe picks
  the right site. Hence the hosts entry in step 3.
- It looks for `sites/common_site_config.json` by walking up for a directory
  containing both `sites/` and `apps/`. There is no bench on the host, so it
  logs `No common_site_config.json found, using default port 8000` and uses
  defaults. **That warning is expected and harmless.**

### Auth and realtime

Login posts to `/api/method/login`; Frappe sets `sid` and `user_id` cookies.
`frontend/src/stores/session.js` reads `user_id` off `document.cookie` to decide
if you are logged in. Writes need the CSRF token from boot.

`frontend/src/socket.js` builds the realtime URL from boot values:
`http://<hostname>:<window.socketio_port>/<window.site_name>` → port **9000**.

### The one non-obvious dependency: `@framework/ui`

`frontend/src/components/Settings/WorkflowAutomations/WorkflowFilters.vue:47`
imports `@framework/ui/components/ConditionBuilder`. That alias resolves to
`../../frappe/ui/src` relative to `frontend/` — i.e. **a sibling `frappe`
checkout**, mirroring how a bench puts `apps/frappe` next to `apps/crm`. The
`ui/` folder exists at the root of `frappe/frappe@develop`.

`frontend/node_modules/@framework/ui` is a symlink to
`/Users/keshavpareta/Documents/git/frappe/ui`. Until that exists the symlink
dangles and the frontend cannot build. Step 13 creates it.

### Summary

```
browser -> crm.test:8080 (Vite, host)           your .vue files, HMR
              |
              |  /api /assets /files /login /app  ->  crm.test:8000 (Frappe, Docker)
              |                                         apps/crm = this repo (bind mount)
              |                                         MariaDB + Redis (containers)
              |
              +-- ws://crm.test:9000/crm.test  (socket.io, Docker)
```

---

## Part 1 — What this machine has and lacks

| Need | Status |
|---|---|
| Docker | ✅ 29.8.0, daemon running |
| Node / yarn | ✅ v26.10.0 / 1.22.22 (`frontend` wants node ≥22.12) |
| Architecture | ✅ arm64 — `frappe/bench` and `mariadb:10.6` both publish native arm64 |
| Python | ❌ 3.9.6; `pyproject.toml` needs ≥3.10 → **backend cannot run natively** |
| bench / MariaDB / Redis | ❌ not installed → **must be Docker** |
| `crm.test` in `/etc/hosts` | ❌ missing → step 3 |
| sibling `frappe` checkout | ❌ missing → step 13 |
| `frappe-ui` submodule | ⚠️ uninitialised; Vite falls back to the npm package, so optional |

---

## Part 2 — Steps

### 1. Confirm Docker is up

```bash
docker info >/dev/null && echo "docker ok"
```

### 2. Go to the repo

```bash
cd /Users/keshavpareta/Documents/git/frappe-crm
```

### 3. Map `crm.test` to localhost

Frappe selects the site from the Host header, and both Playwright
(`playwright.config.ts` → `http://crm.test:8000`) and the Vite proxy depend on
this name. **Run this yourself — it needs sudo:**

```bash
echo "127.0.0.1 crm.test" | sudo tee -a /etc/hosts
```

Verify: `ping -c1 crm.test` resolves to `127.0.0.1`.

### 4. Start the containers

```bash
docker compose -f docker/local/docker-compose.yml up -d
```

Pulls `frappe/bench`, `mariadb:10.6`, `redis:alpine` (first run: several
minutes) and starts all three. The bench container idles on `sleep infinity` so
you drive setup by hand. MariaDB has a healthcheck, so bench waits for a DB that
actually answers.

At this stage the repo is mounted **read-only at `/workspace/crm`, outside the
bench** — see the warning at the top.

Verify: `docker compose -f docker/local/docker-compose.yml ps` shows three
services up and `mariadb` healthy.

### 5. Open a shell in the bench container

```bash
docker compose -f docker/local/docker-compose.yml exec frappe bash
```

**Steps 6–10 run inside this shell.** Check the source mount with
`ls /workspace/crm` — you should see `frontend`, `crm`, `pyproject.toml`.

### 6. Initialise the bench

```bash
cd /home/frappe
bench init \
  --frappe-branch develop \
  --skip-redis-config-generation \
  --skip-assets \
  frappe-bench
cd frappe-bench
```

Clones the Frappe framework into `apps/frappe`, creates the Python virtualenv at
`env/`, and writes `sites/common_site_config.json` and the `Procfile`.

- `--frappe-branch develop` matches `pyproject.toml`'s `frappe >=16.0.0-dev` and
  CI's `FRAPPE_BRANCH: develop`. Do **not** use `version-15`.
- `--skip-assets` skips Frappe's desk bundles, which you do not need.
- Nothing of yours is inside `frappe-bench/` yet, so a rollback here is safe.

Takes 5–10 minutes. Verify: `ls apps/frappe/ui/src` lists the UI library — this
is the `@framework/ui` target.

### 7. Point bench at the service containers

```bash
bench set-mariadb-host mariadb
bench set-redis-cache-host redis://redis:6379
bench set-redis-queue-host redis://redis:6379
bench set-redis-socketio-host redis://redis:6379
sed -i '/redis/d' ./Procfile
sed -i '/watch/d' ./Procfile
```

Rewrites `sites/common_site_config.json` to use compose service names instead of
localhost. The `sed` lines drop Redis from the Procfile (they are their own
containers) and drop `watch` (asset watching is Vite's job on the host).

### 8. Install the CRM app from your checkout

```bash
bench get-app crm /workspace/crm
```

Clones your repo into `apps/crm` and pip-installs it with its `pyproject.toml`
dependencies (`twilio`, `tldextract`). This is the same command CI runs
(`bench get-app crm $GITHUB_WORKSPACE`).

It is a **clone** at this point, so it reflects your last commit, not your
working tree. Step 11 swaps in the live repo.

Verify: `ls apps/crm` and `grep crm sites/apps.txt`.

### 9. Create the site

```bash
bench new-site crm.test \
  --db-root-password 123 \
  --admin-password admin \
  --no-mariadb-socket
bench --site crm.test install-app crm
bench use crm.test
```

Creates the database and `sites/crm.test/`, then installs CRM's DocTypes,
fixtures and roles. `bench use` writes `currentsite.txt`.

Login will be **Administrator / admin**, matching `e2e/helpers/auth.ts`.

### 10. Configure the site for development

```bash
bench --site crm.test set-config developer_mode 1
bench --site crm.test set-config mute_emails 1
bench --site crm.test set-config server_script_enabled 1
bench --site crm.test set-config host_name "http://crm.test:8000"
bench --site crm.test clear-cache
exit
```

`developer_mode 1` is **not optional** — `crm.www.crm.get_context_for_dev`
throws without it, so the dev frontend would never boot (Part 0). `exit` leaves
the container shell.

### 11. Switch the backend to your working tree

On the **host**:

```bash
docker compose -f docker/local/docker-compose.yml \
               -f docker/local/docker-compose.live.yml up -d
```

Recreates the bench container with the repo bind-mounted over `apps/crm`, so
Python edits are live. The editable install from step 8 still points at
`apps/crm`, which is now your repo.

From here on, **always pass both `-f` flags**, and never run `bench init` again.

Verify:

```bash
docker compose -f docker/local/docker-compose.yml -f docker/local/docker-compose.live.yml \
  exec frappe bash -lc 'ls apps/crm/LOCAL_SETUP.md && ./env/bin/python -c "import crm; print(crm.__file__)"'
```

Seeing this file plus a path under `apps/crm` means the live mount is active.

### 12. Start the server

```bash
docker compose -f docker/local/docker-compose.yml \
               -f docker/local/docker-compose.live.yml \
               exec frappe bench start
```

Holds the terminal. Starts gunicorn on **8000** and socket.io on **9000**, both
published to the Mac.

Verify from another host terminal — the same readiness check CI uses:

```bash
curl -s -o /dev/null -w '%{http_code}\n' http://crm.test:8000
```

`200` means **the backend is done**.

---

### 13. Give the host the sibling `frappe` checkout

New terminal, on the **host**. This satisfies `@framework/ui` (Part 0). A sparse
checkout keeps it small — only `ui/` is needed:

```bash
cd /Users/keshavpareta/Documents/git
git clone --branch develop --depth 1 --filter=blob:none --sparse \
  https://github.com/frappe/frappe.git frappe
cd frappe
git sparse-checkout set ui
```

Verify the previously dangling symlink now resolves:

```bash
ls -L /Users/keshavpareta/Documents/git/frappe-crm/frontend/node_modules/@framework/ui
```

### 14. Install frontend dependencies

```bash
cd /Users/keshavpareta/Documents/git/frappe-crm/frontend
yarn install
```

Re-links `@framework/ui` now that its target exists.

### 15. Start the Vite dev server

```bash
yarn dev
```

Serves on **8080**, proxying API traffic to 8000. The line
`No common_site_config.json found, using default port 8000` is expected.

Open **http://crm.test:8080** — the hostname, not `localhost`, so the proxy
forwards the right Host header. Log in as `Administrator` / `admin`.

Vue edits hot-reload; Python edits are live through the bind mount.

---

## Part 3 — Daily use

```bash
COMPOSE="-f docker/local/docker-compose.yml -f docker/local/docker-compose.live.yml"

docker compose $COMPOSE up -d
docker compose $COMPOSE exec frappe bench start
cd frontend && yarn dev            # second terminal

docker compose $COMPOSE stop       # keeps database and bench
```

Full reset (deletes the site and bench volumes; the repo is untouched, and with
the live overlay off there is no mount inside the bench):

```bash
docker compose -f docker/local/docker-compose.yml down -v
```

---

## Part 4 — Tests

**Unit (host, no backend)** — 118 tests, ~250ms:

```bash
cd frontend && yarn test:run
```

**Playwright E2E** — needs the built SPA at `/crm` on 8000, because
`e2e/tests/auth.setup.ts` navigates there to scrape `window.csrf_token`. Build
on the host; output lands in the repo, so the container sees it through the
bind mount:

```bash
cd frontend && yarn build
cd .. && npx playwright install chromium
npx playwright test
```

No `BASE_URL` needed — `crm.test:8000` is already the config default.

**Momentic** — `momentic.config.yaml` currently points its only environment at
the hosted demo shop, unrelated to this app. To aim it here, add an environment
with `baseUrl: http://crm.test:8000`.

---

## Part 5 — Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `PermissionError: 'frappe-bench/sites'` | A bind mount pre-created `frappe-bench/` as root. Do not mount anything inside the bench before step 11. |
| `bench init` offers a rollback | Answer **N** if the live overlay is active — rollback deletes the bench tree, repo included. |
| `Failed to resolve import "@framework/ui/..."` | Step 13 missing or cloned to the wrong path. Must be `git/frappe`, sibling to `git/frappe-crm`. |
| `This method is only meant for developer mode` | `developer_mode` not set — step 10. |
| Blank page, boot request 404s | You opened `localhost:8080`. Use `crm.test:8080`. |
| Site not found / wrong site | `/etc/hosts` entry missing (step 3), or `bench use crm.test` not run. |
| Realtime dead | socket.io needs 9000 published and `bench start` running. |
| `Can't connect to MySQL server on 'mariadb'` | Step 7 not run, or MariaDB not healthy yet. |
| Python edits not picked up | Live overlay not applied — step 11. |
| HMR misses changes | macOS bind-mount watching: `CHOKIDAR_USEPOLLING=true yarn dev`. |
