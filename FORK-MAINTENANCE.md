# Fork Maintenance Workflow

This document describes the rebase-only workflow for maintaining Frappe CRM fork with minimal local patches on top of upstream.

## Repository Structure

```
origin (puzzo-dev fork) → github.com/puzzo-dev/crm.git
upstream (frappe)       → github.com/frappe/crm.git
```

## Current Configuration

The repository is already configured with:
- **Upstream**: https://github.com/frappe/crm.git (Frappe's original)
- **Origin**: Should be https://github.com/puzzo-dev/crm.git (your organization fork)

## Initial Setup

### 1. Update Origin Remote to puzzo-dev

```bash
cd /home/puxxo/CodeBase/erpNext/frappe-bench-v15/apps/crm

# Update origin to point to puzzo-dev organization
git remote set-url origin https://github.com/puzzo-dev/crm.git

# Verify remotes
git remote -v
# origin    https://github.com/puzzo-dev/crm.git (fetch)
# origin    https://github.com/puzzo-dev/crm.git (push)
# upstream  https://github.com/frappe/crm.git (fetch)
# upstream  https://github.com/frappe/crm.git (push)
```

### 2. Create Tracking Branches

```bash
# Fetch all remotes
git fetch --all

# Create local tracking branch for upstream
git branch develop-upstream upstream/develop

# Ensure your working branch tracks origin
git checkout develop
git branch -u origin/develop
```

## Branch Strategy

```
upstream/develop     ← Frappe's original CRM (never modified)
    ↓
develop-upstream     ← Local tracking of upstream (fast-forward only)
    ↓
develop              ← Your branch with patches (rebase on top)
    ↓
origin/develop       ← puzzo-dev fork (force-push safe after rebase)
```

## Daily Workflow

### Syncing Upstream Changes

Run this regularly (daily for fast-moving repos):

```bash
cd /home/puxxo/CodeBase/erpNext/frappe-bench-v15/apps/crm

# 1. Fetch latest from Frappe
git fetch upstream

# 2. Update local upstream mirror (fast-forward only)
git checkout develop-upstream
git merge --ff-only upstream/develop

# 3. Rebase your patches on top
git checkout develop
git rebase develop-upstream

# 4. Push to puzzo-dev fork
git push origin develop --force-with-lease
```

### Making New Changes

```bash
cd /home/puxxo/CodeBase/erpNext/frappe-bench-v15/apps/crm

git checkout develop
git pull origin develop

# Make your changes
git add .
git commit -m "fix: your local patch for puzzo-dev"

# Push to puzzo-dev fork
git push origin develop
```

## Handling Conflicts

When `git rebase develop-upstream` produces conflicts:

### Resolve and Continue

```bash
# Edit conflicting files, remove markers
git add <resolved-files>
git rebase --continue

# Or abort if needed
git rebase --abort
```

### Force Push After Successful Rebase

```bash
# Test your changes first!
git push origin develop --force-with-lease
```

## Recovery Scenarios

### Upstream Fixed Your Issue

```bash
git fetch upstream
git checkout develop-upstream
git merge --ff-only upstream/develop

git checkout develop
git rebase -i develop-upstream
# Mark your redundant commit as "drop"

git push origin develop --force-with-lease
```

### Rebase Went Wrong

```bash
git rebase --abort
git reflog  # Find commit before rebase
git reset --hard <hash-before-rebase>
```

## Tracking Your Patches

```bash
# See all puzzo-dev patches not in Frappe upstream
git log develop-upstream..develop --oneline

# Check if upstream has new changes
git fetch upstream
git log develop..upstream/develop --oneline
```

## Automated Sync (GitHub Actions)

Create `.github/workflows/sync-upstream.yml` in the puzzo-dev/crm repository:

```yaml
name: Sync Frappe CRM Upstream

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM UTC
  workflow_dispatch:

jobs:
  sync:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          ref: develop
          fetch-depth: 0
          token: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Configure Git
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
      
      - name: Add Upstream
        run: |
          git remote add upstream https://github.com/frappe/crm.git
          git fetch upstream
      
      - name: Check for Changes
        id: check
        run: |
          UPSTREAM_COMMIT=$(git rev-parse upstream/develop)
          LOCAL_BASE=$(git merge-base develop upstream/develop)
          
          if [ "$UPSTREAM_COMMIT" != "$LOCAL_BASE" ]; then
            echo "changes=true" >> $GITHUB_OUTPUT
          else
            echo "changes=false" >> $GITHUB_OUTPUT
          fi
      
      - name: Rebase on Upstream
        if: steps.check.outputs.changes == 'true'
        run: |
          git branch -f develop-upstream upstream/develop
          
          if git rebase develop-upstream; then
            git push origin develop --force-with-lease
          else
            git rebase --abort
            exit 1
          fi
      
      - name: Create Issue on Conflict
        if: failure()
        uses: actions/github-script@v7
        with:
          script: |
            github.rest.issues.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              title: '🚨 Frappe CRM Upstream Sync Failed',
              body: `Automated sync from Frappe CRM upstream failed due to conflicts.
              
              **Manual Action Required:**
              1. \`cd /home/puxxo/CodeBase/erpNext/frappe-bench-v15/apps/crm\`
              2. \`git fetch upstream\`
              3. \`git rebase upstream/develop\`
              4. Resolve conflicts
              5. \`git push origin develop --force-with-lease\`
              
              See [FORK-MAINTENANCE.md](./FORK-MAINTENANCE.md) for details.
              
              **Failed Run:** ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}`,
              labels: ['upstream-sync', 'needs-attention']
            })
```

## Quick Reference

### Daily Sync
```bash
cd /home/puxxo/CodeBase/erpNext/frappe-bench-v15/apps/crm
git fetch upstream
git checkout develop-upstream && git merge --ff-only upstream/develop
git checkout develop && git rebase develop-upstream
git push origin develop --force-with-lease
```

### Check Status
```bash
# See puzzo-dev patches
git log develop-upstream..develop --oneline

# Check for upstream updates
git fetch upstream && git log develop..upstream/develop --oneline
```

### Emergency Abort
```bash
git rebase --abort
git reset --hard origin/develop
```

## Force Push Safety

✅ **Safe:** Using `--force-with-lease` on your fork (puzzo-dev/crm)  
✅ **Safe:** After successful rebase and testing  
❌ **Never:** Use `--force` without `--lease`  
❌ **Never:** On shared branches without coordination

## When to Use This Workflow

✅ **Perfect for:**
- Maintaining minimal patches on Frappe CRM
- Staying current with Frappe's fast development
- Clean, linear history
- puzzo-dev organization forks

❌ **Not suitable for:**
- Extensive custom modifications
- Merge-based workflows
- Shared development without rebase knowledge
