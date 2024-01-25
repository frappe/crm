<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs" />
    </template>
  </LayoutHeader>
  <ViewControls
    v-model="callLogs"
    v-model:loadMore="loadMore"
    doctype="CRM Call Log"
  />
  <CallLogsListView
    v-if="callLogs.data && rows.length"
    v-model="callLogs.data.page_length_count"
    :rows="rows"
    :columns="callLogs.data.columns"
    :options="{
      rowCount: callLogs.data.row_count,
      totalCount: callLogs.data.total_count,
    }"
    @loadMore="() => loadMore++"
  />
  <div
    v-else-if="callLogs.data"
    class="flex h-full items-center justify-center"
  >
    <div
      class="flex flex-col items-center gap-3 text-xl font-medium text-gray-500"
    >
      <PhoneIcon class="h-10 w-10" />
      <span>No Logs Found</span>
    </div>
  </div>
</template>

<script setup>
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewControls from '@/components/ViewControls.vue'
import CallLogsListView from '@/components/ListViews/CallLogsListView.vue'
import {
  secondsToDuration,
  dateFormat,
  dateTooltipFormat,
  timeAgo,
} from '@/utils'
import { usersStore } from '@/stores/users'
import { contactsStore } from '@/stores/contacts'
import { Breadcrumbs } from 'frappe-ui'
import { computed, ref } from 'vue'

const { getUser } = usersStore()
const { getContact, getLeadContact } = contactsStore()

const breadcrumbs = [{ label: 'Call Logs', route: { name: 'Call Logs' } }]

// callLogs data is loaded in the ViewControls component
const callLogs = ref({})
const loadMore = ref(1)

const rows = computed(() => {
  if (!callLogs.value?.data?.data) return []
  return callLogs.value?.data.data.map((callLog) => {
    let _rows = {}
    callLogs.value?.data.rows.forEach((row) => {
      _rows[row] = callLog[row]

      let incoming = callLog.type === 'Incoming'

      if (row === 'caller') {
        _rows[row] = {
          label: incoming
            ? getContact(callLog.from)?.full_name ||
              getLeadContact(callLog.from)?.full_name ||
              'Unknown'
            : getUser(callLog.caller).full_name,
          image: incoming
            ? getContact(callLog.from)?.image ||
              getLeadContact(callLog.from)?.image
            : getUser(callLog.caller).user_image,
        }
      } else if (row === 'receiver') {
        _rows[row] = {
          label: incoming
            ? getUser(callLog.receiver).full_name
            : getContact(callLog.to)?.full_name ||
              getLeadContact(callLog.to)?.full_name ||
              'Unknown',
          image: incoming
            ? getUser(callLog.receiver).user_image
            : getContact(callLog.to)?.image ||
              getLeadContact(callLog.to)?.image,
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
          label: statusLabelMap[callLog.status],
          color: statusColorMap[callLog.status],
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

const statusLabelMap = {
  Completed: 'Completed',
  Initiated: 'Initiated',
  Busy: 'Declined',
  Failed: 'Failed',
  Queued: 'Queued',
  Cancelled: 'Cancelled',
  Ringing: 'Ringing',
  'No Answer': 'Missed Call',
  'In Progress': 'In Progress',
}

const statusColorMap = {
  Completed: 'green',
  Busy: 'orange',
  Failed: 'red',
  Initiated: 'gray',
  Queued: 'gray',
  Cancelled: 'gray',
  Ringing: 'gray',
  'No Answer': 'red',
  'In Progress': 'blue',
}
</script>
