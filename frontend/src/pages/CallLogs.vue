<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs" />
    </template>
  </LayoutHeader>
  <div class="flex items-center justify-between px-5 pb-4 pt-3">
    <div class="flex items-center gap-2">
      <SortBy doctype="CRM Call Log" />
      <Filter doctype="CRM Call Log" />
    </div>
    <div class="flex items-center gap-2">
      <ViewSettings doctype="CRM Call Log" v-model="callLogs" />
    </div>
  </div>
  <CallLogsListView
    v-if="callLogs.data"
    :rows="rows"
    :columns="callLogs.data.columns"
  />
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import SortBy from '@/components/SortBy.vue'
import Filter from '@/components/Filter.vue'
import ViewSettings from '@/components/ViewSettings.vue'
import CallLogsListView from '@/components/ListViews/CallLogsListView.vue'
import {
  secondsToDuration,
  dateFormat,
  dateTooltipFormat,
  timeAgo,
} from '@/utils'
import { usersStore } from '@/stores/users'
import { contactsStore } from '@/stores/contacts'
import { useOrderBy } from '@/composables/orderby'
import { useFilter } from '@/composables/filter'
import { useDebounceFn } from '@vueuse/core'
import { createResource, Breadcrumbs } from 'frappe-ui'
import { computed, watch } from 'vue'

const { getUser } = usersStore()
const { getContact } = contactsStore()
const { get: getOrderBy } = useOrderBy()
const { getArgs, storage } = useFilter()

const breadcrumbs = [{ label: 'Call Logs', route: { name: 'Call Logs' } }]

function getParams() {
  const filters = getArgs() || {}
  const order_by = getOrderBy() || 'creation desc'

  return {
    doctype: 'CRM Call Log',
    filters: filters,
    order_by: order_by,
  }
}

const callLogs = createResource({
  url: 'crm.api.doc.get_list_data',
  params: getParams(),
  auto: true,
})

watch(
  () => getOrderBy(),
  (value, old_value) => {
    if (!value && !old_value) return
    callLogs.params = getParams()
    callLogs.reload()
  },
  { immediate: true }
)

watch(
  storage,
  useDebounceFn((value, old_value) => {
    if (JSON.stringify([...value]) === JSON.stringify([...old_value])) return
    callLogs.params = getParams()
    callLogs.reload()
  }, 300),
  { deep: true }
)

const rows = computed(() => {
  if (!callLogs.data?.data) return []
  return callLogs.data.data.map((callLog) => {
    let _rows = {}
    callLogs.data.rows.forEach((row) => {
      _rows[row] = callLog[row]

      let incoming = callLog.type === 'Incoming'

      if (row === 'caller') {
        _rows[row] = {
          label: incoming
            ? getContact(callLog.from)?.full_name || 'Unknown'
            : getUser(callLog.caller).full_name,
          image: incoming
            ? getContact(callLog.from)?.image
            : getUser(callLog.caller).user_image,
        }
      } else if (row === 'receiver') {
        _rows[row] = {
          label: incoming
            ? getUser(callLog.receiver).full_name
            : getContact(callLog.to)?.full_name || 'Unknown',
          image: incoming
            ? getUser(callLog.receiver).user_image
            : getContact(callLog.to)?.image,
        }
      } else if (row === 'duration') {
        _rows[row] = {
          label: secondsToDuration(callLog.duration),
          icon: 'clock',
        }
      } else if (row === 'type') {
        _rows[row] = {
          label: callLog.type,
          icon: incoming ? 'phone-incoming' : 'phone-outgoing',
        }
      } else if (row === 'status') {
        _rows[row] = {
          label: callLog.status,
          color: callLog.status === 'Completed' ? 'green' : 'gray',
        }
      } else if (['modified', 'creation'].includes(row)) {
        _rows[row] = {
          label: dateFormat(callLog[row], dateTooltipFormat),
          timeAgo: timeAgo(callLog[row]),
        }
      }
    })
    return _rows
  })
})
</script>
