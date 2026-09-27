---
name: momentic-spec
description: Improve code correctness using Momentic specs in the feature development process
---

# Momentic spec-driven development

Write the expected product behavior as Momentic tests before implementing it.
The tests define the contract; do not make the tests fit the implementation.

## Non-negotiable sequence

1. Read repository guidance, `momentic.config.yaml`, and nearby tests and
   modules.
2. Identify and report the exact Momentic tests expected to be affected.
3. Create or modify those tests before changing product code.
4. Review the test diff as a product specification.
5. Only then implement the product change.
6. Use fast code-level checks while implementing; do not run Momentic after
   every edit or commit.
7. At a durable end-to-end checkpoint, prepare the required test state, enable
   the affected tests that should now pass, and ask whether to run the smallest
   affected set.

Do not begin product implementation until the intended test specifications are
on disk. If the user changes the requirement, update the spec first again.

## Choose the affected tests

- If the user names specific existing tests, start with those tests and keep the
  work focused on them. Expand the set only when repository evidence shows
  another test or shared module is directly affected.
- For new user-visible functionality, create the smallest new test or tests that
  describe the new user journey.
- For changed functionality, update the existing tests that describe the old
  behavior instead of adding duplicate coverage.
- Trace shared components and modules far enough to find real behavioral impact.
  Do not infer the affected set from filenames alone.
- If no Momentic test is affected, state why before making product changes. Do
  not make cosmetic test edits merely to produce a test diff.

Before editing product code, report each affected test path and whether it will
be added, changed, or left unchanged.

## Write the product specification first

The pre-implementation test should describe the requested outcome, even when the
current product cannot satisfy it yet.

- Preserve unrelated setup, teardown, data, assertions, and test intent.
- Do not weaken an assertion or preserve old behavior just because that matches
  the current implementation.
- Mark a test `disabled: true` when the implementation or a required dependency
  is not ready and the test is not expected to pass yet. Record why it is
  disabled and what must become true before enabling it.
- Do not use `disabled: true` merely because local credentials or a runnable
  environment are unavailable. That is a validation limitation, not necessarily
  an expected product failure.
- Keep the delta narrow. One changed product contract should normally have one
  focused test delta.

After writing the tests, summarize the expected failing or disabled behavior and
confirm the tests express the user's request before implementing it.

## Follow the codebase's testing language

Read nearby tests and follow their established conventions, including folder
placement, naming, modules, setup, data, and preference for AI checks, page
checks, or element checks. Apply baseline Momentic practices where the codebase
does not express a preference:

- Prefer native Momentic steps and natural-language targets over JavaScript or
  selectors.
- Keep assertions minimal and user-driven, with an explicit outcome check after
  a flexible action.
- Reuse existing modules for established flows such as authentication, setup,
  and navigation instead of recreating those flows inline.
- Do not reorganize or modify a shared module unless the requested product
  contract requires it. Account for every test that consumes a changed module.
- Never work around a real product failure by changing the test.

## Prefer AI action V3 for new specifications

For a new test, prefer an AI action V3 `act:` step when a high-level goal reads
more clearly as a product specification, especially for a long flow. Reuse
existing modules for known subflows and use `act:` for the new behavior rather
than hiding reusable setup inside one large goal.

Keep goals short, specific, and outcome-oriented. Pair an `act:` step with the
same assertion style used by nearby tests so the test verifies the result, not
only that the agent stopped.

AI action V3 caches generated steps after a successful run and self-heals when a
cached step misses:

- Keep caching enabled for stable product flows. Cached reruns are faster and
  more deterministic.
- Set `cache: false` only when the goal is inherently dynamic and should be
  re-derived every run, such as opening the most recent record or responding to
  frequently changing content.
- Do not disable cache to hide a stale or incorrect specification. When the
  intended behavior changes, update the goal or step description so its cache
  identity changes.
- When MCP preview returns a `CacheId` for a step that will be persisted, carry
  that cache ID into the saved step as required by the `momentic-test` skill.

## Run at durable end-to-end checkpoints

