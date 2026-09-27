---
name: momentic-maintain
description:
  Diagnose, classify, triage, and repair failing Momentic tests with MCP run
  tools, the Momentic CLI, and manual run artifacts. Use when a developer asks
  what happened on a branch, DevX or on-call asks why main is red, or the user
  wants to inspect classifications, de-flake quarantined or recovered tests,
  reduce retries, re-classify runs, run AI triage, or repair failures.
---

# Maintain Momentic tests

Find the earliest point where a run entered a bad state, classify the cause from
evidence, and repair the test when a durable test change is appropriate. Use MCP
for targeted investigation, `momentic ai classify` for a fresh classifier
verdict, and `momentic ai triage` for automated repair and verification.

Do not weaken a test to hide an application bug, missing fixture, invalid
credentials, outage, or Momentic defect. Report those causes instead of changing
the test to pass.

## Common workflows

- **What happened on my branch?** Call `momentic_list_runs` with the exact `gitBranchName` and bounded `start`/`end`. Start without a status filter, then narrow to `FAILED`, `CANCELLED`, or `recovered=true`. Open exact candidates and compare with main only for a concrete cross-branch question.
- **Why is main red?** List `FAILED` runs on the actual main branch over the incident window and paginate through every page needed for the claim. Narrow with `failureCategory` when investigating a known category, but group symptoms only after inspecting representative runs and step evidence. Read each exact run's saved classification before optionally re-classifying it.
- **De-flake and reduce recovery latency.** Use `momentic_quarantine_list` for quarantined tests, `recovered=true` for successful runs that needed recovery, and `minAttempts` for retry-heavy runs (`2` means at least one retry; `3` means at least two). Inspect earlier attempts, prioritize repeated same-intent failures, fix the earliest unstable postcondition, and measure again.

Know the discovery limits:

- `momentic_list_runs` filters by test, branch, status, quarantine, recovery, effective failure category, minimum total attempts, and time. `failureCategory` uses a manual classification when present, otherwise the automated classification.
- `momentic_quarantine_list` filters by quarantine date and returns each active quarantine's latest retained failed CLI run. It does not filter by branch or classification.
- A category or retry threshold can still span multiple pages. Paginate through all `pageCount` pages needed before calling an inventory exhaustive.

## Maintenance workflow

1. Start from the exact run, branch, run group, commit, or local results target.
2. Inspect existing automated/manual classifications and heal state first.
3. Reconstruct exact failures with MCP and only the necessary run history.
4. Explain the earliest divergence and broken postcondition before editing.
5. Classify afresh only when useful; persist a verdict only when requested.
6. Prepare the exact app and fixtures, then triage when repair is appropriate.
7. Review the diff and replay evidence; re-run inconclusive repairs.
8. Report diagnosis, repair, verification, delivery, and remaining blockers.

## Inspect the existing classification

Fetch raw run metadata before MCP investigation when an API key is available:

```bash
RUN_ID="<run-id>"
MOMENTIC_SERVER_URL="${MOMENTIC_SERVER:-https://api.momentic.ai}"
RUN_INSPECTION_DIR="$(mktemp -d)"

curl --fail --silent --show-error \
  -H "Authorization: Bearer ${MOMENTIC_API_KEY:?Set MOMENTIC_API_KEY}" \
  "${MOMENTIC_SERVER_URL}/v1/runs/${RUN_ID}/metadata" \
  -o "${RUN_INSPECTION_DIR}/metadata.json"

jq '{
  runId: .id,
  status,
  failureReason,
  classification: .failureDetails.classification,
  manualClassification: .failureDetails.manualClassification,
  healStatus,
  healDetails
}' "${RUN_INSPECTION_DIR}/metadata.json"
```

Do not treat a missing field as proof that no human reviewed the failure until
the metadata request succeeds for the exact run and organization. Do not echo,
log, or commit the API key. Treat downloaded metadata and signed artifact URLs
as sensitive run data.

`momentic_get_run` intentionally removes prior classification and heal fields
from the evidence it returns so a fresh investigation is not anchored by an old
verdict. Use the metadata endpoint or dashboard for the existing verdict, then
use MCP for the underlying evidence.

## Helpful MCP tools

`momentic_get_run` - Return run metadata and a summary of the full result tree.
Use it to identify the attempt, failed section, failing step, and nested parent
chain. If the current run is already loaded, call it again only for a different
attempt or missing data.

