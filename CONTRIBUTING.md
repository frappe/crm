# Contributing to Frappe CRM

Thank you for your interest in contributing to Frappe CRM! This document outlines the process for reporting issues, proposing features, and submitting code changes.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Help](#getting-help)
- [Reporting Bugs](#reporting-bugs)
- [Requesting Features](#requesting-features)
- [Setting Up a Development Environment](#setting-up-a-development-environment)
- [Project Structure](#project-structure)
- [Making Changes](#making-changes)
  - [Branching](#branching)
  - [Commit Messages](#commit-messages)
  - [Code Style & Linting](#code-style--linting)
- [Submitting a Pull Request](#submitting-a-pull-request)
- [License](#license)

---

## Code of Conduct

This project follows the [Frappe Code of Conduct](https://github.com/frappe/.github/blob/main/CODE_OF_CONDUCT.md). By participating, you agree to uphold a respectful and collaborative environment for everyone.

---

## Getting Help

Before opening a new issue, check these resources first:

- 📖 [Documentation](https://docs.frappe.io/crm)
- 💬 [Telegram Group](https://t.me/frappecrm)
- 🗣️ [Discuss Forum](https://discuss.frappe.io/c/frappe-crm)

---

## Reporting Bugs

1. Search [existing issues](https://github.com/frappe/crm/issues) to avoid duplicates.
2. Click **New Issue** and choose the **Bug Report** template.
3. Fill in all relevant sections: steps to reproduce, expected vs. actual behaviour, screenshots, browser/OS info, and the version of Frappe CRM you're using.

The more detail you provide, the faster the bug can be triaged and fixed.

---

## Requesting Features

1. Search [existing issues](https://github.com/frappe/crm/issues) and the [Discuss Forum](https://discuss.frappe.io/c/frappe-crm) to see whether the idea has already been raised.
2. Click **New Issue** and choose the **Feature Request** template.
3. Describe the problem you're trying to solve, your proposed solution, and any alternatives you've considered.

For large or architectural changes, open a discussion first so we can align before you invest time writing code.

---

## Setting Up a Development Environment

### Prerequisites

- [Frappe Bench](https://docs.frappe.io/framework/user/en/installation) installed and working.
- Node.js ≥ 18 and Yarn.
- Python ≥ 3.10.

### Local Setup

```sh
# 1. Start the bench (keep this running in a separate terminal)
bench start

# 2. Fetch the app and create a site
bench get-app crm
bench new-site sitename.localhost --install-app crm
bench browse sitename.localhost --user Administrator
```

The CRM is now accessible at `http://sitename.localhost:8000/crm`.

### Frontend Dev Server

```sh
cd frappe-bench/apps/crm
yarn install
yarn dev
```

The Vite dev server runs at `http://sitename.localhost:8080`.

### Docker (Alternative)

```sh
mkdir frappe-crm && cd frappe-crm

wget -O docker-compose.yml https://raw.githubusercontent.com/frappe/crm/develop/docker/docker-compose.yml
wget -O init.sh https://raw.githubusercontent.com/frappe/crm/develop/docker/init.sh

docker compose up -d
```

Open `http://crm.localhost:8000/crm` (default credentials: `Administrator` / `admin`).

### Pre-commit Hooks

This repo uses [pre-commit](https://pre-commit.com/) to enforce linting before every commit. Install it once after cloning:

```sh
pip install pre-commit
pre-commit install
```

Hooks include: trailing-whitespace, JSON/YAML/TOML checks, **oxlint** (JS/TS/Vue), **Prettier** (frontend formatting), **ESLint** (frontend), and **Ruff** (Python linting + formatting).

---

## Project Structure

| Path | Description |
|------|-------------|
| `crm/` | Python backend — Frappe doctypes, APIs, integrations |
| `frontend/` | Vue 3 frontend application |
| `frappe-ui/` | Git submodule — shared Frappe UI component library |
| `docker/` | Docker Compose setup for local development |
| `docs/` | Additional documentation |

---

## Making Changes

### Branching

| Branch | Purpose |
|--------|---------|
| `main` | Stable release (v1.x). Bug fixes and non-breaking improvements. |
| `develop` | Next major version (v2.x). New features and breaking changes. |

- Target `develop` for new features.
- Target `main` for bug fixes that should be back-ported to the current stable release.
- **Do not commit directly to `develop` or `main`.** The `no-commit-to-branch` pre-commit hook enforces this for `develop`.

Create a descriptive branch from the appropriate base:

```sh
git checkout develop
git pull origin develop
git checkout -b feat/my-awesome-feature
```

### Commit Messages

This project uses [Conventional Commits](https://www.conventionalcommits.org/) enforced by **commitlint**. Every commit message must follow this format:

```
<type>(<optional scope>): <short description>
```

Allowed types:

| Type | When to use |
|------|-------------|
| `feat` | A new feature |
| `fix` | A bug fix |
| `docs` | Documentation-only changes |
| `style` | Code style / formatting (no logic changes) |
| `refactor` | Code refactor with no feature or fix |
| `perf` | Performance improvement |
| `test` | Adding or updating tests |
| `build` | Build system or dependency changes |
| `ci` | CI/CD configuration changes |
| `chore` | Maintenance tasks |
| `revert` | Reverting a previous commit |
| `patch` | Small patch not fitting other types |
| `deprecate` | Marking something as deprecated |

**Examples:**

```
feat(leads): add bulk reassign action to list view
fix(call-ui): prevent duplicate ring events on Twilio reconnect
docs: update Docker setup instructions in README
```

### Code Style & Linting

All checks are run automatically by pre-commit. You can also run them manually:

**Frontend (JS / TS / Vue)**

```sh
cd frontend
yarn lint        # ESLint
yarn format      # Prettier
```

**Backend (Python)**

```sh
ruff check --fix crm/
ruff format crm/
```

Please do not disable linting rules without a clear justification in a comment.

---

## Submitting a Pull Request

1. **Fork** the repository and push your branch to your fork.
2. Open a Pull Request against the correct base branch (`main` or `develop`).
3. Fill in the PR description:
   - What problem does this solve?
   - How was it tested?
   - Any breaking changes or migrations required?
4. Link any related issues using GitHub keywords (e.g., `Closes #123`).
5. Ensure all CI checks pass (linting, build).
6. A maintainer will review your PR. Please be responsive to feedback — PRs with no activity for 30 days may be closed.

> **Tip:** Keep PRs small and focused. One logical change per PR makes reviews faster and merge conflicts less likely.

---

## License

By contributing to Frappe CRM, you agree that your contributions will be licensed under the [GNU Affero General Public License v3.0](LICENSE).
