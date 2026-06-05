<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs">
        <template #prefix="{ item }">
          <Icon v-if="item.icon" :icon="item.icon" class="mr-2 h-4" />
        </template>
      </Breadcrumbs>
    </template>
    <template v-if="!errorTitle" #right-header>
      <Button :label="__('Print')" iconLeft="printer" @click="printQuotation" />

      <AssignTo v-model="assignees.data" doctype="CRM Quotation" :docname="props.quotationId" />

      <Button v-if="canConvert" variant="solid" theme="blue" :label="__('Convert to Estimation')"
        :loading="converting" @click="confirmConvert" />

      <Button v-if="isDirty && !isConverted" variant="solid" :label="__('Save')" :loading="quotation.save.loading"
        @click="saveQuotation" />

      <Button v-if="isConverted" :label="__('Converted')" disabled>
        <template #prefix>
          <IndicatorIcon class="text-ink-green-3" />
        </template>
      </Button>

      <Dropdown v-else-if="quotation.doc && stateOptions.length" :options="stateOptions" placement="right">
        <template #default="{ open }">
          <Button v-if="quotation.doc.state" :label="quotation.doc.state"
            :iconRight="open ? 'chevron-up' : 'chevron-down'">
            <template #prefix>
              <IndicatorIcon :class="getStateColor(quotation.doc.state)" />
            </template>
          </Button>
        </template>
      </Dropdown>
    </template>
  </LayoutHeader>

  <div v-if="quotation.doc?.name" class="flex h-full overflow-hidden">
    <!-- LEFT: Tabs -->
    <Tabs v-model="tabIndex" as="div" :tabs="tabs"
      class="flex flex-1 overflow-hidden flex-col [&_[role='tab']]:px-0 [&_[role='tab']]:shrink-0 [&_[role='tablist']]:px-5 [&_[role='tablist']::-webkit-scrollbar]:h-0 [&_[role='tablist']]:min-h-[45px] [&_[role='tablist']]:gap-7.5 [&_[role='tabpanel']:not([hidden])]:flex [&_[role='tabpanel']:not([hidden])]:grow">
      <template #tab-panel="{ tab }">
        <div v-if="tab.name === 'Data'" class="flex-1 overflow-y-auto px-5 pb-8">
          <DataFields doctype="CRM Quotation" :docname="props.quotationId" />
        </div>

        <Activities v-else ref="activities" v-model:reload="reload" v-model:tabIndex="tabIndex" doctype="CRM Quotation"
          :docname="props.quotationId" :tabs="tabs" />
      </template>
    </Tabs>

    <!-- RIGHT: Sidebar -->
    <Resizer side="right" class="flex flex-col justify-between border-l">
      <!-- ID Header -->
      <div class="flex h-[45px] cursor-copy items-center border-b px-5 py-2.5 text-lg font-medium text-ink-gray-9"
        @click="copyToClipboard(props.quotationId)">
        {{ props.quotationId }}
      </div>

      <!-- Title + Actions -->
      <div class="flex items-center justify-start gap-5 border-b p-5">
        <Tooltip :text="__('Quotation')">
          <div class="group relative size-12">
            <Avatar size="3xl" class="size-12" :label="title" />
          </div>
        </Tooltip>
        <div class="flex flex-col gap-2.5 truncate text-ink-gray-9">
          <Tooltip :text="quotation.doc?.subject || __('Set a Subject')">
            <div class="truncate text-2xl font-medium">
              {{ title }}
              <span v-if="quotation.doc?.is_void" class="text-base font-semibold text-ink-red-4">({{ __('VOID') }})</span>
            </div>
          </Tooltip>
          <div class="flex gap-1.5">
            <Button :tooltip="__('Print')" icon="printer" @click="printQuotation" />
            <Button :tooltip="__('Attach a File')" :icon="AttachmentIcon" @click="showFilesUploader = true" />
            <Button v-if="!isConverted" :tooltip="quotation.doc?.is_void ? __('Unvoid') : __('Void')" variant="subtle"
              icon="slash" :theme="quotation.doc?.is_void ? 'gray' : 'orange'" @click="toggleVoid" />
            <Button :tooltip="__('Delete')" variant="subtle" icon="trash-2" theme="red" @click="deleteQuotation" />
          </div>
        </div>
      </div>

      <!-- Sidebar sections (Side Panel layout from DB) -->
      <div v-if="sections.data" class="flex flex-1 flex-col justify-between overflow-hidden">
        <SidePanelLayout :sections="sections.data" doctype="CRM Quotation" :docname="props.quotationId"
          @reload="sections.reload" />
      </div>
    </Resizer>
  </div>

  <ErrorPage v-else-if="errorTitle" :errorTitle="errorTitle" :errorMessage="errorMessage" />

  <FilesUploader v-model="showFilesUploader" doctype="CRM Quotation" :docname="props.quotationId" @after="
    () => {
      activities?.all_activities?.reload()
      changeTabTo('Attachments')
    }
  " />

  <!-- Konten cetak (tersembunyi di layar, tampil hanya saat print) -->
  <Teleport to="body">
    <div v-if="quotation.doc?.name" id="qp-print-root">
      <QuotationPrintContent :doc="quotation.doc" />
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  createDocumentResource,
  createResource,
  Breadcrumbs,
  Button,
  Dropdown,
  Tabs,
  Tooltip,
  Avatar,
  toast,
  call,
} from 'frappe-ui'
import LayoutHeader from '@/components/LayoutHeader.vue'
import Resizer from '@/components/Resizer.vue'
import ErrorPage from '@/components/ErrorPage.vue'
import Icon from '@/components/Icon.vue'
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
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
import QuotationPrintContent from '@/components/Quotation/QuotationPrintContent.vue'
import { copyToClipboard } from '@/utils'
import { getView } from '@/utils/view'
import { useDocument } from '@/data/document'
import { getMeta } from '@/stores/meta'
import { createDialog } from '@/utils/dialogs'
import { useActiveTabManager } from '@/composables/useActiveTabManager'

