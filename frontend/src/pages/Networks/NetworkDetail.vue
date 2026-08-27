<template>
  <div class="flex flex-col h-full overflow-y-auto px-3 pb-3 sm:px-10 sm:pb-5">

    <!-- ── NETWORK HERO CARD ─────────────────────────────────────────────── -->
    <div class="mt-4 rounded-xl border-2 border-outline-gray-2 bg-surface-white dark:bg-surface-gray-1 p-5">

      <!-- Loading skeleton -->
      <div v-if="networkResource.loading" class="space-y-2">
        <div v-for="n in 3" :key="n" class="h-4 animate-pulse rounded bg-surface-gray-2" />
      </div>

      <!-- View mode -->
      <template v-else-if="!editingNetwork">
        <div class="mb-1 flex flex-wrap items-start justify-between gap-2">
          <div class="flex flex-wrap items-center gap-2">
            <h1 class="text-xl font-bold text-ink-gray-9">{{ networkDoc?.display_name || networkSlug }}</h1>
            <span class="font-mono text-xs text-ink-gray-4">{{ networkDoc?.slug || networkSlug }}</span>
            <span :class="enabledPill(networkDoc?.enabled)">
              {{ networkDoc?.enabled ? __('Enabled') : __('Disabled') }}
            </span>
          </div>
          <div class="flex items-center gap-2">
            <router-link
              to="/networks"
              class="text-xs text-ink-gray-5 hover:text-ink-gray-7"
            >← {{ __('Back to Networks') }}</router-link>
            <Button variant="subtle" size="sm" @click="startEditNetwork">{{ __('Edit Network') }}</Button>
          </div>
        </div>
        <p class="text-sm text-ink-gray-5">
          {{ [networkDoc?.contact_email, networkDoc?.footer_legal_name].filter(Boolean).join(' · ') || '—' }}
        </p>
      </template>

      <!-- Edit mode -->
      <template v-else>
        <div class="mb-4 flex items-center justify-between">
          <h2 class="text-sm font-semibold text-ink-gray-9">{{ __('Edit Network') }}</h2>
        </div>
        <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <div class="flex flex-col gap-1">
            <label class="text-xs font-medium text-ink-gray-6">{{ __('Display Name') }} <span class="text-red-600">*</span></label>
            <input
              v-model="networkForm.display_name"
              type="text"
              class="rounded border border-outline-gray-2 bg-surface-white px-3 py-1.5 text-sm text-ink-gray-9 focus:outline-none focus:ring-2 focus:ring-red-600 dark:bg-surface-gray-3 dark:text-ink-gray-3"
            />
          </div>
          <div class="flex flex-col gap-1">
            <label class="text-xs font-medium text-ink-gray-6">{{ __('Contact Email') }}</label>
            <input
              v-model="networkForm.contact_email"
              type="email"
              class="rounded border border-outline-gray-2 bg-surface-white px-3 py-1.5 text-sm text-ink-gray-9 focus:outline-none focus:ring-2 focus:ring-red-600 dark:bg-surface-gray-3 dark:text-ink-gray-3"
            />
          </div>
          <div class="flex flex-col gap-1">
            <label class="text-xs font-medium text-ink-gray-6">{{ __('Footer Legal Name') }}</label>
            <input
              v-model="networkForm.footer_legal_name"
              type="text"
              class="rounded border border-outline-gray-2 bg-surface-white px-3 py-1.5 text-sm text-ink-gray-9 focus:outline-none focus:ring-2 focus:ring-red-600 dark:bg-surface-gray-3 dark:text-ink-gray-3"
            />
          </div>
          <div class="flex flex-col gap-1">
            <label class="text-xs font-medium text-ink-gray-6">{{ __('Logo URL') }}</label>
            <input
              v-model="networkForm.logo_url"
              type="url"
              class="rounded border border-outline-gray-2 bg-surface-white px-3 py-1.5 text-sm text-ink-gray-9 focus:outline-none focus:ring-2 focus:ring-red-600 dark:bg-surface-gray-3 dark:text-ink-gray-3"
            />
          </div>
          <div class="flex flex-col gap-1">
            <label class="text-xs font-medium text-ink-gray-6">{{ __('Primary Colour') }}</label>
            <div class="flex items-center gap-2">
              <input
                v-model="networkForm.primary_colour"
                type="color"
                class="h-8 w-10 cursor-pointer rounded border border-outline-gray-2 bg-surface-white p-0.5"
              />
              <input
                v-model="networkForm.primary_colour"
                type="text"
                class="flex-1 rounded border border-outline-gray-2 bg-surface-white px-3 py-1.5 text-sm text-ink-gray-9 focus:outline-none focus:ring-2 focus:ring-red-600 dark:bg-surface-gray-3 dark:text-ink-gray-3"
                placeholder="#e53e3e"
              />
            </div>
          </div>
          <div class="flex flex-col gap-1">
            <label class="text-xs font-medium text-ink-gray-6">{{ __('Price List Override') }}</label>
            <input
              v-model="networkForm.price_list_override"
              type="text"
              class="rounded border border-outline-gray-2 bg-surface-white px-3 py-1.5 text-sm text-ink-gray-9 focus:outline-none focus:ring-2 focus:ring-red-600 dark:bg-surface-gray-3 dark:text-ink-gray-3"
            />
          </div>
          <div class="flex flex-col gap-1">
            <label class="text-xs font-medium text-ink-gray-6">{{ __('Status') }}</label>
            <label class="flex cursor-pointer items-center gap-2 pt-1.5">
              <input
                v-model="networkForm.enabled"
                type="checkbox"
                class="h-4 w-4 rounded border-outline-gray-3 accent-red-600"
              />
              <span class="text-sm text-ink-gray-7">{{ __('Enabled') }}</span>
            </label>
          </div>
        </div>

        <p v-if="networkFormError" class="mt-2 text-xs text-red-600">{{ networkFormError }}</p>
        <div class="mt-4 flex gap-2">
          <Button variant="solid" :loading="saveNetworkResource.loading" @click="saveNetwork">{{ __('Save') }}</Button>
          <Button variant="subtle" @click="cancelEditNetwork">{{ __('Cancel') }}</Button>
        </div>
      </template>
    </div>

    <!-- ── PREQUALIFIED CONTACTS ─────────────────────────────────────────── -->
    <div class="mt-6 flex items-center justify-between">
      <h2 class="text-base font-semibold text-ink-gray-9">{{ __('Prequalified Contacts') }}</h2>
      <div class="flex gap-2">
        <Button variant="subtle" size="sm" @click="toggleCsvSection">{{ __('Import CSV') }}</Button>
        <Button variant="solid" size="sm" @click="openAddForm">{{ __('+ Add Contact') }}</Button>
      </div>
    </div>

    <!-- Loading skeleton -->
    <div v-if="facilitiesResource.loading" class="mt-4 space-y-2">
      <div v-for="n in 3" :key="n" class="h-10 animate-pulse rounded-lg bg-surface-gray-2" />
    </div>

    <!-- Empty state -->
    <div
      v-else-if="!contactRows.length && !showForm"
      class="mt-16 flex flex-col items-center gap-3 text-center"
    >
      <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 text-ink-gray-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
        <polyline points="14 2 14 8 20 8"/>
        <line x1="16" y1="13" x2="8" y2="13"/>
        <line x1="16" y1="17" x2="8" y2="17"/>
      </svg>
      <p class="text-sm font-medium text-ink-gray-5">{{ __('No prequalified contacts') }}</p>
      <p class="text-xs text-ink-gray-4">{{ __('Add facilities to this network to allow them to opt in.') }}</p>
      <Button class="mt-2" variant="solid" @click="openAddForm">{{ __('+ Add Contact') }}</Button>
    </div>

    <!-- Contacts table -->
    <div v-else-if="contactRows.length" class="mt-3 overflow-x-auto rounded-lg border border-outline-gray-2">
      <table class="w-full text-sm">
        <thead class="bg-surface-gray-1 text-xs uppercase tracking-wide text-ink-gray-5">
          <tr>
            <th class="px-4 py-2.5 text-left font-medium">{{ __('MFL Code') }}</th>
            <th class="px-4 py-2.5 text-left font-medium">{{ __('Facility Name') }}</th>
            <th class="px-4 py-2.5 text-left font-medium">{{ __('KEPH Level') }}</th>
            <th class="px-4 py-2.5 text-left font-medium">{{ __('Status') }}</th>
            <th class="px-4 py-2.5 text-left font-medium">{{ __('Contact Name') }}</th>
            <th class="px-4 py-2.5 text-left font-medium">{{ __('Contact Email') }}</th>
            <th class="px-4 py-2.5 text-right font-medium">{{ __('Actions') }}</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-outline-elevation-2">
          <tr
            v-for="row in contactRows"
            :key="row.name"
            class="transition-colors hover:bg-surface-gray-1"
          >
            <td class="px-4 py-3 font-mono text-xs font-medium text-ink-gray-9">{{ row.mfl_code }}</td>
            <td class="px-4 py-3 text-ink-gray-7">{{ row.facility_name }}</td>
            <td class="px-4 py-3 text-xs text-ink-gray-6">{{ row.keph_level || '—' }}</td>
            <td class="px-4 py-3">
              <span :class="statusPill(networkMembership(row)?.status)">
                {{ networkMembership(row)?.status || '—' }}
              </span>
            </td>
            <td class="px-4 py-3 text-xs text-ink-gray-7">{{ networkMembership(row)?.contact_name || '—' }}</td>
            <td class="px-4 py-3 text-xs text-ink-gray-6">{{ networkMembership(row)?.contact_email || '—' }}</td>
            <td class="px-4 py-3 text-right" @click.stop>
              <div class="flex items-center justify-end gap-2">
                <Button size="sm" variant="subtle" @click="editContact(row)">{{ __('Edit') }}</Button>
                <button
                  class="rounded px-2 py-1 text-xs font-medium text-red-600 hover:bg-surface-red-1 disabled:opacity-50"
                  :disabled="removingName === row.name"
                  @click="removeContact(row)"
                >
                  <span v-if="removingName === row.name" class="inline-flex items-center gap-1">
                    <span class="h-3 w-3 animate-spin rounded-full border border-red-600 border-t-transparent" />
                  </span>
                  <span v-else>{{ __('Remove') }}</span>
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Pagination -->
      <div v-if="contactTotal > pageSize" class="flex items-center justify-between border-t border-outline-gray-2 px-4 py-3">
        <span class="text-xs text-ink-gray-5">
          {{ __('Showing {0}–{1} of {2}', [page * pageSize + 1, Math.min((page + 1) * pageSize, contactTotal), contactTotal]) }}
        </span>
        <div class="flex gap-2">
          <Button size="sm" variant="subtle" :disabled="page === 0" @click="prevPage">{{ __('Prev') }}</Button>
          <Button size="sm" variant="subtle" :disabled="(page + 1) * pageSize >= contactTotal" @click="nextPage">{{ __('Next') }}</Button>
        </div>
      </div>
    </div>

    <!-- Add / Edit inline form -->
    <div v-if="showForm" class="mt-3 rounded-xl border border-outline-gray-2 bg-surface-gray-1 dark:bg-surface-gray-2 p-5">
      <h3 class="mb-4 text-sm font-semibold text-ink-gray-9">
        {{ editingFacility ? __('Edit Contact') : __('Add Contact') }}
      </h3>

      <!-- Row 1: MFL lookup -->
      <div class="mb-4 flex flex-wrap items-end gap-3">
        <div class="flex flex-col gap-1">
          <label class="text-xs font-medium text-ink-gray-6">{{ __('MFL Code') }} <span class="text-red-600">*</span></label>
          <input
            v-model="form.mfl_code"
            type="text"
            :disabled="!!editingFacility"
            class="w-32 rounded border border-outline-gray-2 bg-surface-white px-3 py-1.5 text-sm text-ink-gray-9 focus:outline-none focus:ring-2 focus:ring-red-600 disabled:opacity-50 dark:bg-surface-gray-3 dark:text-ink-gray-3"
            placeholder="12345"
          />
        </div>
        <button
          class="rounded border border-outline-gray-2 bg-surface-white px-3 py-1.5 text-sm text-ink-gray-7 hover:bg-surface-gray-2 disabled:opacity-50 dark:bg-surface-gray-3 dark:text-ink-gray-4"
          :disabled="hfrLoading"
          @click="lookupHFR"
        >
          <span v-if="hfrLoading" class="inline-flex items-center gap-1.5">
            <span class="h-3 w-3 animate-spin rounded-full border border-ink-gray-6 border-t-transparent" />
            {{ __('Looking up…') }}
          </span>
          <span v-else>{{ __('Lookup HFR') }}</span>
        </button>
        <div v-if="form.facility_name" class="flex flex-col gap-1">
          <label class="text-xs font-medium text-ink-gray-6">{{ __('Facility Name') }}</label>
          <input
            v-model="form.facility_name"
            type="text"
            class="w-56 rounded border border-outline-gray-2 bg-surface-white px-3 py-1.5 text-sm text-ink-gray-9 focus:outline-none focus:ring-2 focus:ring-red-600 dark:bg-surface-gray-3 dark:text-ink-gray-3"
          />
        </div>
        <div v-if="form.keph_level" class="flex flex-col gap-1">
          <label class="text-xs font-medium text-ink-gray-6">{{ __('KEPH Level') }}</label>
          <input
            v-model="form.keph_level"
            type="text"
            class="w-28 rounded border border-outline-gray-2 bg-surface-white px-3 py-1.5 text-sm text-ink-gray-9 focus:outline-none focus:ring-2 focus:ring-red-600 dark:bg-surface-gray-3 dark:text-ink-gray-3"
          />
        </div>
      </div>

      <!-- Row 2: Contact fields -->
      <div class="mb-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div class="flex flex-col gap-1">
          <label class="text-xs font-medium text-ink-gray-6">{{ __('Contact Name') }} <span class="text-red-600">*</span></label>
          <input
            v-model="form.contact_name"
            type="text"
            class="rounded border border-outline-gray-2 bg-surface-white px-3 py-1.5 text-sm text-ink-gray-9 focus:outline-none focus:ring-2 focus:ring-red-600 dark:bg-surface-gray-3 dark:text-ink-gray-3"
          />
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-xs font-medium text-ink-gray-6">{{ __('Contact Email') }} <span class="text-red-600">*</span></label>
          <input
            v-model="form.contact_email"
            type="email"
            class="rounded border border-outline-gray-2 bg-surface-white px-3 py-1.5 text-sm text-ink-gray-9 focus:outline-none focus:ring-2 focus:ring-red-600 dark:bg-surface-gray-3 dark:text-ink-gray-3"
          />
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-xs font-medium text-ink-gray-6">{{ __('Contact Phone') }}</label>
          <input
            v-model="form.contact_phone"
            type="tel"
            class="rounded border border-outline-gray-2 bg-surface-white px-3 py-1.5 text-sm text-ink-gray-9 focus:outline-none focus:ring-2 focus:ring-red-600 dark:bg-surface-gray-3 dark:text-ink-gray-3"
          />
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-xs font-medium text-ink-gray-6">{{ __('Status') }}</label>
          <select
            v-model="form.status"
            class="rounded border border-outline-gray-2 bg-surface-white px-3 py-1.5 text-sm text-ink-gray-7 focus:outline-none focus:ring-2 focus:ring-red-600 dark:bg-surface-gray-3 dark:text-ink-gray-4"
          >
            <option value="Active">{{ __('Active') }}</option>
            <option value="Opted In">{{ __('Opted In') }}</option>
            <option value="Declined">{{ __('Declined') }}</option>
          </select>
        </div>
      </div>

      <p v-if="formError" class="mb-2 text-xs text-red-600">{{ formError }}</p>
      <div class="flex gap-2">
        <Button variant="solid" :loading="saveLoading" @click="saveContact">{{ __('Save') }}</Button>
        <Button variant="subtle" @click="cancelForm">{{ __('Cancel') }}</Button>
      </div>
    </div>

    <!-- CSV Import section -->
    <div v-if="showCsvSection" class="mt-3 rounded-xl border border-outline-gray-2 bg-surface-gray-1 dark:bg-surface-gray-2 p-5">
      <h3 class="mb-3 text-sm font-semibold text-ink-gray-9">{{ __('Import Contacts via CSV') }}</h3>
      <p class="mb-3 text-xs text-ink-gray-5">
        {{ __('Upload a CSV file to bulk-add facilities to this network.') }}
        <button @click="downloadTemplate" class="text-ink-blue-6 underline hover:text-ink-blue-7">{{ __('Download template') }}</button>
      </p>
      <input type="file" accept=".csv" @change="onFileChange" class="mb-3 text-sm text-ink-gray-7" />

      <!-- Preview table -->
      <div v-if="csvPreviewRows.length" class="mb-3 overflow-x-auto rounded-lg border border-outline-gray-2">
        <table class="w-full text-xs">
          <thead class="bg-surface-gray-1 text-xs uppercase tracking-wide text-ink-gray-5">
            <tr>
              <th class="px-3 py-2 text-left font-medium">{{ __('Row') }}</th>
              <th class="px-3 py-2 text-left font-medium">{{ __('MFL Code') }}</th>
              <th class="px-3 py-2 text-left font-medium">{{ __('Facility Name') }}</th>
              <th class="px-3 py-2 text-left font-medium">{{ __('Contact Email') }}</th>
              <th class="px-3 py-2 text-left font-medium">{{ __('Status') }}</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-outline-elevation-2">
            <tr
              v-for="r in csvPreviewRows"
              :key="r.row"
              :class="r.error ? 'bg-red-50 dark:bg-red-900/10' : ''"
            >
              <td class="px-3 py-2 text-ink-gray-6">{{ r.row }}</td>
              <td class="px-3 py-2 font-mono text-ink-gray-9">{{ r.mfl_code }}</td>
              <td class="px-3 py-2 text-ink-gray-7">{{ r.facility_name }}</td>
              <td class="px-3 py-2 text-ink-gray-6">{{ r.contact_email }}</td>
              <td v-if="r.error" class="px-3 py-2 text-red-600">{{ r.error }}</td>
              <td v-else class="px-3 py-2 text-green-600">{{ __('OK') }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="csvFile" class="flex gap-2">
        <Button variant="solid" :loading="csvImporting" @click="importCsv">
          {{ __('Import {0} rows', [validCsvCount]) }}
        </Button>
        <Button variant="subtle" @click="clearCsv">{{ __('Clear') }}</Button>
      </div>
      <p v-if="csvResult" class="mt-2 text-sm text-ink-gray-7">{{ csvResult }}</p>
    </div>

    <div class="h-8" />
  </div>
</template>

<script setup>
import { ref, computed, reactive, watch } from 'vue'
import { createResource, Button } from 'frappe-ui'

const props = defineProps({
  networkSlug: { type: String, required: true },
})

// ── Network doc ────────────────────────────────────────────────────────────

const networkResource = createResource({
  url: 'frappe.client.get',
  makeParams: () => ({ doctype: 'CRM Opt-In Network', name: props.networkSlug }),
  auto: true,
})

const networkDoc = computed(() => networkResource.data ?? null)

// ── Network edit form ──────────────────────────────────────────────────────

const editingNetwork = ref(false)
const networkFormError = ref('')
const networkForm = reactive({
  display_name: '',
  enabled: true,
  contact_email: '',
  footer_legal_name: '',
  logo_url: '',
  primary_colour: '#e53e3e',
  price_list_override: '',
})

function startEditNetwork() {
  const doc = networkDoc.value
  Object.assign(networkForm, {
    display_name: doc?.display_name ?? '',
    enabled: !!doc?.enabled,
    contact_email: doc?.contact_email ?? '',
    footer_legal_name: doc?.footer_legal_name ?? '',
    logo_url: doc?.logo_url ?? '',
    primary_colour: doc?.primary_colour ?? '#e53e3e',
    price_list_override: doc?.price_list_override ?? '',
  })
  networkFormError.value = ''
  editingNetwork.value = true
}

function cancelEditNetwork() {
  editingNetwork.value = false
  networkFormError.value = ''
}

const saveNetworkResource = createResource({ url: 'crm.api.optin_admin.save_network' })

async function saveNetwork() {
  if (!networkForm.display_name.trim()) {
    networkFormError.value = __('Display Name is required.')
    return
  }
  networkFormError.value = ''
  const data = {
    name: props.networkSlug,
    slug: props.networkSlug,
    ...networkForm,
  }
  try {
    await saveNetworkResource.submit({ data })
    editingNetwork.value = false
    networkResource.reload()
  } catch (e) {
    networkFormError.value = e?.messages?.[0] ?? e?.message ?? __('Save failed.')
  }
}

// ── Facilities list ────────────────────────────────────────────────────────

const page = ref(0)
const pageSize = 20

const facilitiesResource = createResource({
  url: 'crm.api.optin_admin.list_facilities',
  makeParams: () => ({ network: props.networkSlug, page: page.value, page_size: pageSize }),
  auto: true,
})

const contactRows = computed(() => facilitiesResource.data?.rows ?? [])
const contactTotal = computed(() => facilitiesResource.data?.total ?? 0)

function prevPage() {
  page.value--
  facilitiesResource.reload()
}

function nextPage() {
  page.value++
  facilitiesResource.reload()
}

function networkMembership(row) {
  const memberships = row.memberships ?? []
  return memberships.find((m) => m.network === props.networkSlug) ?? memberships[0] ?? null
}

// ── Add / Edit contact form ────────────────────────────────────────────────

const showForm = ref(false)
const editingFacility = ref(null)
const formError = ref('')
const saveLoading = ref(false)
const removingName = ref(null)
const hfrLoading = ref(false)

const form = reactive({
  mfl_code: '',
  facility_name: '',
  keph_level: '',
  contact_name: '',
  contact_email: '',
  contact_phone: '',
  status: 'Active',
})

function resetForm() {
  form.mfl_code = ''
  form.facility_name = ''
  form.keph_level = ''
  form.contact_name = ''
  form.contact_email = ''
  form.contact_phone = ''
  form.status = 'Active'
  formError.value = ''
  editingFacility.value = null
}

function openAddForm() {
  resetForm()
  showForm.value = true
}

function editContact(row) {
  const m = networkMembership(row) ?? {}
  Object.assign(form, {
    mfl_code: row.mfl_code ?? '',
    facility_name: row.facility_name ?? '',
    keph_level: row.keph_level ?? '',
    contact_name: m.contact_name ?? '',
    contact_email: m.contact_email ?? '',
    contact_phone: m.contact_phone ?? '',
    status: m.status ?? 'Active',
  })
  editingFacility.value = row
  formError.value = ''
  showForm.value = true
}

function cancelForm() {
  showForm.value = false
  resetForm()
}

const hfrResource = createResource({ url: 'crm.api.optin_admin.lookup_hfr' })

async function lookupHFR() {
  if (!form.mfl_code.trim()) return
  hfrLoading.value = true
  formError.value = ''
  try {
    const result = await hfrResource.submit({ mfl_code: form.mfl_code.trim() })
    if (result) {
      form.facility_name = result.facility_name ?? form.facility_name
      form.keph_level = result.keph_level ?? form.keph_level
    }
  } catch (e) {
    formError.value = e?.messages?.[0] ?? __('HFR lookup failed.')
  } finally {
    hfrLoading.value = false
  }
}

const saveFacilityResource = createResource({ url: 'crm.api.optin_admin.save_facility' })

async function saveContact() {
  if (!form.mfl_code.trim()) { formError.value = __('MFL Code is required.'); return }
  if (!form.contact_name.trim()) { formError.value = __('Contact Name is required.'); return }
  if (!form.contact_email.trim()) { formError.value = __('Contact Email is required.'); return }
  formError.value = ''
  saveLoading.value = true
  const data = {
    mfl_code: form.mfl_code,
    facility_name: form.facility_name,
    keph_level: form.keph_level,
    memberships: [{
      network: props.networkSlug,
      status: form.status,
      contact_name: form.contact_name,
      contact_email: form.contact_email,
      contact_phone: form.contact_phone,
    }],
  }
  if (editingFacility.value?.name) data.name = editingFacility.value.name
  try {
    await saveFacilityResource.submit({ data })
    facilitiesResource.reload()
    showForm.value = false
    resetForm()
  } catch (e) {
    formError.value = e?.messages?.[0] ?? e?.message ?? __('Save failed.')
  } finally {
    saveLoading.value = false
  }
}

const deleteFacilityResource = createResource({ url: 'crm.api.optin_admin.delete_facility' })

async function removeContact(row) {
  if (!confirm(__('Remove "{0}" from this network? This cannot be undone.', [row.facility_name]))) return
  removingName.value = row.name
  try {
    await deleteFacilityResource.submit({ name: row.name })
    facilitiesResource.reload()
  } finally {
    removingName.value = null
  }
}

// ── CSV Import ─────────────────────────────────────────────────────────────

const showCsvSection = ref(false)
const csvFile = ref(null)
const csvPreviewRows = ref([])
const csvImporting = ref(false)
const csvResult = ref('')

const validCsvCount = computed(() => csvPreviewRows.value.filter((r) => !r.error).length)

function toggleCsvSection() {
  showCsvSection.value = !showCsvSection.value
}

function readFileAsText(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = (e) => resolve(e.target.result)
    reader.onerror = () => reject(new Error('File read failed'))
    reader.readAsText(file)
  })
}

