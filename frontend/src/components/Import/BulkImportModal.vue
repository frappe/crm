<template>
  <Dialog v-model:open="show" :size="'3xl'">
    <template #title>
      <div class="flex items-center justify-between">
        <div class="text-xl font-semibold text-ink-gray-9">
          {{ __('Bulk Import') }}
        </div>
        <div class="text-xs font-medium text-ink-gray-5">
          {{ __('Step {0} of 4: {1}', [currentStepNumber, currentStepTitle]) }}
        </div>
      </div>
    </template>
    <template #default>
      <div class="flex flex-col gap-5 py-2">
        <!-- Wizard Step Indicators -->
        <div class="flex items-center justify-between border-b pb-3 text-sm">
          <div
            v-for="(st, idx) in steps"
            :key="st.key"
            class="flex items-center gap-2"
            :class="[
              step === st.key
                ? 'font-semibold text-ink-gray-9'
                : idx < currentStepNumber - 1
                ? 'text-ink-gray-7'
                : 'text-ink-gray-4',
            ]"
          >
            <span
              class="flex size-6 items-center justify-center rounded-full text-xs"
              :class="[
                step === st.key
                  ? 'bg-surface-gray-7 text-surface-white'
                  : idx < currentStepNumber - 1
                  ? 'bg-surface-gray-3 text-ink-gray-8'
                  : 'bg-surface-gray-2 text-ink-gray-5',
              ]"
            >
              {{ idx + 1 }}
            </span>
            <span>{{ st.title }}</span>
            <span v-if="idx < steps.length - 1" class="text-ink-gray-3">/</span>
          </div>
        </div>

        <!-- ============================================== -->
        <!-- STEP 1: SELECT FILE -->
        <!-- ============================================== -->
        <div v-if="step === 'file'" class="flex flex-col gap-4">
          <div
            class="flex min-h-[220px] cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-6 text-center transition-colors"
            :class="[
              isDragging
                ? 'border-surface-gray-7 bg-surface-gray-2'
                : selectedFile
                ? 'border-surface-gray-5 bg-surface-gray-1'
                : 'border-outline-gray-2 bg-surface-white hover:bg-surface-gray-1',
            ]"
            @dragover.prevent="isDragging = true"
            @dragleave.prevent="isDragging = false"
            @drop.prevent="onFileDrop"
            @click="triggerFileInput"
          >
            <input
              ref="fileInputRef"
              type="file"
              accept=".csv,.xlsx,.xls,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel"
              class="hidden"
              @change="onFileSelected"
            />

            <div v-if="!selectedFile" class="flex flex-col items-center gap-2">
              <div class="rounded-full bg-surface-gray-2 p-3 text-ink-gray-6">
                <svg class="size-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
              </div>
              <div class="text-base font-medium text-ink-gray-9">
                {{ __('Select File to Import') }}
              </div>
              <p class="text-sm text-ink-gray-6">
                {{ __('Drag and drop your file here, or click to browse') }}
              </p>
              <p class="text-xs text-ink-gray-5">
                {{ __('Supported formats: CSV, XLSX, XLS. First row must contain column headers.') }}
              </p>
            </div>

            <div v-else class="flex flex-col items-center gap-2">
              <div class="rounded-full bg-surface-gray-3 p-3 text-ink-gray-8">
                <svg class="size-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <div class="text-base font-semibold text-ink-gray-9">
                {{ selectedFile.name }}
              </div>
              <div class="text-xs text-ink-gray-5">
                {{ formatFileSize(selectedFile.size) }}
              </div>
              <div class="inline-flex items-center gap-1.5 rounded-full bg-surface-green-2 px-3 py-1 text-xs font-medium text-ink-green-4">
                <svg class="size-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                </svg>
                <span>{{ __('File uploaded successfully') }}</span>
              </div>
              <button
                type="button"
                class="mt-1 text-xs text-ink-red-4 hover:underline"
                @click.stop="clearSelectedFile"
              >
                {{ __('Choose a different file') }}
              </button>
            </div>
          </div>

          <ErrorMessage v-if="error" :message="error" />
        </div>

        <!-- ============================================== -->
        <!-- STEP 2: FIELD MAPPING -->
        <!-- ============================================== -->
        <div v-if="step === 'mapping'" class="flex flex-col gap-4">
          <div class="rounded-lg bg-surface-gray-2 p-3 text-xs text-ink-gray-7">
            <div class="font-medium">
              {{ __('Mapping Guidelines:') }}
            </div>
            <ul class="list-disc pl-4 pt-1 space-y-0.5 text-ink-gray-6">
              <li>{{ __('Map each column from your file to the destination CRM field.') }}</li>
              <li>{{ __('Extra file columns (notes, revenue, etc.) are safely ignored.') }}</li>
              <li>{{ __('Empty optional values are treated as empty and will not fail the import.') }}</li>
            </ul>
          </div>

          <div class="max-h-[380px] overflow-y-auto rounded-lg border border-outline-gray-2">
            <table class="w-full text-left text-sm">
              <thead class="sticky top-0 bg-surface-gray-2 font-medium text-ink-gray-7">
                <tr>
                  <th class="px-4 py-2.5 w-1/2">{{ __('Uploaded File Column') }}</th>
                  <th class="px-4 py-2.5 w-1/2">{{ __('CRM Destination Field') }}</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-outline-gray-1 bg-surface-white">
                <tr
                  v-for="(crmField, idx) in crmDestinationFields"
                  :key="crmField.fieldname"
                  class="hover:bg-surface-gray-1"
                >
                  <td class="px-4 py-2.5">
                    <div class="font-medium text-ink-gray-9">
                      {{ crmField.label }}
                      <span v-if="crmField.required" class="text-ink-red-4">*</span>
                    </div>
                    <div class="text-xs text-ink-gray-5">
                      {{ crmField.description }}
                    </div>
                  </td>
                  <td class="px-4 py-2.5">
                    <select
                      v-model="fieldMapping[crmField.fieldname]"
                      class="w-full rounded-md border border-outline-gray-2 bg-surface-white px-3 py-1.5 text-sm text-ink-gray-9 focus:border-surface-gray-7 focus:outline-none"
                    >
                      <option value="">
                        {{ __('— Skip / None —') }}
                      </option>
                      <option
                        v-for="col in parsedData.columns"
                        :key="col"
                        :value="col"
                      >
                        {{ col }}
                      </option>
                    </select>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <ErrorMessage v-if="error" :message="error" />
        </div>

        <!-- ============================================== -->
        <!-- STEP 3: PREVIEW -->
        <!-- ============================================== -->
        <div v-if="step === 'preview'" class="flex flex-col gap-4">
          <!-- Metrics Cards -->
          <div class="grid grid-cols-2 gap-3 sm:grid-cols-5">
            <div class="rounded-lg border border-outline-gray-2 bg-surface-gray-1 p-3 text-center">
              <div class="text-2xl font-bold text-ink-gray-9">{{ previewData.total_rows }}</div>
              <div class="text-xs text-ink-gray-6">{{ __('Total Rows') }}</div>
            </div>
            <div class="rounded-lg border border-outline-gray-2 bg-surface-gray-1 p-3 text-center">
              <div class="text-2xl font-bold text-ink-green-4">{{ previewData.valid_rows }}</div>
              <div class="text-xs text-ink-gray-6">{{ __('Valid Rows') }}</div>
            </div>
            <div class="rounded-lg border border-outline-gray-2 bg-surface-gray-1 p-3 text-center">
              <div class="text-2xl font-bold text-ink-amber-5">{{ previewData.missing_values_count }}</div>
              <div class="text-xs text-ink-gray-6">{{ __('Missing Values') }}</div>
            </div>
            <div class="rounded-lg border border-outline-gray-2 bg-surface-gray-1 p-3 text-center">
              <div class="text-2xl font-bold text-ink-blue-4">{{ previewData.orgs_to_create_count }}</div>
              <div class="text-xs text-ink-gray-6">{{ __('Orgs to Create') }}</div>
            </div>
            <div class="rounded-lg border border-outline-gray-2 bg-surface-gray-1 p-3 text-center">
              <div class="text-2xl font-bold text-ink-purple-4">{{ previewData.existing_orgs_count }}</div>
              <div class="text-xs text-ink-gray-6">{{ __('Existing Orgs') }}</div>
            </div>
          </div>

          <!-- Helper notice -->
          <div class="rounded-lg bg-surface-gray-2 p-2.5 text-xs text-ink-gray-7">
            <p>
              {{ __('Sample data preview below shows how mapped fields will be imported into CRM Contact and Organization.') }}
              {{ __('Extra columns are safely ignored.') }}
            </p>
          </div>

          <!-- Sample Table -->
          <div class="max-h-[260px] overflow-auto rounded-lg border border-outline-gray-2 text-xs">
            <table class="w-full text-left">
              <thead class="sticky top-0 bg-surface-gray-2 font-medium text-ink-gray-7">
                <tr>
                  <th class="px-3 py-2">{{ __('First Name') }}</th>
                  <th class="px-3 py-2">{{ __('Last Name') }}</th>
                  <th class="px-3 py-2">{{ __('Designation') }}</th>
                  <th class="px-3 py-2">{{ __('Email') }}</th>
                  <th class="px-3 py-2">{{ __('Mobile') }}</th>
                  <th class="px-3 py-2">{{ __('Organization') }}</th>
                  <th class="px-3 py-2">{{ __('Status') }}</th>
                  <th class="px-3 py-2">{{ __('City') }}</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-outline-gray-1 bg-surface-white">
                <tr
                  v-for="(row, idx) in previewData.sample_preview"
                  :key="idx"
                  class="hover:bg-surface-gray-1"
                >
                  <td class="px-3 py-1.5 font-medium">{{ row.first_name || '—' }}</td>
                  <td class="px-3 py-1.5">{{ row.last_name || '—' }}</td>
                  <td class="px-3 py-1.5 text-ink-gray-7">{{ row.designation || '—' }}</td>
                  <td class="px-3 py-1.5">{{ row.email || '—' }}</td>
                  <td class="px-3 py-1.5">{{ row.mobile_no || '—' }}</td>
                  <td class="px-3 py-1.5 font-medium text-ink-blue-4">{{ row.organization || '—' }}</td>
                  <td class="px-3 py-1.5">
                    <span class="inline-flex rounded-full bg-surface-gray-3 px-2 py-0.5 text-[10px] font-medium">
                      {{ row.status || 'New' }}
                    </span>
                  </td>
                  <td class="px-3 py-1.5">{{ row.city || '—' }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <ErrorMessage v-if="error" :message="error" />
        </div>

        <!-- ============================================== -->
        <!-- STEP 4: EXECUTION & RESULTS -->
        <!-- ============================================== -->
        <div v-if="step === 'results'" class="flex flex-col gap-5 py-2">
          <!-- Loading state -->
          <div v-if="isImporting" class="flex flex-col items-center justify-center gap-3 py-8 text-center">
            <div class="size-8 animate-spin rounded-full border-2 border-surface-gray-7 border-t-transparent" />
            <div class="text-base font-semibold text-ink-gray-9">
              {{ __('Importing records...') }}
            </div>
            <p class="text-xs text-ink-gray-6">
              {{ __('Creating and linking Contacts, Organizations, and Addresses...') }}
            </p>
          </div>

          <!-- Finished state -->
          <div v-else class="flex flex-col gap-4">
            <div class="flex items-center gap-2.5">
              <div class="flex size-7 items-center justify-center rounded-full bg-surface-green-2 text-ink-green-4">
                <svg class="size-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <div>
                <div class="text-base font-semibold text-ink-gray-9">{{ __('Import Complete') }}</div>
                <div class="text-xs text-ink-gray-6">{{ __('Records have been imported and relationships created.') }}</div>
              </div>
            </div>

            <div class="grid grid-cols-3 gap-3">
              <div class="rounded-lg border border-outline-gray-2 bg-surface-gray-1 p-3 text-center">
                <div class="text-2xl font-bold text-ink-gray-9">{{ importResult.total }}</div>
                <div class="text-xs text-ink-gray-6">{{ __('Total Records') }}</div>
              </div>
              <div class="rounded-lg border border-outline-gray-2 bg-surface-green-2 p-3 text-center">
                <div class="text-2xl font-bold text-ink-green-4">{{ importResult.imported }}</div>
                <div class="text-xs text-ink-green-5">{{ __('Successfully Imported') }}</div>
              </div>
              <div class="rounded-lg border border-outline-gray-2 bg-surface-red-2 p-3 text-center">
                <div class="text-2xl font-bold text-ink-red-4">{{ importResult.errors?.length || 0 }}</div>
                <div class="text-xs text-ink-red-5">{{ __('Failed') }}</div>
              </div>
            </div>

            <!-- Row-level Result List -->
            <div v-if="importResult.results && importResult.results.length > 0" class="flex flex-col gap-2">
              <div class="text-xs font-semibold uppercase tracking-wider text-ink-gray-6">{{ __('Imported Records') }}</div>
              <div class="max-h-[220px] overflow-auto rounded-lg border border-outline-gray-2 text-xs">
                <table class="w-full text-left">
                  <thead class="sticky top-0 bg-surface-gray-2 font-medium text-ink-gray-7">
                    <tr>
                      <th class="px-3 py-2 w-12">{{ __('#') }}</th>
                      <th class="px-3 py-2">{{ __('Name') }}</th>
                      <th class="px-3 py-2">{{ __('Designation') }}</th>
                      <th class="px-3 py-2">{{ __('Organization') }}</th>
                      <th class="px-3 py-2">{{ __('Email') }}</th>
                      <th class="px-3 py-2 w-20 text-right">{{ __('Status') }}</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-outline-gray-1 bg-surface-white">
                    <tr v-for="(rec, idx) in importResult.results" :key="idx" class="hover:bg-surface-gray-1">
                      <td class="px-3 py-1.5 text-ink-gray-5">{{ rec.row }}</td>
                      <td class="px-3 py-1.5 font-medium text-ink-gray-9">{{ rec.name }}</td>
                      <td class="px-3 py-1.5 text-ink-gray-6">{{ rec.designation || '—' }}</td>
                      <td class="px-3 py-1.5 text-ink-blue-4">{{ rec.organization || '—' }}</td>
                      <td class="px-3 py-1.5 text-ink-gray-6">{{ rec.email || '—' }}</td>
                      <td class="px-3 py-1.5 text-right">
                        <span class="inline-flex rounded-full bg-surface-green-2 px-2 py-0.5 text-[10px] font-medium text-ink-green-4">
                          {{ __('Success') }}
                        </span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <!-- Error list if any -->
            <div
              v-if="importResult.errors && importResult.errors.length > 0"
              class="max-h-[180px] overflow-y-auto rounded-lg border border-outline-red-2 bg-surface-red-1 p-3 text-xs text-ink-red-4"
            >
              <div class="font-semibold mb-1">{{ __('Failed Records Details:') }}</div>
              <ul class="list-disc pl-4 space-y-1">
                <li v-for="(err, idx) in importResult.errors" :key="idx">
                  <span class="font-medium">Row {{ err.row }} ({{ err.name }}):</span> {{ err.message }}
                </li>
              </ul>
            </div>

            <!-- Quick Navigation Actions -->
            <div class="flex flex-wrap items-center justify-center gap-2 pt-2">
              <Button
                variant="subtle"
                :label="__('View Contacts')"
                iconLeft="lucide-users"
                @click="navigateTo('Contacts')"
              />
              <Button
                variant="subtle"
                :label="__('View Organizations')"
                iconLeft="lucide-building"
                @click="navigateTo('Organizations')"
              />
            </div>
          </div>
        </div>
      </div>
    </template>
    <template #actions>
      <div class="flex w-full justify-between gap-2">
        <div>
          <Button
            v-if="step === 'mapping' || step === 'preview'"
            variant="subtle"
            :label="__('Back')"
            :disabled="loading || isImporting"
            @click="goBack"
          />
        </div>
        <div class="flex gap-2">
          <Button
            v-if="step !== 'results'"
            variant="subtle"
            :label="__('Cancel')"
            :disabled="loading || isImporting"
            @click="show = false"
          />

          <!-- Step 1 Button -->
          <Button
            v-if="step === 'file'"
            variant="solid"
            :label="__('Next: Map Fields')"
            :disabled="!selectedFile || loading"
            :loading="loading"
            @click="processFileAndProceed"
          />

          <!-- Step 2 Button -->
          <Button
            v-if="step === 'mapping'"
            variant="solid"
            :label="__('Next: Preview')"
            :loading="loading"
            @click="previewAndProceed"
          />

          <!-- Step 3 Button -->
          <Button
            v-if="step === 'preview'"
            variant="solid"
            :label="__('Start Import')"
            :loading="loading"
            @click="startImport"
          />

          <!-- Step 4 Button -->
          <Button
            v-if="step === 'results'"
            variant="solid"
            :label="__('Done')"
            :disabled="isImporting"
            @click="finish"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { Dialog, Button, ErrorMessage, call, toast } from 'frappe-ui'
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:modelValue', 'imported'])
const router = useRouter()

const show = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
})

