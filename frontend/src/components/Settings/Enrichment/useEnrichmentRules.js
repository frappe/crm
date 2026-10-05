import { call, useList } from 'frappe-ui'
import { computed, reactive, ref } from 'vue'

// Sites hold a few dozen rules, so there's no paging; past this the section
// says only the first ones are shown.
export const RULE_LIMIT = 500

// Shared load / dirty-tracking / save plumbing for one rule_type; callers
// supply row shape and payloads.
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
  // Patterns come with each rule as a child table. refetch is off so it only
  // fetches when load asks.
  const list = useList({
    doctype: 'CRM Enrichment Rule',
    filters: { rule_type: ruleType },
    fields: [
      'name',
      'enabled',
      ...fields,
      { patterns: ['name', 'pattern', 'is_regex', 'idx'] },
    ],
    orderBy: 'modified desc',
    limit: RULE_LIMIT,
    immediate: false,
    refetch: false,
    // Unsaved edits carry across a reload.
    onSuccess: buildRows,
  })

  // Only the first load shows the spinner; reloads keep the rows on screen.
  const loadedOnce = ref(false)

  const loading = computed(() => !loadedOnce.value && list.loading)

  const error = computed(() => list.error)

  const saving = ref(false)

  // hasNextPage starts true, so it only counts once a load has landed.
  const truncated = computed(() => loadedOnce.value && list.hasNextPage)

  const savedRows = ref([])

  // Kept apart from savedRows so a reload doesn't sweep away unsaved new rows.
  const localRows = ref([])

  let localRowSeq = 0

  // Deleted rows stay flagged until Save; a failed delete reappears, locked, to
  // show its error.
  const rows = computed(() => [
    ...savedRows.value.filter((row) => !row.removed || row.serverError),
    ...localRows.value,
  ])

  // Shared by every rule_type, so tracked here, not in each isRowChanged.
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

  async function load() {
    await list.reload()
    return !list.error
  }

  // Social edits only the first pattern, so the order can't be left to the
  // server.
  function sortByIdx(patternRows) {
    return [...(patternRows || [])].sort((a, b) => a.idx - b.idx)
  }

  function buildRows(rules) {
    loadedOnce.value = true
    // Carry unsaved edits, errors and deletes across the rebuild; rows Save
    // just wrote take the server's copy.
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
        enabled: held ? held.enabled : Boolean(rule.enabled),
        savedEnabled: Boolean(rule.enabled),
        removed: held ? held.removed : false,
        serverError: held ? held.serverError : '',
        ...buildRow(rule, sortByIdx(rule.patterns), held),
      })
    })
  }

  function addRow() {
    localRows.value.push(
      reactive({
        key: `new-${(localRowSeq += 1)}`,
        name: null,
        enabled: true,
        savedEnabled: true,
        removed: false,
        serverError: '',
        ...newRow(),
      }),
    )
  }

  function deleteRow(row) {
    if (!row.name) {
      localRows.value = localRows.value.filter((other) => other !== row)
      return
    }
    row.removed = true
  }

  function toggleEnabled(row) {
    if (row.removed) return
    row.enabled = !row.enabled
    row.serverError = ''
  }

  // Validate up front so a Save either starts with every row valid or doesn't
  // start at all.
  function validate() {
    let valid = true
    rows.value.forEach((row) => {
      if (row.removed) return
      // A status-only edit sends just `enabled`, so stored fields aren't held
      // to the form's checks.
      if (row.name && !isRowChanged(row)) return
      clearErrors(row)
      row.serverError = ''
      const others = rows.value.filter(
        (other) => other !== row && !other.removed,
      )
      if (!validateRow(row, others)) valid = false
    })
    return valid
  }

  // The server's own text (duplicate target, bad regex) is shown as-is.
  function serverMessage(err, fallback) {
    return err?.messages?.[0] || fallback
  }

  async function runDelete(row) {
    row.serverError = ''
    try {
      await call('frappe.client.delete', {
        doctype: 'CRM Enrichment Rule',
        name: row.name,
      })
      // Dropped now, not on reload, so it can't come back even if the reload
      // fails.
      savedRows.value = savedRows.value.filter((other) => other !== row)
      return true
    } catch (err) {
      // Still flagged, so the next Save retries the delete.
      row.serverError = __('{0}. Save to try deleting it again.', [
        serverMessage(err, messages.deleteError).replace(/\.+$/, ''),
      ])
      return false
    }
  }

  // set_value merges only the given fields, so unsent ones (weight,
  // match_scope) keep their values.
  // The rule is re-read so hidden patterns are current, not from page load.
  async function runUpdate(row) {
    try {
      let values = {}
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
      return true
    } catch (err) {
      row.serverError = serverMessage(err, messages.updateError)
      return false
    }
  }

  // One document, so a failed insert leaves nothing half-created.
  async function runInsert(row) {
    try {
      const doc = await toInsert(row)
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
      row.serverError = serverMessage(err, messages.insertError)
      return false
    }
  }

  // Deletes first, so a removed-and-re-added rule frees its target before the
  // insert needs it; updates before inserts for the same reason.
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
        ...(await Promise.all(updated.map(runUpdate))),
        ...(await Promise.all(inserted.map(runInsert))),
      ]

      const loaded = await load()

      return loaded && results.every(Boolean)
    } finally {
      saving.value = false
    }
  }

  load()

  return {
    rows,
    dirtyRows,
    loading,
    error,
    saving,
    load,
    truncated,
    addRow,
    deleteRow,
    toggleEnabled,
    validate,
    save,
  }
}
