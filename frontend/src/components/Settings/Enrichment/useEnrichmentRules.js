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
  // the same here as it does in Desk.
  const resource = createListResource({
    doctype: 'CRM Enrichment Rule',
    filters: { rule_type: ruleType },
    fields: ['name', 'rule_name', 'enabled', ...fields],
    orderBy: 'modified desc',
    pageLength: 99,
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

  function isRowDirty(row) {
    if (!row.name || row.removed) return true
    return isRowChanged(row)
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

  // get_list never returns child tables, so the patterns have to be fetched
  // separately: one frappe.client.get per rule, which is what the rest of
  // Settings already does for a single doc (see WorkflowAutomationDetail.vue). A
  // handful of rules means a handful of parallel requests -- cheaper than adding
  // a backend endpoint for a read-only list.
  async function loadPatterns(rules) {
    patternsLoading.value = true
    try {
      const docs = await Promise.all(
        rules.map((rule) =>
          call('frappe.client.get', {
            doctype: 'CRM Enrichment Rule',
            name: rule.name,
          }),
        ),
      )
      docs.forEach((doc) => {
        patterns[doc.name] = doc.patterns || []
      })
      buildRows(rules)
      return true
    } catch (err) {
      // A row with no patterns loaded would read as an empty pattern box, and
      // saving that box would wipe the stored patterns -- so drop the rows rather
      // than offer edits built on a half-loaded rule.
      savedRows.value = []
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
    // save, the error under it, a delete that didn't go through.
    const carried = new Map()
    savedRows.value.forEach((row) => {
      if (isRowDirty(row) || row.serverError) carried.set(row.name, row)
    })

    savedRows.value = rules.map((rule) => {
      const held = carried.get(rule.name)
      return reactive({
        key: rule.name,
        name: rule.name,
        ruleName: rule.rule_name,
        enabled: Boolean(rule.enabled),
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
        // Inserted as enabled, so the row shouldn't read as disabled while local.
        enabled: true,
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

  // Every changed row is checked before anything is sent, so a Save either
  // starts with every row valid or doesn't start at all. `others` is every other
  // row still on screen, for the duplicate checks.
  function validate() {
    let valid = true
    rows.value.forEach((row) => {
      if (!isRowDirty(row)) return
      clearErrors(row)
      row.serverError = ''
      const others = rows.value.filter((other) => other !== row)
      if (!validateRow(row, others)) valid = false
    })
    return valid
  }

  // What the server said, in words an admin can act on. A unique rule_name
  // collision comes back as a DuplicateEntryError (insert) or a
  // UniqueValidationError (update) whose raw text names the column, not the
  // rule; anything else is passed through as the server wrote it.
  function serverMessage(err, ruleName, fallback) {
    if (
      ['DuplicateEntryError', 'UniqueValidationError'].includes(err?.exc_type)
    ) {
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
  // not the ones stored when the page loaded.
  async function runUpdate(row) {
    let values
    try {
      const doc = await call('frappe.client.get', {
        doctype: 'CRM Enrichment Rule',
        name: row.name,
      })
      values = await toUpdate(row, doc)
      await call('frappe.client.set_value', {
        doctype: 'CRM Enrichment Rule',
        name: row.name,
        fieldname: values,
      })
      return true
    } catch (err) {
      row.serverError = serverMessage(
        err,
        values?.rule_name || row.ruleName,
        messages.updateError,
      )
      return false
    }
  }

  // Rule and patterns go in as one document, so a failed insert leaves nothing
  // half-created behind.
  async function runInsert(row) {
    let doc
    try {
      doc = await toInsert(row)
      await call('frappe.client.insert', {
        doc: { doctype: 'CRM Enrichment Rule', rule_type: ruleType, ...doc },
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

  // Deletes go first, so a rule removed and re-added under the same name in one
  // Save frees its rule_name before the insert asks for it; then updates, then
  // inserts. Resolves true only when every request succeeded -- a row that
  // failed stays changed, with its error under it, so it is still pending.
  async function save() {
    const removed = savedRows.value.filter((row) => row.removed)
    const updated = savedRows.value.filter(
      (row) => !row.removed && isRowChanged(row),
    )
    const inserted = [...localRows.value]

    if (!removed.length && !updated.length && !inserted.length) return true

    saving.value = true
    try {
      const results = [
        ...(await Promise.all(removed.map(runDelete))),
        ...(await Promise.all(updated.map(runUpdate))),
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
    validate,
    save,
  }
}
