<template>
  <div class="mt-6 space-y-5 px-3 pb-6 sm:px-0">

    <!-- ── EXEC NOTES ────────────────────────────────────────────────────── -->
    <div class="rounded-lg border border-outline-gray-2 bg-surface-white p-4 dark:bg-surface-gray-1">
      <label
        class="mb-1 block text-xs font-medium uppercase tracking-wide text-ink-gray-4"
        for="exec-notes"
      >
        {{ __('Exec Notes') }}
      </label>
      <textarea
        id="exec-notes"
        v-model="execNotes"
        rows="4"
        :placeholder="__('Record your review notes here...')"
        class="w-full rounded-md border border-outline-gray-2 bg-surface-white p-2 text-sm text-ink-gray-9 placeholder-ink-gray-4 focus:outline-none focus:ring-2 focus:ring-outline-blue-4 dark:bg-surface-gray-1"
        @blur="saveNotes"
      />
    </div>

    <!-- ── GENERATE CONTRACT FORM ─────────────────────────────────────────── -->
    <div class="flex items-center justify-between border-b border-outline-gray-2 pb-3">
      <h3 class="text-base font-semibold text-ink-gray-9">
        {{ __('Send Contract for Signing') }}
      </h3>
    </div>

    <!-- Success banner -->
    <div
      v-if="successMsg"
      class="flex items-start gap-2 rounded-lg border border-green-200 bg-green-50 px-4 py-3 dark:border-green-800 dark:bg-green-900/20"
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        class="mt-0.5 h-4 w-4 flex-shrink-0 text-green-600 dark:text-green-400"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <polyline points="20 6 9 17 4 12"/>
      </svg>
      <p class="text-sm text-green-800 dark:text-green-300">{{ successMsg }}</p>
    </div>

    <!-- Error banner -->
    <div
      v-if="errorMsg"
      class="flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 dark:border-red-800 dark:bg-red-900/20"
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        class="mt-0.5 h-4 w-4 flex-shrink-0 text-red-600 dark:text-red-400"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <circle cx="12" cy="12" r="10"/>
        <line x1="15" y1="9" x2="9" y2="15"/>
        <line x1="9" y1="9" x2="15" y2="15"/>
      </svg>
      <p class="text-sm text-red-800 dark:text-red-300">{{ errorMsg }}</p>
    </div>

    <!-- Permission notice — visible-but-informative, never hidden -->
    <div
      v-if="!canGenerate"
      class="rounded-lg border border-amber-200 bg-amber-50 px-4 py-2.5 dark:border-amber-800 dark:bg-amber-900/20"
    >
      <p class="text-xs text-amber-700 dark:text-amber-400">
        {{ __('Sales Manager role required to generate contracts.') }}
      </p>
    </div>

    <!-- Nomination form -->
    <div class="rounded-lg border border-outline-gray-2 bg-surface-white p-4 dark:bg-surface-gray-1">
      <p class="mb-4 text-xs font-medium uppercase tracking-wide text-ink-gray-4">
        {{ __('Nominate Signatories & Approvers') }}
      </p>

      <!-- Facility Signatory -->
      <div class="mb-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div>
          <label class="mb-1 block text-xs font-medium text-ink-gray-6">
            {{ __('Facility Signatory Name') }}<span class="text-red-500">*</span>
          </label>
          <input
            v-model="facilitySignatoryName"
            type="text"
            :placeholder="__('Full legal name')"
            :disabled="formLocked"
            class="w-full rounded-lg border border-outline-gray-2 bg-surface-white px-3 py-2 text-sm text-ink-gray-9 placeholder-ink-gray-4 focus:outline-none focus:ring-2 focus:ring-outline-blue-4 dark:bg-surface-gray-2 disabled:cursor-not-allowed disabled:opacity-50"
          />
        </div>
        <div>
          <label class="mb-1 block text-xs font-medium text-ink-gray-6">
            {{ __('Facility Signatory Email') }}<span class="text-red-500">*</span>
          </label>
          <input
            v-model="facilitySignatoryEmail"
            type="email"
            :placeholder="__('signatory@hospital.org')"
            :disabled="formLocked"
            class="w-full rounded-lg border border-outline-gray-2 bg-surface-white px-3 py-2 text-sm text-ink-gray-9 placeholder-ink-gray-4 focus:outline-none focus:ring-2 focus:ring-outline-blue-4 dark:bg-surface-gray-2 disabled:cursor-not-allowed disabled:opacity-50"
          />
        </div>
      </div>

      <!-- Facility Witness -->
      <div class="mb-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div>
          <label class="mb-1 block text-xs font-medium text-ink-gray-6">
            {{ __('Facility Witness Name') }}<span class="text-red-500">*</span>
          </label>
          <input
            v-model="facilityWitnessName"
            type="text"
            :placeholder="__('Full legal name')"
            :disabled="formLocked"
            class="w-full rounded-lg border border-outline-gray-2 bg-surface-white px-3 py-2 text-sm text-ink-gray-9 placeholder-ink-gray-4 focus:outline-none focus:ring-2 focus:ring-outline-blue-4 dark:bg-surface-gray-2 disabled:cursor-not-allowed disabled:opacity-50"
          />
        </div>
        <div>
          <label class="mb-1 block text-xs font-medium text-ink-gray-6">
            {{ __('Facility Witness Email') }}<span class="text-red-500">*</span>
          </label>
          <input
            v-model="facilityWitnessEmail"
            type="email"
            :placeholder="__('witness@hospital.org')"
            :disabled="formLocked"
            class="w-full rounded-lg border border-outline-gray-2 bg-surface-white px-3 py-2 text-sm text-ink-gray-9 placeholder-ink-gray-4 focus:outline-none focus:ring-2 focus:ring-outline-blue-4 dark:bg-surface-gray-2 disabled:cursor-not-allowed disabled:opacity-50"
          />
        </div>
      </div>

      <!-- Internal approvers -->
      <div class="mb-6 grid grid-cols-1 gap-3 sm:grid-cols-3">
        <div>
          <label class="mb-1 block text-xs font-medium text-ink-gray-6">
            {{ __('Network Approver 1') }}<span class="text-red-500">*</span>
          </label>
          <div :class="{ 'pointer-events-none opacity-50': formLocked }">
            <Combobox
              :model-value="networkApprover1"
              :options="userOptions"
              :placeholder="__('Search user...')"
              @update:model-value="networkApprover1 = $event"
            />
          </div>
        </div>
        <div>
          <label class="mb-1 block text-xs font-medium text-ink-gray-6">
            {{ __('Network Approver 2') }}<span class="text-red-500">*</span>
          </label>
          <div :class="{ 'pointer-events-none opacity-50': formLocked }">
            <Combobox
              :model-value="networkApprover2"
              :options="userOptions"
              :placeholder="__('Search user...')"
              @update:model-value="networkApprover2 = $event"
            />
          </div>
        </div>
        <div>
          <label class="mb-1 block text-xs font-medium text-ink-gray-6">
            {{ __('Tiberbu Approver') }}<span class="text-red-500">*</span>
          </label>
          <div :class="{ 'pointer-events-none opacity-50': formLocked }">
            <Combobox
              :model-value="tiberbuApprover"
              :options="userOptions"
              :placeholder="__('Search user...')"
              @update:model-value="tiberbuApprover = $event"
            />
          </div>
        </div>
      </div>

      <!-- Action row -->
      <div class="flex flex-wrap items-center justify-end gap-3">
        <span v-if="contractExists && !successMsg" class="text-xs text-ink-gray-5">
          {{ __('Contract already generated — see lifecycle strip below.') }}
        </span>
        <Button
          v-if="contractExists"
          variant="subtle"
          :loading="downloadLoading"
          @click="doDownloadPdf"
        >
          <template #prefix>
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-3.5 w-3.5"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="7 10 12 15 17 10"/>
              <line x1="12" y1="15" x2="12" y2="3"/>
            </svg>
          </template>
          {{ __('Download PDF') }}
        </Button>
        <Button
          variant="solid"
          :disabled="generateDisabled"
          :loading="isGenerating"
          @click="doGenerate"
        >
          {{ __('Generate Contract') }}
        </Button>
      </div>
    </div>

    <!-- ── LIFECYCLE STRIP ───────────────────────────────────────────────── -->
    <div class="rounded-lg border border-outline-gray-2 bg-surface-white p-4 dark:bg-surface-gray-1">
      <p class="mb-3 text-xs font-medium uppercase tracking-wide text-ink-gray-4">
        {{ __('Deal Progress') }}
      </p>

      <!-- Loading skeleton when lifecycle prop not yet available -->
      <div v-if="!props.lifecycle" class="flex gap-2">
        <div v-for="n in 6" :key="n" class="h-14 flex-1 animate-pulse rounded-lg bg-surface-gray-2" />
      </div>

      <!-- Lifecycle cards grid -->
      <div v-else class="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:flex lg:flex-row lg:gap-3">

        <!-- Opt-In Submission -->
        <div class="rounded-lg border border-outline-gray-2 bg-surface-gray-1 p-3 dark:bg-surface-gray-2">
          <p class="mb-1 text-xs font-medium text-ink-gray-4">{{ __('Opt-In') }}</p>
          <p class="truncate text-xs font-semibold text-ink-gray-8">
            {{ lc.submission?.ref ?? '—' }}
          </p>
          <div class="mt-1.5 flex items-center gap-1">
            <span :class="statusDot(submissionStatus)" class="h-1.5 w-1.5 flex-shrink-0 rounded-full" />
            <span class="text-xs" :class="statusText(submissionStatus)">{{ __(submissionStatus) }}</span>
          </div>
        </div>

        <!-- Quote -->
        <div class="rounded-lg border border-outline-gray-2 bg-surface-gray-1 p-3 dark:bg-surface-gray-2">
          <p class="mb-1 text-xs font-medium text-ink-gray-4">{{ __('Quote') }}</p>
          <p class="truncate text-xs font-semibold text-ink-gray-8">
            {{ lc.quotation?.name ?? '—' }}
          </p>
          <div class="mt-1.5 flex items-center gap-1">
            <span :class="statusDot(quotationStatus)" class="h-1.5 w-1.5 flex-shrink-0 rounded-full" />
            <span class="text-xs" :class="statusText(quotationStatus)">{{ __(quotationStatus) }}</span>
          </div>
        </div>

        <!-- Contract -->
        <div class="rounded-lg border border-outline-gray-2 bg-surface-gray-1 p-3 dark:bg-surface-gray-2">
          <p class="mb-1 text-xs font-medium text-ink-gray-4">{{ __('Contract') }}</p>
          <p class="truncate text-xs font-semibold text-ink-gray-8">
            {{ lc.contract?.name ?? '—' }}
          </p>
          <div class="mt-1.5 flex items-center gap-1">
            <span :class="statusDot(contractStatus)" class="h-1.5 w-1.5 flex-shrink-0 rounded-full" />
            <span class="text-xs" :class="statusText(contractStatus)">{{ __(contractStatus) }}</span>
          </div>
        </div>

        <!-- Signatories -->
        <div class="rounded-lg border border-outline-gray-2 bg-surface-gray-1 p-3 dark:bg-surface-gray-2">
          <p class="mb-1.5 text-xs font-medium text-ink-gray-4">{{ __('Signatories') }}</p>
          <div v-if="!lc.signatories?.length" class="text-xs text-ink-gray-4">—</div>
          <div v-else class="space-y-1.5">
            <div
              v-for="s in lc.signatories"
              :key="s.role"
              class="flex flex-wrap items-center gap-x-1.5 gap-y-1"
            >
              <span :class="statusDot(s.status)" class="h-1.5 w-1.5 flex-shrink-0 rounded-full" />
              <span class="text-xs text-ink-gray-6">{{ __(s.role) }}</span>
              <span class="ml-auto text-xs font-medium" :class="statusText(s.status)">
                {{ __(s.status) }}
              </span>
              <!-- Resend / regenerate signing link — visible-but-disabled without permission -->
              <button
                v-if="(s.status || '').toLowerCase() === 'pending'"
                type="button"
                class="basis-full text-left text-xs underline text-ink-gray-5 hover:text-ink-gray-7 disabled:opacity-40 disabled:no-underline"
                :disabled="!canGenerate || resendingRole === s.role"
                :title="canGenerate ? __('Regenerate and re-send the signing link') : __('Sales Manager role required')"
                @click="doResend(s.role)"
              >
                {{ resendingRole === s.role ? __('Sending…') : __('Resend link') }}
              </button>
            </div>
          </div>
        </div>

        <!-- Approval -->
        <div class="rounded-lg border border-outline-gray-2 bg-surface-gray-1 p-3 dark:bg-surface-gray-2">
          <p class="mb-1 text-xs font-medium text-ink-gray-4">{{ __('Approval') }}</p>
          <p class="truncate text-xs font-semibold text-ink-gray-8">
            {{ lc.onboarding?.name ?? '—' }}
          </p>
          <div class="mt-1.5 flex items-center gap-1">
            <span :class="statusDot(approvalStatus)" class="h-1.5 w-1.5 flex-shrink-0 rounded-full" />
            <span class="text-xs" :class="statusText(approvalStatus)">{{ __(approvalStatus) }}</span>
          </div>
        </div>

        <!-- Invoice -->
        <div class="rounded-lg border border-outline-gray-2 bg-surface-gray-1 p-3 dark:bg-surface-gray-2">
          <p class="mb-1 text-xs font-medium text-ink-gray-4">{{ __('Invoice') }}</p>
          <p class="truncate text-xs font-semibold text-ink-gray-8">
            {{ lc.sales_invoice?.name ?? '—' }}
          </p>
          <div class="mt-1.5 flex items-center gap-1">
            <span :class="statusDot(invoiceStatus)" class="h-1.5 w-1.5 flex-shrink-0 rounded-full" />
            <span class="text-xs" :class="statusText(invoiceStatus)">{{ __(invoiceStatus) }}</span>
          </div>
        </div>

      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { createResource, toast, Button, Combobox } from 'frappe-ui'