const steps = [
  { key: 'file', title: __('Select File') },
  { key: 'mapping', title: __('Field Mapping') },
  { key: 'preview', title: __('Preview') },
  { key: 'results', title: __('Results') },
]

const step = ref('file')
const loading = ref(false)
const isImporting = ref(false)
const error = ref('')

const selectedFile = ref(null)
const isDragging = ref(false)
const fileInputRef = ref(null)

const parsedData = reactive({
  file_token: '',
  file_name: '',
  total_rows: 0,
  columns: [],
  sample_rows: [],
  suggested_mapping: {},
})

const previewData = reactive({
  total_rows: 0,
  valid_rows: 0,
  missing_values_count: 0,
  orgs_to_create_count: 0,
  existing_orgs_count: 0,
  sample_preview: [],
})

const importResult = reactive({
  total: 0,
  imported: 0,
  skipped: 0,
  errors: [],
  results: [],
})

const crmDestinationFields = [
  { fieldname: 'first_name', label: __('First Name'), description: __('Person\'s first or given name'), required: false },
  { fieldname: 'last_name', label: __('Last Name'), description: __('Person\'s last or family name'), required: false },
  { fieldname: 'designation', label: __('Designation'), description: __('Job title or role of the contact'), required: false },
  { fieldname: 'id', label: __('ID'), description: __('Existing Record ID or Contact Name'), required: false },
  { fieldname: 'status', label: __('Status'), description: __('Contact status'), required: false },
  { fieldname: 'email', label: __('Email'), description: __('Primary email address for Contact'), required: false },
  { fieldname: 'mobile_no', label: __('Mobile Number'), description: __('Primary phone or mobile number'), required: false },
  { fieldname: 'organization', label: __('Organization Name'), description: __('Company / Organization to link or create'), required: false },
  { fieldname: 'website', label: __('Website'), description: __('Company website URL'), required: false },
  { fieldname: 'city', label: __('City'), description: __('Address City'), required: false },
  { fieldname: 'state', label: __('State'), description: __('Address State / Province'), required: false },
  { fieldname: 'country', label: __('Country'), description: __('Address Country'), required: false },
]

