<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs v-model="viewControls" routeName="Campaigns" />
    </template>
    <template #right-header>
      <CustomActions
        v-if="campaignsListView?.customListActions"
        :actions="campaignsListView.customListActions"
      />
      <Button
        variant="solid"
        :label="__('Create')"
        @click="showDealModal = true"
      >
        <template #prefix><FeatherIcon name="plus" class="h-4" /></template>
      </Button>
    </template>
  </LayoutHeader>
  <ViewControls
    ref="viewControls"
    v-model="campigns"
    v-model:loadMore="loadMore"
    v-model:resizeColumn="triggerResize"
    v-model:updatedPageCount="updatedPageCount"
    doctype="CRM Campaign"
    :options="{
      allowedViews: ['list'],
    }"
  />


  <CampaignsListView
    ref="campaignsListView"
    v-if="campigns.data && rows.length"
    v-model="campigns.data.page_length_count"
    v-model:list="campigns"
    :rows="rows"
    :columns="campigns.data.columns"
    :options="{
      showTooltip: true,
      resizeColumn: true,
      rowCount: campigns.data.row_count,
      totalCount: campigns.data.total_count,
    }"
    @loadMore="() => loadMore++"
    @columnWidthUpdated="() => triggerResize++"
    @updatePageCount="(count) => (updatedPageCount = count)"
    @applyFilter="(data) => viewControls.applyFilter(data)"
    @applyDefaultStatusFilter="(value) => viewControls.applyDefaultStatusFilter(value)"
    @applyLikeFilter="(data) => viewControls.applyLikeFilter(data)"
    @likeDoc="(data) => viewControls.likeDoc(data)"
  />
  <div v-else-if="campigns.data" class="flex h-full items-center justify-center">
    <div
      class="flex flex-col items-center gap-3 text-xl font-medium text-gray-500"
    >
      <DealsIcon class="h-10 w-10" />
      <span>{{ __('No {0} Found', [__('Campaigns')]) }}</span>
      <Button :label="__('Create')" @click="showDealModal = true">
        <template #prefix><FeatherIcon name="plus" class="h-4" /></template>
      </Button>
    </div>
  </div>
  <CampaignModal
    v-if="showDealModal"
    v-model="showDealModal"
    v-model:quickEntry="showQuickEntryModal"
    :defaults="defaults"
  />
</template>

<script setup>
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import CustomActions from '@/components/CustomActions.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import DealsIcon from '@/components/Icons/DealsIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import CampaignModal from '@/components/Modals/CampaignModal.vue'
import ViewControls from '@/components/ViewControls.vue'
import { globalStore } from '@/stores/global'
import { callEnabled } from '@/composables/settings'
import { useRoute } from 'vue-router'
import { ref, reactive, computed, h } from 'vue'
import CampaignsListView from '../components/ListViews/CampaignsListView.vue'

const { makeCall } = globalStore()

const route = useRoute()

const campaignsListView = ref(null)
const showDealModal = ref(false)
const showQuickEntryModal = ref(false)

const defaults = reactive({})

// campigns data is loaded in the ViewControls component
const campigns = ref({})
const loadMore = ref(1)
const triggerResize = ref(1)
const updatedPageCount = ref(20)
const viewControls = ref(null)

function getRow(name, field) {
  function getValue(value) {
    if (value && typeof value === 'object' && !Array.isArray(value)) {
      return value
    }
    return { label: value }
  }
  return getValue(rows.value?.find((row) => row.name == name)[field])
}

// Rows
const rows = computed(() => {
  if (!campigns.value?.data?.data){
    return []
  } 
  else{
    return campigns.value?.data.data
  }
})

function onNewClick(column) {
  let column_field = campigns.value.params.column_field

  if (column_field) {
    defaults[column_field] = column.column.name
  }

  showDealModal.value = true
}


function actions(itemName) {
  let mobile_no = getRow(itemName, 'mobile_no')?.label || ''
  let actions = [
    {
      icon: h(PhoneIcon, { class: 'h-4 w-4' }),
      label: __('Make a Call'),
      onClick: () => makeCall(mobile_no),
      condition: () => mobile_no && callEnabled.value,
    },
    {
      icon: h(NoteIcon, { class: 'h-4 w-4' }),
      label: __('New Note'),
      onClick: () => showNote(itemName),
    },
    {
      icon: h(TaskIcon, { class: 'h-4 w-4' }),
      label: __('New Task'),
      onClick: () => showTask(itemName),
    },
  ]
  return actions.filter((action) =>
    action.condition ? action.condition() : true,
  )
}

const docname = ref('')
const showNoteModal = ref(false)
const note = ref({
  title: '',
  content: '',
})

function showNote(name) {
  docname.value = name
  showNoteModal.value = true
}

const showTaskModal = ref(false)
const task = ref({
  title: '',
  description: '',
  assigned_to: '',
  due_date: '',
  priority: 'Low',
  status: 'Backlog',
})

function showTask(name) {
  docname.value = name
  showTaskModal.value = true
}
</script>
