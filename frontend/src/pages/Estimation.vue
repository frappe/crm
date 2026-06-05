<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs" />
    </template>
    <template v-if="estimation.doc?.name" #right-header>
      <AssignTo v-model="assignees.data" doctype="CRM Estimation" :docname="props.estimationId" />
    </template>
  </LayoutHeader>

  <div v-if="estimation.doc?.name" class="flex h-full overflow-hidden">
    <!-- LEFT: Tabs -->
    <Tabs v-model="tabIndex" as="div" :tabs="tabs"
      class="flex flex-1 overflow-hidden flex-col [&_[role='tab']]:px-0 [&_[role='tab']]:shrink-0 [&_[role='tablist']]:px-5 [&_[role='tablist']::-webkit-scrollbar]:h-0 [&_[role='tablist']]:min-h-[45px] [&_[role='tablist']]:gap-7.5 [&_[role='tabpanel']:not([hidden])]:flex [&_[role='tabpanel']:not([hidden])]:grow">
      <template #tab-panel="{ tab }">
        <div v-if="tab.name === 'Data'" class="flex-1 overflow-y-auto px-5 pb-8">
          <DataFields doctype="CRM Estimation" :docname="props.estimationId" />
        </div>

        <div v-else-if="tab.name === 'Route'" class="flex-1 overflow-y-auto px-5 py-6">
          <EstimationRoute :docname="props.estimationId" />
        </div>

        <Activities v-else ref="activities" v-model:reload="reload" v-model:tabIndex="tabIndex"
          doctype="CRM Estimation" :docname="props.estimationId" :tabs="tabs" />
      </template>
    </Tabs>

    <!-- RIGHT: Sidebar -->
    <Resizer side="right" class="flex flex-col justify-between border-l">
      <div class="flex h-[45px] cursor-copy items-center border-b px-5 py-2.5 text-lg font-medium text-ink-gray-9"
        @click="copyToClipboard(props.estimationId)">
        {{ props.estimationId }}
      </div>

      <div class="flex items-center justify-start gap-5 border-b p-5">
        <Tooltip :text="__('Estimation')">
          <div class="group relative size-12">
            <Avatar size="3xl" class="size-12" :label="title" />
          </div>
        </Tooltip>
        <div class="flex flex-col gap-2.5 truncate text-ink-gray-9">
          <div class="truncate text-2xl font-medium">{{ title }}</div>
          <div class="flex gap-1.5">
            <Button :tooltip="__('Attach a File')" :icon="AttachmentIcon" @click="showFilesUploader = true" />
            <Button :tooltip="__('Delete')" variant="subtle" icon="trash-2" theme="red" @click="deleteEstimation" />
          </div>
        </div>
      </div>

      <div v-if="sections.data" class="flex flex-1 flex-col justify-between overflow-hidden">
        <SidePanelLayout :sections="sections.data" doctype="CRM Estimation" :docname="props.estimationId"
          @reload="sections.reload" />
      </div>
    </Resizer>
  </div>

  <ErrorPage v-else-if="errorTitle" :errorTitle="errorTitle" :errorMessage="errorMessage" />

  <FilesUploader v-model="showFilesUploader" doctype="CRM Estimation" :docname="props.estimationId" @after="
    () => {
      activities?.all_activities?.reload()
      changeTabTo('Attachments')
    }
  " />
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  createDocumentResource,
  createResource,
  Breadcrumbs,
  Button,
  Tabs,
  Tooltip,
  Avatar,
} from 'frappe-ui'
import LayoutHeader from '@/components/LayoutHeader.vue'
import Resizer from '@/components/Resizer.vue'
import ErrorPage from '@/components/ErrorPage.vue'
import ActivityIcon from '@/components/Icons/ActivityIcon.vue'
import CommentIcon from '@/components/Icons/CommentIcon.vue'
import DetailsIcon from '@/components/Icons/DetailsIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import AttachmentIcon from '@/components/Icons/AttachmentIcon.vue'
import Activities from '@/components/Activities/Activities.vue'
import FilesUploader from '@/components/FilesUploader/FilesUploader.vue'
import SidePanelLayout from '@/components/SidePanelLayout.vue'
import DataFields from '@/components/Activities/DataFields.vue'
import AssignTo from '@/components/AssignTo.vue'
import EstimationRoute from '@/components/Estimation/EstimationRoute.vue'
import { copyToClipboard } from '@/utils'
import { getView } from '@/utils/view'
import { useDocument } from '@/data/document'
import { useActiveTabManager } from '@/composables/useActiveTabManager'

const router = useRouter()
const route = useRoute()

const props = defineProps({
  estimationId: { type: String, required: true },
})

const errorTitle = ref('')
const errorMessage = ref('')
const reload = ref(false)
const showFilesUploader = ref(false)
const activities = ref(null)

const estimation = createDocumentResource({
  doctype: 'CRM Estimation',
  name: props.estimationId,
  cache: ['estimation', props.estimationId],
  auto: true,
  onError(err) {
    errorTitle.value = __(
      err.exc_type === 'DoesNotExistError' ? 'Estimation Not Found' : 'Error',
    )
    errorMessage.value = __(err.messages?.[0] || 'An Error Occurred')
  },
})

const sections = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_sidepanel_sections',
  params: { doctype: 'CRM Estimation' },
  auto: true,
})

// Filter item per-grid (dokumen yang dipakai DataFields): Revenue vs Expense.
const { document: gridDoc, assignees } = useDocument('CRM Estimation', props.estimationId)
if (!gridDoc.fieldPropertyOverrides) gridDoc.fieldPropertyOverrides = {}
gridDoc.fieldPropertyOverrides['revenue_items.type_id'] = {
  link_filters: JSON.stringify({ item_category: 'Revenue' }),
}
gridDoc.fieldPropertyOverrides['expense_items.type_id'] = {
  link_filters: JSON.stringify({ item_category: 'Expense' }),
}

const title = computed(
  () => estimation.doc?.customer_id || estimation.doc?.estimation_no || props.estimationId,
)

const breadcrumbs = computed(() => {
  const items = [{ label: __('Estimations'), route: { name: 'Estimations' } }]
  if (route.query.view || route.query.viewType) {
    const view = getView(route.query.view, route.query.viewType, 'CRM Estimation')
    if (view) {
      items.push({
        label: __(view.label),
        icon: view.icon,
        route: {
          name: 'Estimations',
          params: { viewType: route.query.viewType },
          query: { view: route.query.view },
        },
      })
    }
  }
  items.push({ label: title.value })
  return items
})

const tabs = computed(() => [
  { name: 'Data', label: __('Data'), icon: DetailsIcon },
  { name: 'Route', label: __('Route'), icon: DetailsIcon },
  { name: 'Activity', label: __('Activity'), icon: ActivityIcon },
  { name: 'Comments', label: __('Comments'), icon: CommentIcon },
  { name: 'Notes', label: __('Notes'), icon: NoteIcon },
  { name: 'Attachments', label: __('Attachments'), icon: AttachmentIcon },
])

const { tabIndex } = useActiveTabManager(tabs, 'lastEstimationTab')

function changeTabTo(name) {
  const idx = tabs.value.findIndex((t) => t.name === name)
  if (idx >= 0) tabIndex.value = idx
}

function deleteEstimation() {
  if (confirm(__('Delete this estimation?'))) {
    estimation.delete.submit().then(() => {
      router.push({ name: 'Estimations' })
    })
  }
}
</script>
