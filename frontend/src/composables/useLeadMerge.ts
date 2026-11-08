import { call } from 'frappe-ui'
import { computed, ref, toValue, type MaybeRefOrGetter } from 'vue'
import { usersStore } from '@/stores/users'
import { formatNumber } from '@/utils/numberFormat'
import { withRecipientConfirmation } from '@/utils/whatsappRecipient'

// Step 2 of the lead merge: the fields the two leads differ on and, for each,
// which lead's value survives. `target` is the lead being kept, `source` the
// one merged into it. `picks` is the only state; everything else derives from it.

export type MergeSide = 'source' | 'target'

export interface MergeField {
  fieldname: string
  label: string
  fieldtype: string
  options: string | null
  source_value: unknown
  target_value: unknown
  // plain text, formatted on the server
  source_display: string
  target_display: string
}

// the server fills a target field only from a truthy source value
const isSet = (value: unknown) => Boolean(value)

export const isConflict = (field: MergeField) =>
  isSet(field.source_value) && isSet(field.target_value)

// the server formats currency with its symbol; the design shows the amount only
export const formatAmount = (value: unknown) => formatNumber(value, '', 2)

function errorMessage(e: unknown, fallback: string): string {
  const err = e as { messages?: string[]; message?: string }
  return err?.messages?.[0] || err?.message || fallback
}

export function useLeadMerge(
  target: MaybeRefOrGetter<string>,
  source: MaybeRefOrGetter<string>,
  targetAssignees: MaybeRefOrGetter<string[]>,
) {
  const { getUser } = usersStore()

  const fields = ref<MergeField[]>([])
  const picks = ref<Record<string, MergeSide>>({})
  const sourceAssignees = ref<string[]>([])
  const loaded = ref(false)
  const loading = ref(false)
  const merging = ref(false)
  const error = ref('')

  const conflicts = computed(() => fields.value.filter(isConflict))
  const autoFields = computed(() => fields.value.filter((f) => !isConflict(f)))
  // both leads' assignees: the merge moves the source's open ToDos over
  const assignees = computed(() => [
    ...new Set([...toValue(targetAssignees), ...sourceAssignees.value]),
  ])

  // drops a response that lands after the modal moved on to another source
  let loadId = 0

  async function load() {
    const id = ++loadId
    loaded.value = false
    loading.value = true
    error.value = ''
    fields.value = []
    picks.value = {}
    try {
      const [mergeFields, sourceAssignedUsers] = await Promise.all([
        call('crm.api.lead.get_lead_merge_fields', {
          source: toValue(source),
          target: toValue(target),
        }) as Promise<MergeField[]>,
        call('crm.api.doc.get_assigned_users', {
          doctype: 'CRM Lead',
          name: toValue(source),
        }) as Promise<string[]>,
      ])
      if (id !== loadId) return
      fields.value = mergeFields
      sourceAssignees.value = sourceAssignedUsers || []
      picks.value = Object.fromEntries(
        mergeFields.map((f) => [
          f.fieldname,
          isSet(f.target_value) ? 'target' : 'source',
        ]),
      )
      loaded.value = true
    } catch (e) {
      if (id === loadId) {
        error.value = errorMessage(e, __('Could not load the leads to merge'))
      }
    } finally {
      if (id === loadId) loading.value = false
    }
  }

  function pick(fieldname: string, side: MergeSide) {
    picks.value[fieldname] = side
  }

  function valueOf(field: MergeField, side: MergeSide) {
    return side === 'source' ? field.source_value : field.target_value
  }

  function displayOf(field: MergeField, side: MergeSide): string {
    const value = valueOf(field, side)
    if (field.fieldtype === 'Link' && field.options === 'User' && value) {
      return getUser(value as string).full_name
    }
    if (field.fieldtype === 'Currency' && value) return formatAmount(value)
    return side === 'source' ? field.source_display : field.target_display
  }

  const pickedValue = (field: MergeField) =>
    valueOf(field, picks.value[field.fieldname])
  const pickedDisplay = (field: MergeField) =>
    displayOf(field, picks.value[field.fieldname])

  // only conflicts the user resolved to the source: a field empty on the target
  // when the dialog loaded is left to the server, which fills it only if it is
  // still empty, so an edit saved meanwhile isn't overwritten
  const takeFromSource = computed(() =>
    conflicts.value
      .map((f) => f.fieldname)
      .filter((f) => picks.value[f] === 'source'),
  )

  async function merge(): Promise<string | null> {
    merging.value = true
    error.value = ''
    try {
      // taking the source's mobile_no moves the target off a number it may have a
      // WhatsApp conversation with; the server refuses until the user confirms
      const result = await withRecipientConfirmation((confirm?: object) =>
        call('crm.api.lead.merge_leads', {
          target: toValue(target),
          source: toValue(source),
          take_from_source: takeFromSource.value,
          ...confirm,
        }),
      )
      return result?.target ?? null
    } catch (e) {
      error.value = errorMessage(e, __('Failed to merge leads'))
      return null
    } finally {
      merging.value = false
    }
  }

  return {
    fields,
    conflicts,
    autoFields,
    picks,
    assignees,
    loaded,
    loading,
    merging,
    error,
    load,
    pick,
    displayOf,
    pickedValue,
    pickedDisplay,
    merge,
  }
}