const fieldMapping = reactive({
  first_name: '',
  last_name: '',
  designation: '',
  id: '',
  status: '',
  email: '',
  mobile_no: '',
  organization: '',
  website: '',
  city: '',
  state: '',
  country: '',
})

const currentStepNumber = computed(() => {
  return steps.findIndex((s) => s.key === step.value) + 1
})

const currentStepTitle = computed(() => {
  const current = steps.find((s) => s.key === step.value)
  return current ? current.title : ''
})

function triggerFileInput() {
  fileInputRef.value?.click()
}

function onFileSelected(e) {
  const file = e.target.files?.[0]
  if (file) {
    handleFile(file)
  }
}

function onFileDrop(e) {
  isDragging.value = false
  const file = e.dataTransfer?.files?.[0]
  if (file) {
    handleFile(file)
  }
}

function handleFile(file) {
  error.value = ''
  const name = file.name.toLowerCase()
  if (!name.endsWith('.csv') && !name.endsWith('.xlsx') && !name.endsWith('.xls')) {
    error.value = __('Please select a valid CSV or Excel (.xlsx, .xls) file.')
    return
  }
  selectedFile.value = file
}

function clearSelectedFile() {
  selectedFile.value = null
  if (fileInputRef.value) fileInputRef.value.value = ''
}

