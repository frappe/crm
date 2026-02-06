<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs v-model="viewControls" routeName="Enquiries" />
    </template>
    <template #right-header>
      <CustomActions
        v-if="enquiriesListView?.customListActions"
        :actions="enquiriesListView.customListActions"
      />
      <Button
        variant="solid"
        :label="__('Create enquiry')"
        iconLeft="plus"
        @click="showEnquiryModal = true"
      />
    </template>
  </LayoutHeader>
  <ViewControls
    ref="viewControls"
    v-model="enquiries"
    v-model:loadMore="loadMore"
    v-model:resizeColumn="triggerResize"
    v-model:updatedPageCount="updatedPageCount"
    doctype="CRM Enquiry"
    :options="{
      allowedViews: ['list'],
    }"
  />
  <EnquiriesListView
    ref="enquiriesListView"
    v-if="enquiries.data && rows.length"
    v-model="enquiries.data.page_length_count"
    v-model:list="enquiries"
    :rows="rows"
    :columns="columns"
    :options="{
      showTooltip: false,
      resizeColumn: true,
      rowCount: enquiries.data.row_count,
      totalCount: enquiries.data.total_count,
    }"
    @loadMore="() => loadMore++"
    @columnWidthUpdated="() => triggerResize++"
    @updatePageCount="(count) => (updatedPageCount = count)"
    @applyFilter="(data) => viewControls.applyFilter(data)"
    @applyLikeFilter="(data) => viewControls.applyLikeFilter(data)"
    @likeDoc="(data) => viewControls.likeDoc(data)"
    @selectionsChanged="
      (selections) => viewControls.updateSelections(selections)
    "
  />
  <EmptyState v-else-if="enquiries.data && !rows.length" name="enquiries" />
  <EnquiryModal v-if="showEnquiryModal" v-model="showEnquiryModal" />
</template>

<script setup>
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import CustomActions from '@/components/CustomActions.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import EnquiriesListView from '@/components/ListViews/EnquiriesListView.vue'
import EmptyState from '@/components/ListViews/EmptyState.vue'
import EnquiryModal from '@/components/Modals/EnquiryModal.vue'
import ViewControls from '@/components/ViewControls.vue'
import { usersStore } from '@/stores/users'
import { statusesStore } from '@/stores/statuses'
import { formatDate, timeAgo } from '@/utils'
import { ref, computed } from 'vue'

const { getUser } = usersStore()
const { getEnquiryStatus } = statusesStore()

const enquiriesListView = ref(null)
const showEnquiryModal = ref(false)

const enquiries = ref({})
const loadMore = ref(1)
const triggerResize = ref(1)
const updatedPageCount = ref(20)
const viewControls = ref(null)

const rows = computed(() => {
  if (!enquiries.value?.data?.data) return []
  return parseRows(enquiries.value?.data.data, enquiries.value.data.columns)
})

const columns = computed(() => {
  let _columns = enquiries.value?.data?.columns || []
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

function parseRows(rows, columns = []) {
  return rows.map((enquiry) => {
    let _rows = {}
    enquiries.value?.data.rows.forEach((row) => {
      _rows[row] = enquiry[row]

      let fieldType = columns?.find((col) => col.key == row)?.type
      if (fieldType && ['Date', 'Datetime'].includes(fieldType)) {
        _rows[row] = formatDate(enquiry[row], '', true, fieldType == 'Datetime')
      }

      if (row == 'status') {
        _rows[row] = {
          label: enquiry.status,
          color: getEnquiryStatus(enquiry.status)?.color,
        }
      } else if (row == 'enquiry_owner') {
        _rows[row] = {
          label: enquiry.enquiry_owner && getUser(enquiry.enquiry_owner).full_name,
          ...(enquiry.enquiry_owner && getUser(enquiry.enquiry_owner)),
        }
      } else if (row == '_assign') {
        let assignees = JSON.parse(enquiry._assign || '[]')
        _rows[row] = assignees.map((user) => ({
          name: user,
          image: getUser(user).user_image,
          label: getUser(user).full_name,
        }))
      } else if (['modified', 'creation'].includes(row)) {
        _rows[row] = {
          label: formatDate(enquiry[row]),
          timeAgo: __(timeAgo(enquiry[row])),
        }
      }
    })
    return _rows
  })
}
</script>
