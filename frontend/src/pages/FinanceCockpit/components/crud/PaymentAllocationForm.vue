<template>
  <div class="fc-payment-form pb-24">
    <!-- FC-11: Review panel (in-place transition) -->
    <template v-if="reviewing">
      <div class="mb-5">
        <p class="text-xs font-medium text-ink-gray-5">Review Payment</p>
        <h2 class="text-xl font-bold text-ink-gray-9">Confirm & Post</h2>
      </div>

      <div
        v-if="reviewError"
        class="mb-4 rounded-lg border border-red-300 bg-red-50 text-red-700 dark:bg-red-500/10 dark:border-red-500/30 dark:text-red-400 text-sm px-4 py-3 flex items-start gap-2 whitespace-pre-line"
      >
        <FcIcon name="alert-circle" :size="18" class="mt-0.5 flex-shrink-0" />
        <span>{{ reviewError }}</span>
      </div>

      <SectionCard title="Payment Summary" icon="banknote" tone="positive">
        <dl class="divide-y divide-outline-gray-1">
          <div class="flex items-center justify-between py-2.5">
            <dt class="text-xs font-medium text-ink-gray-5">Customer</dt>
            <dd class="text-sm font-medium text-ink-gray-8">{{ customer }}</dd>
          </div>
          <div class="flex items-center justify-between py-2.5">
            <dt class="text-xs font-medium text-ink-gray-5">Amount</dt>
            <dd class="text-sm font-bold text-ink-gray-9 tabular-nums">{{ formatCurrency(totalAllocated, activeCurrency) }}</dd>
          </div>
          <div class="flex items-center justify-between py-2.5">
            <dt class="text-xs font-medium text-ink-gray-5">Mode</dt>
            <dd class="text-sm text-ink-gray-8">{{ modeOfPayment || '—' }}</dd>
          </div>
          <div v-if="refFields.refNo" class="flex items-center justify-between py-2.5">
            <dt class="text-xs font-medium text-ink-gray-5">{{ refFields.refNo }}</dt>
            <dd class="text-sm text-ink-gray-8">{{ referenceNo || '—' }}</dd>
          </div>
          <div class="flex items-center justify-between py-2.5">
            <dt class="text-xs font-medium text-ink-gray-5">Date</dt>
            <dd class="text-sm text-ink-gray-8">{{ postingDate }}</dd>
          </div>
        </dl>
      </SectionCard>

      <SectionCard title="Allocations" icon="receipt" class="mt-4" tone="positive" :badge="selectedRows.length">
        <div class="divide-y divide-outline-gray-1">
          <div
            v-for="row in selectedRows"
            :key="row.name"
            class="flex items-center justify-between py-2.5"
          >
            <span class="text-sm font-medium text-ink-gray-8">{{ row.name }}</span>
            <span class="text-sm tabular-nums text-ink-gray-7">{{ formatCurrency(row._allocated, activeCurrency) }}</span>
          </div>
        </div>
        <div class="mt-3 pt-3 border-t border-outline-gray-1 flex items-center justify-between text-sm">
          <span class="text-ink-gray-5">Unallocated</span>
          <span class="tabular-nums" :class="unallocated > 0.005 ? 'text-amber-600 font-medium' : 'text-ink-gray-7'">
            {{ formatCurrency(unallocated, activeCurrency) }}
          </span>
        </div>
      </SectionCard>

      <!-- Success state -->
      <div
        v-if="successPe"
        class="mt-4 rounded-lg border border-outline-green-1 bg-surface-green-1 px-4 py-3 flex items-center justify-between"
      >
        <span class="text-sm font-medium text-ink-green-7">{{ successPe }} posted</span>
        <a
          :href="'/app/payment-entry/' + successPe"
          target="_blank"
          class="text-xs text-ink-green-6 hover:underline font-medium"
        >View in Accounts →</a>
      </div>
    </template>

    <!-- Main form -->
    <template v-else>
      <div class="mb-5">
        <p class="text-xs font-medium text-ink-gray-5">New Document</p>
        <h2 class="text-xl font-bold text-ink-gray-9">Receive Payment</h2>
        <p class="text-sm text-ink-gray-5 mt-0.5">
          Record a customer receipt and allocate it across outstanding invoices.
        </p>
      </div>

      <!-- Error banner (non-review) -->
      <div
        v-if="errorMsg"
        class="mb-4 rounded-lg border border-red-300 bg-red-50 text-red-700 dark:bg-red-500/10 dark:border-red-500/30 dark:text-red-400 text-sm px-4 py-3 flex items-start gap-2 whitespace-pre-line"
      >
        <FcIcon name="alert-circle" :size="18" class="mt-0.5 flex-shrink-0" />
        <span>{{ errorMsg }}</span>
      </div>

      <form class="space-y-5" @submit.prevent>
        <!-- Payment details -->
        <SectionCard title="Payment Details" icon="banknote" tone="positive">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-x-5 gap-y-4">
            <!-- FC-08: Customer smart search (name + customer_name) -->
            <div class="md:col-span-2">
              <label class="block text-xs font-medium text-ink-gray-6 mb-1">
                Customer<span class="text-red-500 ml-0.5">*</span>
              </label>
              <Combobox
                :model-value="customer"
                :options="customerOptions"
                :filterable="false"
                placeholder="Search customer..."
                @update:model-value="onCustomerChange"
                @update:query="onCustomerQuery"
              />
              <!-- FC-08: Balance chip -->
              <div v-if="customer && customerBalance !== null" class="mt-1.5 text-xs text-ink-gray-5">
                <span class="inline-flex items-center gap-1">
                  <span class="font-medium text-ink-gray-7">{{ formatCurrency(customerBalance, activeCurrency) }}</span>
                  outstanding
                  <span v-if="customerInvoiceCount > 0">({{ customerInvoiceCount }} {{ customerInvoiceCount === 1 ? 'invoice' : 'invoices' }})</span>
                </span>
              </div>
            </div>

            <!-- FC-09: Amount received input -->
            <div class="md:col-span-2">
              <label class="block text-xs font-medium text-ink-gray-6 mb-1">Amount Received</label>
              <div class="flex items-center gap-2">
                <div class="flex items-center gap-1.5 flex-1">
                  <span v-if="activeCurrency" class="text-xs font-medium text-ink-gray-5 w-8 text-right flex-shrink-0">{{ activeCurrency }}</span>
                  <input
                    type="number"
                    min="0"
                    step="any"
                    class="flex-1 text-sm rounded-lg border border-outline-gray-2 bg-surface-white px-3 py-2 text-ink-gray-8 focus:outline-none focus:ring-1 focus:ring-blue-500"
                    :value="paidAmount"
                    placeholder="0.00"
                    @input="paidAmount = parseFloat($event.target.value) || null"
                  />
                </div>
                <button
                  v-if="canAutoAllocate"
                  type="button"
                  class="text-xs font-medium text-blue-600 border border-outline-gray-2 rounded-lg px-3 py-2 hover:bg-surface-gray-1 transition-colors whitespace-nowrap"
                  @click="autoAllocate"
                >
                  Auto-Allocate
                </button>
              </div>
            </div>

            <div>
              <label class="block text-xs font-medium text-ink-gray-6 mb-1">Posting Date</label>
              <DatePicker :model-value="postingDate" @update:model-value="postingDate = $event" />
            </div>

            <!-- FC-07: Mode of Payment pill group -->
            <div>
              <label class="block text-xs font-medium text-ink-gray-6 mb-1">Mode of Payment</label>
              <div class="flex flex-wrap gap-1.5">
                <button
                  v-for="mode in visibleModes"
                  :key="mode"
                  type="button"
                  class="text-xs font-medium px-3 py-1.5 rounded-full border transition-colors"
                  :class="modeOfPayment === mode
                    ? 'bg-surface-gray-4 border-outline-gray-3 text-ink-gray-9'
                    : 'bg-surface-white border-outline-gray-2 text-ink-gray-6 hover:bg-surface-gray-1'"
                  @click="selectMode(mode)"
                >{{ mode }}</button>
                <div class="relative">
                  <button
                    type="button"
                    class="text-xs font-medium px-3 py-1.5 rounded-full border border-outline-gray-2 bg-surface-white text-ink-gray-6 hover:bg-surface-gray-1 transition-colors"
                    :class="moreOpen ? 'bg-surface-gray-1' : ''"
                    @click="moreOpen = !moreOpen"
                  >+ More ▾</button>
                  <div
                    v-if="moreOpen"
                    class="absolute left-0 mt-1 z-20 bg-surface-white border border-outline-gray-2 rounded-xl shadow-lg min-w-[160px] py-1"
                  >
                    <Combobox
                      :model-value="null"
                      :options="extraModeOptions"
                      :filterable="false"
                      placeholder="Search mode..."
                      class="p-2"
                      @update:model-value="selectMode($event); moreOpen = false"
                      @update:query="onModeQuery"
                    />
                  </div>
                </div>
              </div>
            </div>

            <!-- FC-12: Reference labels adapt to payment mode -->
            <template v-if="refFields.refNo">
              <FormControl
                type="text"
                :label="refFields.refNo"
                :model-value="referenceNo"
                @update:model-value="referenceNo = $event"
              />
            </template>
            <div v-if="refFields.refDate">
              <label class="block text-xs font-medium text-ink-gray-6 mb-1">{{ refFields.refDate }}</label>
              <DatePicker :model-value="referenceDate" @update:model-value="referenceDate = $event" />
            </div>
          </div>
        </SectionCard>

        <!-- Outstanding invoices — FC-10: sort, Select All, overdue -->
        <SectionCard title="Allocate to Invoices" icon="receipt" hero :badge="selectedCount || ''">
          <div v-if="!customer" class="text-sm text-ink-gray-5 py-6 text-center">
            Select a customer to load their outstanding invoices.
          </div>

          <div v-else-if="invoicesLoading" class="space-y-2">
            <div v-for="n in 4" :key="n" class="h-11 bg-surface-gray-2 rounded-lg animate-pulse" />
          </div>

          <div v-else-if="!invoices.length" class="text-sm text-ink-gray-5 py-6 text-center">
            No outstanding invoices for this customer.
          </div>

          <div v-else class="overflow-x-auto -mx-1">
            <!-- FC-09: Footer bar above table -->
            <div v-if="paidAmount" class="mb-2 flex items-center gap-4 text-xs text-ink-gray-5 px-1">
              <span>Allocated <span class="font-semibold text-ink-gray-8 tabular-nums">{{ formatCurrency(totalAllocated, activeCurrency) }}</span></span>
              <span class="text-outline-gray-3">|</span>
              <span :class="unallocated > 0.005 ? 'text-amber-600 font-medium' : ''">
                Unallocated <span class="font-semibold tabular-nums">{{ formatCurrency(unallocated, activeCurrency) }}</span>
              </span>
              <span class="text-outline-gray-3">|</span>
              <span>Total <span class="font-semibold text-ink-gray-8 tabular-nums">{{ formatCurrency(paidAmount || 0, activeCurrency) }}</span></span>
            </div>
            <table class="w-full text-sm">
              <thead>
                <tr class="text-left text-xs font-semibold text-ink-gray-5 uppercase tracking-wide border-b border-outline-gray-1">
                  <!-- FC-10: Select All checkbox -->
                  <th class="px-2 py-2 w-8">
                    <input
                      type="checkbox"
                      class="rounded border-outline-gray-3 text-blue-600 focus:ring-blue-500"
                      :checked="allSelected"
                      :indeterminate="someSelected && !allSelected"
                      @change="toggleAll($event.target.checked)"
                    />
                  </th>
                  <!-- FC-10: Sortable column headers -->
                  <th
                    class="px-2 py-2 cursor-pointer hover:text-ink-gray-8 select-none"
                    @click="setSort('name')"
                  >
                    Invoice <span class="ml-0.5">{{ sortIndicator('name') }}</span>
                  </th>
                  <th
                    class="px-2 py-2 cursor-pointer hover:text-ink-gray-8 select-none"
                    @click="setSort('due_date')"
                  >
                    Due <span class="ml-0.5">{{ sortIndicator('due_date') }}</span>
                  </th>
                  <th
                    class="px-2 py-2 text-right cursor-pointer hover:text-ink-gray-8 select-none"
                    @click="setSort('outstanding_amount')"
                  >
                    Outstanding <span class="ml-0.5">{{ sortIndicator('outstanding_amount') }}</span>
                  </th>
                  <th class="px-2 py-2 text-right w-40">Allocate</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="row in sortedInvoices"
                  :key="row.name"
                  class="border-b border-outline-gray-1 last:border-0"
                  :class="row._selected ? 'bg-blue-50/50 dark:bg-blue-500/5' : ''"
                >
                  <td class="px-2 py-2">
                    <input
                      type="checkbox"
                      class="rounded border-outline-gray-3 text-blue-600 focus:ring-blue-500"
                      :checked="row._selected"
                      @change="toggleRow(row, $event.target.checked)"
                    />
                  </td>
                  <td class="px-2 py-2">
                    <span class="font-medium text-ink-gray-8">{{ row.name }}</span>
                    <span
                      v-if="row.days_overdue > 0"
                      class="ml-1.5 text-xs text-red-500 dark:text-red-400"
                    >{{ row.days_overdue }}d overdue</span>
                  </td>
                  <!-- FC-10: overdue date cell in red -->
                  <td
                    class="px-2 py-2"
                    :class="row.days_overdue > 0 ? 'text-red-500 dark:text-red-400' : 'text-ink-gray-6'"
                  >{{ row.due_date || '—' }}</td>
                  <td class="px-2 py-2 text-right tabular-nums text-ink-gray-7">
                    {{ formatCurrency(row.outstanding_amount, row.currency) }}
                  </td>
                  <td class="px-2 py-2 text-right">
                    <input
                      type="number"
                      min="0"
                      :max="row.outstanding_amount"
                      step="any"
                      class="w-32 text-right text-sm rounded-lg border border-outline-gray-2 bg-surface-white px-2 py-1 tabular-nums disabled:bg-surface-gray-2 disabled:text-ink-gray-4"
                      :disabled="!row._selected"
                      :value="row._allocated"
                      @input="onAllocInput(row, $event.target.value)"
                    />
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </SectionCard>
      </form>
    </template>

    <!-- Sticky action bar -->
    <div class="fixed bottom-0 inset-x-0 z-30 bg-surface-white/95 backdrop-blur border-t border-outline-gray-2">
      <div class="max-w-screen-2xl mx-auto px-6 py-3 flex items-center justify-between gap-3">
        <div class="hidden sm:flex items-center gap-2 text-sm text-ink-gray-5">
          <span>Total Allocated</span>
          <span class="text-base font-bold text-ink-gray-9 tabular-nums">{{ formatCurrency(totalAllocated, activeCurrency) }}</span>
        </div>
        <div class="flex items-center gap-2 ml-auto">
          <Button variant="outline" theme="gray" :label="reviewing ? '← Back to Edit' : 'Cancel'" @click="onBack" />
          <Button
            v-if="reviewing"
            variant="solid"
            theme="blue"
            :loading="saving"
            :disabled="saving || !!successPe"
            @click="onConfirmPost"
          >
            <template #prefix><FcIcon name="send" :size="15" /></template>
            Confirm & Post
          </Button>
          <Button
            v-else
            variant="solid"
            theme="blue"
            :disabled="!canReview"
            @click="reviewing = true"
          >
            Review →
          </Button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Button, FormControl, Combobox, DatePicker, createResource, debounce, toast } from 'frappe-ui'