`momentic_list_runs` - List recent runs for the test. Always pass
`gitBranchName` when it exists on the target run so comparisons are more likely
to use the same test version. Omit it only when cross-branch history answers a
specific question. Pass `recovered=true` to inspect recovered runs.
Pass `failureCategory` to select effective manual/automated classifications and
`minAttempts: 2` or higher to find retried runs.

`momentic_quarantine_list` - List active local test quarantines and each test's
latest retained failed CLI run. Use a bounded quarantine-date range.

`momentic_get_step_result` - Return command details, before/after screenshots,
and optionally the full trace for one step. Pass `parentStepIdChain` for nested
steps. Request `includeTrace=true` only when screenshots and normal fields do
not answer the question.

`momentic_get_test_steps_for_run` - Return the simplified test definition
recorded on a run. Use it when test intent remains unclear or when comparing
whether the authored test changed between runs.

`momentic_submit_result_classification` - Persist a manual MCP classification.
Call it only after the investigation is complete and only when the user asked to
record the verdict. Do not call it in addition to `ai classify --save` for the
same conclusion.

## Investigation workflow

Start with the current run before relying on history.

1. Call `momentic_get_run` and identify the failing attempt, section (`beforeSteps`, main steps, or `afterSteps`), failing step, and any `parentStepIdChain`.
2. Pull the failing step result with screenshots and trace. If the step is nested, also pull the nearest parent container or module result.
3. Decide whether the failing step's before-screenshot is the correct baseline for that action. If it is already wrong, walk backward through the current run until you find the step/container that produced that bad state.
4. For repeated modules or repeated workflows, compare invocations inside the same current run before comparing older runs. The later failure is often caused by an earlier invocation that succeeded, recovered, or left an invalid postcondition.
5. Treat successful containers with failed or recovered child steps as partial failures until you inspect the container's final after-screenshot and URL.
6. Use past runs only for specific comparison questions once the current-run behavior is understood.

Before classifying, be able to answer:

- What is the test's intended behavior?
- What is the earliest divergent step/container?
- What did that step intend to do?
- Which element/state did it actually interact with or observe?
- What changed in the screenshot, URL, DOM, trace, or recovery log after the step?
- Why is the later failure a consequence of that earlier divergence?

Avoid vague root causes such as "setup was unreliable" or "the page was in the wrong state." Name the broken postcondition directly: for example, "the row-level plus button was clicked, but the app stayed on the parent page instead of opening the child-page editor; the following global `Add to` assertion passed against unrelated page text, so the untargeted type step never entered the child title."

## Evidence standards

- Screenshots are the default truth source for page state. Use trace fields and DOM/HTML to explain why the screenshot changed or did not change.
- Verify every causal claim. Do not say an overlay, side peek, modal, or menu was present unless the relevant before/after screenshot, URL, or DOM proves it.
- Separate "the target is missing now" from "the browser is in the state where that target should exist." A missing target is often a symptom of an earlier failed action.
- For click/type/action steps, record the intended action, actual interacted element when available, before/after URL, and whether the expected UI state appeared.
- For assertions, check whether the assertion is scoped enough to prove the intended state. A broad page-content assertion can pass for unrelated text.
- For recovery, inspect both the failed child step and the recovered container final state. Recovery can pass a retried assertion while leaving state that later steps did not expect.

## Run AI classification

`momentic ai classify` runs Momentic's result-classification agent over failed
runs. It reads the run artifacts, uses relevant run history and repository
context, and returns a category, recoverability, confidence, reasoning, and
citations. It explains the failure; it does not edit the test.

Use one selector per command:

```bash
npx momentic ai classify --run-id "$RUN_ID" --output-format json
npx momentic ai classify --run-group-id "<run-group-id>"
npx momentic ai classify --git-commit "<commit-sha>"
```

- Omit `--save` for a diagnostic re-classification. Add `--save` only when the
  new verdict should replace the saved classification on the local archive or
  cloud run.
- Use `--no-cache` when the existing cached classifier result is suspected to
  be stale and the user explicitly needs a fresh analysis.
- Use `--skip-classified` when resuming a batch without revisiting runs that
  already have saved classifications.
- Use `--output-format json` for automation and multi-run bookkeeping.
- Classify multiple related run IDs together when useful, but keep each result
  mapped to its exact run.

For one run in a real terminal, keep the classifier conversation open:

