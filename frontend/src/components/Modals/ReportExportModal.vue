<template>
  <Dialog
    v-model:open="showModal"
    :title="__('Export Report: {0}', [reportName])"
    size="md"
    @close="close"
  >
    <template #default>
      <div class="flex flex-col gap-4 py-1 text-ink-gray-8">
        <!-- File Format Selector -->
        <FormControl
          v-model="fileFormat"
          type="select"
          :label="__('File Format')"
          :options="[
            { label: 'Excel (.xlsx)', value: 'Excel' },
            { label: 'CSV (.csv)', value: 'CSV' },
          ]"
        />

        <!-- Options -->
        <div class="flex flex-col gap-2.5 pt-2 border-t border-outline-gray-1">
          <label
            class="flex items-center gap-2 text-sm text-ink-gray-7 cursor-pointer select-none"
          >
            <Checkbox v-model="includeFilters" />
            <span>{{ __('Include applied filters') }}</span>
          </label>

          <label
            class="flex items-center gap-2 text-sm text-ink-gray-7 cursor-pointer select-none"
          >
            <Checkbox v-model="includeHiddenColumns" />
            <span>{{ __('Include hidden columns') }}</span>
          </label>
        </div>

        <!-- CSV Settings (Collapsible / Visible if CSV) -->
        <div
          v-if="fileFormat === 'CSV'"
          class="flex flex-col gap-3 pt-3 border-t border-outline-gray-1"
        >
          <div
            class="text-xs font-semibold uppercase tracking-wider text-ink-gray-5"
          >
            {{ __('CSV Settings') }}
          </div>

          <div class="grid grid-cols-2 gap-3">
            <FormControl
              v-model="csvDelimiter"
              type="select"
              :label="__('Delimiter')"
              :options="[
                { label: 'Comma (,)', value: ',' },
                { label: 'Semicolon (;)', value: ';' },
                { label: 'Tab (\\t)', value: '\t' },
                { label: 'Pipe (|)', value: '|' },
              ]"
            />

            <FormControl
              v-model="csvQuoting"
              type="select"
              :label="__('Quoting')"
              :options="[
                { label: 'Non-numeric', value: 2 },
                { label: 'Minimal', value: 0 },
                { label: 'All', value: 1 },
                { label: 'None', value: 3 },
              ]"
            />
          </div>
        </div>
      </div>
    </template>

    <template #actions>
      <div class="flex items-center justify-end gap-2">
        <Button variant="outline" :label="__('Cancel')" @click="close" />
        <Button
          variant="solid"
          :label="__('Download')"
          :iconLeft="LucideDownload"
          :loading="isExporting"
          @click="handleExport"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import LucideDownload from '~icons/lucide/download'
import {
  getServerErrorMessage,
  isExpectedFileResponse,
  triggerDownload,
} from '@/utils/reports'
import { Dialog, Button, Checkbox, FormControl, toast } from 'frappe-ui'
import { ref, computed } from 'vue'

const props = defineProps<{
  open: boolean
  reportName: string
  filters?: Record<string, any>
  // keyed by label, with display values, for the "include filters" header
  appliedFilters?: Record<string, any>
  columns?: Array<{ key: string; label: string; [key: string]: any }>
}>()

const emit = defineEmits<{
  (e: 'update:open', val: boolean): void
}>()

const showModal = computed({
  get: () => props.open,
  set: (val: boolean) => emit('update:open', val),
})

const fileFormat = ref<'Excel' | 'CSV'>('Excel')
const includeFilters = ref(true)
const includeHiddenColumns = ref(false)
const csvDelimiter = ref(',')
const csvQuoting = ref(2)
const isExporting = ref(false)

function close() {
  showModal.value = false
}

async function handleExport() {
  if (isExporting.value) return
  isExporting.value = true

  const extension = fileFormat.value === 'Excel' ? 'xlsx' : 'csv'
  const filename = `${props.reportName || 'Report'}.${extension}`

  try {
    const payload = {
      report_name: props.reportName,
      file_format_type: fileFormat.value,
      filters: props.filters || {},
      applied_filters: props.appliedFilters || {},
      visible_columns: props.columns?.map((c) => c.key || c.fieldname) || [],
      include_filters: includeFilters.value ? 1 : 0,
      include_hidden_columns: includeHiddenColumns.value ? 1 : 0,
      csv_delimiter: csvDelimiter.value,
      csv_quoting: Number(csvQuoting.value),
    }

    const res = await fetch('/api/method/crm.api.report.export_report', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Frappe-CSRF-Token': (window as any).csrf_token || '',
      },
      body: JSON.stringify(payload),
    })

    // anything but the file (an error, even with status 200) is reported, not saved
    if (isExpectedFileResponse(res, extension)) {
      triggerDownload(await res.blob(), filename)
      toast.success(__('Report exported successfully'))
      close()
      return
    }

    toast.error(await getServerErrorMessage(res, __('Failed to export report')))
  } catch {
    toast.error(__('Failed to export report'))
  } finally {
    isExporting.value = false
  }
}
</script>