import SectionCard from './SectionCard.vue'
import FcIcon from './FcIcon.vue'
import { useCompanyContext } from '../../composables/useCompanyContext.js'
import { useCurrency } from '../../composables/useCurrency.js'

const emit = defineEmits(['saved', 'close'])

const { company } = useCompanyContext()
const { formatCurrency } = useCurrency()

const MOP_STORAGE_KEY = 'fc_recent_modes'
const DEFAULT_MODES = ['Cash', 'Bank Transfer']

// FC-12: Reference field labels per mode.
const REF_LABELS = {
  'Bank Transfer': { refNo: 'Bank Reference / RTGS Ref', refDate: 'Value Date' },
  'M-Pesa':        { refNo: 'M-Pesa Transaction ID',     refDate: 'Transaction Date' },
  Cheque:          { refNo: 'Cheque Number',              refDate: 'Cheque Date' },
  Cash:            { refNo: null,                         refDate: null },
}

function localToday() {
  const d = new Date()
  const off = d.getTimezoneOffset() * 60000
  return new Date(d.getTime() - off).toISOString().slice(0, 10)
}

const customer = ref(null)
const postingDate = ref(localToday())
const modeOfPayment = ref('')
const referenceNo = ref('')
const referenceDate = ref('')
const paidAmount = ref(null)
const saving = ref(false)
const errorMsg = ref('')
const invoices = ref([])
const reviewing = ref(false)
const reviewError = ref('')
const successPe = ref('')

