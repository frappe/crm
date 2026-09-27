---
name: momentic-test
description: Create, run, and maintain Momentic browser E2E tests and modules stored as *.test.yaml and *.module.yaml files.
---

# Momentic model

Momentic turns structured natural language into browser automation using forked
Playwright, CDP, and custom agents. Interactive steps resolve natural-language
targets, assertions can use multimodal models, and AI actions can complete
broader goals.

# Project files and formats

Tests use `*.test.yaml`; reusable modules use `*.module.yaml`. Test IDs live in
the test file's `id` field. Check `momentic.config.yaml` and test-level metadata
before assuming project defaults apply.

`fileType: momentic/test/v2` and `fileType: momentic/module/v2` identify v2
files. Treat missing or different `fileType` as deprecated v1. Never edit v1
YAML directly; persist changes through `momentic_test_splice_steps`.

A v2 test selects its environment with `defaultEnv`, and `--env <name>`
overrides it. There is no fallback to the only environment in the config. The
base URL comes from `--url-override`, then the test's own `url`, then
`env.BASE_URL`, so a test that sets `url` keeps it in every environment. With
no base URL the run fails: "Cannot run test with no base URL and no BASE_URL
variable defined in its environment".

V2 can reference modules, JavaScript, and auth state with relative paths. Paths
resolve from the YAML file containing the reference. Use `./...` or `../...`,
never absolute paths or `~`. Before moving, renaming, or deleting a referenced
file, grep its path and update or remove every reference. Do not add internal or
generated fields to v2 YAML.

# Choose the workflow

Prefer these compact workflows unless the user requests something else:

- **Known v2 change:** inspect nearby patterns -> edit YAML -> lint when syntax
  or references are uncertain -> reload or restart if validating -> run the
  relevant range. This is fastest and produces the clearest reviewable diff.
- **V1, unknown UI, or interactive validation:** start MCP session -> run any
  prerequisites -> preview a logical checkpoint -> splice it -> validate the
  saved range -> terminate. This grounds each edit in the live app without
  repeatedly running the whole test.
- **New test:** create with `momentic_test_create` -> author a known v2 sequence
  in one YAML edit, or use MCP step-by-step when discovery is needed.
  `momentic_session_start` only opens an existing test.

Use MCP as the default interactive interface: it returns structured results,
screenshots, artifacts, step refs, and pollable execution. Preview and run tools
wait 30 seconds by default, then return a `stepRunnerId` while work continues.
Leave `timeoutSeconds` unset for most calls, especially single preset steps.
Set it below 30 seconds only when the coding agent's tool-call timeout is
shorter. Raise it only to wait longer within a larger tool-call timeout; poll
returned handles with `momentic_poll_runner`.

Polling has a separate `timeoutSeconds` (default 0, maximum 30). Pass the
returned `stepRunnerId` and use a nonzero wait within the coding agent's
tool-call timeout instead of repeatedly polling without a wait.

# Before editing

Confirm the test goal, user-visible success criteria, start environment, auth,
and env requirements. Ask before previewing or running any step or AI Action
that may submit, purchase, delete, send, create, or cause another non-idempotent
side effect. If approved, execute it at most once. Also ask before editing a
shared module, restarting a long flow, or running an expensive full test.

# Authoring rules

- Prefer natural-language targets. Use selectors or coordinates only when the
  AI cannot see the target or the user requires selector-level precision.
- Use native Momentic steps for browser actions and checks. See **JavaScript**
  under **Test execution behavior** for the exceptions.
- Do not add initial navigation; a session starts at the test's base URL.
- Keep assertions minimal and user-driven. After navigation or a material state
  change, validate the contract before dependent actions.
- Prefer `waitForUrl` for URL contracts, page/element checks for stable text or
  structure, and AI assertions for semantic visual state.
- Prefer AI Action V3 for new tests unless the exact interaction sequence is
  part of the contract.
- Do not add optional or default-valued fields unless correctness requires them.
- Keep changes narrow. Preserve unrelated values, comments, ordering, and step
  style. Do not weaken a test to hide a broken app or service.
- Preserve the existing `before` / `steps` / `after` structure unless the test
  intent requires a change.

## AI Action V3

AI Action V3 takes a natural-language goal and determines the browser steps.

- **Cached by default:** save and replay a successful flow, self-healing failed
  replay steps. Use for repeatable flows.
- **Uncached:** run the agent fresh each time. Set `cache: false` in v2 or use
  `--disable-cache` with `AI_ACTION_DYNAMIC`. Prefer this for chats, agentic
  workflows, exploratory tests, and other dynamic or nondeterministic behavior.