function formatFileSize(bytes) {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

function readFileAsBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result)
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}

async function processFileAndProceed() {
  if (!selectedFile.value) return
  loading.value = true
  error.value = ''

  try {
    const base64Data = await readFileAsBase64(selectedFile.value)
    const res = await call('crm.api.import_data.parse_import_file', {
      file_content: base64Data,
      file_name: selectedFile.value.name,
    })

    parsedData.file_token = res.file_token
    parsedData.file_name = res.file_name
    parsedData.total_rows = res.total_rows
    parsedData.columns = res.columns || []
    parsedData.sample_rows = res.sample_rows || []
    parsedData.suggested_mapping = res.suggested_mapping || {}

    // Pre-populate field mappings from suggested mapping
    for (const key of Object.keys(fieldMapping)) {
      fieldMapping[key] = parsedData.suggested_mapping[key] || ''
    }

    step.value = 'mapping'
  } catch (err) {
    console.error(err)
    error.value = err.messages?.[0] || err.message || __('Failed to parse the file.')
  } finally {
    loading.value = false
  }
}

async function previewAndProceed() {
  loading.value = true
  error.value = ''

  try {
    const res = await call('crm.api.import_data.preview_import', {
      file_token: parsedData.file_token,
      column_mapping: { ...fieldMapping },
    })

    previewData.total_rows = res.total_rows
    previewData.valid_rows = res.valid_rows
    previewData.missing_values_count = res.missing_values_count
    previewData.orgs_to_create_count = res.orgs_to_create_count
    previewData.existing_orgs_count = res.existing_orgs_count
    previewData.sample_preview = res.sample_preview || []

    step.value = 'preview'
  } catch (err) {
    console.error(err)
    error.value = err.messages?.[0] || err.message || __('Failed to generate preview.')
  } finally {
    loading.value = false
  }
}

async function startImport() {
  step.value = 'results'
  isImporting.value = true
  error.value = ''

  try {
    const res = await call('crm.api.import_data.execute_bulk_import', {
      file_token: parsedData.file_token,
      column_mapping: { ...fieldMapping },
    })

    importResult.total = res.total
    importResult.imported = res.imported
    importResult.skipped = res.skipped
    importResult.errors = res.errors || []
    importResult.results = res.results || []

    toast.success(__('Import completed: {0} imported', [res.imported]))
    emit('imported', res)
  } catch (err) {
    console.error(err)
    error.value = err.messages?.[0] || err.message || __('Import failed.')
  } finally {
    isImporting.value = false
  }
}

function goBack() {
  if (step.value === 'mapping') {
    step.value = 'file'
  } else if (step.value === 'preview') {
    step.value = 'mapping'
  }
}

function finish() {
  show.value = false
  step.value = 'file'
  clearSelectedFile()
}

function navigateTo(routeName) {
  show.value = false
  router.push({ name: routeName })
}
</script>

