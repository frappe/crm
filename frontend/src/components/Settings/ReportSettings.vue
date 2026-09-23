<template>
  <div class="flex h-full flex-col gap-6 py-8 px-6 text-ink-gray-8">
    <!-- Header -->
    <div class="flex justify-between items-start px-2">
      <div class="flex flex-col gap-1">
        <h2 class="flex gap-2 text-2xl-semibold leading-none h-5">
          {{ __('Reports') }}
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{
            __(
              'Configure reports available under the FCRM module to display in your CRM sidebar.',
            )
          }}
        </p>
      </div>
      <div class="flex items-center space-x-2 shrink-0">
        <Button
          :label="__('Add Existing Report')"
          :iconLeft="LucidePlus"
          variant="solid"
          @click="openAddModal"
        />
      </div>
    </div>

    <!-- Configured Reports List -->
    <div class="flex-1 overflow-y-auto px-2">
      <div
        v-if="pinnedReports.loading && !pinnedReports.data"
        class="py-12 flex items-center justify-center"
      >
        <LoadingIndicator class="w-6 text-ink-gray-5" />
      </div>

      <!-- Empty State -->
      <div
        v-else-if="!pinnedReports.data?.length"
        class="py-16 flex flex-col items-center justify-center text-center rounded-lg border border-dashed border-outline-gray-2 bg-surface-gray-1 p-8"
      >
        <div
          class="size-10 rounded-full bg-surface-gray-3 flex items-center justify-center mb-3 text-ink-gray-6"
        >
          <LucideFileText class="size-5" />
        </div>
        <div class="text-base-medium text-ink-gray-8 mb-1">
          {{ __('No reports configured') }}
        </div>
        <p class="text-sm text-ink-gray-5 max-w-sm mb-4">
          {{
            __(
              'Add existing reports from the FCRM module to access them dynamically from your CRM sidebar.',
            )
          }}
        </p>
        <Button
          :label="__('Add Existing Report')"
          variant="subtle"
          :iconLeft="LucidePlus"
          @click="openAddModal"
        />
      </div>

      <!-- List of Configured Reports -->
      <div v-else class="flex flex-col divide-y divide-outline-elevation-2">
        <div
          v-for="report in pinnedReports.data"
          :key="report.name || report.report"
          class="flex items-center justify-between py-3 px-2 hover:bg-surface-gray-2 rounded-lg transition-colors group"
        >
          <div class="flex items-center gap-3 min-w-0">
            <div
              class="size-8 rounded bg-surface-gray-2 flex items-center justify-center shrink-0 text-ink-gray-6"
            >
              <LucideFileText class="size-4" />
            </div>
            <div class="flex flex-col min-w-0">
              <div class="text-base-medium text-ink-gray-8 truncate">
                {{ report.title || report.report }}
              </div>
              <div class="text-xs text-ink-gray-5 truncate">
                {{ report.report }}
              </div>
            </div>
          </div>

          <div class="flex items-center gap-2 shrink-0">
            <Button
              variant="ghost"
              :label="__('Remove')"
              class="!text-ink-red-6 hover:!bg-surface-red-2 hover:!text-ink-red-7"
              :loading="
                removingReport === report.report ||
                removingReport === report.name
              "
              @click="removeReport(report)"
            />
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Add Existing Report Modal -->
  <Dialog
    v-model:open="showAddModal"
    :title="__('Add Existing Report')"
    :size="'lg'"
    @close="closeAddModal"
  >
    <template #default>
      <div class="flex flex-col gap-4">
        <p class="text-sm text-ink-gray-6">
          {{
            __(
              'Select existing reports from the FCRM module to add to your sidebar.',
            )
          }}
        </p>

        <!-- Search Input if several reports -->
        <TextInput
          v-if="unaddedReports.length > 5 || searchQuery"
          v-model="searchQuery"
          :placeholder="__('Search reports...')"
          type="search"
        />

        <!-- Loading -->
        <div
          v-if="availableReports.loading && !availableReports.data"
          class="py-8 flex items-center justify-center"
        >
          <LoadingIndicator class="w-6 text-ink-gray-5" />
        </div>

        <!-- No Reports under FCRM module -->
        <div
          v-else-if="!availableReports.data?.length"
          class="py-8 text-center text-sm text-ink-gray-5"
        >
          {{
            __(
              'No reports found under the FCRM module. Create a Query Report or Script Report in Desk with module "FCRM" to see it here.',
            )
          }}
        </div>

        <!-- All Reports Already Added -->
        <div
          v-else-if="unaddedReports.length === 0"
          class="py-8 text-center text-sm text-ink-gray-5"
        >
          {{
            __('All available reports have already been added to your sidebar.')
          }}
        </div>

        <!-- Selectable Reports List -->
        <div v-else class="max-h-80 overflow-y-auto flex flex-col gap-1 pr-1">
          <!-- Select All -->
          <div
            v-if="filteredReports.length > 1"
            class="flex items-center justify-between py-2 px-3 text-xs font-medium text-ink-gray-6 cursor-pointer select-none bg-surface-gray-2 rounded-md mb-1"
            @click="toggleSelectAll"
          >
            <span class="flex items-center gap-2">
              <Checkbox
                :modelValue="isAllSelected"
                @click.stop="toggleSelectAll"
              />
              <span>{{ __('Select All') }}</span>
            </span>
            <span class="text-ink-gray-5">
              {{ selectedReportNames.length }} / {{ filteredReports.length }}
              {{ __('selected') }}
            </span>
          </div>

          <!-- Report Items -->
          <div
            v-for="report in filteredReports"
            :key="report.name"
            class="flex items-center justify-between py-2.5 px-3 rounded-md hover:bg-surface-gray-2 cursor-pointer select-none transition-colors"
            @click="toggleReportSelection(report.name)"
          >
            <div class="flex items-center gap-3 min-w-0">
              <Checkbox
                :modelValue="isSelected(report.name)"
                @click.stop
                @update:modelValue="() => toggleReportSelection(report.name)"
              />
              <div class="flex flex-col min-w-0">
                <div class="text-sm font-medium text-ink-gray-8 truncate">
                  {{ report.title || report.name }}
                </div>
                <div class="text-xs text-ink-gray-5 truncate">
                  {{ report.report_type }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>

    <template #actions>
      <div class="flex items-center justify-end gap-2">
        <Button
          variant="outline"
          :label="__('Cancel')"
          @click="closeAddModal"
        />
        <Button
          variant="solid"
          :label="__('Save')"
          :disabled="selectedReportNames.length === 0 || isSaving"
          :loading="isSaving"
          @click="saveReports"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import LoadingIndicator from '@/components/Icons/LoadingIndicator.vue'
import LucidePlus from '~icons/lucide/plus'
import LucideFileText from '~icons/lucide/file-text'
import {
  createResource,
  toast,
  Dialog,
  Button,
  Checkbox,
  TextInput,
} from 'frappe-ui'
import { ref, computed } from 'vue'

const showAddModal = ref(false)
const selectedReportNames = ref<string[]>([])
const searchQuery = ref('')
const isSaving = ref(false)
const removingReport = ref<string | null>(null)

// Current user's pinned reports in the sidebar
const pinnedReports = createResource({
  url: 'crm.api.report.get_pinned_reports',
  cache: 'pinnedReports',
  auto: true,
})

// All reports under FCRM / CRM module available for selection
const availableReports = createResource({
  url: 'crm.api.report.get_fcrm_reports',
  auto: true,
})

const pinReportsResource = createResource({
  url: 'crm.api.report.pin_reports',
  method: 'POST',
})

const unpinReportResource = createResource({
  url: 'crm.api.report.unpin_report',
  method: 'POST',
})

// Set of report names that are already pinned
const pinnedReportNames = computed(() => {
  const set = new Set<string>()
  if (pinnedReports.data) {
    for (const r of pinnedReports.data) {
      if (r.report) set.add(r.report)
      if (r.name) set.add(r.name)
    }
  }
  return set
})

// Unadded reports available to be added (prevents duplicates)
const unaddedReports = computed(() => {
  if (!availableReports.data) return []
  return availableReports.data.filter(
    (report: { name: string; title: string; pinned?: boolean }) =>
      !pinnedReportNames.value.has(report.name) && !report.pinned,
  )
})

// Filtered unadded reports by search query
const filteredReports = computed(() => {
  if (!searchQuery.value.trim()) return unaddedReports.value
  const query = searchQuery.value.toLowerCase().trim()
  return unaddedReports.value.filter(
    (report: { name: string; title: string }) =>
      report.name.toLowerCase().includes(query) ||
      (report.title && report.title.toLowerCase().includes(query)),
  )
})

const isAllSelected = computed(() => {
  if (!filteredReports.value.length) return false
  return filteredReports.value.every((r: { name: string }) =>
    selectedReportNames.value.includes(r.name),
  )
})

function isSelected(reportName: string) {
  return selectedReportNames.value.includes(reportName)
}

function toggleReportSelection(reportName: string) {
  const index = selectedReportNames.value.indexOf(reportName)
  if (index === -1) {
    selectedReportNames.value.push(reportName)
  } else {
    selectedReportNames.value.splice(index, 1)
  }
}

function toggleSelectAll() {
  if (isAllSelected.value) {
    const namesToUncheck = new Set(
      filteredReports.value.map((r: { name: string }) => r.name),
    )
    selectedReportNames.value = selectedReportNames.value.filter(
      (name) => !namesToUncheck.has(name),
    )
  } else {
    const currentSet = new Set(selectedReportNames.value)
    for (const r of filteredReports.value) {
      currentSet.add(r.name)
    }
    selectedReportNames.value = Array.from(currentSet)
  }
}

function openAddModal() {
  selectedReportNames.value = []
  searchQuery.value = ''
  availableReports.reload()
  showAddModal.value = true
}

function closeAddModal() {
  showAddModal.value = false
  selectedReportNames.value = []
  searchQuery.value = ''
}

async function saveReports() {
  if (!selectedReportNames.value.length || isSaving.value) return
  isSaving.value = true
  try {
    const payload = selectedReportNames.value.map((name) => {
      const rep = availableReports.data?.find((r: any) => r.name === name)
      return {
        report: name,
        title: rep?.title || name,
        icon: 'lucide-file-text',
      }
    })

    await pinReportsResource.submit({ reports: payload })
    toast.success(__('Reports added successfully'))
    showAddModal.value = false
    selectedReportNames.value = []
    searchQuery.value = ''
    pinnedReports.reload()
    availableReports.reload()
  } catch (e: any) {
    toast.error(e?.messages?.[0] || e?.message || __('Failed to add reports'))
  } finally {
    isSaving.value = false
  }
}

async function removeReport(report: { report?: string; name?: string }) {
  const reportKey = report.report || report.name
  if (!reportKey) return
  removingReport.value = reportKey
  try {
    await unpinReportResource.submit({ report: reportKey })
    toast.success(__('Report removed successfully'))
    pinnedReports.reload()
    availableReports.reload()
  } catch (e: any) {
    toast.error(e?.messages?.[0] || e?.message || __('Failed to remove report'))
  } finally {
    removingReport.value = null
  }
}
</script>