import { usersStore } from '@/stores/users'
import { sessionStore } from '@/stores/session'

// ---------------------------------------------------------------------------
// Props / Emits
// ---------------------------------------------------------------------------
const props = defineProps({
  dealId:   { type: String, required: true },
  oisDoc:   { type: Object, default: null },
  lifecycle: { type: Object, default: null },
})

const emit = defineEmits(['lifecycle-reload'])

// ---------------------------------------------------------------------------
// Stores — mirrors AppSidebar.vue lines 444-445 exactly
// ---------------------------------------------------------------------------
const { user: sessionUser } = sessionStore()
const { isManager } = usersStore()

// ---------------------------------------------------------------------------
// Lifecycle alias (null-safe)
// ---------------------------------------------------------------------------
const lc = computed(() => props.lifecycle ?? {})

const contractExists = computed(() => !!lc.value.contract?.name)

// ---------------------------------------------------------------------------
// Deal doc — for exec_notes pre-fill only
// ---------------------------------------------------------------------------
const dealDocResource = createResource({
  url: 'frappe.client.get',
  makeParams: () => ({ doctype: 'CRM Deal', name: props.dealId }),
  auto: true,
})
const dealDoc = computed(() => dealDocResource.data ?? null)

// ---------------------------------------------------------------------------
// Users list for approver Comboboxes
// ---------------------------------------------------------------------------
const usersListResource = createResource({ url: 'frappe.client.get_list' })