const router = useRouter()
const route = useRoute()

const props = defineProps({
  quotationId: { type: String, required: true },
})

const errorTitle = ref('')
const errorMessage = ref('')
const isDirty = ref(false)
const originalDoc = ref(null)
const reload = ref(false)
const showFilesUploader = ref(false)
const activities = ref(null)
const converting = ref(false)

const { getFields } = getMeta('CRM Quotation')
// Preload meta child produk supaya lock kolom grid bisa dipasang.
const productMeta = getMeta('CRM Quotation Product')

// Quotation document
const quotation = createDocumentResource({
  doctype: 'CRM Quotation',
  name: props.quotationId,
  cache: ['quotation', props.quotationId],
  auto: true,
  onSuccess(doc) {
    originalDoc.value = JSON.stringify(doc)
    isDirty.value = false
  },
  onError(err) {
    errorTitle.value = __(
      err.exc_type === 'DoesNotExistError' ? 'Quotation Not Found' : 'Error',
    )
    errorMessage.value = __(err.messages?.[0] || 'An Error Occurred')
  },
})

// Sidebar layout (Side Panel from DB)
const sections = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_sidepanel_sections',
  params: { doctype: 'CRM Quotation' },
  auto: true,
})

watch(
  () => quotation.doc,
  (newDoc) => {
    if (newDoc && originalDoc.value) {
      isDirty.value = JSON.stringify(newDoc) !== originalDoc.value
    }
  },
  { deep: true },
)

// Kalkulasi live amount + net_total pada dokumen yang dipakai grid (DataFields).
const { document: gridDoc, assignees } = useDocument('CRM Quotation', props.quotationId)
watch(
  () => (gridDoc.doc?.products || []).map((p) => `${p.qty}|${p.price}`).join(';'),
  () => {
    if (!gridDoc.doc) return
    let total = 0
    ;(gridDoc.doc.products || []).forEach((p) => {
      p.amount = (Number(p.qty) || 0) * (Number(p.price) || 0)
      total += p.amount
    })
    gridDoc.doc.net_total = total
  },
)

// Quotation yang sudah Converted → semua field (termasuk kolom grid produk) read-only.
function lockField(key) {
  if (!gridDoc.fieldPropertyOverrides) gridDoc.fieldPropertyOverrides = {}
  gridDoc.fieldPropertyOverrides[key] = {
    ...(gridDoc.fieldPropertyOverrides[key] || {}),
    read_only: 1,
  }
}

function applyConvertedLock() {
  if (gridDoc.doc?.state !== 'Converted') return
  const fields = getFields ? getFields({ restrictNoValueFields: false }) : []
  if (!fields.length) return // meta belum termuat; watcher akan fire lagi saat siap.
  fields.forEach((f) => {
    if (!f.fieldname) return
    lockField(f.fieldname)
    // Tabel child: kunci tiap kolom via dot-notation parent.child (Grid baca key ini).
    if (f.fieldtype === 'Table' && f.options) {
      const cm = getMeta(f.options)
      const childFields = cm?.getFields
        ? cm.getFields({ restrictNoValueFields: false })
        : []
      childFields.forEach((cf) => cf.fieldname && lockField(`${f.fieldname}.${cf.fieldname}`))
    }
  })
}

watch(
  () => [
    gridDoc.doc?.state,
    getFields ? getFields({ restrictNoValueFields: false }).length : 0,
    productMeta?.getFields ? productMeta.getFields({ restrictNoValueFields: false }).length : 0,
  ],
  () => applyConvertedLock(),
  { immediate: true },
)

const title = computed(() => quotation.doc?.subject || props.quotationId)

const isConverted = computed(() => quotation.doc?.state === 'Converted')
const canConvert = computed(
  () => quotation.doc && !quotation.doc.is_void && quotation.doc.state !== 'Converted',
)

