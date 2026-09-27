---
name: momentic-triage-quarantined-tests
description:
  Triage and repair Momentic tests that are currently quarantined. Use when the
  user asks to work through the quarantine backlog, re-check quarantined tests,
  fix or heal quarantined tests, or produce a PR, patch, or report for them.
---

# Triage quarantined tests

A quarantined test is one Momentic still runs but whose failures no longer fail
the pipeline. Quarantine stops the bleeding; it does not fix anything. This skill
works the quarantine backlog: find the quarantined tests, get a failed run for
each, classify why it failed, then let `momentic ai triage` attempt a repair and
deliver the accepted fixes.

Two starting points, depending on what the user has:

- **Fresh run** — rerun the quarantined tests now and triage what fails. Use this
  when nothing recent exists, or when the user wants current results.
- **Existing failures** — triage the failed runs the quarantined tests already
  produced. Use this when the user points at a run group, a commit, or the
  backlog on the dashboard.

## Ask once, then proceed

Ask these together in a single message, state the recommended answer for each,
and apply the defaults for anything the user leaves out. Do not re-ask later.

1. **Which starting point** — fresh run (default) or existing failed runs.
2. **How far back** to look for quarantined failures when using existing runs.
   Default to the last 7 days.
3. **How to deliver successful repairs** — see the table below. Default to a
   pull request.
4. **How many tests to triage at once** — default `--parallel 2`, and do not go
   above 4. Each triage drives a real browser, so oversubscribing the machine
   makes runs stall rather than finish sooner.

If the user just says "go", use every default and start.

### Delivering repairs

| Choice        | Flag                                          | Behavior                                                                        |
| ------------- | --------------------------------------------- | ------------------------------------------------------------------------------- |
| Pull request  | `--on-heal-success pull-request`              | Opens a ready-for-review PR with the accepted repairs.                          |
| Draft PR      | `--on-heal-success draft-pull-request`        | Opens a draft PR instead.                                                       |
| Direct commit | `--on-heal-success direct-commit-except-main` | Commits and pushes to the current branch, falling back to a draft PR on `main`. |
| Patch         | `--on-heal-success patch`                     | Prints a `git apply`-ready patch to stdout.                                     |
| Local only    | `--on-heal-success nothing`                   | Leaves the repairs in the worktree.                                             |
| Report only   | `--dry-run`                                   | Prints the failure bucketing plan and exits without healing.                    |

Always pass the chosen flag explicitly. It overrides the project's configured
heal behavior both in and out of CI, so the outcome does not depend on where the
command runs. Prefix commands with `npx` when the project invokes Momentic that
way.

## Before triaging

- **Start the app the way CI starts it.** Read the project's CI workflow and
  `momentic.config.yaml` for the app's start command, environment, and readiness
  URL, and confirm the app is reachable that way. A quarantined test that fails
  against a differently-configured app tells you nothing. If it is not running,
  ask the user how to start it rather than guessing a command.
- **Confirm Momentic access**: the project config resolves and the API key works.
- **Install browsers** if this machine has not run Momentic before:
  `npx momentic install-browsers chromium`, or `npx momentic doctor` to check.
- **Clean up leftovers** from earlier attempts. Stale dev servers, build workers,
  and orphaned browsers from a previous run compete for the same CPU and memory
  and are a common cause of triage stalls. Only stop processes you can confirm
  belong to this worktree, and never stop the app under test.

## Fresh run

Run just the quarantined tests into a results directory, then triage it:

```bash
npx momentic run --only-quarantined --output-dir test-results
npx momentic ai triage test-results \
  --parallel 2 \
  --yes \
  --on-heal-success pull-request
```

`--only-quarantined` runs only quarantined tests and, unlike a normal run, lets
their failures set a non-zero exit code — which is what you want when the whole
point is to see what is still broken.

## Existing failures

1. List what is quarantined. `momentic quarantine list` prints the quarantined
   test files in the project. With Momentic's MCP server connected,
   `momentic_quarantine_list` is better for this workflow: it takes a quarantine
   date range and returns the quarantine reason plus the latest retained failed
   run for each test. Page through the results — the first page is usually not
   the whole backlog.
2. Note the tests whose latest failed run has aged out of retention. They need a
   fresh run instead; do not invent run ids for them.
3. Classify the failures so you know what you are repairing. Deduplicate run ids
   first:

   ```bash
   npx momentic ai classify --run-id <run-id> [<run-id> ...] --output-format json
   ```

   Add `--skip-classified` to skip runs that already have a saved classification.
   Classification explains the failure; it does not repair anything, so keep
   going.

4. Triage the same runs:

   ```bash
   npx momentic ai triage --run-id <run-id> [<run-id> ...] \
     --parallel 2 \
     --yes \
     --on-heal-success pull-request
   ```

   Pass the run ids as one space-separated list after a single `--run-id`, not one
   command per run — triage buckets failures that share a root cause and fixes
   them together, which it cannot do if you split them up. A run group or commit
   works as a selector too: `--run-group-id <id>` or `--git-commit <sha>`.

With more runs than your parallelism, work in batches of a few runs, keep a todo
list so no test is silently dropped, and finish one batch before starting the
next so batches do not compete for the machine.

## While triage runs

Keep the command attached and watch its streamed output. One triage typically
takes a few minutes. Treat several minutes of no progress, repeated browser
timeouts, or a single interaction taking far longer than the original test as a
signal to check the machine rather than to wait longer: look at free memory, CPU
load, and whether something other than Momentic is consuming them. If the machine
is saturated, let the current batch finish, then lower `--parallel`.

If triage reports that it could not run because of the browser, the machine, or
the app being unavailable, that is not the same as "this test cannot be fixed."
Say so explicitly, fix the environment, and rerun those tests.

## Report back

Summarize:

- how many tests are quarantined, and the date range you covered;
- which tests had a usable failed run and which need a fresh one;
- the classification and triage outcome per test;
- what was delivered (PR, commit, patch, or worktree changes); and
- anything that blocked a test from being triaged at all.

**Never remove a test from quarantine just because triage produced a fix.** A
repair is a proposal until someone reviews it and the test passes again. Leave
quarantine state alone unless the user explicitly asks to change it, and when
they do, validate first with `npx momentic run --ignore-quarantine`.

---

Generated for momentic 3.60.2 (skills 1790392498). Run `npx momentic skills` after you upgrade momentic.