```bash
npx momentic ai classify --run-id "$RUN_ID" --interactive
```

Use the chat to ask why it chose the category, what evidence it relied on, how
the current run differs from a prior run, or what a durable fix would require.
Interactive classification is single-run only, requires stdin to be a TTY, and
cannot be combined with JSON output.

## Prepare triage

Treat application readiness as a hard precondition. Triage replays the test in
a real browser; it cannot repair a test against an unavailable app, missing
fixture, wrong environment, unseeded database, invalid account, or cold compiler.

Before triage:

1. Read `momentic.config.yaml`, the target test and its setup modules, repository
   scripts, and the CI workflow that normally runs the test. Use the same URL,
   environment, credentials, headers, files, services, and data fixtures.
2. Confirm `MOMENTIC_API_KEY`, project configuration, dependencies, and the
   requested browser are available.
3. Inspect `git status` and preserve unrelated work. Decide the repair delivery
   before running the command; do not let an unknown dashboard default create a
   pull request or commit unexpectedly.
4. Build the application before starting triage. Prefer a production or
   otherwise precompiled build and a stable server over Next.js, webpack, Vite,
   or another development server that compiles routes incrementally.
5. Start every required service and wait for the actual readiness URL. Warm any
   unavoidable dev-only compilation path before triage and verify that the
   relevant route no longer shows a compile/loading screen or incurs a long
   first request.
6. Run a focused smoke or the failing test once when necessary to prove the app,
   fixture, authentication, and browser are ready. Fix setup failures before
   blaming triage.
7. Start with `--parallel 1`. Raise it only when the machine has enough CPU and
   memory for one browser and application workload per worker.

If the repository exposes a stable server command, either start it separately
or let triage own it with `--start` and `--wait-on`:

```bash
# Build first; use the repository's actual commands and readiness URL.
pnpm build
npx momentic ai triage --run-id "$RUN_ID" \
  --start "pnpm start" \
  --wait-on "http://localhost:3000/health" \
  --parallel 1 \
  --yes \
  --on-heal-success nothing
```

Do not copy these example commands blindly. Discover the real build, start, and
readiness contract from the repository and CI configuration.

## Run AI triage

`momentic ai triage` groups failures by shared root cause, decides which ones
are repairable, edits the relevant tests, replays them in a browser, and accepts
only repairs that satisfy its verification. It can leave changes locally,
produce a patch, commit, or open a pull request. It cannot fix an application
bug, external outage, or missing fixture by changing a test.

Run classification first when the user wants an explicit diagnosis, then pass
the same target to triage:

```bash
npx momentic ai classify --run-id "$RUN_ID" --output-format json
npx momentic ai triage --run-id "$RUN_ID" \
  --parallel 1 \
  --yes \
  --on-heal-success nothing
```

For a local run group, pass the results directory instead:

```bash
npx momentic ai triage ./test-results \
  --parallel 1 \
  --yes \
  --on-heal-success nothing
```

Best practices:

- Pass multiple related run IDs after one `--run-id` so the bucketing agent can
  group shared causes. Do not launch one competing triage command per run.
- Set `--on-heal-success` explicitly: use `nothing` for local review, `patch`
  for a portable diff, or a pull-request/commit behavior only when the user
  asked for that delivery.
- Pass `--yes` only after the environment and delivery choice are confirmed so
  dependency prompts do not stall an autonomous run.
- Use `--dry-run --no-save` to inspect bucketing without editing tests or saving
  triage metadata. Dry-run is not a repair attempt.
- Use `--regenerate-heal` only when a cached heal is stale or failed and a new
  repair should be generated from scratch.
- Keep the command attached and monitor reasoning, tool calls, browser progress,
  CPU, and memory. Several minutes without browser progress can indicate app
  startup, cold compilation, resource pressure, or a missing fixture.
- Inspect every resulting diff. Do not accept deleted assertions, broadened
  checks, arbitrary sleeps, or longer timeouts that merely conceal the cause.
- Do not remove quarantine solely because triage produced a patch. Re-run the
  repaired test first.

Use interactive triage when the user wants to question the repair agent:

```bash
npx momentic ai triage --run-id "$RUN_ID" \
  --parallel 1 \
  --yes \
  --on-heal-success nothing \
  --interactive
```

Interactive triage requires a TTY, cannot be combined with `--json`, and is
available only when the command runs the bucketing agent. Use it to ask why a
fix was accepted or rejected, what setup it observed, and what evidence remains
unresolved.