const breadcrumbs = computed(() => {
  const items = [{ label: __('Quotations'), route: { name: 'Quotations' } }]

  if (route.query.view || route.query.viewType) {
    const view = getView(route.query.view, route.query.viewType, 'CRM Quotation')
    if (view) {
      items.push({
        label: __(view.label),
        icon: view.icon,
        route: {
          name: 'Quotations',
          params: { viewType: route.query.viewType },
          query: { view: route.query.view },
        },
      })
    }
  }

  items.push({ label: title.value })
  return items
})

// Tabs
const tabs = computed(() => [
  { name: 'Data', label: __('Data'), icon: DetailsIcon },
  { name: 'Activity', label: __('Activity'), icon: ActivityIcon },
  { name: 'Comments', label: __('Comments'), icon: CommentIcon },
  { name: 'Notes', label: __('Notes'), icon: NoteIcon },
  { name: 'Attachments', label: __('Attachments'), icon: AttachmentIcon },
])

const { tabIndex } = useActiveTabManager(tabs, 'lastQuotationTab')

function changeTabTo(name) {
  const idx = tabs.value.findIndex((t) => t.name === name)
  if (idx >= 0) tabIndex.value = idx
}

// State transitions
const stateOptions = computed(() => {
  const transitions = {
    Draft: ['Created'],
    Created: ['Sent'],
    Sent: ['Approved', 'Rejected'],
    Approved: [],
    Rejected: [],
    Expired: [],
  }
  const current = quotation.doc?.state || 'Draft'
  const targets = transitions[current] || []
  return targets.map((newState) => ({
    label: newState,
    onClick: () => updateState(newState),
  }))
})

function getStateColor(state) {
  return {
    Draft: 'text-ink-gray-5',
    Created: 'text-ink-blue-3',
    Sent: 'text-ink-blue-3',
    Approved: 'text-ink-green-3',
    Rejected: 'text-ink-red-4',
    Expired: 'text-ink-orange-3',
    Converted: 'text-ink-green-3',
  }[state] || 'text-ink-gray-5'
}

function updateState(newState) {
  quotation.setValue.submit({ state: newState }).then(() => {
    toast.success(__(`State updated to ${newState}`))
  })
}

async function saveQuotation() {
  try {
    await quotation.save.submit()
    originalDoc.value = JSON.stringify(quotation.doc)
    isDirty.value = false
    toast.success(__('Saved'))
  } catch (e) {
    toast.error(e.message || __('Failed to save'))
  }
}

function printQuotation() {
  // Cetak in-page: print CSS menyembunyikan UI app & menampilkan #qp-print-root.
  window.print()
}

function deleteQuotation() {
  if (confirm(__('Delete this quotation?'))) {
    quotation.delete.submit().then(() => {
      router.push({ name: 'Quotations' })
    })
  }
}

function confirmConvert() {
  createDialog({
    title: __('Convert to Estimation'),
    message: __(
      'Apakah anda yakin untuk convert ini? Setelah di-convert ke estimasi, quotation ini dianggap final dan tidak bisa diubah.',
    ),
    actions: [
      {
        label: __('Convert'),
        variant: 'solid',
        onClick: async (close) => {
          const ok = await doConvert()
          if (ok) close()
        },
      },
      {
        label: __('Batal'),
        onClick: (close) => close(),
      },
    ],
  })
}

async function doConvert() {
  converting.value = true
  try {
    const name = await call(
      'crm.fcrm.doctype.crm_quotation.crm_quotation.convert_to_estimation',
      { quotation: props.quotationId },
    )
    toast.success(__('Quotation converted to estimation'))
    router.push({ name: 'Estimation', params: { estimationId: name } })
    return true
  } catch (e) {
    toast.error(e.messages?.[0] || e.message || __('Failed to convert'))
    return false
  } finally {
    converting.value = false
  }
}

async function toggleVoid() {
  const isVoid = quotation.doc?.is_void
  let reason = null
  if (isVoid) {
    if (!confirm(__('Unvoid this quotation?'))) return
  } else {
    reason = prompt(__('Reason for voiding this quotation?'))
    if (reason === null) return
  }
  try {
    await call('crm.api.void.void_document', {
      doctype: 'CRM Quotation',
      name: props.quotationId,
      void: isVoid ? 0 : 1,
      reason,
    })
    quotation.reload()
    toast.success(isVoid ? __('Quotation unvoided') : __('Quotation voided'))
  } catch (e) {
    toast.error(e.message || __('Failed'))
  }
}
</script>

<style>
/* Print in-page: sembunyikan UI app, tampilkan hanya dokumen cetak. */
#qp-print-root {
  display: none;
}
@media print {
  body > *:not(#qp-print-root) {
    display: none !important;
  }
  #qp-print-root {
    display: block !important;
  }
}
</style>