Momentic is true end-to-end validation, not the coding agent's inner feedback
loop. Do not run affected Momentic tests after every file edit, implementation
step, commit, or small refactor.

Editing and linting Momentic tests is allowed without confirmation. Before a
long-running Momentic test or suite, get confirmation based on the expected
duration and scope. If the duration is unknown, treat the run as long-running.
At a durable checkpoint:

1. Stop before a long-running Momentic run.
2. Tell the user exactly which tests or command you propose to run and, when
   known, the expected duration.
3. Ask the user to confirm whether to run them.
4. Run only after explicit confirmation. A direct request to run the specified
   tests counts as confirmation.

Confirmation covers only the proposed long-running run. Ask again before
another long-running Momentic execution unless the user explicitly authorized
iterative reruns. Short, focused runs may proceed without confirmation when
they are the normal validation step for the requested work. If the user declines
or does not confirm a long-running run, continue with non-Momentic checks and
report the tests as not run.

Use faster repository checks such as unit tests, typechecking, and linting while
building. Run Momentic when the app has reached a logical checkpoint that is
durable and usable through the real UI:

- For a small change, the checkpoint is usually the fully implemented change.
- For a multi-stage or extra-large feature, a checkpoint can be a completed,
  independently usable UI slice with all prerequisites needed for its affected
  test. Do not wait for the entire feature when a meaningful component is
  already testable end to end.
- Do not treat an arbitrary commit boundary as a checkpoint. The deciding
  question is whether a user can exercise the intended behavior through the
  product and observe the specified outcome.

At each checkpoint, propose the smallest affected test set. For a long-running
set, run it once after confirmation, diagnose failures, and make a coherent fix.
Request confirmation again before a long-running rerun unless iterative reruns
were already authorized. Rerun only when there is a reasonable expectation that
the end-to-end outcome changed. Keep future specifications disabled until their
checkpoint exists.

## Own the test data and application state

The coding agent implementing the product change is responsible for making the
checkpoint cleanly runnable. Before invoking Momentic, identify and establish
the required data, account state, feature flags, permissions, integrations, and
service state. Do not leave prerequisite creation for the browser agent to
improvise through unrelated UI flows.

Prefer existing test setup facilities. When the application lacks a reliable
way to create prerequisites, the coding agent is encouraged to build safe,
test-environment-only capabilities such as:

- idempotent endpoints or scripts that seed deterministic records and state
- fixtures and factories for realistic test data
- dedicated test accounts, roles, and authentication state
- test-only controls for feature flags or external-service substitutes
- scoped cleanup or unique-data mechanisms that prevent cross-run pollution

Any new test capability must be inaccessible in production, explicitly gated to
approved test environments, authenticated where appropriate, narrowly scoped,
and safe to call repeatedly. Never add a production backdoor, weaken production
authorization, or encode the behavior under test inside the seed mechanism.

Document the setup contract and either execute it before the Momentic run or
invoke it from the test's established setup section. The resulting test should
be repeatable from a clean environment without relying on accidental state from
a previous run.

## Edit and validate safely

Use the installed `momentic-test` skill for detailed authoring, format, and MCP
guidance.

- Edit v2 tests (`fileType: momentic/test/v2`) directly when the change is small
  and the intended steps are clear.
- Do not edit v1 test YAML directly. Use Momentic MCP tools to persist v1
  changes.
- Use MCP browser validation when UI discovery, live state, or locator behavior
  is uncertain.
- Lint the test specifications before product implementation when possible.
- At a durable end-to-end checkpoint, remove `disabled: true` from tests that
  are now expected to pass, establish their required state, and ask whether to
  run the smallest affected set.
- Leave a test disabled only when it is still intentionally not expected to
  pass, and include the reason and enablement condition in the handoff.

Run the repository's required product-code checks after implementation. In the
handoff, list the affected tests, their enabled or disabled state, the product
behavior implemented, and every validation that was or was not run.

---

Generated for momentic 3.60.2 (skills 1790392498). Run `npx momentic skills` after you upgrade momentic.
