<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs" />
    </template>
    <template #right-header>
      <CustomActions
        v-if="callLogsListView?.customListActions"
        :actions="callLogsListView.customListActions"
      />
    </template>
  </LayoutHeader>
  <ViewControls
    ref="viewControls"
    v-model="callLogs"
    v-model:loadMore="loadMore"
    v-model:resizeColumn="triggerResize"
    v-model:updatedPageCount="updatedPageCount"
    doctype="CRM Call Log"
  />
  <CallLogsListView
    ref="callLogsListView"
    v-if="callLogs.data && rows.length"
    v-model="callLogs.data.page_length_count"
    v-model:list="callLogs"
    :rows="rows"
    :columns="callLogs.data.columns"
    :options="{
      showTooltip: false,
      resizeColumn: true,
      rowCount: callLogs.data.row_count,
      totalCount: callLogs.data.total_count,
    }"
    @showCallLog="showCallLog"
    @loadMore="() => loadMore++"
    @columnWidthUpdated="() => triggerResize++"
    @updatePageCount="(count) => (updatedPageCount = count)"
    @applyFilter="(data) => viewControls.applyFilter(data)"
  />
  <div
    v-else-if="callLogs.data"
    class="flex h-full items-center justify-center"
  >
    <div
      class="flex flex-col items-center gap-3 text-xl font-medium text-gray-500"
    >
      <PhoneIcon class="h-10 w-10" />
      <span>{{ __('No Logs Found') }}</span>
    </div>
  </div>
  <CallLogModal
    v-model="showCallLogModal"
    v-model:reloadCallLogs="callLogs"
    :callLog="callLog"
  />
</template>

<script setup>
import CustomActions from '@/components/CustomActions.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewControls from '@/components/ViewControls.vue'
import CallLogsListView from '@/components/ListViews/CallLogsListView.vue'
import CallLogModal from '@/components/Modals/CallLogModal.vue'
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

const breadcrumbs = [{ label: __('Call Logs'), route: { name: 'Call Logs' } }]

const callLogsListView = ref(null)

// callLogs data is loaded in the ViewControls component
const callLogs = ref({})
const loadMore = ref(1)
const triggerResize = ref(1)
const updatedPageCount = ref(20)
const viewControls = ref(null)

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
          timeAgo: __(timeAgo(callLog[row])),
        }
      }
    })
    return _rows
  })
})

const showCallLogModal = ref(false)

const callLog = ref({
  name: '',
  caller: '',
  receiver: '',
  duration: '',
  type: '',
  status: '',
  from: '',
  to: '',
  note: '',
  recording_url: '',
  reference_doctype: '',
  reference_docname: '',
  creation: '',
})

function showCallLog(name) {
  let d = rows.value?.find((row) => row.name === name)
  callLog.value = {
    name: d.name,
    caller: d.caller,
    receiver: d.receiver,
    duration: d.duration,
    type: d.type,
    status: d.status,
    from: d.from,
    to: d.to,
    note: d.note,
    recording_url: d.recording_url,
    reference_doctype: d.reference_doctype,
    reference_docname: d.reference_docname,
    creation: d.creation,
  }
  showCallLogModal.value = true
}

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