const csvPreviewResource = createResource({ url: 'crm.api.optin_admin.import_facilities_csv' })
const csvImportResource = createResource({ url: 'crm.api.optin_admin.import_facilities_csv' })

async function onFileChange(e) {
  const file = e.target.files?.[0] ?? null
  csvFile.value = file
  csvPreviewRows.value = []
  csvResult.value = ''
  if (!file) return
  try {
    const csvData = await readFileAsText(file)
    const result = await csvPreviewResource.submit({
      csv_data: csvData,
      network_slug: props.networkSlug,
      dry_run: 1,
    })
    csvPreviewRows.value = result?.rows ?? []
  } catch (e) {
    csvResult.value = e?.messages?.[0] ?? __('Preview failed.')
  }
}

async function importCsv() {
  if (!csvFile.value) return
  csvImporting.value = true
  csvResult.value = ''
  try {
    const csvData = await readFileAsText(csvFile.value)
    const result = await csvImportResource.submit({
      csv_data: csvData,
      network_slug: props.networkSlug,
      dry_run: 0,
    })
    const imported = result?.imported ?? 0
    const errors = result?.errors ?? 0
    csvResult.value = __('{0} imported, {1} errors.', [imported, errors])
    facilitiesResource.reload()
    csvFile.value = null
    csvPreviewRows.value = []
  } catch (e) {
    csvResult.value = e?.messages?.[0] ?? __('Import failed.')
  } finally {
    csvImporting.value = false
  }
}

