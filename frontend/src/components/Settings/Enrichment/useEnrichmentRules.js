import { call, createListResource } from 'frappe-ui'
import { computed, reactive, ref } from 'vue'

// One rule_type's worth of the Rules tab: the list, the pattern child rows the
// list call can't bring back, and the editable rows built from both. Social and
// Industry rules differ only in the fields on a row and in the document each one
// sends -- the loading, the dirty tracking, and the insert/update/delete plumbing
// the header Save runs are the same, so they live here once.
//
// Nothing is written while the admin edits. Every row keeps what the server last
// confirmed next to what is in its boxes; Save validates every changed row, then
// sends the removed ones as deletes, the edited ones as updates and the new ones
// as inserts.
//
// The caller supplies the shape of a row (buildRow / newRow), what counts as an
// edit (isRowChanged), the per-row validation, and the documents to send.
export function useEnrichmentRules({
  ruleType,
  fields = [],
  buildRow,
  newRow,
  isRowChanged,
  validateRow,
  toInsert,
  toUpdate,
  clearErrors,
  messages,
}) {
  // order_by matches the doctype's own sort (modified desc), so the list reads
  // the same here as it does in Desk. There is no pager on the section, so every
  // rule of the type is loaded -- a rule left off the page could not be edited
  // or deleted here at all.
  const resource = createListResource({
    doctype: 'CRM Enrichment Rule',
    filters: { rule_type: ruleType },
    fields: ['name', 'rule_name', 'enabled', ...fields],
    orderBy: 'modified desc',
    pageLength: 99999,
  })

  // rule name -> the rule's pattern child rows, as stored
  const patterns = reactive({})
  const patternsLoading = ref(false)
  const patternsError = ref(null)

  // The spinner stands in for the whole section, so it only belongs on the first
  // load. The reload after a save leaves the rows on screen and swaps them when
  // the new ones land.
  const loadedOnce = ref(false)

  const loading = computed(
    () => !loadedOnce.value && (resource.list.loading || patternsLoading.value),
  )

  const error = computed(() => resource.list.error || patternsError.value)

  const saving = ref(false)

  // One editable row per stored rule, rebuilt whenever the list reloads.
  const savedRows = ref([])

  // Rows added by the section's "+ Add" button that have nothing behind them
  // yet. They live apart from savedRows so a reload rebuilds the stored rows
  // without sweeping away a new one.
  const localRows = ref([])

  let localRowSeq = 0

  // A stored rule the admin deleted stays in savedRows, flagged, until Save
  // actually deletes it -- so the delete can be undone by not saving, and a
  // failed delete can put the row back where it was.
  const rows = computed(() => [
    ...savedRows.value.filter((row) => !row.removed),
    ...localRows.value,
  ])

  // The status switch in the row's menu is the one edit every rule_type shares,
  // so it is tracked here rather than in each caller's isRowChanged.
  function isEnabledChanged(row) {
    return row.enabled !== row.savedEnabled
  }

  function isRowDirty(row) {
    if (!row.name || row.removed) return true
    return isRowChanged(row) || isEnabledChanged(row)
  }

  const dirtyRows = computed(() => [
    ...savedRows.value.filter(isRowDirty),
    ...localRows.value,
  ])

  // The list and every rule's patterns, awaited as one, so the reload after a
  // save has finished rebuilding the rows by the time Save reports back.
  async function load() {
    patternsError.value = null
    // resource.list.error carries the message for the section either way; the
    // catch only keeps a rethrown failure from becoming console noise.
    await resource.reload().catch(() => {})
    if (resource.list.error) {
      loadedOnce.value = true
      return false
    }
    return loadPatterns(resource.data || [])
  }

  // get_list never returns child tables, so every rule's patterns come from one
  // get_list on the child doctype itself (`parent` is what frappe checks the
  // read permission against), grouped back onto their rules here.
  async function loadPatterns(rules) {
    patternsLoading.value = true
    try {
      const patternRows = rules.length
        ? await call('frappe.client.get_list', {
            doctype: 'CRM Enrichment Rule Pattern',
            parent: 'CRM Enrichment Rule',
            filters: {
              parenttype: 'CRM Enrichment Rule',
              parentfield: 'patterns',
              parent: ['in', rules.map((rule) => rule.name)],
            },
            fields: ['name', 'parent', 'pattern', 'is_regex', 'idx'],
            order_by: 'idx asc',
            limit_page_length: 0,
          })
        : []
      const byRule = {}
      patternRows.forEach((row) => {
        ;(byRule[row.parent] ||= []).push(row)
      })
      rules.forEach((rule) => {
        patterns[rule.name] = byRule[rule.name] || []
      })
      buildRows(rules)
      return true
    } catch (err) {
      // A row with no patterns loaded would read as an empty pattern box, and
      // saving that box would wipe the stored patterns -- so no rows are built
      // from this load. Rows from an earlier, complete load stay on screen.
      patternsError.value = err
      return false
    } finally {
      patternsLoading.value = false
      loadedOnce.value = true
    }
  }

  function buildRows(rules) {
    // Every row is rebuilt from the reload, so whatever the admin still had in
    // flight on a row that survived is carried across: an edit that failed to
    // save, the error under it, a delete that didn't go through. A row Save just
    // wrote is not carried -- the server's copy is the truth now, even where it
    // differs from what was typed (a platform stored lowercased).
    const carried = new Map()
    savedRows.value.forEach((row) => {
      if (row.committed) return
      if (isRowDirty(row) || row.serverError) carried.set(row.name, row)
    })

    savedRows.value = rules.map((rule) => {
      const held = carried.get(rule.name)
      return reactive({
        key: rule.name,
        name: rule.name,
        ruleName: rule.rule_name,
        enabled: held ? held.enabled : Boolean(rule.enabled),
        savedEnabled: Boolean(rule.enabled),
        removed: held ? held.removed : false,
        serverError: held ? held.serverError : '',
        ...buildRow(rule, patterns[rule.name] || [], held),
      })
    })
  }

  function addRow() {
    localRows.value.push(
      reactive({
        key: `new-${(localRowSeq += 1)}`,
        name: null,
        ruleName: '',
        // Starts enabled; the menu's status switch can turn it off before the
        // first Save.
        enabled: true,
        savedEnabled: true,
        removed: false,
        serverError: '',
        ...newRow(),
      }),
    )
  }

  // A row that was never inserted is only on screen, so dropping it is a local
  // splice. A stored one is only flagged; Save does the delete.
  function deleteRow(row) {
    if (!row.name) {
      localRows.value = localRows.value.filter((other) => other !== row)
      return
    }
    row.removed = true
  }

  function toggleEnabled(row) {
    row.enabled = !row.enabled
    row.serverError = ''
  }

  // Every changed row is checked before anything is sent, so a Save either
  // starts with every row valid or doesn't start at all. `others` is every other
  // row still on screen, for the duplicate checks.
  function validate() {
    let valid = true
    rows.value.forEach((row) => {
      // A stored rule whose only edit is its status sends nothing but
      // `enabled`, so the fields it already had aren't held to the form's checks.
      if (row.name && !isRowChanged(row)) return
      clearErrors(row)
      row.serverError = ''
      const others = rows.value.filter((other) => other !== row)
      if (!validateRow(row, others)) valid = false
    })
    return valid
  }

  function isNameCollision(err) {
    return ['DuplicateEntryError', 'UniqueValidationError'].includes(
      err?.exc_type,
    )
  }

  // What the server said, in words an admin can act on. A unique rule_name
  // collision comes back as a DuplicateEntryError (insert) or a
  // UniqueValidationError (update) whose raw text names the column, not the
  // rule; anything else is passed through as the server wrote it.
  function serverMessage(err, ruleName, fallback) {
    if (isNameCollision(err)) {
      return __('A rule named "{0}" already exists', [ruleName])
    }
    return err?.messages?.[0] || fallback
  }

  async function runDelete(row) {
    try {
      await call('frappe.client.delete', {
        doctype: 'CRM Enrichment Rule',
        name: row.name,
      })
      delete patterns[row.name]
      return true
    } catch (err) {
      // Back on screen, so the error has a row to sit under.
      row.removed = false
      row.serverError = serverMessage(err, row.ruleName, messages.deleteError)
      return false
    }
  }

  // frappe.client.set_value loads the rule on the server, lays only the given
  // fields over it and saves -- so a field the form doesn't send (an Industry
  // rule's weight, match_scope) keeps whatever it already had. The rule is
  // re-read first so the patterns the form doesn't show are the ones stored now,
  // not the ones stored when the page loaded. A status-only change skips all of
  // that and sends just `enabled`. Resolves to what runUpdates needs to untangle
  // renames: whether it went through, the rule_name it asked for (null when the
  // name isn't moving) and whether another rule holding that name turned it away.
  async function runUpdate(row) {
    let values = {}
    try {
      if (isRowChanged(row)) {
        const doc = await call('frappe.client.get', {
          doctype: 'CRM Enrichment Rule',
          name: row.name,
        })
        values = await toUpdate(row, doc)
      }
      if (isEnabledChanged(row)) values.enabled = row.enabled ? 1 : 0
      await call('frappe.client.set_value', {
        doctype: 'CRM Enrichment Rule',
        name: row.name,
        fieldname: values,
      })
      row.committed = true
      return { ok: true }
    } catch (err) {
      row.serverError = serverMessage(
        err,
        values?.rule_name || row.ruleName,
        messages.updateError,
      )
      return {
        ok: false,
        target: values?.rule_name || null,
        collided: isNameCollision(err),
      }
    }
  }

  // Rule and patterns go in as one document, so a failed insert leaves nothing
  // half-created behind.
  async function runInsert(row) {
    let doc
    try {
      doc = await toInsert(row)
      await call('frappe.client.insert', {
        doc: {
          doctype: 'CRM Enrichment Rule',
          rule_type: ruleType,
          ...doc,
          enabled: row.enabled ? 1 : 0,
        },
      })
      localRows.value = localRows.value.filter((other) => other !== row)
      return true
    } catch (err) {
      row.serverError = serverMessage(
        err,
        doc?.rule_name || '',
        messages.insertError,
      )
      return false
    }
  }

  // A pass where every update failed is stuck unless the rows are waiting on
  // each other in a ring: X waits on Y when X was refused the name Y holds.
  // Names are unique, so each row waits on at most one other, and following the
  // waits from any row either runs out -- the name belongs to a rule outside
  // this Save, or to a row failing for another reason, a real duplicate -- or
  // comes back round. Returns a row on the ring, or null when there is none.
  // Compared lowercased, as the unique index does.
  function findRenameCycle(failed, held) {
    const holder = new Map()
    failed.forEach(({ row }) => holder.set(held.get(row).toLowerCase(), row))

    const waitsOn = new Map()
    failed.forEach(({ row, target, collided }) => {
      if (!collided || !target) return
      const other = holder.get(target.toLowerCase())
      if (other && other !== row) waitsOn.set(row, other)
    })

    for (const { row: start } of failed) {
      const seen = new Set()
      let row = start
      while (row && !seen.has(row)) {
        seen.add(row)
        row = waitsOn.get(row)
      }
      // The first row reached twice is on the ring, not just leading into it.
      if (row) return row
    }
    return null
  }

  function setRuleName(row, ruleName) {
    return call('frappe.client.set_value', {
      doctype: 'CRM Enrichment Rule',
      name: row.name,
      fieldname: { rule_name: ruleName },
    })
  }

  // Updates can hand rule_names along a chain (A takes B's name while B moves to
  // C), and rule_name is unique -- so they go one at a time, and any that failed
  // are tried again after the rest. When a pass frees nothing, a ring of renames
  // (A <-> B, A -> B -> C -> A) is broken by parking one row on it under a
  // placeholder no one else can want, which frees its name for the row waiting
  // on it; the ring then unwinds like a chain. No ring means a real collision,
  // and it stops there with the message under the row. Each row is parked at
  // most once, so this always ends.
  async function runUpdates(rows) {
    // rule_name each row holds on the server right now.
    const held = new Map(rows.map((row) => [row, row.ruleName]))
    const parked = new Set()
    let pending = rows
    while (pending.length) {
      const failed = []
      for (const row of pending) {
        const result = await runUpdate(row)
        if (!result.ok) failed.push({ row, ...result })
      }
      if (failed.length === pending.length) {
        const row = findRenameCycle(failed, held)
        if (!row || parked.has(row)) break
        // Not run through __(): rule_name is stored data.
        const placeholder = `${row.ruleName} (renaming ${row.name})`
        try {
          await setRuleName(row, placeholder)
        } catch (err) {
          row.serverError = serverMessage(
            err,
            row.ruleName,
            messages.updateError,
          )
          break
        }
        held.set(row, placeholder)
        parked.add(row)
      }
      failed.forEach(({ row }) => (row.serverError = ''))
      pending = failed.map(({ row }) => row)
    }

    // A parked row whose own update never went through gets its name back, so
    // no placeholder is left behind. Best effort: if the row that was waiting on
    // it has already taken that name, the placeholder stays, the row keeps its
    // edit and error through the reload, and the next Save moves it on.
    for (const row of pending) {
      if (!parked.has(row)) continue
      try {
        await setRuleName(row, row.ruleName)
      } catch {
        // Left under the placeholder; see above.
      }
    }
    return !pending.length
  }

  // Deletes go first, so a rule removed and re-added under the same name in one
  // Save frees its rule_name before the insert asks for it; then updates, then
  // inserts. Resolves true only when every request succeeded -- a row that
  // failed stays changed, with its error under it, so it is still pending.
  async function save() {
    const removed = savedRows.value.filter((row) => row.removed)
    const updated = savedRows.value.filter(
      (row) => !row.removed && (isRowChanged(row) || isEnabledChanged(row)),
    )
    const inserted = [...localRows.value]

    if (!removed.length && !updated.length && !inserted.length) return true

    saving.value = true
    try {
      const results = [
        ...(await Promise.all(removed.map(runDelete))),
        await runUpdates(updated),
        ...(await Promise.all(inserted.map(runInsert))),
      ]

      // A row that saved cleanly takes the server's values on the rebuild; the
      // carried ones keep their edits and errors.
      const loaded = await load()

      return loaded && results.every(Boolean)
    } finally {
      saving.value = false
    }
  }

  load()

  return {
    resource,
    patterns,
    rows,
    dirtyRows,
    loading,
    error,
    saving,
    load,
    addRow,
    deleteRow,
    toggleEnabled,
    validate,
    save,
  }
}