Treat “make sure you can do X” as goal-based testing unless the user specifies a
route. Use granular steps when controls, order, intermediate assertions,
deterministic replay, speed, or a risky side effect is itself under test. Keep
existing granular tests granular unless asked to change strategy.

# Test execution behavior

## Cache and memory

Momentic caches resolved selectors, text, coordinates, and other metadata so
most runs avoid repeated AI calls. AI assertions may also reuse past-result
memory. Stale cache or memory can explain a fast wrong-element match or a
repeated borderline verdict.

Cache is scoped by git metadata, including branch. Protected branches read cache
but do not write it unless `--save-cache` is used or `CI` is set.

- Change a granular step description when its intent changes. Never add
  `DANGEROUS_FORCE_DYNAMIC` or `--disable-cache` to locator steps; built-in cache
  validation handles changing content.
- Carry a successful preview's `CacheId` into the exact step being spliced.
- Reword an assertion when old memory no longer matches its intended condition.
- For AI Action V3 cache behavior, see **AI Action V3** above.

## Readiness and timing

Smart waiting runs before targeting steps and defaults to five seconds. Within
that window, do not add sleeps. For longer or semantic readiness, wait for a URL
or use a page, element, or AI check that describes the required positive state.
Checks retry until their timeout; increase that timeout instead of polling the
UI with JavaScript. See the
[browser configuration](https://momentic.ai/docs/configuration/browser) for
project-wide timing settings.

## Test context

Each run has a test-scoped `env` that persists across steps and modules.

- In v2, save returned values with `saveAs`; in MCP step strings, use
  `--env-key`. Use `setVariable(name, value)` in JavaScript when saving several
  values.
- Use `env.NAME` in JavaScript and module input expressions. Use
  `{{ env.NAME }}` in string fields, but not inside JavaScript source.
- Module inputs are JavaScript fragments stored as strings. Quote literal
  strings and use `env.X` for variables.

## JavaScript

Use native click, type, hover, wait, and check steps for browser behavior. They
retain Momentic's smart waiting, cache, traces, and retries. Do not use browser
JavaScript to click or type, and do not poll the UI when a check can retry until
its timeout.

Use Node JavaScript for test setup, data generation, APIs, databases,
OTP/email/SMS, and Momentic helpers. Use Browser JavaScript to access
`window`, `document`, client-side state, or inject page scripts when no native
step expresses the operation. Keep one-off code short and follow nearby project
conventions for reusable v2 scripts. See the
[JavaScript guide](https://momentic.ai/docs/integrations/javascript) for runtime
APIs and timeout details.

# Working with v2 YAML

V2 is human-editable. Tests use `before`, `steps`, and `after`; modules use
`steps`. Each step has one command key, with options nested beneath it. Durations
are milliseconds, and step IDs are not stored in YAML.

Make the smallest edit and match nearby syntax. If syntax is unclear, consult
the generated v2 format reference at
`infra/scripts/v2-json-schema/build/v2-format-reference.md` when working in the
Momentic monorepo, or https://static.momentic.ai/v2-format-reference.md in an
installed skill. Run `npx momentic lint` when
schema or file-reference risk warrants it; `momentic app` and `momentic run`
also lint automatically.

After a disk edit, reload the active MCP test if the tool is available;
otherwise terminate and restart the session. `momentic_test_get` reads persisted
state but does not refresh an active session unless its description says so.

# MCP browser workflow

Use the tool descriptions and the Step Authoring Guide returned by session start
for current arguments and step syntax. Do not duplicate that reference material
from this skill.

## Start and fetch context

Do not call context tools as session-start boilerplate. Use them on demand and
follow their descriptions, especially when they offer filters or return large
project data.

- If the test ID is known, start `momentic_session_start` by itself. Its Test
  Content provides the active steps and runnable IDs.
- Use `momentic_get_artifacts` only to discover project paths, tests, modules, or
  environments that are not already known. Avoid redundant refreshes.
- Use `momentic_test_get` to inspect persisted state before starting, or to read
  a different test. Prefer active session and splice responses afterward.
- Use filtered `momentic_get_environment_variables` only when a step needs env
  data that is not already known.
- Use `momentic_module_recommend` -> `momentic_module_get` only when evaluating
  reuse; recommendation invokes AI and is not required to start a session.

V2 YAML has no runnable step IDs. Use IDs returned by session start or later
splice responses.

Only one browser operation may run per session. Do not issue concurrent preview,
run, state, or splice operations against the same session.

## Preview -> splice -> validate

1. For mid-test work, run through the preceding step once and keep the same
   session. This avoids authoring against the wrong page state.
2. Preview forward in logical checkpoints such as login complete, form ready,
   or submission complete. Checkpoints make the browser state reusable and keep
   persistence calls reviewable.
3. Use `momentic_preview_steps` for adjacent steps. It supports the same preset,
   AI Action, and module steps as `momentic_preview_step`.
4. Read the returned screenshot first. Request browser state only when the image
   lacks enough targeting or diagnostic context; request it again once if the
   page may still be settling.
5. Splice the successful checkpoint. Attach each returned `CacheId` only to its
   exact step; cacheless steps are normal. Read the splice response immediately
   for the active step refs.
6. Run the next dependent saved step or range. If any preview or run returns a
   `stepRunnerId`, poll it instead of starting another browser operation.
7. Before finishing, when safe, run the smallest saved range covering the
   prerequisites, changed step, and next dependent contract. Reset first when
   accumulated state could mask a failure.
8. Terminate the session when finished.

Batch obvious low-risk fields. Preview uncertain locators individually. For
submit, purchase, delete, send, or other non-idempotent actions, preview setup,
splice the checkpoint, then run the approved saved action at most once.

Do not reset between routine edits. For nested steps, use the parent chain
returned by the active session or splice response.

# Modules

For a logical flow of roughly four or more reusable steps, check
`momentic_module_recommend` -> `momentic_module_get` -> reuse or inline. Reuse
reduces duplicated setup and keeps tests focused on their unique contract.

Modules cannot contain modules. Ask before changing a shared module. Respect its
declared parameters, defaults, and enum values; module inputs are JavaScript
fragments, not `{{ }}` templates.

# Troubleshooting

## Page state and timing

- Wrong or stale page: inspect the latest screenshot or session state; retry
  state capture once if the page is settling.
- Slow readiness at one checkpoint: add the narrowest page, element, or AI check,
  or increase the existing check's timeout. Checks already retry; do not poll
  with JavaScript.
- Broadly slow targeting across the project: consider increasing
  `browser.smartWaitingTimeoutMs`. Do not use it to mask one slow assertion.
- Long jobs or uploads: check for a stable positive result with an appropriate
  timeout, not a sleep.
- Drifted session: rerun the required saved range with `resetSession: true`.

## Browser and host resource pressure

Retry or reset once after a browser, CDP, page-load, screenshot, or snapshot
timeout. If it persists or affects several browser tools, stop changing the
test. Do not hide resource pressure with waits, weaker assertions, cache flags,
or repeated browser calls.

Signals include an unresponsive page, document-tree or page-execution timeout,
empty HTML snapshot, browser or inspector crash, and `data-momentic-id` timeout.
A page-load timeout alone may instead indicate the app or network.

Inspect CPU, memory, and top processes with available host tools. Check the
browser, Momentic, app server, compiler/bundler, database, and unrelated
workloads. For completed runs, correlate with
`attempts/<n>/assets/resource-usage.ndjson` when present.

Report the error, step, URL, retry result, resource pressure, largest consumers,
and supported cause. If evidence cannot distinguish the host, app, services, or
Momentic, say so.

## Targeting and assertions

- Element absent: debug the prerequisite. Element visible but not found: use a
  stable description based on visible text, role, and nearby context.
- Fast wrong-element match: consider stale cache, then correct the description.
- In normal mode, errors that an element is hidden, disabled, detached, covered,
  moving, or outside the viewport originate in Playwright's actionability
  enforcement, which Momentic surfaces; they are not failures in Momentic's
  locator AI. Fix the page state or prerequisite. Use force only when bypassing
  actionability is part of the intended behavior.
- For controls that intentionally cannot satisfy Playwright actionability, such
  as some rich-text editors, `browser.visualActions: true` uses coordinate-based
  actions instead. It avoids those checks but also gives up their stability
  guarantees. See [Visual actions](https://momentic.ai/docs/configuration/browser#browser-visualactions).
- Use quoted text only when the exact text must appear; otherwise describe
  meaning. Make assertions concrete about region, object, count, or state.
- Use `assertVisually` when the condition is visual and fully inside the
  current viewport, e.g. an event block sitting in the 11:30–12:00 row of a
  calendar grid, or a detail inside a video frame or canvas drawing. Scroll the
  target into view if necessary before calling it; otherwise use `assert`.
- Assert stable final state with step assertions. For brief toasts or
  change-over-time comparisons, use video-backed
  [run assertions](https://momentic.ai/docs/core-concepts/writing-assertions#run-assertions).

## Format and data

- V2 load failure: lint the file and check relative references.
- Module failure: re-check parameters, defaults, enums, and input expressions.
- Missing env value: verify the producing save and `env.X` versus
  `{{ env.X }}` at the consumer.
- JavaScript failure: verify Node versus Browser context.

After about three attempts at the same failure, stop and ask the user for
direction.

---

Generated for momentic 3.60.2 (skills 1790392498). Run `npx momentic skills` after you upgrade momentic.