function clearCsv() {
  csvFile.value = null
  csvPreviewRows.value = []
  csvResult.value = ''
}

const csvTemplateResource = createResource({ url: 'crm.api.optin_admin.csv_template' })

async function downloadTemplate() {
  try {
    const csvString = await csvTemplateResource.submit({})
    const blob = new Blob([csvString], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'facility_import_template.csv'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  } catch (e) {
    console.error('Template download failed', e)
  }
}

// ── Helpers ────────────────────────────────────────────────────────────────

function enabledPill(enabled) {
  const base = 'rounded-full px-2 py-0.5 text-xs font-medium'
  return enabled
    ? `${base} bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400`
    : `${base} bg-surface-gray-2 text-ink-gray-6 dark:bg-surface-gray-4 dark:text-ink-gray-4`
}

function statusPill(status) {
  const base = 'rounded-full px-2 py-0.5 text-xs font-medium'
  const map = {
    'Active':   `${base} bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400`,
    'Opted In': `${base} bg-surface-gray-3 text-ink-gray-8 dark:bg-surface-gray-5 dark:text-ink-gray-3`,
    'Declined': `${base} bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400`,
  }
  return map[status] ?? `${base} bg-surface-gray-2 text-ink-gray-6 dark:bg-surface-gray-4 dark:text-ink-gray-4`
}
</script>