const userOptions = computed(() =>
  (usersListResource.data ?? []).map((u) => ({
    label: u.full_name ?? u.name,
    value: u.name,
  }))
)

onMounted(async () => {
  try {
    await usersListResource.submit({
      doctype: 'User',
      fields: JSON.stringify(['name', 'full_name']),
      filters: JSON.stringify([['enabled', '=', 1]]),
      limit_page_length: 50,
      order_by: 'full_name asc',
    })
  } catch {
    // non-fatal — Combobox still usable if user types a valid email
  }
})

// ---------------------------------------------------------------------------
// OIS raw_json (parsed from prop — no fetch, parent owns the resource)
// ---------------------------------------------------------------------------
const oisRawJson = computed(() => {
  const raw = props.oisDoc?.raw_json
  if (!raw) return {}
  try { return JSON.parse(raw) } catch { return {} }
})

// ---------------------------------------------------------------------------
// Exec Notes
// ---------------------------------------------------------------------------
const execNotes      = ref('')
const execNotesReady = ref(false)

watch(
  () => dealDoc.value?.exec_notes,
  (notes) => {
    if (!execNotesReady.value && notes !== undefined) {
      execNotes.value      = notes ?? ''
      execNotesReady.value = true
    }
  },
  { immediate: true }
)

const saveNotesResource = createResource({ url: 'frappe.client.set_value' })