## Download run artifacts manually

Prefer MCP for ordinary inspection because `momentic_get_run` downloads and
extracts cloud attempts automatically. Use the API when MCP output is missing,
when raw files must be grepped, or when independently verifying the agent.

The export endpoint returns run metadata plus one short-lived signed ZIP URL per
attempt; it does not return one combined run ZIP. Download and extract them
without printing the URLs:

```bash
RUN_ID="<run-id>"
MOMENTIC_SERVER_URL="${MOMENTIC_SERVER:-https://api.momentic.ai}"
RUN_INSPECTION_DIR="$(mktemp -d)"

curl --fail --silent --show-error \
  -H "Authorization: Bearer ${MOMENTIC_API_KEY:?Set MOMENTIC_API_KEY}" \
  "${MOMENTIC_SERVER_URL}/v1/runs/${RUN_ID}/export" \
  -o "${RUN_INSPECTION_DIR}/export.json"

jq '.run' "${RUN_INSPECTION_DIR}/export.json" \
  > "${RUN_INSPECTION_DIR}/metadata.json"

jq -r '.attemptZipUrls | to_entries[] | select(.value != null) |
  [(.key + 1), .value] | @tsv' "${RUN_INSPECTION_DIR}/export.json" |
  while IFS=$'\t' read -r attempt url; do
    mkdir -p "${RUN_INSPECTION_DIR}/attempts/${attempt}"
    curl --fail --silent --show-error "$url" \
      -o "${RUN_INSPECTION_DIR}/attempt-${attempt}.zip"
    unzip -q "${RUN_INSPECTION_DIR}/attempt-${attempt}.zip" \
      -d "${RUN_INSPECTION_DIR}/attempts/${attempt}"
  done
```

Inspect `metadata.json`, each attempt's `metadata.json`, screenshots, DOM
snapshots, console logs, HAR logs, video, resource usage, and crash archives.
Keep attempt numbers intact. Do not commit the export response, run artifacts,
signed URLs, credentials, or customer data. Remove the temporary directory when
the investigation is complete.

## Background

### Test run result structure

When momentic tests are run via the CLI, the results are stored in a "run group". The data for this run group is stored in a single directory within the momentic project. By default, the directory is called `test-results`, but can be changed in momentic project settings or on a single run of a run group. The run group results folder has the following structure:

```
test-results/
├── metadata.json         data about the run group, including git metadata and timing info.
└── runs/                 On zip for each test run in the run group.
    ├── <runId_1>.zip         a zipped run directory containing data about this specific test run.  Follows the structure described below.
    └── <runId_2>.zip
```

When unzipped, run directories have the following structure:

```
<runId>/
├── metadata.json           run-level metadata.
└── attempts/<n>/           one folder per attempt (1-based n).
    ├── metadata.json       attempt outcome and step results.
    ├── console.json        optional browser console output.
    └── assets/
        ├── <snapshotId>.jpeg     before/after screenshot for each step (see attempt metadata.json for snapshot ID).
        ├── <snapshotId>.html     before/after DOM snapshot for each step (see attempt metadata.json for snapshot ID).
        ├── har-pages.log         HAR pages (ndjson).
        ├── har-entries.log       HAR network entries (ndjson).
        ├── resource-usage.ndjson CPU/memory samples taken during the attempt.
        ├── <videoName>           video recording (when video recording is enabled).
        └── browser-crash.zip     browser crash dump (only present on crash).
```

When getting run results via the momentic MCP, tools such as `momentic_get_run` will return links to the MCP working directory (default `.momentic-mcp`). This directory will contain unzipped run result folders, following the structure above, named `run-result-<runId>`.

### Element locators

Certain step types that interact with elements have a "target" property, or **locator**, that specifies which element the step should interact with.

#### Locator caches

Locators identify elements by sending the page state html/xml to an llm as well as a screenshot. The llm identifies which element on the page the user is referring to. Momentic will attempt to "cache" the answer from the llm so that future runs don't require AI calls. On future runs, the page state is checked against the cached element to determine whether the element is still usable, or the page has changed enough such that another AI call is required.

A locator cache can bust for a variety of reasons:

- the element description has changed, in which case we'll always bust the cache
- the cached element could not be located in the current page state
- the cached element was located in the page state, but fails certain checks specified on the cache entry, such as requiring a certain position, shape, or content.

