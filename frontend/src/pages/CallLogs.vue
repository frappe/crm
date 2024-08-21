<template>
  <LayoutHeader>
    <template #left-header>
      <div class="flex items-center">
        <router-link
          :to="{ name: 'Call Logs' }"
          class="px-0.5 py-1 text-lg font-medium focus:outline-none focus-visible:ring-2 focus-visible:ring-gray-400 text-gray-600 hover:text-gray-700"
        >
          {{ __('Call Logs') }}
        </router-link>
        <span class="mx-0.5 text-base text-gray-500" aria-hidden="true">
          /
        </span>
        <Dropdown
          v-if="viewControls"
          :options="viewControls.viewsDropdownOptions"
        >
          <template #default="{ open }">
            <Button
              variant="ghost"
              class="text-lg font-medium"
              :label="__(viewControls.currentView.label)"
            >
              <template #prefix>
                <Icon :icon="viewControls.currentView.icon" class="h-4" />
              </template>
              <template #suffix>
                <FeatherIcon
                  :name="open ? 'chevron-up' : 'chevron-down'"
                  class="h-4 text-gray-800"
                />
              </template>
            </Button>
          </template>
        </Dropdown>
      </div>
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
    @applyLikeFilter="(data) => viewControls.applyLikeFilter(data)"
    @likeDoc="(data) => viewControls.likeDoc(data)"
  />
  <div
    v-else-if="callLogs.data"
    class="flex h-full items-center justify-center"
  >
    <div
      class="flex flex-col items-center gap-3 text-xl font-medium text-gray-500"
    >
      <PhoneIcon class="h-10 w-10" />
      <span>{{ __('No {0} Found', [__('Logs')]) }}</span>
    </div>
  </div>
  <CallLogModal v-model="showCallLogModal" :name="selectedCallLog" />
</template>

<script setup>
import Icon from '@/components/Icon.vue'
import CustomActions from '@/components/CustomActions.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewControls from '@/components/ViewControls.vue'
import CallLogsListView from '@/components/ListViews/CallLogsListView.vue'
import CallLogModal from '@/components/Modals/CallLogModal.vue'
import { getCallLogDetail } from '@/utils/callLog'
import { Dropdown } from 'frappe-ui'
import { computed, ref } from 'vue'

const callLogsListView = ref(null)

// callLogs data is loaded in the ViewControls component
const callLogs = ref({})
const loadMore = ref(1)
const triggerResize = ref(1)
const updatedPageCount = ref(20)
const viewControls = ref(null)

const rows = computed(() => {
  if (
    !callLogs.value?.data?.data ||
    !['list', 'group_by'].includes(callLogs.value.data.view_type)
  )
    return []
  return callLogs.value?.data.data.map((callLog) => {
    let _rows = {}
    callLogs.value?.data.rows.forEach((row) => {
      _rows[row] = getCallLogDetail(row, callLog)
    })
    return _rows
  })
})

const showCallLogModal = ref(false)
const selectedCallLog = ref(null)

function showCallLog(name) {
  selectedCallLog.value = name
  showCallLogModal.value = true
}
</script>