async function saveNotes() {
  try {
    await saveNotesResource.submit({
      doctype: 'CRM Deal',
      name: props.dealId,
      fieldname: 'exec_notes',
      value: execNotes.value,
    })
  } catch {
    // best-effort; non-fatal
  }
}

// ---------------------------------------------------------------------------
// Form state
// ---------------------------------------------------------------------------
const facilitySignatoryName  = ref('')
const facilitySignatoryEmail = ref('')
const facilityWitnessName    = ref('')
const facilityWitnessEmail   = ref('')
const networkApprover1       = ref('')
const networkApprover2       = ref('')
const tiberbuApprover        = ref('')

// Pre-fill signatory fields from oisDoc prop
// Priority: explicit fields > raw_json contact > empty
watch(
  () => props.oisDoc,
  (doc) => {
    if (!doc) return
    const explicitName  = (doc.facility_signatory_name  ?? '').trim()
    const explicitEmail = (doc.facility_signatory_email ?? '').trim()
    const rawContact    = oisRawJson.value?.contact

    if (!facilitySignatoryName.value) {
      facilitySignatoryName.value = explicitName
        || [rawContact?.first_name, rawContact?.last_name].filter(Boolean).join(' ')
    }
    if (!facilitySignatoryEmail.value) {
      facilitySignatoryEmail.value = explicitEmail || (rawContact?.email ?? '')
    }
  },
  { immediate: true }
)