// FC-10: sort state (default: due_date asc — oldest first)
const sortField = ref('due_date')
const sortAsc = ref(true)

function setSort(field) {
  if (sortField.value === field) {
    sortAsc.value = !sortAsc.value
  } else {
    sortField.value = field
    sortAsc.value = true
  }
}
function sortIndicator(field) {
  if (sortField.value !== field) return ''
  return sortAsc.value ? '▲' : '▼'
}

const sortedInvoices = computed(() => {
  const arr = invoices.value.slice()
  const f = sortField.value
  return arr.sort((a, b) => {
    const av = a[f] ?? ''
    const bv = b[f] ?? ''
    if (av < bv) return sortAsc.value ? -1 : 1
    if (av > bv) return sortAsc.value ? 1 : -1
    return 0
  })
})

const allSelected = computed(() => invoices.value.length > 0 && invoices.value.every((r) => r._selected))
const someSelected = computed(() => invoices.value.some((r) => r._selected))

function toggleAll(checked) {
  invoices.value.forEach((r) => {
    r._selected = checked
    r._allocated = checked ? Number(r.outstanding_amount) : 0
  })
}

/* ---- FC-07: Mode of Payment pill group ---- */
const recentModes = ref((() => {
  try { return JSON.parse(localStorage.getItem(MOP_STORAGE_KEY) || '[]') } catch { return [] }
})())
const allLoadedModes = ref([])
const moreOpen = ref(false)
const modeSearchResults = ref([])
const modeRes = createResource({ url: 'frappe.client.get_list' })

