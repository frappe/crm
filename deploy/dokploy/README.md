# Frappe CRM on Dokploy

This deployment uses the official Frappe Docker production service layout and
a custom image built from this repository. It is separate from `docker/`, which
is the local development environment.

## 1. Build the custom image

1. Push this deployment commit to the branch you want to deploy.
2. Open **GitHub → Actions → Build Dokploy Image**.
3. Run the workflow for that branch, or let its configured push trigger run.
4. Wait for the `ghcr.io/nyrexcoder/crm:dokploy` image to finish publishing.
5. In GitHub package settings, make the package public, or configure Dokploy
   with GHCR credentials that have `read:packages` access.

The workflow also publishes an immutable `sha-<commit>` tag for rollback.

## 2. Configure Dokploy

Create a **Docker Compose** service with:

- Repository: `Nyrexcoder/crm`
- Branch: the same branch used to build the image
- Compose path: `./deploy/dokploy/compose.yml`
- Trigger type: manual for the first deployment

Copy `.env.example` into Dokploy's **Environment** tab and replace:

- `SITE_NAME` with the real CRM domain
- `DB_PASSWORD` with a strong random database password
- `ADMIN_PASSWORD` with a different strong Administrator password

Do not commit real passwords to Git.

MariaDB only applies `DB_PASSWORD` when its data volume is initialized for the
first time. If an initial deployment used a placeholder password, changing the
environment variable is not enough. For a new installation with no data, delete
the Compose stack with **Delete volumes** enabled, recreate it with the final
passwords, and deploy again. Never delete volumes from an installation that
contains data unless a verified backup exists.

Use **Preview Compose** before deployment. The one-shot services must complete
in this order: `configurator`, `create-site`, and `migrator`. The long-running
services then start: `backend`, `frontend`, `websocket`, both queues, scheduler,
MariaDB, and Redis.

## 3. Configure the domain

Before adding the domain, point its DNS `A` record to the Dokploy server.

In **Dokploy → Domains → Add Domain** use:

- Host: the same value as `SITE_NAME`
- Service: `frontend`
- Container port: `8080`
- Path: `/`
- HTTPS: enabled

Redeploy after changing a Docker Compose domain.

CRM will be available at `https://<SITE_NAME>/crm`. Sign in as
`Administrator` with the configured `ADMIN_PASSWORD`.

## 4. Automated deployments

Do not enable repository AutoDeploy before the image build completes; otherwise
Dokploy can pull the previous `dokploy` tag.

For ordered deployments:

1. Copy the Dokploy webhook URL.
2. Add it in GitHub as an Actions secret named `DOKPLOY_WEBHOOK_URL`.
3. Keep Dokploy's direct repository AutoDeploy disabled.

The image workflow will call Dokploy only after the new image is available.

## 5. Backups and operations

Configure Dokploy backups for the `db-data` and `sites` named volumes. Also add
a daily Compose job on the `backend` service:

```bash
bench --site all backup --with-files --compress
```

Before an upgrade, verify that both database and site-file backups completed.
The `migrator` service runs `bench migrate` automatically on every deployment.

To roll back application code, set `CUSTOM_TAG` to a previously published
`sha-<commit>` tag and redeploy. A database restore may still be required when
rolling back across incompatible schema migrations.

## Troubleshooting

- **Image pull denied:** make the GHCR package public or add GHCR credentials.
- **Site creation fails:** check `db`, `configurator`, then `create-site` logs.
- **Migration fails:** check `migrator` logs and restore the latest backup if
  the migration cannot safely be retried.
- **502/404 on the domain:** confirm the domain targets `frontend` port `8080`
  and `SITE_NAME` exactly matches the host.
- **Changes not visible:** confirm the workflow built the intended branch and
  Dokploy pulled the new image tag.