// ---------------------------------------------------------------------------
// Permission check — mirrors AppSidebar.vue / existing ContractingPanel
// ---------------------------------------------------------------------------
const canGenerate = computed(() => isManager(sessionUser.value))

// ---------------------------------------------------------------------------
// Form locking + validation
// ---------------------------------------------------------------------------
const isGenerating = ref(false)

// Locked: no permission, OR contract exists, OR currently generating
const formLocked = computed(
  () => !canGenerate.value || contractExists.value || isGenerating.value
)

const formValid = computed(() =>
  facilitySignatoryName.value.trim()  !== '' &&
  facilitySignatoryEmail.value.trim() !== '' &&
  facilityWitnessName.value.trim()    !== '' &&
  facilityWitnessEmail.value.trim()   !== '' &&
  networkApprover1.value.trim()       !== '' &&
  networkApprover2.value.trim()       !== '' &&
  tiberbuApprover.value.trim()        !== ''
)

// Disabled: locked, form incomplete, or no quote yet
const generateDisabled = computed(
  () => formLocked.value || !formValid.value || !lc.value.quotation
)

// ---------------------------------------------------------------------------
// Banners
// ---------------------------------------------------------------------------
const successMsg = ref(null)
const errorMsg   = ref(null)

// ---------------------------------------------------------------------------
// Generate contract
// ---------------------------------------------------------------------------
const generateResource = createResource({ url: 'crm.api.contracts.generate' })

async function doGenerate() {
  if (generateDisabled.value) return
  isGenerating.value = true
  successMsg.value   = null
  errorMsg.value     = null
  try {
    await generateResource.submit({
      deal:                     props.dealId,
      quote:                    lc.value.quotation?.name ?? '',
      facility_signatory_name:  facilitySignatoryName.value.trim(),
      facility_signatory_email: facilitySignatoryEmail.value.trim(),
      facility_witness_name:    facilityWitnessName.value.trim(),
      facility_witness_email:   facilityWitnessEmail.value.trim(),
      network_approver_1:       networkApprover1.value.trim(),
      network_approver_2:       networkApprover2.value.trim(),
      tiberbu_approver:         tiberbuApprover.value.trim(),
    })
    successMsg.value = __(
      'Contract sent — signing invitation emailed to {0}',
      [facilitySignatoryEmail.value.trim()]
    )
    toast.success(successMsg.value)
    emit('lifecycle-reload')
  } catch (err) {
    const msg = err?.messages?.[0] ?? err?.message ?? __('Contract generation failed.')
    errorMsg.value = msg
    toast.error(msg)
  } finally {
    isGenerating.value = false
  }
}

// ---------------------------------------------------------------------------
// Resend / regenerate signing invitation
// ---------------------------------------------------------------------------
const resendResource = createResource({ url: 'crm.api.contracts.resend_invitation' })
const resendingRole  = ref('')

