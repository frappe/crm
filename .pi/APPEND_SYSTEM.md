# CRM project — behavioral extensions

## Ask before deciding

For anything where multiple valid approaches exist, present the options with
tradeoffs and wait for a decision before implementing. This applies especially to:

- Prop/composable/API naming
- Breaking changes to script API (form script authors are users)
- Structural refactors (FieldLayout, Grid, Field inject chains)
- New options on formDialog() or setFieldProperty

The PLAN.md design principles are the source of truth for this project's direction.

## Docs discipline

When completing a feature or fixing a meaningful bug:

- Move completed phases from PLAN.md → ARCHIVE.md
- Update SPEC.md if the stable API surface changed
- Update feats/ guides if user-facing behavior changed
- Do not leave PLAN.md describing completed work

## Test requirement

Run `cd frontend && yarn test:run` after any change to `src/utils/`. All 118 tests
must pass before committing. If adding new pure logic to `src/utils/`, add unit tests
alongside it.

## Pre-commit hooks

The repo runs prettier + eslint + oxlint via pre-commit. If a hook modifies a file,
`git add` the modified file and commit again — do not skip hooks.

## Form Script API is user-facing

`setFieldProperty`, `formDialog`, helpers, and lifecycle hook names are used by CRM
administrators in Form Script records. Treat them as a public API:

- No silent renames
- Additive changes only (new options, new helpers)
- Deprecate with a warning before removing anything
