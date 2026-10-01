import { call, createListResource } from 'frappe-ui'
import { computed, reactive, ref } from 'vue'

const PAGE_LENGTH = 50

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
  // Paged; "Load more" appends the next page (loadMore). frappe-ui's reload()
  // re-reads every page already loaded, so a post-save reload keeps them.
  const resource = createListResource({
    doctype: 'CRM Enrichment Rule',
    filters: { rule_type: ruleType },
    fields: ['name', 'rule_name', 'enabled', ...fields],
    orderBy: 'modified desc',
    pageLength: PAGE_LENGTH,
  })

  // rule name -> the rule's pattern child rows, as stored
  const patterns = reactive({})
  const patternsLoading = ref(false)
  const patternsError = ref(null)

  // Only the first load shows the spinner; reloads keep the rows on screen.
  const loadedOnce = ref(false)

  const loading = computed(
    () => !loadedOnce.value && (resource.list.loading || patternsLoading.value),
  )

  const error = computed(() => resource.list.error || patternsError.value)

  const saving = ref(false)

  const loadingMore = ref(false)

  const hasMore = computed(() => resource.hasNextPage)

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

  // Awaited together so a post-save reload has rebuilt the rows before Save
  // reports back.
  async function load() {
    patternsError.value = null
    // The error is in resource.list.error; the catch just avoids console noise.
    await resource.reload().catch(() => {})
    if (resource.list.error) {
      loadedOnce.value = true
      return false
    }
    return loadPatterns(resource.data || [])
  }

  // Appends the next page; only its rules need patterns fetched. Rows are
  // rebuilt from the whole list, so unsaved edits carry across.
  async function loadMore() {
    if (loadingMore.value || !resource.hasNextPage) return
    loadingMore.value = true
    const previousData = resource.originalData
    const loaded = new Set((resource.data || []).map((rule) => rule.name))
    try {
      resource.start += resource.pageLength
      await resource.list.fetch().catch(() => {})
      if (resource.list.error) {
        resource.start -= resource.pageLength
        return false
      }
      const allRules = resource.data || []
      const added = allRules.filter((rule) => !loaded.has(rule.name))
      const ok = await loadPatterns(added, allRules)
      if (!ok) {
        // A rule without patterns can't get a row, so roll the page back and
        // let Load more retry.
        resource.start -= resource.pageLength
        resource.setData(previousData)
      }
      return ok
    } finally {
      loadingMore.value = false
    }
  }

  // get_list skips child tables, so query the child doctype (`parent` is what
  // frappe permission-checks). Patterns are fetched for `rules`; rows are built
  // from `allRules`.
  async function loadPatterns(rules, allRules = rules) {
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
      buildRows(allRules)
      return true
    } catch (err) {
      // Rows without patterns would show empty boxes that wipe patterns on
      // save, so keep the old rows.
      patternsError.value = err
      return false
    } finally {
      patternsLoading.value = false
      loadedOnce.value = true
    }
  }

  function buildRows(rules) {
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

  function isNameCollision(err) {
    return ['DuplicateEntryError', 'UniqueValidationError'].includes(
      err?.exc_type,
    )
  }

  // rule_name collisions come back with raw text naming the column, so reword
  // them for the admin.
  function serverMessage(err, ruleName, fallback) {
    if (isNameCollision(err)) {
      return __('A rule named "{0}" already exists', [ruleName])
    }
    return err?.messages?.[0] || fallback
  }

  async function runDelete(row) {
    row.serverError = ''
    try {
      await call('frappe.client.delete', {
        doctype: 'CRM Enrichment Rule',
        name: row.name,
      })
      delete patterns[row.name]
      return true
    } catch (err) {
      // Still flagged, so the next Save retries the delete.
      const message = serverMessage(err, row.ruleName, messages.deleteError)
      row.serverError = __('{0}. Save to try deleting it again.', [
        message.replace(/\.+$/, ''),
      ])
      return false
    }
  }

  // set_value merges only the given fields, so unsent ones (weight,
  // match_scope) keep their values.
  // The rule is re-read so hidden patterns are current, not from page load.
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

  // One document, so a failed insert leaves nothing half-created.
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

  // When every update in a pass failed, look for a ring of rows each refused
  // the name another holds.
  // Returns a row on the ring, or null (a real duplicate). Lowercased to match
  // the unique index.
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

  // rule_name is unique and renames can chain, so updates run one at a time and
  // failures are retried.
  // A rename ring is broken by parking one row under a placeholder; each row
  // parks at most once.
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

    // Give parked rows that never updated their name back; best effort, the
    // next Save moves them on.
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

  // Deletes first, so a removed-and-re-added rule frees its rule_name before
  // the insert needs it.
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
    loadMore,
    loadingMore,
    hasMore,
    addRow,
    deleteRow,
    toggleEnabled,
    validate,
    save,
  }
}