You can find the `cacheBustReason` on the `trace` property in the results for a given step, but only when you explicitly request `includeTrace=true`. The `cache` property is also listed on the results, showing the full cache saved for that element.

#### Identifying bad caches

Sometimes the element that was cached is not the element that the user intended to target. This can cause failures or unexpected behaviors in tests. In these cases, it helps to verify exactly why the wrong cache was saved in the first place. Only request `includeTrace=true` for these cache-debugging cases or when you suspect incorrect Momentic execution data. Use the `runId` property of the `targetUpdateLoggerTags` on the incorrect cache to get the details of the original run, calling `momentic_get_run` with this runId. This will return the run where the cache target was updated.

### Module caching

Cached modules skip executing their steps when the module cache key and resolved inputs are unchanged, and reuse the cached return value from the module's last step.

Authentication modules can also save and restore browser auth state from the module cache, including cookies, localStorage, and IndexedDB. They may use a page-content check after restoring auth state to decide whether the cache is still valid.

### File uploads

A file upload step prepares one file for the next native file picker, so it must run before the action that opens the picker.

Sources can be remote URLs, `file://` references to earlier downloads, CLI-local paths, or uploaded user files. The step can also override the presented filename, and Momentic wires the prepared file into the browser's file chooser handling.

## Using past runs

Past runs are comparison evidence, not a substitute for reconstructing the current run. Use them when the current run does not answer:

- When did this test start failing?
- What differed vs the last passing run?
- Did the same action behave differently on an earlier run?
- Is this a test weakness, an application change, a real application bug, or a temporary slowdown?

Use step results and screenshots on past runs to answer these questions. Do NOT rely only on summaries from `momentic_get_run` or `momentic_list_runs` to understand what happened in a test run. Look at the specific run details, including step results and screenshots, before citing a past run as evidence.

When looking at past runs, use the following workflow:

1. Call the `momentic_list_runs` tool to identify the runs you want more detail on. Always pass `gitBranchName` when it exists on the run in question. Omit it when you need runs from other branches.
2. Call `momentic_get_run` for that specific run to get the run details.
3. Call `momentic_get_step_result` for the same step/container or closest equivalent you are comparing, especially for screenshots.

When past runs are irrelevant because the current run already proves the root cause, say that briefly instead of forcing historical evidence.

### Multi-attempt runs

When `momentic_list_runs` shows a passing run with `attempts > 1`, treat it as a partial failure worth investigating, not a clean passing run. Use the `attemptNumber` parameter to retrieve earlier failed attempt results for that run to understand what was going wrong before the retry succeeded.

### Flakiness and intermittent failures

- Call a test flaky only when the same app and test behavior fails intermittently.
  One failure is insufficient; rule out application and test changes using run
  evidence before attributing the pattern to flakiness.

### Test temporality

- Any past results may not necessarily match today’s test file. The test may have changed, meaning the result was on a different version of the test.
- You can call `get_test_steps_for_run` to help you determine if the test itself changed between runs, although note that this tool returns a _summary_ of each test step. If you suspect that specific details on certain steps have changed between test runs, full step details are included in the response from `momentic_get_step_result`; only request `includeTrace=true` when those fields and screenshots still are not enough.

## Common failure modes to watch for

- A setup module appears to pass but leaves the wrong page, overlay, filter, search, selected row, or side peek open. Classify from the step/container that left the bad postcondition, not only from the next step that failed.
- A click reports success and targets the intended element, but the application does not transition to the intended state. Verify the post-state; do not assume the click worked because the locator was correct.
- A weak global assertion such as "page contains X" passes because unrelated text on the page matches. The next step may then type or click in the wrong context.
- A type step without a specific target can silently type nowhere useful if the preceding action failed to focus the intended field.
- A locator or cache can be technically valid but semantically wrong. Check the interacted element and, for bad caches, inspect the original cache-update run from `targetUpdateLoggerTags.runId`.
- A recovered step can hide the first failure. Inspect failed child steps inside recovered modules and compare the recovered final state to the next step's expected baseline.
- A timeout is not automatically `INFRA`. First rule out missing data, wrong page state, changed app flow, bad locator/assertion, and setup failure.

## Identifying related vs unrelated issues

- Determine intent from the test name, description, and simplified steps. Treat
  failures outside that intent, including most setup/teardown failures, as
  unrelated. Relatedness qualifies bugs and changes; it does not change an
  `INFRA` failure into another category.

