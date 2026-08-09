<template>
  <div class="fc-payment-form pb-24">
    <!-- Header -->
    <div class="mb-5">
      <p class="text-xs font-medium text-ink-gray-5">New Document</p>
      <h2 class="text-xl font-bold text-ink-gray-9">Receive Payment</h2>
      <p class="text-sm text-ink-gray-5 mt-0.5">
        Record a customer receipt and allocate it across outstanding invoices.
      </p>
    </div>

    <!-- Error banner -->
    <div
      v-if="errorMsg"
      class="mb-4 rounded-lg border border-red-300 bg-red-50 text-red-700 dark:bg-red-500/10 dark:border-red-500/30 dark:text-red-400 text-sm px-4 py-3 flex items-start gap-2 whitespace-pre-line"
    >
      <FcIcon name="alert-circle" :size="18" class="mt-0.5 flex-shrink-0" />
      <span>{{ errorMsg }}</span>
    </div>

    <form class="space-y-5" @submit.prevent="onSave">
      <!-- Payment details -->
      <SectionCard title="Payment Details" icon="banknote" tone="positive">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-x-5 gap-y-4">
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
          </div>

          <div>
            <label class="block text-xs font-medium text-ink-gray-6 mb-1">Posting Date</label>
            <DatePicker :model-value="postingDate" @update:model-value="postingDate = $event" />
          </div>

          <FormControl
            type="select"
            label="Mode of Payment"
            :options="modeOptions"
            :model-value="modeOfPayment"
            @update:model-value="modeOfPayment = $event"
          />

          <FormControl
            type="text"
            label="Reference No."
            :model-value="referenceNo"
            @update:model-value="referenceNo = $event"
          />

          <div>
            <label class="block text-xs font-medium text-ink-gray-6 mb-1">Reference Date</label>
            <DatePicker :model-value="referenceDate" @update:model-value="referenceDate = $event" />
          </div>
        </div>
      </SectionCard>

      <!-- Outstanding invoices -->
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
          <table class="w-full text-sm">
            <thead>
              <tr class="text-left text-xs font-semibold text-ink-gray-5 uppercase tracking-wide border-b border-outline-gray-1">
                <th class="px-2 py-2 w-8"></th>
                <th class="px-2 py-2">Invoice</th>
                <th class="px-2 py-2">Due</th>
                <th class="px-2 py-2 text-right">Outstanding</th>
                <th class="px-2 py-2 text-right w-40">Allocate</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="row in invoices"
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
                    class="ml-1.5 text-xs text-red-600 dark:text-red-400"
                  >{{ row.days_overdue }}d overdue</span>
                </td>
                <td class="px-2 py-2 text-ink-gray-6">{{ row.due_date || '—' }}</td>
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

    <!-- Sticky action bar -->
    <div class="fixed bottom-0 inset-x-0 z-30 bg-surface-white/95 backdrop-blur border-t border-outline-gray-2">
      <div class="max-w-screen-2xl mx-auto px-6 py-3 flex items-center justify-between gap-3">
        <div class="hidden sm:flex items-center gap-2 text-sm text-ink-gray-5">
          <span>Total Allocated</span>
          <span class="text-base font-bold text-ink-gray-9 tabular-nums">{{ formatCurrency(totalAllocated, activeCurrency) }}</span>
        </div>
        <div class="flex items-center gap-2 ml-auto">
          <Button variant="outline" theme="gray" label="Cancel" @click="$emit('close')" />
          <Button
            variant="solid"
            theme="blue"
            :loading="saving"
            :disabled="!canSave"
            @click="onSave"
          >
            <template #prefix><FcIcon name="save" :size="15" /></template>
            Save & Submit
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

// Local calendar date (YYYY-MM-DD) for the user's own timezone — toISOString()
// would roll back a day for anyone east of UTC late in the day.
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
const saving = ref(false)
const errorMsg = ref('')
const invoices = ref([])

/* ---- Customer link search ---- */
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
      filters: query ? JSON.stringify([['name', 'like', `%${query}%`]]) : '[]',
      fields: JSON.stringify(['name']),
      limit_page_length: 10,
      order_by: 'modified desc',
    })
    customerResults.value = (rows || []).map((r) => ({ label: r.name, value: r.name }))
  } catch {
    customerResults.value = []
  }
}, 250)

/* ---- Mode of payment options ---- */
const modeOptions = ref([{ label: 'Cash', value: 'Cash' }])
const modeRes = createResource({ url: 'frappe.client.get_list' })

/* ---- Outstanding invoices ---- */
const invoicesRes = createResource({ url: 'crm.finance.api.get_customer_outstanding_invoices' })
const invoicesLoading = ref(false)

async function onCustomerChange(val) {
  customer.value = val
  invoices.value = []
  // Reset receipt details so a prior customer's reference/mode never leaks onto
  // a new party's payment.
  referenceNo.value = ''
  referenceDate.value = ''
  modeOfPayment.value = ''
  if (!val) return
  invoicesLoading.value = true
  errorMsg.value = ''
  try {
    const rows = await invoicesRes.submit({ company: company.value, customer: val })
    invoices.value = (rows || []).map((r) => ({ ...r, _selected: false, _allocated: 0 }))
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

const selectedRows = computed(() => invoices.value.filter((r) => r._selected && Number(r._allocated) > 0))
const selectedCount = computed(() => selectedRows.value.length)
const totalAllocated = computed(() => selectedRows.value.reduce((s, r) => s + Number(r._allocated || 0), 0))
const activeCurrency = computed(() => invoices.value[0]?.currency || '')
const canSave = computed(() => !!customer.value && totalAllocated.value > 0 && !saving.value)

function readable(err) {
  if (!err) return 'Something went wrong.'
  if (Array.isArray(err.messages) && err.messages.length) return err.messages.join('\n')
  return err.message || String(err)
}

const createRes = createResource({ url: 'crm.finance.api.create_customer_payment' })

async function onSave() {
  if (!canSave.value) return
  saving.value = true
  errorMsg.value = ''
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
    toast.success('Payment ' + (res?.name || '') + ' recorded')
    emit('saved', res)
  } catch (err) {
    errorMsg.value = readable(err)
    toast.error('Could not record payment')
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
    if (rows && rows.length) modeOptions.value = rows.map((r) => ({ label: r.name, value: r.name }))
  } catch {
    /* keep Cash fallback */
  }
})
</script>
