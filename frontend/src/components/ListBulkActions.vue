<template>
  <EditValueModal
    v-if="showEditModal"
    v-model="showEditModal"
    :doctype="doctype"
    :selectedValues="selectedValues"
    @reload="reload"
  />
  <AssignmentModal
    v-if="showAssignmentModal"
    v-model="showAssignmentModal"
    v-model:assignees="bulkAssignees"
    :docs="selectedValues"
    :doctype="doctype"
    @reload="reload"
  />
  <DeleteLinkedDocModal
    v-if="showDeleteDocModal.showLinkedDocsModal"
    v-model="showDeleteDocModal.showLinkedDocsModal"
    :doctype="props.doctype"
    :docname="showDeleteDocModal.docname"
    :reload="reload"
  />
  <BulkDeleteLinkedDocModal
    v-if="showDeleteDocModal.showDeleteModal"
    v-model="showDeleteDocModal.showDeleteModal"
    :doctype="props.doctype"
    :items="showDeleteDocModal.items"
    :reload="reload"
  />
  <BulkEmailModal
    v-if="showBulkEmailModal"
    v-model="showBulkEmailModal"
    :doctype="props.doctype"
    :selectedValues="selectedValues"
    @reload="reload"
  />
</template>

<script setup>
import EditValueModal from '@/components/Modals/EditValueModal.vue'
import AssignmentModal from '@/components/Modals/AssignmentModal.vue'
import BulkEmailModal from '@/components/Modals/BulkEmailModal.vue'
import { setupListCustomizations } from '@/utils'
import { globalStore } from '@/stores/global'
import { useTelemetry } from '@framework/ui/telemetry'
import { call, toast } from 'frappe-ui'
import { createToast, scriptToast } from '@/utils/scriptToast'
import { usersStore } from '@/stores/users'
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  doctype: { type: String, default: '' },
  currentTab: { type: String, default: '' },
  options: {
    type: Object,
    default: () => ({
      hideEdit: false,
      hideDelete: false,
      hideAssign: false,
    }),
  },
})

const emit = defineEmits(['reload'])

const list = defineModel({ type: Object })

const router = useRouter()

const { $dialog, $socket } = globalStore()
const { capture } = useTelemetry()

const showEditModal = ref(false)
const showBulkEmailModal = ref(false)
const selectedValues = ref([])
const unselectAllAction = ref(() => {})
const showDeleteDocModal = ref({
  showLinkedDocsModal: false,
  showDeleteModal: false,
  docname: null,
})
function editValues(selections, unselectAll) {
  selectedValues.value = selections
  showEditModal.value = true
  unselectAllAction.value = unselectAll
}

function convertToDeal(selections, unselectAll) {
  $dialog({
    title: __('Convert to Deal'),
    message: __('Are you sure you want to convert {0} item(s) to deal(s)?', [
      selections.size,
    ]),
    variant: 'solid',
    theme: 'blue',
    actions: [
      {
        label: __('Convert'),
        variant: 'solid',
        onClick: async ({ close }) => {
          capture('bulk_convert_to_deal')
          try {
            const res = await call('crm.api.daily_allocation.bulk_convert_to_deal', {
              doctype: props.doctype,
              names: Array.from(selections),
            })
            if (res.converted > 0) {
              toast.success(__('Successfully converted {0} record(s) to deal(s).', [res.converted]))
            }
            if (res.errors && res.errors.length) {
              toast.warning(res.errors[0])
            }
            reload(unselectAll)
            close()
          } catch (err) {
            toast.error(err.message || __('Failed to convert to deal'))
          }
        },
      },
    ],
  })
}

function openBulkEmail(selections, unselectAll) {
  selectedValues.value = selections
  unselectAllAction.value = unselectAll
  showBulkEmailModal.value = true
}

const crmLeadStatuses = [
  'New',
  'Contacted',
  'Nurture',
  'Qualified',
  'Converted',
  'Unqualified',
  'Junk',
]

function getChangeStatusOptions(selections, unselectAll) {
  return crmLeadStatuses.map((st) => ({
    label: __(st),
    onClick: () => changeProspectStatus(selections, st, unselectAll),
  }))
}

async function changeProspectStatus(selections, newStatus, unselectAll) {
  try {
    const res = await call('crm.api.daily_allocation.change_prospect_status', {
      doctype: props.doctype,
      names: Array.from(selections),
      status: newStatus,
    })
    if (res.updated > 0) {
      toast.success(__('Updated CRM Lead status to {0} for {1} prospect(s)', [newStatus, res.updated]))
    }
    if (res.skipped > 0) {
      toast.warning(__('Skipped {0} record(s) without linked CRM Lead', [res.skipped]))
    }
    reload(unselectAll)
  } catch (error) {
    toast.error(error.message || __('Failed to update status'))
  }
}

function deleteValues(selections, unselectAll) {
  unselectAllAction.value = unselectAll

  const selectedDocs = Array.from(selections)
  if (selectedDocs.length == 1) {
    showDeleteDocModal.value = {
      showLinkedDocsModal: true,
      docname: selectedDocs[0],
    }
  } else {
    showDeleteDocModal.value = {
      showDeleteModal: true,
      items: selectedDocs,
    }
  }
}

const showAssignmentModal = ref(false)
const bulkAssignees = ref([])

function assignValues(selections, unselectAll) {
  showAssignmentModal.value = true
  selectedValues.value = selections
  unselectAllAction.value = unselectAll
}