## Bug vs change

- Bug: something very clearly went wrong when it should not have, such as an error message appearing. It is obvious just by looking at a single step or two that this is a bug.
- Change: a clear change in the application behavior that you can prove through screenshots.

## Recoverability

Along with the category, determine one recoverability value:

- `RECOVERABLE` — The failure can be automatically fixed by updating the test itself so that future runs pass.
  - Examples: an application change that requires a test update; vague locators or assertions that can be rewritten to pass stably.
- `ONE_TIME_RECOVERABLE` — The failure can be recovered for this specific run without persisting a test change.
  - Examples: a random modal that can be dismissed without affecting test purpose; a temporary delay where waiting or retrying would likely succeed.
- `NON_RECOVERABLE` — The failure cannot be automatically addressed and requires manual intervention.
  - Examples: missing credentials; missing local files required for upload; outages likely caused by third-party systems where test steps cannot fix the issue.

## Formal classification output

- Exactly one category id — no new labels, no multi-label.
- Ground your decision in data. Be sure that you've fully investigated the run before assigning the category.
- Prefer human-readable references over UUIDs when the step/module can be identified colloquially: `module create-subpage-under-parent-page`, `the last invocation of module <name>`, `substep 4 (0-indexed)`, `the failed setup assertion`, etc. Tool calls still require exact IDs, but final reasoning should be readable.
- When referencing past runs in final output, use clickable Momentic URLs rather than bare UUIDs: `https://app.momentic.ai/runs/<runId>`. Do not shorten UUIDs inside those URLs.
- The reasoning must include the earliest divergent step/container and the broken postcondition it produced, not just the final failing step.

```text
Reasoning: <a few sentences tied to the earliest divergence, screenshots/traces, past runs if used, and test intent>
Category: <one id from the list>
Recoverable: <RECOVERABLE | ONE_TIME_RECOVERABLE | NON_RECOVERABLE>
Confidence: <high | medium | low>
```

Confidence levels:

- `high` — direct evidence, such as a clear screenshot of a label change or crash
- `medium` — strong inference from multiple signals but no single conclusive screenshot or data point
- `low` — ambiguous evidence; the classification required significant inference or the root cause is unclear

## Category ids

Use these strings verbatim:

- `NO_FAILURE` — The run had no failures; all attempts passed.
- `APPLICATION_CHANGE` — The test is out of date because the application's flow or UI has changed; updating the test to match the new behavior would permanently fix the failure.
- `BUG` — Something clearly went wrong in the application that shouldn't have, such as an error message appearing or expected content failing to render.
- `TEST_AUTHORSHIP` — The test can be permanently updated to prevent the failure while still validating its original intent, and you can recommend a specific authorship change such as adding or modifying a step, rewriting a vague assertion, or making a locator description more specific. If you cannot name a concrete change, choose a different category. Timeouts, slow page loads, and any failure whose recommended fix is to "wait longer" or to increase a timeout are NOT authorship issues — those are `INFRA`, even when the test could technically be edited to wait longer.
  - Examples: race conditions that can be fixed by adding or modifying steps **other than** waits/timeouts (e.g. replacing a "type with pressEnter" step with an explicit "select from list" step so the test no longer races the application); vague assertions or locator descriptions that can be rewritten to be more specific.
- `TEST_SETUP` — Missing test data or files necessary to run the test, where the fix requires user action outside of the test itself.
  - Examples: missing file for a file upload step; missing or incorrect credentials needed by the test.
- `INFRA` — The failure was unrelated to the application or application code and was caused by an infrastructure outage, long load times, or some other issue due to outside factors.
  - Examples: browser crash; high resource usage; rate limiting; a step or assertion that timed out waiting for the page or application to reach a slow-but-eventual state.
- `MOMENTIC_ISSUE` — Some issue occurred with the execution of the test or Momentic data was incorrect (e.g. cache is wrong, global locator redirect did something weird, AI hallucinations).
  - Examples: unexpected behavior when viewing the run trace; the AI clearly misread or hallucinated data that is unambiguous in the screenshot, and no reasonable test alternative exists to avoid the AI step.
- `OTHER` — The failure doesn't fit any of the other categories.

---

Generated for momentic 3.60.2 (skills 1790392498). Run `npx momentic skills` after you upgrade momentic.
