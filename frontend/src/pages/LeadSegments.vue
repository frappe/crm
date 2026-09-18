<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs v-model="viewControls" routeName="Lead Segments" />
    </template>
    <template #right-header>
      <CustomActions
        v-if="segmentsListView?.customListActions"
        :actions="segmentsListView.customListActions"
      />
      <Button
        variant="solid"
        :label="__('Create')"
        iconLeft="plus"
        @click="createSegment"
      />
    </template>
  </LayoutHeader>
  <ViewControls
    ref="viewControls"
    v-model="segments"
    v-model:loadMore="loadMore"
    v-model:resizeColumn="triggerResize"
    v-model:updatedPageCount="updatedPageCount"
    doctype="CRM Lead Segment"
    :options="{ allowedViews: ['list'] }"
  />
  <LeadSegmentsListView
    v-if="segments.data && rows.length"
    ref="segmentsListView"
    v-model="segments.data.page_length_count"
    v-model:list="segments"
    :rows="rows"
    :columns="columns"
    :options="{
      showTooltip: false,
      resizeColumn: true,
      rowCount: segments.data.row_count,
      totalCount: segments.data.total_count,
    }"
    @loadMore="() => loadMore++"
    @columnWidthUpdated="() => triggerResize++"
    @updatePageCount="(count) => (updatedPageCount = count)"
    @applyFilter="(data) => viewControls.applyFilter(data)"
    @selectionsChanged="
      (selections) => viewControls.updateSelections(selections)
    "
  />
  <EmptyState
    v-else-if="segments.data && !rows.length"
    name="Lead Segments"
    :icon="SegmentIcon"
  />
</template>

<script setup>
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import CustomActions from '@/components/CustomActions.vue'
import SegmentIcon from '@/components/Icons/SegmentIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import LeadSegmentsListView from '@/components/ListViews/LeadSegmentsListView.vue'
import EmptyState from '@/components/ListViews/EmptyState.vue'
import ViewControls from '@/components/ViewControls.vue'
import { useDoctypeModal } from '@/composables/doctypeModal'
import { usersStore } from '@/stores/users'
import { timestampCell } from '@/composables/useTimelinePreferences'
import { ref, computed } from 'vue'

const { getUser } = usersStore()
const { showModal } = useDoctypeModal()

const segmentsListView = ref(null)

// segments data is loaded in the ViewControls component
const segments = ref({})
const loadMore = ref(1)
const triggerResize = ref(1)
const updatedPageCount = ref(20)
const viewControls = ref(null)

const segmentCallbacks = {
  afterInsert: () => segments.value?.reload(),
  afterUpdate: () => segments.value?.reload(),
}

function createSegment() {
  showModal({
    doctype: 'CRM Lead Segment',
    title: 'Lead Segment',
    callbacks: segmentCallbacks,
  })
}

const rows = computed(() => {
  if (
    !segments.value?.data?.data ||
    !['list', 'group_by'].includes(segments.value.data.view_type)
  )
    return []
  return segments.value?.data.data.map((segment) => {
    let _rows = {}
    segments.value?.data.rows.forEach((row) => {
      _rows[row] = segment[row]

      if (row == 'assigned_to') {
        _rows[row] = {
          label: segment.assigned_to && getUser(segment.assigned_to).full_name,
          ...(segment.assigned_to && getUser(segment.assigned_to)),
        }
      } else if (['modified', 'creation'].includes(row)) {
        _rows[row] = timestampCell(segment[row])
      }
    })
    return _rows
  })
})

const columns = computed(() => {
  let _columns = segments.value?.data?.columns || []

  // Set align right for last column
  if (_columns.length) {
    _columns = _columns.map((col, index) => {
      if (index === _columns.length - 1) {
        return { ...col, align: 'right' }
      }
      return col
    })
  }

  return _columns
})
</script>