function clearAssignments(selections, unselectAll) {
  $dialog({
    title: __('Clear Assignment'),
    message: __('Are you sure you want to clear assignment for {0} item(s)?', [
      selections.size,
    ]),
    variant: 'solid',
    theme: 'red',
    actions: [
      {
        label: __('Clear Assignment'),
        variant: 'solid',
        theme: 'red',
        onClick: ({ close }) => {
          capture('bulk_clear_assignment')
          call('frappe.desk.form.assign_to.remove_multiple', {
            doctype: props.doctype,
            names: JSON.stringify(Array.from(selections)),
            ignore_permissions: true,
          }).then(() => {
            toast.success(__('Assignment Cleared Successfully'))
            reload(unselectAll)
            close()
          })
        },
      },
    ],
  })
}

function markAsDropped(selections, unselectAll) {
  $dialog({
    title: __('Mark as Dropped'),
    message: __(
      'Are you sure you want to mark {0} contact(s) as Dropped? They will appear only in the Dropped tab.',
      [selections.size],
    ),
    variant: 'solid',
    theme: 'red',
    actions: [
      {
        label: __('Mark as Dropped'),
        variant: 'solid',
        theme: 'red',
        onClick: async ({ close }) => {
          capture('bulk_mark_dropped')
          try {
            const res = await call('crm.api.contact.mark_contacts_dropped', {
              names: JSON.stringify(Array.from(selections)),
              dropped: 1,
            })
            toast.success(res?.message || __('Marked as Dropped'))
            reload(unselectAll)
            close()
          } catch (err) {
            toast.error(err.message || __('Failed to mark contacts as dropped'))
          }
        },
      },
    ],
  })
}

function restoreContacts(selections, unselectAll) {
  $dialog({
    title: __('Restore to Unassigned'),
    message: __(
      'Are you sure you want to restore {0} contact(s) to Unassigned?',
      [selections.size],
    ),
    variant: 'solid',
    theme: 'blue',
    actions: [
      {
        label: __('Restore'),
        variant: 'solid',
        theme: 'blue',
        onClick: async ({ close }) => {
          capture('bulk_restore_dropped')
          try {
            const res = await call('crm.api.contact.mark_contacts_dropped', {
              names: JSON.stringify(Array.from(selections)),
              dropped: 0,
            })
            toast.success(res?.message || __('Restored to Unassigned'))
            reload(unselectAll)
            close()
          } catch (err) {
            toast.error(err.message || __('Failed to restore contacts'))
          }
        },
      },
    ],
  })
}

const customBulkActions = ref([])
const customListActions = ref([])

function bulkActions(selections, unselectAll) {
  let actions = []
  const { isAdmin, isManager } = usersStore()
  const isSuperOrManager = isAdmin() || isManager()
  const restrictedDeleteDocs = ['Contact', 'CRM Organization', 'CRM Lead', 'CRM Daily Allocation']
  const canDelete = !restrictedDeleteDocs.includes(props.doctype) || isAdmin()

  if (!props.options.hideEdit) {
    actions.push({
      label: __('Edit'),
      onClick: () => editValues(selections, unselectAll),
    })
  }

  if (!props.options.hideDelete && canDelete) {
    actions.push({
      label: __('Delete'),
      onClick: () => deleteValues(selections, unselectAll),
    })
  }

  if (!props.options.hideAssign && isSuperOrManager) {
    actions.push({
      label: __('Assign To'),
      onClick: () => assignValues(selections, unselectAll),
    })
    actions.push({
      label: __('Clear Assignment'),
      onClick: () => clearAssignments(selections, unselectAll),
    })
  }

  if (props.doctype === 'CRM Lead' || props.doctype === 'Contact') {
    actions.push({
      label: __('Convert to Deal'),
      onClick: () => convertToDeal(selections, unselectAll),
    })
  }

  actions.push({
    label: __('Bulk Email'),
    onClick: () => openBulkEmail(selections, unselectAll),
  })

  actions.push({
    label: __('Change Status'),
    submenu: getChangeStatusOptions(selections, unselectAll),
  })

  if (props.doctype === 'Contact' && isSuperOrManager) {
    if (props.currentTab === 'dropped') {
      actions.push({
        label: __('Restore to Unassigned'),
        onClick: () => restoreContacts(selections, unselectAll),
      })
    } else {
      actions.push({
        label: __('Mark as Dropped'),
        onClick: () => markAsDropped(selections, unselectAll),
      })
    }
  }

  customBulkActions.value.forEach((action) => {
    actions.push({
      label: __(action.label),
      onClick: () =>
        action.onClick({
          list: list.value,
          selections,
          unselectAll,
          call,
          createToast,
          toast: scriptToast,
          $dialog,
          router,
        }),
    })
  })
  return actions
}

function reload(unselectAll) {
  showDeleteDocModal.value = {
    showLinkedDocsModal: false,
    showDeleteModal: false,
    docname: null,
  }

  unselectAllAction.value?.()
  unselectAll?.()
  list.value?.reload()
  emit('reload')
}

onMounted(async () => {
  if (!list.value?.data) return
  let customization = await setupListCustomizations(list.value.data, {
    list: list.value,
    call,
    $dialog,
    $socket,
    router,
  })
  customBulkActions.value =
    customization?.bulkActions || list.value?.data?.bulkActions || []
  customListActions.value =
    customization?.actions || list.value?.data?.listActions || []
})

defineExpose({
  bulkActions,
  customListActions,
})
</script>
