<template>
  <Dialog
    v-model:open="showModal"
    :title="__('Print Report: {0}', [title || reportName])"
    size="lg"
    @close="close"
  >
    <template #default>
      <div class="flex flex-col gap-4 py-1 text-ink-gray-8">
        <!-- Orientation Selector -->
        <FormControl
          v-model="orientation"
          type="select"
          :label="__('Orientation')"
          :options="[
            { label: __('Landscape (Recommended)'), value: 'Landscape' },
            { label: __('Portrait'), value: 'Portrait' },
          ]"
        />

        <!-- Include Filters Checkbox -->
        <div class="pt-2 border-t border-outline-gray-1">
          <label
            class="flex items-center gap-2 text-sm text-ink-gray-7 cursor-pointer select-none"
          >
            <Checkbox v-model="includeFilters" />
            <span>{{ __('Include applied filters in print header') }}</span>
          </label>
        </div>

        <!-- Pick Columns Section -->
        <div class="flex flex-col gap-3 pt-3 border-t border-outline-gray-1">
          <div class="flex items-center justify-between">
            <label
              class="flex items-center gap-2 text-sm font-medium text-ink-gray-8 cursor-pointer select-none"
            >
              <Checkbox v-model="pickColumns" />
              <span>{{ __('Pick Columns') }}</span>
            </label>

            <div
              v-if="pickColumns"
              class="flex items-center gap-2 text-xs text-ink-gray-5"
            >
              <button
                type="button"
                class="text-ink-blue-3 hover:underline"
                @click="selectAllColumns"
              >
                {{ __('Select All') }}
              </button>
              <span>·</span>
              <button
                type="button"
                class="text-ink-gray-5 hover:underline"
                @click="deselectAllColumns"
              >
                {{ __('Deselect All') }}
              </button>
            </div>
          </div>

          <!-- Column Checkbox Grid -->
          <div
            v-if="pickColumns"
            class="max-h-48 overflow-y-auto grid grid-cols-2 sm:grid-cols-3 gap-2 p-2.5 rounded-lg border border-outline-gray-2 bg-surface-gray-1"
          >
            <label
              v-for="col in columns"
              :key="col.key"
              class="flex items-center gap-2 text-xs text-ink-gray-7 cursor-pointer select-none p-1 rounded hover:bg-surface-gray-2"
            >
              <Checkbox
                :modelValue="selectedColumnKeys.includes(col.key)"
                @update:modelValue="toggleColumn(col.key)"
              />
              <span class="truncate">{{ col.label || col.key }}</span>
            </label>
          </div>
        </div>
      </div>
    </template>

    <template #actions>
      <div class="flex items-center justify-end gap-2">
        <Button variant="outline" :label="__('Cancel')" @click="close" />
        <Button
          variant="subtle"
          :label="__('Download PDF')"
          :iconLeft="LucideFileDown"
          :loading="isGeneratingPDF"
          @click="generatePDF"
        />
        <Button
          variant="solid"
          :label="__('Print')"
          :iconLeft="LucidePrinter"
          @click="handlePrint"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import LucidePrinter from '~icons/lucide/printer'
import LucideFileDown from '~icons/lucide/file-down'
import {
  generateReportPrintHTML,
  isExpectedFileResponse,
  printHTML,
  triggerDownload,
} from '@/utils/reports'
import { Dialog, Button, Checkbox, FormControl, toast } from 'frappe-ui'
import { ref, computed, watch } from 'vue'

const props = defineProps<{
  open: boolean
  reportName: string
  title?: string
  // keyed by label, with display values
  appliedFilters?: Record<string, any>
  columns?: Array<{
    key: string
    label: string
    align?: string
    [key: string]: any
  }>
  rows?: Array<Record<string, any>>
  totalRow?: Record<string, any> | null
  visibleColumnKeys?: string[]
  formatValue?: (row: Record<string, any>, column: any) => string
}>()

const emit = defineEmits<{
  (e: 'update:open', val: boolean): void
}>()

const showModal = computed({
  get: () => props.open,
  set: (val: boolean) => emit('update:open', val),
})

const orientation = ref<'Landscape' | 'Portrait'>('Landscape')
const includeFilters = ref(true)
const pickColumns = ref(false)
const selectedColumnKeys = ref<string[]>([])
const isGeneratingPDF = ref(false)

// Initialize selected columns from visibleColumnKeys or all columns
watch(
  () => props.open,
  (isOpen) => {
    if (isOpen) {
      if (props.visibleColumnKeys?.length) {
        selectedColumnKeys.value = [...props.visibleColumnKeys]
      } else if (props.columns?.length) {
        selectedColumnKeys.value = props.columns.map((c) => c.key)
      }
    }
  },
  { immediate: true },
)

function close() {
  showModal.value = false
}

function toggleColumn(key: string) {
  const idx = selectedColumnKeys.value.indexOf(key)
  if (idx === -1) {
    selectedColumnKeys.value.push(key)
  } else {
    selectedColumnKeys.value.splice(idx, 1)
  }
}

function selectAllColumns() {
  if (props.columns) {
    selectedColumnKeys.value = props.columns.map((c) => c.key)
  }
}

function deselectAllColumns() {
  selectedColumnKeys.value = []
}

const activeColumns = computed(() => {
  if (!props.columns) return []
  if (!pickColumns.value) {
    // If not picking custom columns, use visibleColumnKeys if available, else all columns
    if (props.visibleColumnKeys?.length) {
      const visibleSet = new Set(props.visibleColumnKeys)
      return props.columns.filter((c) => visibleSet.has(c.key))
    }
    return props.columns
  }
  const selectedSet = new Set(selectedColumnKeys.value)
  return props.columns.filter((c) => selectedSet.has(c.key))
})

function getReportHTML() {
  return generateReportPrintHTML({
    title: props.title || props.reportName,
    filters: props.appliedFilters || {},
    includeFilters: includeFilters.value,
    columns: activeColumns.value,
    rows: props.rows || [],
    totalRow: props.totalRow,
    orientation: orientation.value,
    formatValue: (value, column, row) =>
      props.formatValue ? props.formatValue(row, column) : value,
  })
}

function handlePrint() {
  if (!activeColumns.value.length) {
    toast.error(__('Please select at least one column to print'))
    return
  }
  const html = getReportHTML()
  printHTML(html)
  close()
}

async function generatePDF() {
  if (!activeColumns.value.length) {
    toast.error(__('Please select at least one column to print'))
    return
  }
  if (isGeneratingPDF.value) return
  isGeneratingPDF.value = true

  const html = getReportHTML()

  try {
    const formData = new URLSearchParams()
    formData.append('html', html)
    formData.append('orientation', orientation.value)

    const res = await fetch(
      '/api/method/frappe.utils.print_format.report_to_pdf',
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-Frappe-CSRF-Token': (window as any).csrf_token || '',
        },
        body: formData.toString(),
      },
    )

    // only a real PDF is saved; an error page or JSON falls back to printing
    if (isExpectedFileResponse(res, 'pdf')) {
      triggerDownload(
        await res.blob(),
        `${props.title || props.reportName}.pdf`,
      )
      toast.success(__('PDF downloaded successfully'))
      close()
      return
    }
    throw new Error(__('Server could not generate PDF'))
  } catch {
    // Fallback: trigger print dialog which supports Save to PDF natively
    toast.error(
      __('PDF generation unavailable. Opening browser print dialog...'),
    )
    printHTML(html)
    close()
  } finally {
    isGeneratingPDF.value = false
  }
}
</script>
