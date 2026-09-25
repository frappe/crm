import { call, createListResource, toast } from 'frappe-ui'
import { computed, reactive, ref } from 'vue'

// One rule_type's worth of the Rules tab: the list, the pattern child rows the
// list call can't bring back, and the editable rows built from both. Social and
// Industry rules differ only in the fields on a row and in the document each one
// sends -- the loading, the carry-over across reloads, and the insert/save/delete
// plumbing around them are the same, so they live here once.
//
// The caller supplies the shape of a row (buildRow / newRow), what counts as an
// unsaved edit (isRowPending), and the toast copy; everything else is handled.
export function useEnrichmentRules({
  ruleType,
  fields = [],
  buildRow,
  newRow,
  isRowPending,
  // A row rebuilt by a reload keeps what the admin still had in flight. Pending
  // edits qualify by default; a section with more than one error field says so.
  isRowHeld = (row) => isRowPending(row) || Boolean(row.error),
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
    auto: true,
    onSuccess: (rules) => loadPatterns(rules),
  })

  // rule name -> the rule's pattern child rows, as stored
  const patterns = reactive({})
  const patternsLoading = ref(false)

  // The spinner stands in for the whole section, so it only belongs on the first
  // load. A reload after an insert or a delete leaves the rows on screen and
  // swaps them when the new ones land.
  const loadedOnce = ref(false)

  // createListResource keeps its fetch state on `.list`, not on the resource
  // itself -- the patterns land after it, so the spinner has to cover both.
  const loading = computed(
    () => !loadedOnce.value && (resource.list.loading || patternsLoading.value),
  )

  // One editable row per stored rule, rebuilt whenever the list reloads.
  const savedRows = ref([])

  // Rows added by the section's "+ Add" button that have nothing behind them
  // yet. They live apart from savedRows so a reload rebuilds the stored rows
  // without sweeping away a half-filled new one.
  const localRows = ref([])

  let localRowSeq = 0

  const rows = computed(() => [...savedRows.value, ...localRows.value])

  const pendingRows = computed(() => rows.value.filter(isRowPending))

  // reload() rethrows on a second failure, and an unguarded rejection here would
  // only show up as console noise -- the error state already renders the message.
  function retry() {
    resource.reload().catch(() => {})
  }

  // A reload after an insert or a delete no longer blanks the section, so a
  // failure would otherwise leave the old rows up with nothing said. The rows
  // are still the last thing the server confirmed, so they stay -- the toast is
  // what tells the admin the list may have drifted.
  function reloadRules() {
    resource.reload().catch(() => {
      toast.error(messages.refreshError)
    })
  }

  // get_list never returns child tables, so the patterns have to be fetched
  // separately: one frappe.client.get per rule, which is what the rest of
  // Settings already does for a single doc (see WorkflowAutomationDetail.vue). A
  // handful of rules means a handful of parallel requests -- cheaper than adding
  // a backend endpoint for a read-only list. createDocumentResource per rule was
  // the other option, but a resource can't be created inside v-for: it would have
  // to be built and cached outside the render, and its save/setValue machinery is
  // dead weight next to the plain get/save this form already makes.
  async function loadPatterns(rules) {
    if (!rules?.length) {
      savedRows.value = []
      loadedOnce.value = true
      return
    }

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
    } catch (err) {
      // A row with no patterns loaded would read as an empty pattern box, and
      // saving that box would wipe the stored patterns -- so drop the rows rather
      // than offer edits built on a half-loaded rule.
      savedRows.value = []
      toast.error(err.messages?.[0] || messages.patternsError)
    } finally {
      patternsLoading.value = false
      loadedOnce.value = true
    }
  }

  function buildRows(rules) {
    // Every row is rebuilt from the reload, so whatever the admin still had in
    // flight on a row that survived is carried across: the values in its boxes
    // and the error under them. Otherwise deleting one row would quietly discard
    // a half-typed edit, or a red border, on another.
    const carried = new Map()
    savedRows.value.forEach((row) => {
      if (isRowHeld(row)) carried.set(row.name, row)
    })

    savedRows.value = rules.map((rule) =>
      reactive({
        key: rule.name,
        name: rule.name,
        enabled: Boolean(rule.enabled),
        saving: false,
        ...buildRow(rule, patterns[rule.name] || [], carried.get(rule.name)),
      }),
    )
  }

  function addRow() {
    localRows.value.push(
      reactive({
        key: `new-${(localRowSeq += 1)}`,
        name: null,
        // Inserted as enabled, so the row shouldn't read as disabled while local.
        enabled: true,
        saving: false,
        ...newRow(),
      }),
    )
  }

  function dropLocalRow(row) {
    localRows.value = localRows.value.filter((other) => other !== row)
  }

  // Rule and patterns go in as one document, so a failed insert leaves nothing
  // half-created behind. `doc` is everything past the doctype and rule_type.
  async function insertRow(row, doc) {
    row.saving = true
    try {
      await call('frappe.client.insert', {
        doc: { doctype: 'CRM Enrichment Rule', rule_type: ruleType, ...doc },
      })
    } catch (err) {
      toast.error(err.messages?.[0] || messages.insertError)
      return
    } finally {
      row.saving = false
    }

    toast.success(messages.inserted)
    // The reload rebuilds every stored row, so the local one is dropped first
    // and the saved one takes its place rather than sitting beside it.
    dropLocalRow(row)
    reloadRules()
  }

  // frappe.client.set_value can reach a child row by its own name, but it takes
  // one field at a time -- a row where several boxes changed would be several
  // saves and several chances to half-apply. Re-reading the doc and posting the
  // whole thing back with frappe.client.save sends the complete patterns table in
  // one request, so the pattern rows a section doesn't show ride along exactly as
  // stored. The doc is re-read rather than reused from load so its `modified` is
  // fresh and the save isn't rejected as a stale write.
  //
  // `mutate` lays the row's values onto the fetched doc, `onSaved` takes what came
  // back, and `rollback` puts the row back to what the server last confirmed so
  // the screen never shows a value that isn't stored.
  async function updateRow(row, { mutate, onSaved, rollback }) {
    row.saving = true
    try {
      const doc = await call('frappe.client.get', {
        doctype: 'CRM Enrichment Rule',
        name: row.name,
      })

      mutate(doc)

      const saved = await call('frappe.client.save', { doc })

      patterns[row.name] = saved.patterns || []
      onSaved(saved)
      toast.success(messages.updated)

      // The duplicate check reads resource.data, and the fields it checks have
      // just moved underneath it. Without this, retargeting a rule leaves the
      // list still claiming the old value is taken, and the next row to ask for
      // it is refused against a rule that no longer holds it.
      reloadRules()
    } catch (err) {
      toast.error(err.messages?.[0] || messages.updateError)
      rollback()
    } finally {
      row.saving = false
    }
  }

  // A row that was never inserted is only on screen, so dropping it is a local
  // splice -- there is nothing to delete.
  async function deleteRow(row) {
    if (!row.name) {
      dropLocalRow(row)
      return
    }

    row.saving = true
    try {
      await call('frappe.client.delete', {
        doctype: 'CRM Enrichment Rule',
        name: row.name,
      })
    } catch (err) {
      toast.error(err.messages?.[0] || messages.deleteError)
      return
    } finally {
      row.saving = false
    }

    toast.success(messages.deleted)
    delete patterns[row.name]
    reloadRules()
  }

  return {
    resource,
    patterns,
    rows,
    pendingRows,
    loading,
    retry,
    reloadRules,
    addRow,
    insertRow,
    updateRow,
    deleteRow,
  }
}