const visibleModes = computed(() => {
  const recent = recentModes.value.length ? recentModes.value : DEFAULT_MODES
  return recent.slice(0, 4)
})

const extraModeOptions = computed(() => {
  const base = modeSearchResults.value.length ? modeSearchResults.value : allLoadedModes.value
  return base.filter((m) => !visibleModes.value.includes(m)).map((m) => ({ label: m, value: m }))
})

const onModeQuery = debounce(async (q) => {
  const rows = await modeRes.submit({
    doctype: 'Mode of Payment',
    filters: q ? JSON.stringify([['name', 'like', `%${q}%`]]) : '[]',
    fields: JSON.stringify(['name']),
    limit_page_length: 20,
    order_by: 'name asc',
  })
  modeSearchResults.value = (rows || []).map((r) => r.name)
}, 200)

function selectMode(mode) {
  if (!mode) return
  modeOfPayment.value = mode
  const updated = [mode, ...recentModes.value.filter((m) => m !== mode)].slice(0, 4)
  recentModes.value = updated
  try { localStorage.setItem(MOP_STORAGE_KEY, JSON.stringify(updated)) } catch { /* ignore */ }
  moreOpen.value = false
  // Clear ref fields when switching to Cash (FC-12).
  if (mode === 'Cash') { referenceNo.value = ''; referenceDate.value = '' }
}

