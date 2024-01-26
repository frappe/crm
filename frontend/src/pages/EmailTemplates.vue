<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs" />
    </template>
  </LayoutHeader>
  <ViewControls
    v-model="emailTemplates"
    v-model:loadMore="loadMore"
    doctype="Email Template"
  />
  <EmailTemplatesListView
    v-if="emailTemplates.data && rows.length"
    v-model="emailTemplates.data.page_length_count"
    :rows="rows"
    :columns="emailTemplates.data.columns"
    :options="{
      rowCount: emailTemplates.data.row_count,
      totalCount: emailTemplates.data.total_count,
    }"
    @loadMore="() => loadMore++"
  />
  <div
    v-else-if="emailTemplates.data"
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
import EmailTemplatesListView from '@/components/ListViews/EmailTemplatesListView.vue'
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

const breadcrumbs = [
  { label: 'Email Templates', route: { name: 'Email Templates' } },
]

// emailTemplates data is loaded in the ViewControls component
const emailTemplates = ref({})
const loadMore = ref(1)

const rows = computed(() => {
  if (!emailTemplates.value?.data?.data) return []
  return emailTemplates.value?.data.data.map((emailTemplate) => {
    let _rows = {}
    emailTemplates.value?.data.rows.forEach((row) => {
      _rows[row] = emailTemplate[row]

      if (row === 'status') {
        _rows[row] = {
          label: statusLabelMap[emailTemplate.status],
          color: statusColorMap[emailTemplate.status],
        }
      } else if (['modified', 'creation'].includes(row)) {
        _rows[row] = {
          label: dateFormat(emailTemplate[row], dateTooltipFormat),
          timeAgo: timeAgo(emailTemplate[row]),
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
