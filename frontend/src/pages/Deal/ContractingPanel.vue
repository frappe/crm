<template>
  <div class="mt-6 space-y-5 px-3 pb-6 sm:px-0">

    <!-- ── DEAL PROGRESS (prominent hero) ─────────────────────────────────── -->
    <div class="rounded-xl border border-outline-gray-2 bg-surface-white p-5 shadow-sm dark:bg-surface-gray-1">
      <div class="mb-4 flex items-end justify-between gap-3">
        <div>
          <h3 class="text-base font-semibold text-ink-gray-9">{{ __('Deal Progress') }}</h3>
          <p class="mt-0.5 text-xs text-ink-gray-5">
            {{ __('{0} of {1} stages complete', [doneCount, stages.length]) }}
          </p>
        </div>
        <span class="text-2xl font-bold leading-none text-ink-gray-9">{{ progressPct }}%</span>
      </div>

      <!-- Overall progress bar -->
      <div class="mb-6 h-2 w-full overflow-hidden rounded-full bg-surface-gray-3">
        <div
          class="h-full rounded-full bg-green-500 transition-all duration-500 dark:bg-green-400"
          :style="{ width: progressPct + '%' }"
        />
      </div>

      <!-- Loading skeleton when lifecycle prop not yet available -->
      <div v-if="!props.lifecycle" class="flex gap-2">
        <div v-for="n in 6" :key="n" class="h-16 flex-1 animate-pulse rounded-lg bg-surface-gray-2" />
      </div>

      <!-- Stepper: vertical timeline on mobile, horizontal on lg -->
      <ol v-else class="flex flex-col gap-6 lg:flex-row lg:gap-0">
        <li
          v-for="(st, i) in stages"
          :key="st.key"
          class="relative flex flex-1 items-start gap-3 lg:flex-col lg:items-center lg:gap-0 lg:text-center"
        >
          <!-- Connector to the previous node -->
          <span
            v-if="i > 0"
            class="absolute left-4 top-[-24px] h-6 w-0.5 lg:left-auto lg:right-1/2 lg:top-4 lg:h-0.5 lg:w-full"
            :class="stages[i - 1].state === 'done' ? 'bg-green-500 dark:bg-green-400' : 'bg-surface-gray-3'"
          />

          <!-- Node circle -->
          <div
            class="relative z-10 flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full border text-xs font-semibold"
            :class="nodeClass(st.state)"
          >
            <svg
              v-if="st.state === 'done'"
              class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor"
              stroke-width="3" stroke-linecap="round" stroke-linejoin="round"
            >
              <polyline points="20 6 9 17 4 12" />
            </svg>
            <svg
              v-else-if="st.state === 'blocked'"
              class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor"
              stroke-width="3" stroke-linecap="round" stroke-linejoin="round"
            >
              <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
            </svg>
            <span v-else>{{ i + 1 }}</span>
          </div>

          <!-- Label + reference + status pill -->
          <div class="min-w-0 lg:mt-2 lg:w-full lg:px-1">
            <p class="text-xs font-semibold text-ink-gray-8">{{ __(st.label) }}</p>
            <p class="truncate text-xs text-ink-gray-5" :title="st.ref || ''">{{ st.ref || '—' }}</p>
            <span
              class="mt-1 inline-flex items-center gap-1 rounded-full bg-surface-gray-2 px-2 py-0.5 dark:bg-surface-gray-3"
            >
              <span :class="statusDot(st.status)" class="h-1.5 w-1.5 flex-shrink-0 rounded-full" />
              <span class="text-xs font-medium" :class="statusText(st.status)">{{ __(st.statusLabel) }}</span>
            </span>
          </div>
        </li>
      </ol>

      <!-- Signatory detail: edit unsigned signatories, resend/regenerate links -->
      <div
        v-if="contractExists && lc.signatories?.length"
        class="mt-6 border-t border-outline-gray-2 pt-4"
      >
        <p class="mb-2 text-xs font-medium uppercase tracking-wide text-ink-gray-4">
          {{ __('Signatories') }}
        </p>
        <div class="space-y-2">
          <div
            v-for="s in lc.signatories"
            :key="s.role"
            class="rounded-lg border border-outline-gray-2 bg-surface-gray-1 p-3 dark:bg-surface-gray-2"
          >
            <!-- Display row -->
            <div v-if="editingRole !== s.role" class="flex flex-wrap items-center gap-x-3 gap-y-1">
              <span :class="statusDot(s.status)" class="h-2 w-2 flex-shrink-0 rounded-full" />
              <div class="min-w-0">
                <p class="truncate text-sm font-medium text-ink-gray-8">{{ s.name || __(s.role) }}</p>
                <p class="truncate text-xs text-ink-gray-5">
                  {{ __(s.role) }}<template v-if="s.email"> · {{ s.email }}</template>
                </p>
              </div>
              <span class="ml-auto text-xs font-medium" :class="statusText(s.status)">{{ __(s.status) }}</span>

              <!-- Actions for still-pending signatories -->
              <div
                v-if="isPending(s.status)"
                class="flex w-full items-center gap-4 pt-1 sm:w-auto sm:basis-full sm:justify-end sm:pt-1"
              >
                <button
                  type="button"
                  class="text-xs underline text-ink-gray-6 hover:text-ink-gray-8 disabled:opacity-40 disabled:no-underline"
                  :disabled="!canGenerate || resendingRole === s.role"
                  :title="canGenerate ? __('Edit this signatory') : __('Sales Manager role required')"
                  @click="startEdit(s)"
                >
                  {{ __('Edit') }}
                </button>
                <button
                  type="button"
                  class="text-xs underline text-ink-gray-6 hover:text-ink-gray-8 disabled:opacity-40 disabled:no-underline"
                  :disabled="!canGenerate || resendingRole === s.role"
                  :title="canGenerate ? __('Regenerate and re-send the signing link') : __('Sales Manager role required')"
                  @click="doResend(s.role)"
                >
                  {{ resendingRole === s.role ? __('Sending…') : __('Resend link') }}
                </button>
              </div>
            </div>

            <!-- Inline edit form -->
            <div v-else class="space-y-2">
              <div class="grid grid-cols-1 gap-2 sm:grid-cols-2">
                <input
                  v-model="editName"
                  type="text"
                  :placeholder="__('Full legal name')"
                  class="w-full rounded-lg border border-outline-gray-2 bg-surface-white px-3 py-2 text-sm text-ink-gray-9 placeholder-ink-gray-4 focus:outline-none focus:ring-2 focus:ring-outline-blue-4 dark:bg-surface-gray-1"
                />
                <input
                  v-model="editEmail"
                  type="email"
                  :placeholder="__('signatory@hospital.org')"
                  class="w-full rounded-lg border border-outline-gray-2 bg-surface-white px-3 py-2 text-sm text-ink-gray-9 placeholder-ink-gray-4 focus:outline-none focus:ring-2 focus:ring-outline-blue-4 dark:bg-surface-gray-1"
                />
              </div>
              <p class="text-xs text-ink-gray-4">
                {{ __('Changing the email invalidates the old link and re-sends a fresh one to the new address.') }}
              </p>
              <div class="flex items-center justify-end gap-2">
                <Button variant="subtle" @click="cancelEdit">{{ __('Cancel') }}</Button>
                <Button
                  variant="solid"
                  :loading="savingEdit"
                  :disabled="!editName.trim() || !editEmail.trim()"
                  @click="saveEdit(s.role)"
                >
                  {{ __('Save') }}
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

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
        {{ __('Nominate Facility Signatory & Witness') }}
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

      <!-- Co-signatories — resolved from the network config + Opt-In Settings,
           not nominated here. Invited automatically (7-day link) once both
           facility parties have signed; each signs via the same OTP + pad. -->
      <div class="mb-6">
        <div class="mb-2 flex items-center justify-between">
          <label class="block text-xs font-medium text-ink-gray-6">
            {{ __('Network & Tiberbu Co-Signatories') }}
          </label>
          <span v-if="coSignersLoading" class="text-xs text-ink-gray-4">{{ __('Loading…') }}</span>
        </div>

        <!-- Populated: read-only chips resolved from configuration -->
        <div v-if="coSigners.length" class="space-y-2">
          <div
            v-for="(cs, i) in coSigners"
            :key="`${cs.signer_role}:${cs.email}:${i}`"
            class="flex items-center gap-3 rounded-lg border border-outline-gray-2 bg-surface-gray-1 px-3 py-2 dark:bg-surface-gray-2"
          >
            <span class="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full bg-surface-gray-3 text-xs font-semibold text-ink-gray-7 dark:bg-surface-gray-4">
              {{ initials(cs.full_name || cs.email) }}
            </span>
            <div class="min-w-0">
              <p class="truncate text-sm font-medium text-ink-gray-8">{{ cs.full_name || cs.email }}</p>
              <p class="truncate text-xs text-ink-gray-5">
                {{ __(cs.signer_role) }}<template v-if="cs.email"> · {{ cs.email }}</template>
              </p>
            </div>
          </div>
          <p class="text-xs text-ink-gray-4">
            {{ __('These co-signatories are invited automatically once the facility signatory and witness have both signed.') }}
          </p>
        </div>

        <!-- Empty: nothing configured — surfaces the config gap instead of failing silently -->
        <div
          v-else-if="!coSignersLoading"
          class="rounded-lg border border-amber-200 bg-amber-50 px-4 py-2.5 dark:border-amber-800 dark:bg-amber-900/20"
        >
          <p class="text-xs text-amber-700 dark:text-amber-400">
            {{ __('No Network Signatories are configured for this network, and no Tiberbu Signatory is set in Opt-In Settings. Configure them so the contract can be co-signed.') }}
          </p>
        </div>
      </div>

      <!-- Action row -->
      <div class="flex flex-wrap items-center justify-end gap-3">
        <span v-if="contractExists && !successMsg" class="text-xs text-ink-gray-5">
          {{ __('Contract already generated — see Deal Progress above.') }}
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

  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { createResource, toast, Button } from 'frappe-ui'
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
// Co-signatories — Network Signatories (per network) + Tiberbu Signatory,
// auto-resolved from configuration. Displayed read-only; not nominated here.
// ---------------------------------------------------------------------------
const coSignersResource = createResource({ url: 'crm.api.contracts.get_network_signatories' })
const coSignersLoading  = ref(true)