// FC-12: computed ref field labels.
const refFields = computed(() => {
  return REF_LABELS[modeOfPayment.value] || { refNo: 'Reference No.', refDate: 'Reference Date' }
})

/* ---- FC-08: Customer smart search ---- */
const customerResults = ref([])
const customerListRes = createResource({ url: 'frappe.client.get_list' })
const customerOptions = computed(() => {
  const opts = customerResults.value.slice()
  if (customer.value && !opts.some((o) => o.value === customer.value)) {
    opts.unshift({ label: customer.value, value: customer.value })
  }
  return opts
})
const onCustomerQuery = debounce(async (query) => {
  try {
    const rows = await customerListRes.submit({
      doctype: 'Customer',
      // Search both name (code) and customer_name (display name).
      or_filters: query ? JSON.stringify([
        ['name', 'like', `%${query}%`],
        ['customer_name', 'like', `%${query}%`],
      ]) : '[]',
      filters: '[]',
      fields: JSON.stringify(['name', 'customer_name']),
      limit_page_length: 10,
      order_by: 'modified desc',
    })
    customerResults.value = (rows || []).map((r) => ({
      label: r.customer_name || r.name,
      value: r.name,
    }))
  } catch {
    customerResults.value = []
  }
}, 250)

/* ---- FC-08: Customer balance chip ---- */
const customerBalance = ref(null)
const customerInvoiceCount = ref(0)

