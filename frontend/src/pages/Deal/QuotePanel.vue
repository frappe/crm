<template>
  <div class="mt-4">
    <!-- Section header -->
    <div class="mb-2 flex flex-wrap items-center justify-between gap-2">
      <div class="flex items-center gap-2">
        <h2 class="text-base font-semibold text-ink-gray-9">{{ __('Quotation') }}</h2>
        <span v-if="data?.name" class="font-mono text-xs text-ink-gray-4">{{ data.name }}</span>
      </div>
      <div class="flex items-center gap-2">
        <!-- Price list (ERPNext Item Price architecture) -->
        <label class="flex items-center gap-1.5 text-xs text-ink-gray-5">
          {{ __('Price List') }}
          <select
            :value="data?.price_list"
            :disabled="!canEdit || switchingList"
            class="rounded-md border border-outline-gray-2 bg-surface-white px-2 py-1 text-xs text-ink-gray-9 focus:outline-none focus:ring-2 focus:ring-outline-red-4 disabled:cursor-not-allowed disabled:opacity-60 dark:bg-surface-gray-2"
            @change="onChangePriceList($event.target.value)"
          >
            <option v-for="pl in priceListOptions" :key="pl.value" :value="pl.value">{{ pl.label }}</option>
          </select>
        </label>
        <span v-if="data?.status" :class="pillClass(data.status)">{{ __(data.status) }}</span>
      </div>
    </div>

    <!-- Card -->
    <div class="overflow-hidden rounded-xl border border-outline-gray-2 bg-surface-white dark:bg-surface-gray-1">

      <!-- Loading -->
      <div v-if="resource.loading" class="space-y-2 p-4">
        <div v-for="n in 4" :key="n" class="h-8 animate-pulse rounded bg-surface-gray-2" />
      </div>

      <template v-else>
        <!-- Editable line-item table -->
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead class="bg-surface-gray-2 text-xs uppercase tracking-wide text-ink-gray-5 dark:bg-surface-gray-3">
              <tr>
                <th class="px-3 py-2.5 text-left font-medium w-8">{{ __('#') }}</th>
                <th class="px-3 py-2.5 text-left font-medium">{{ __('Item') }}</th>
                <th class="px-3 py-2.5 text-right font-medium w-20">{{ __('Qty') }}</th>
                <th class="px-3 py-2.5 text-right font-medium w-48">{{ __('Negotiated Unit Price (KES)') }}</th>
                <th class="px-3 py-2.5 text-right font-medium w-40">{{ __('Amount (KES)') }}</th>
                <th class="px-3 py-2.5 w-10" />
              </tr>
            </thead>
            <tbody class="divide-y divide-outline-elevation-2">
              <tr v-for="(line, i) in lines" :key="i" class="align-top">
                <td class="px-3 py-3 text-ink-gray-4">{{ i + 1 }}</td>
                <td class="px-3 py-3">
                  <div class="font-medium text-ink-gray-9">{{ line.item_name }}</div>
                  <div class="mt-0.5 font-mono text-xs text-ink-gray-4">{{ line.item_code }}</div>
                  <div v-if="line.description" class="mt-0.5 text-xs text-ink-gray-5">{{ line.description }}</div>
                </td>
                <td class="px-3 py-3 text-right">
                  <input
                    v-model.number="line.qty"
                    type="number" min="0" step="1"
                    :disabled="!canEdit"
                    class="w-16 rounded-md border border-outline-gray-2 bg-surface-white px-2 py-1 text-right text-sm text-ink-gray-9 focus:outline-none focus:ring-2 focus:ring-outline-red-4 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-surface-gray-2"
                    @input="markDirty"
                  />
                </td>
                <td class="px-3 py-3 text-right">
                  <input
                    v-model.number="line.rate"
                    type="number" min="0" step="0.01"
                    :disabled="!canEdit"
                    class="w-40 rounded-md border border-outline-gray-2 bg-surface-white px-2 py-1 text-right text-sm text-ink-gray-9 focus:outline-none focus:ring-2 focus:ring-outline-red-4 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-surface-gray-2"
                    @input="markDirty"
                  />
                </td>
                <td class="px-3 py-3 text-right font-semibold text-ink-gray-9">
                  {{ fmt((line.qty || 0) * (line.rate || 0)) }}
                </td>
                <td class="px-3 py-3 text-right">
                  <button
                    v-if="canEdit"
                    type="button"
                    class="rounded p-1 text-ink-gray-4 hover:bg-surface-gray-2 hover:text-red-600 dark:hover:bg-surface-gray-3"
                    :title="__('Remove line')"
                    @click="removeLine(i)"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                  </button>
                </td>
              </tr>

              <tr v-if="!lines.length">
                <td colspan="6" class="px-3 py-8 text-center text-sm text-ink-gray-4">
                  {{ __('No line items on this quote.') }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Add line -->
        <div v-if="canEdit" class="flex flex-wrap items-end gap-2 border-t border-outline-gray-2 px-3 py-3">
          <div class="min-w-[240px] flex-1">
            <label class="mb-1 block text-xs font-medium text-ink-gray-5">{{ __('Add item from catalogue') }}</label>
            <Combobox
              :model-value="addItemCode"
              :options="catalogueOptions"
              :placeholder="__('Search catalogue...')"
              @update:model-value="addItemCode = $event"
            />
          </div>
          <Button variant="subtle" :disabled="!addItemCode" @click="addLine">
            <template #prefix>
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
            </template>
            {{ __('Add line') }}
          </Button>
        </div>

        <!-- Totals -->
        <div class="flex justify-end border-t border-outline-gray-2 bg-surface-gray-1 px-4 py-4 dark:bg-surface-gray-2">
          <div class="w-72 space-y-1.5 text-sm">
            <div class="flex justify-between">
              <span class="text-ink-gray-6">{{ __('Sub Total (Excl. VAT)') }}</span>
              <span class="text-ink-gray-9">{{ fmt(subtotal) }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-ink-gray-6">{{ __('VAT 16%') }}</span>
              <span class="text-ink-gray-9">{{ fmt(vat) }}</span>
            </div>
            <div class="my-1.5 border-t border-outline-gray-2" />
            <div class="flex justify-between rounded-lg bg-red-600 px-3 py-2 font-bold text-white">
              <span>{{ __('Grand Total (Incl. VAT)') }}</span>
              <span>{{ fmt(grandTotal) }}</span>
            </div>
          </div>
        </div>

        <!-- Footer: permission notices + save -->
        <div class="flex flex-wrap items-center justify-between gap-3 border-t border-outline-gray-2 px-4 py-3">
          <p v-if="!data?.editable" class="text-xs text-ink-gray-5">
            {{ __('This quote has been {0} and can no longer be edited.', [data?.status]) }}
          </p>
          <p v-else-if="!isMgr" class="text-xs text-amber-700 dark:text-amber-400">
            {{ __('Sales Manager role required to adjust pricing.') }}
          </p>
          <span v-else class="text-xs" :class="dirty ? 'text-amber-700 dark:text-amber-400' : 'text-ink-gray-4'">
            {{ dirty ? __('Unsaved changes') : __('All changes saved') }}
          </span>

          <div class="flex items-center gap-2">
            <Button variant="subtle" @click="doDownloadPdf">
              <template #prefix>
                <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
              </template>
              {{ __('PDF') }}
            </Button>
            <Button
              variant="solid"
              :disabled="!canEdit || !dirty"
              :loading="saving"
              @click="save"
            >
              {{ __('Save Adjustments') }}
            </Button>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { createResource, Button, Combobox, toast } from 'frappe-ui'
import { usersStore } from '@/stores/users'
import { sessionStore } from '@/stores/session'

const props = defineProps({
  dealId:    { type: String, required: true },
  quoteName: { type: String, required: true },
})
const emit = defineEmits(['saved'])

const { user: sessionUser } = sessionStore()
const { isManager } = usersStore()
const isMgr = computed(() => isManager(sessionUser.value))

// ── Quote lines ────────────────────────────────────────────────────────────
const lines = ref([])
const dirty = ref(false)

const resource = createResource({
  url: 'crm.api.quotes.get_quote_lines',
  makeParams: () => ({ quote: props.quoteName }),
  auto: true,
  onSuccess: (d) => {
    lines.value = (d?.lines ?? []).map((l) => ({ ...l }))
    dirty.value = false
  },
})
const data = computed(() => resource.data ?? null)

watch(() => props.quoteName, () => resource.reload())

const canEdit = computed(() => !!data.value?.editable && isMgr.value)

// ── Price list (ERPNext Item Price architecture) ─────────────────────────────
const priceListsResource = createResource({
  url: 'crm.api.quotes.list_price_lists',
  auto: true,
})
const priceListOptions = computed(() => priceListsResource.data ?? [])

const switchingList = ref(false)
const switchListResource = createResource({ url: 'crm.api.quotes.set_quote_price_list' })

async function onChangePriceList(priceList) {
  if (!priceList || priceList === data.value?.price_list) return
  if (!canEdit.value) return
  switchingList.value = true
  try {
    await switchListResource.submit({ quote: props.quoteName, price_list: priceList })
    toast.success(__('Price list switched — line rates re-defaulted'))
    resource.reload()
    catalogueResource.reload()
    emit('saved')
  } catch (err) {
    toast.error(err?.messages?.[0] ?? err?.message ?? __('Failed to switch price list'))
  } finally {
    switchingList.value = false
  }
}

function markDirty() { dirty.value = true }

function removeLine(i) {
  lines.value.splice(i, 1)
  dirty.value = true
}

// ── Totals (live, client-side) ───────────────────────────────────────────────
const subtotal   = computed(() => lines.value.reduce((s, l) => s + (l.qty || 0) * (l.rate || 0), 0))
const vat        = computed(() => subtotal.value * 0.16)
const grandTotal = computed(() => subtotal.value + vat.value)

// ── Catalogue picker ─────────────────────────────────────────────────────────
const catalogueResource = createResource({
  url: 'crm.api.quotes.list_catalogue_items',
  auto: true,
})
const catalogueOptions = computed(() =>
  (catalogueResource.data ?? []).map((c) => ({ label: `${c.label} — ${c.item_code}`, value: c.item_code }))
)
const addItemCode = ref('')

function addLine() {
  const code = addItemCode.value
  if (!code) return
  const meta = (catalogueResource.data ?? []).find((c) => c.item_code === code)
  lines.value.push({
    item_code:     code,
    item_name:     meta?.label ?? code,
    description:   '',
    facility_name: '',
    package_tier:  '',
    qty:           1,
    rate:          meta?.rate ?? 0,
    amount:        meta?.rate ?? 0,
  })
  addItemCode.value = ''
  dirty.value = true
}

// ── Save ─────────────────────────────────────────────────────────────────────
const saving = ref(false)
const saveResource = createResource({ url: 'crm.api.quotes.save_quote_lines' })

async function save() {
  if (!canEdit.value || !dirty.value) return
  saving.value = true
  try {
    await saveResource.submit({
      quote: props.quoteName,
      lines: JSON.stringify(lines.value),
    })
    dirty.value = false
    toast.success(__('Quote pricing saved'))
    resource.reload()
    emit('saved')
  } catch (err) {
    toast.error(err?.messages?.[0] ?? err?.message ?? __('Failed to save quote'))
  } finally {
    saving.value = false
  }
}

// ── PDF ────────────────────────────────────────────────────────────────────
function doDownloadPdf() {
  window.open(
    `/api/method/frappe.utils.print_format.download_pdf?doctype=Quotation&name=${encodeURIComponent(props.quoteName)}&format=Careverse+Quote+Standard`,
    '_blank'
  )
}

// ── Helpers ──────────────────────────────────────────────────────────────────
function fmt(v) {
  if (!v && v !== 0) return '0'
  return Math.round(parseFloat(v)).toLocaleString('en-KE')
}

function pillClass(status) {
  const base = 'rounded-full px-2 py-0.5 text-xs font-medium'
  const map = {
    Draft:    `${base} bg-surface-gray-3 text-ink-gray-7 dark:bg-surface-gray-4 dark:text-ink-gray-3`,
    Sent:     `${base} bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400`,
    Accepted: `${base} bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400`,
    Rejected: `${base} bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400`,
  }
  return map[status] ?? map.Draft
}
</script>