async function doResend(role) {
  if (!canGenerate.value || resendingRole.value) return
  resendingRole.value = role
  try {
    const res = await resendResource.submit({
      contract: lc.value.contract?.name ?? '',
      role,
    })
    toast.success(__('Signing link re-sent to {0}', [res?.email ?? role]))
    emit('lifecycle-reload')
  } catch (err) {
    const msg = err?.messages?.[0] ?? err?.message ?? __('Could not resend the signing link.')
    toast.error(msg)
  } finally {
    resendingRole.value = ''
  }
}

// ---------------------------------------------------------------------------
// Download PDF
// ---------------------------------------------------------------------------
const downloadPdfResource = createResource({ url: 'crm.api.contracts.download_pdf' })
const downloadLoading     = ref(false)

async function doDownloadPdf() {
  if (!contractExists.value) return
  downloadLoading.value = true
  try {
    const result = await downloadPdfResource.submit({
      contract: lc.value.contract.name,
    })
    const b64 = result?.pdf_b64
    if (!b64) {
      toast.error(__('PDF generation failed.'))
      return
    }
    const bytes = atob(b64)
    const arr   = new Uint8Array(bytes.length)
    for (let i = 0; i < bytes.length; i++) arr[i] = bytes.charCodeAt(i)
    const blob = new Blob([arr], { type: 'application/pdf' })
    const url  = URL.createObjectURL(blob)
    const a    = document.createElement('a')
    a.href     = url
    a.download = `contract-${lc.value.contract.name ?? 'document'}.pdf`
    a.click()
    URL.revokeObjectURL(url)
  } catch (err) {
    const msg = err?.messages?.[0] ?? err?.message ?? __('PDF download failed.')
    toast.error(msg)
  } finally {
    downloadLoading.value = false
  }
}

// ---------------------------------------------------------------------------
// Lifecycle status derived from prop
// ---------------------------------------------------------------------------

const submissionStatus = computed(() => lc.value.submission?.status  ?? 'None')
const quotationStatus  = computed(() => lc.value.quotation?.status   ?? 'None')
const contractStatus   = computed(() =>
  lc.value.contract?.workflow_state ?? lc.value.contract?.status ?? 'None'
)
const approvalStatus   = computed(() => lc.value.onboarding?.approval_status ?? 'None')
const invoiceStatus    = computed(() => {
  const inv = lc.value.sales_invoice
  if (!inv) return 'None'
  const ds = inv.docstatus ?? 0
  if (ds === 0) return 'Draft'
  if (ds === 1) return 'Submitted'
  return 'Cancelled'
})

// ---------------------------------------------------------------------------
// Status colour helpers — tokens only, never hex
// ---------------------------------------------------------------------------

/**
 * Green  = done/success  (Processed, Accepted, Signed, Approved, Submitted, Fully Executed)
 * Amber  = in-progress   (Pending, Processing, Awaiting, Draft, Sent)
 * Red    = failure/stop  (Failed, Rejected, Cancelled)
 * Gray   = absent/none
 */
function statusDot(status) {
  const s = (status ?? '').toLowerCase()
  if (['processed', 'accepted', 'signed', 'approved', 'submitted', 'fully executed'].some((k) => s.includes(k))) {
    return 'bg-green-500 dark:bg-green-400'
  }
  if (['failed', 'rejected', 'cancelled'].some((k) => s.includes(k))) {
    return 'bg-red-500 dark:bg-red-400'
  }
  if (s === 'none' || s === '') {
    return 'bg-surface-gray-4 dark:bg-surface-gray-5'
  }
  return 'bg-amber-500 dark:bg-amber-400'
}

function statusText(status) {
  const s = (status ?? '').toLowerCase()
  if (['processed', 'accepted', 'signed', 'approved', 'submitted', 'fully executed'].some((k) => s.includes(k))) {
    return 'text-green-700 dark:text-green-400'
  }
  if (['failed', 'rejected', 'cancelled'].some((k) => s.includes(k))) {
    return 'text-red-600 dark:text-red-400'
  }
  if (s === 'none' || s === '') {
    return 'text-ink-gray-4'
  }
  return 'text-amber-700 dark:text-amber-400'
}
</script>