const coSigners = computed(() => coSignersResource.data?.signers ?? [])

onMounted(async () => {
  try {
    await coSignersResource.submit({ deal: props.dealId })
  } catch {
    // non-fatal — the empty-state notice covers a failed/empty resolve
  } finally {
    coSignersLoading.value = false
  }
})

function initials(nameOrEmail) {
  const s = (nameOrEmail ?? '').trim()
  if (!s) return '?'
  const parts = s.split(/[\s@.]+/).filter(Boolean)
  const first = parts[0]?.[0] ?? ''
  const second = parts.length > 1 ? (parts[1]?.[0] ?? '') : ''
  return (first + second).toUpperCase() || '?'
}

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

// Pre-fill signatory + witness fields from oisDoc prop
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

    // Witness captured during opt-in submission — pre-fill so the exec doesn't
    // have to re-key it (still editable before generating).
    if (!facilityWitnessName.value) {
      facilityWitnessName.value = (doc.facility_witness_name ?? '').trim()
    }
    if (!facilityWitnessEmail.value) {
      facilityWitnessEmail.value = (doc.facility_witness_email ?? '').trim()
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
  facilityWitnessEmail.value.trim()   !== ''
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
// Edit an unsigned signatory
// ---------------------------------------------------------------------------
const updateSignatoryResource = createResource({ url: 'crm.api.contracts.update_signatory' })
const editingRole = ref('')
const editName    = ref('')
const editEmail   = ref('')
const savingEdit  = ref(false)

function isPending(status) {
  return (status ?? '').toLowerCase() === 'pending'
}

function startEdit(s) {
  if (!canGenerate.value) return
  editingRole.value = s.role
  editName.value    = s.name ?? ''
  editEmail.value   = s.email ?? ''
}

function cancelEdit() {
  editingRole.value = ''
  editName.value    = ''
  editEmail.value   = ''
}

async function saveEdit(role) {
  if (!editName.value.trim() || !editEmail.value.trim() || savingEdit.value) return
  savingEdit.value = true
  try {
    const res = await updateSignatoryResource.submit({
      contract: lc.value.contract?.name ?? '',
      role,
      name:  editName.value.trim(),
      email: editEmail.value.trim(),
    })
    toast.success(
      res?.resent
        ? __('Signatory updated — new signing link sent to {0}', [res.email])
        : __('Signatory updated.')
    )
    cancelEdit()
    emit('lifecycle-reload')
  } catch (err) {
    const msg = err?.messages?.[0] ?? err?.message ?? __('Could not update the signatory.')
    toast.error(msg)
  } finally {
    savingEdit.value = false
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

// Signatories roll up into a single lifecycle stage.
const signatoriesStatus = computed(() => {
  const list = lc.value.signatories ?? []
  if (!list.length) return 'None'
  const signed = list.filter((s) => (s.status ?? '').toLowerCase() === 'signed').length
  if (signed === list.length) return 'Signed'
  if (signed > 0) return 'Awaiting Signatures'
  return 'Pending'
})

const signatoriesSummary = computed(() => {
  const list = lc.value.signatories ?? []
  if (!list.length) return ''
  const signed = list.filter((s) => (s.status ?? '').toLowerCase() === 'signed').length
  return __('{0} of {1} signed', [signed, list.length])
})

// ---------------------------------------------------------------------------
// Stepper model — six ordered lifecycle stages
// ---------------------------------------------------------------------------
const stages = computed(() =>
  [
    { key: 'optin',       label: 'Opt-In',      ref: lc.value.submission?.ref,     status: submissionStatus.value },
    { key: 'quote',       label: 'Quote',       ref: lc.value.quotation?.name,     status: quotationStatus.value },
    { key: 'contract',    label: 'Contract',    ref: lc.value.contract?.name,      status: contractStatus.value },
    { key: 'signatories', label: 'Signatories', ref: signatoriesSummary.value,     status: signatoriesStatus.value },
    { key: 'approval',    label: 'Approval',    ref: lc.value.onboarding?.name,    status: approvalStatus.value },
    { key: 'invoice',     label: 'Invoice',     ref: lc.value.sales_invoice?.name, status: invoiceStatus.value },
  ].map((s) => ({ ...s, state: stageState(s.status), statusLabel: s.status }))
)

const doneCount   = computed(() => stages.value.filter((s) => s.state === 'done').length)
const progressPct = computed(() =>
  stages.value.length ? Math.round((doneCount.value / stages.value.length) * 100) : 0
)

// ---------------------------------------------------------------------------
// Status colour helpers — tokens only, never hex
// ---------------------------------------------------------------------------

const DONE_KEYS    = ['processed', 'accepted', 'signed', 'approved', 'submitted', 'fully executed', 'paid']
const BLOCKED_KEYS = ['failed', 'rejected', 'cancelled']

function isDone(status) {
  const s = (status ?? '').toLowerCase()
  return DONE_KEYS.some((k) => s.includes(k))
}
function isBlocked(status) {
  const s = (status ?? '').toLowerCase()
  return BLOCKED_KEYS.some((k) => s.includes(k))
}
function isIdle(status) {
  const s = (status ?? '').toLowerCase()
  return s === '' || s === 'none'
}

/**
 * Stage node state:
 *   done    = green (completed)
 *   blocked = red   (failed/rejected/cancelled)
 *   idle    = gray  (not started)
 *   active  = amber (in progress)
 */
function stageState(status) {
  if (isBlocked(status)) return 'blocked'
  if (isDone(status)) return 'done'
  if (isIdle(status)) return 'idle'
  return 'active'
}

function nodeClass(state) {
  return {
    done:    'border-green-500 bg-green-500 text-white dark:border-green-400 dark:bg-green-400',
    active:  'border-amber-400 bg-amber-50 text-amber-600 dark:border-amber-500 dark:bg-amber-900/20 dark:text-amber-400',
    blocked: 'border-red-400 bg-red-50 text-red-600 dark:border-red-500 dark:bg-red-900/20 dark:text-red-400',
    idle:    'border-outline-gray-2 bg-surface-gray-2 text-ink-gray-4',
  }[state] ?? 'border-outline-gray-2 bg-surface-gray-2 text-ink-gray-4'
}

/**
 * Green  = done/success  (Processed, Accepted, Signed, Approved, Submitted, Fully Executed)
 * Amber  = in-progress   (Pending, Processing, Awaiting, Draft, Sent)
 * Red    = failure/stop  (Failed, Rejected, Cancelled)
 * Gray   = absent/none
 */
function statusDot(status) {
  const state = stageState(status)
  return {
    done:    'bg-green-500 dark:bg-green-400',
    blocked: 'bg-red-500 dark:bg-red-400',
    idle:    'bg-surface-gray-4 dark:bg-surface-gray-5',
    active:  'bg-amber-500 dark:bg-amber-400',
  }[state]
}

function statusText(status) {
  const state = stageState(status)
  return {
    done:    'text-green-700 dark:text-green-400',
    blocked: 'text-red-600 dark:text-red-400',
    idle:    'text-ink-gray-4',
    active:  'text-amber-700 dark:text-amber-400',
  }[state]
}
</script>
