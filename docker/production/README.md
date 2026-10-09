# Production Docker stack

This directory holds a deployable stack for Frappe CRM. It is **not** the same
thing as `../docker-compose.yml`, which is a development bench.

| | `../docker-compose.yml` | this stack |
| --- | --- | --- |
| Image | `frappe/bench:latest` | `ghcr.io/frappe/crm` (prebuilt) |
| Startup | Runs `bench init`, downloads and builds Frappe | Starts the built app |
| Time to first response | ~10-30 minutes | seconds (plus one-time site creation) |
| Web server | `bench start` (dev server) | gunicorn behind nginx |
| Needs a host bind mount | Yes (`.:/workspace`) | No |
| Deploys your local code | No, pulls `crm` from GitHub `main` | No, runs the released image |

The dev stack cannot pass a platform health check, for the reasons in the first
two rows: its entrypoint script lives on the host and is bind-mounted in, and
even when that works it does not listen on a port until the build finishes.

## Deploying

```bash
cp .env.example .env
$EDITOR .env          # set DB_ROOT_PASSWORD, ADMIN_PASSWORD, SITE_NAME, CRM_HTTP_PORT
docker compose up -d
```

Point the platform at `docker/production/docker-compose.yml`, and mark
**`frontend`** as the primary service — it is the only one publishing a port.

## Health checks

`frontend` has a Compose-level health check against `/api/method/ping` with a
300s `start_period`. On the very first deploy the `create-site` job has to build
the database and install the app before that endpoint answers, which takes a few
minutes.

**Set the platform's health check grace period to at least 5 minutes.** A probe
that starts failing the container after 30-60s will kill the stack mid-site
creation, and because the half-created site persists in the `sites` volume, the
retry can come up in a broken state. If that happens, clear the volumes and
redeploy:

```bash
docker compose down -v && docker compose up -d
```

Subsequent deploys are fast — `create-site` sees the existing site and exits.

## Port

The platform health check in the failing deploy targeted **8052**, which is the
default for `CRM_HTTP_PORT`. Inside the container nginx always listens on 8080;
only the published port is configurable. If the platform assigns a port
dynamically, set `CRM_HTTP_PORT` from its injected variable rather than
hardcoding it.

## Host header

`FRAPPE_SITE_NAME_HEADER` is pinned to `SITE_NAME`. Frappe is multi-tenant and
normally picks the site from the Host header, so a probe hitting a bare IP or an
internal hostname would get "Site does not exist" and fail the check even though
the app is healthy. Pinning it forces every request to resolve to the one site.

## TLS

This stack serves plain HTTP on `CRM_HTTP_PORT`. Terminate TLS at the platform's
load balancer. If it forwards `X-Forwarded-For`, set `UPSTREAM_REAL_IP_ADDRESS`
in the compose file to the balancer's address so client IPs are logged correctly.

## Persistence

Four named volumes: `db-data`, `sites`, `logs`, `redis-queue-data`. `db-data`
and `sites` hold all durable state — the database and the site's files,
including uploads and `site_config.json`. Back both up together; they must be
restored as a matched pair. If the platform does not persist named volumes
across deploys, this stack will recreate the site from scratch every time.