/* ---- Outstanding invoices ---- */
const invoicesRes = createResource({ url: 'crm.finance.api.get_customer_outstanding_invoices' })
const invoicesLoading = ref(false)

async function onCustomerChange(val) {
  customer.value = val
  invoices.value = []
  customerBalance.value = null
  customerInvoiceCount.value = 0
  paidAmount.value = null
  // FC-07: do NOT reset modeOfPayment on customer change (spec FC-07: delete line 231).
  referenceNo.value = ''
  referenceDate.value = ''
  if (!val) return
  invoicesLoading.value = true
  errorMsg.value = ''
  try {
    const rows = await invoicesRes.submit({ company: company.value, customer: val })
    invoices.value = (rows || []).map((r) => ({ ...r, _selected: false, _allocated: 0 }))
    // Compute balance chip values.
    customerInvoiceCount.value = invoices.value.length
    customerBalance.value = invoices.value.reduce((s, r) => s + Number(r.outstanding_amount || 0), 0)
  } catch (err) {
    errorMsg.value = readable(err)
  } finally {
    invoicesLoading.value = false
  }
}

function toggleRow(row, checked) {
  row._selected = checked
  row._allocated = checked ? Number(row.outstanding_amount) : 0
}
function onAllocInput(row, raw) {
  const n = parseFloat(raw)
  const capped = Number.isNaN(n) ? 0 : Math.min(Math.max(n, 0), Number(row.outstanding_amount))
  row._allocated = capped
}

/* ---- FC-09: Auto-allocate ---- */
const canAutoAllocate = computed(() => !!customer.value && paidAmount.value > 0 && invoices.value.length > 0)

function autoAllocate() {
  let remaining = Number(paidAmount.value) || 0
  // Sort by due_date asc to fill oldest first.
  const byDue = invoices.value.slice().sort((a, b) => (a.due_date || '') < (b.due_date || '') ? -1 : 1)
  byDue.forEach((row) => {
    if (remaining <= 0) {
      row._selected = false
      row._allocated = 0
      return
    }
    const avail = Number(row.outstanding_amount)
    const alloc = Math.min(avail, remaining)
    row._selected = alloc > 0
    row._allocated = alloc
    remaining -= alloc
  })
}

const selectedRows = computed(() => invoices.value.filter((r) => r._selected && Number(r._allocated) > 0))
const selectedCount = computed(() => selectedRows.value.length)
const totalAllocated = computed(() => selectedRows.value.reduce((s, r) => s + Number(r._allocated || 0), 0))
const activeCurrency = computed(() => invoices.value[0]?.currency || '')
const unallocated = computed(() => Math.max(0, (paidAmount.value || 0) - totalAllocated.value))
const canReview = computed(() => !!customer.value && totalAllocated.value > 0 && !saving.value)

function readable(err) {
  if (!err) return 'Something went wrong.'
  if (Array.isArray(err.messages) && err.messages.length) return err.messages.join('\n')
  return err.message || String(err)
}

function onBack() {
  if (reviewing.value) {
    reviewing.value = false
    reviewError.value = ''
  } else {
    emit('close')
  }
}

const createRes = createResource({ url: 'crm.finance.api.create_customer_payment' })

async function onConfirmPost() {
  if (!canReview.value) return
  saving.value = true
  reviewError.value = ''
  try {
    const allocations = selectedRows.value.map((r) => ({ invoice: r.name, amount: Number(r._allocated) }))
    const res = await createRes.submit({
      company: company.value,
      customer: customer.value,
      mode_of_payment: modeOfPayment.value || undefined,
      posting_date: postingDate.value || undefined,
      reference_no: referenceNo.value || undefined,
      reference_date: referenceDate.value || undefined,
      allocations: JSON.stringify(allocations),
      submit: 1,
    })
    successPe.value = res?.name || ''
    toast.success('Payment ' + (res?.name || '') + ' recorded')
    emit('saved', res)
  } catch (err) {
    reviewError.value = readable(err)
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  onCustomerQuery('')
  try {
    const rows = await modeRes.submit({
      doctype: 'Mode of Payment',
      fields: JSON.stringify(['name']),
      limit_page_length: 20,
      order_by: 'name asc',
    })
    if (rows && rows.length) allLoadedModes.value = rows.map((r) => r.name)
  } catch {
    allLoadedModes.value = ['Cash', 'Bank Transfer', 'M-Pesa', 'Cheque']
  }
})
</script>
