<template>
  <div class="mx-auto max-w-3xl px-5 py-6">
    <div class="mb-6">
      <h2 class="text-lg font-semibold text-ink-gray-9">{{ __('Review & Send') }}</h2>
      <p class="mt-1 text-sm text-ink-gray-5">{{ __('Review the quote before sending to the customer.') }}</p>
    </div>

    <!-- Quote preview -->
    <div class="rounded-xl border border-outline-elevation-2 bg-surface-white dark:bg-surface-gray-1 overflow-hidden mb-6">
      <!-- Header -->
      <div class="flex items-start justify-between bg-blue-900 px-6 py-4 text-white">
        <div>
          <div class="text-lg font-extrabold tracking-tight">TIBERBU</div>
          <div class="text-xs text-blue-200 mt-0.5">Tiberbu Healthnet Solutions Limited</div>
          <div class="text-xs text-blue-300 mt-0.5">18th Floor, 4th Avenue Tower, Ngong Road, Nairobi</div>
          <div class="text-xs text-blue-300">sales@tiberbu.com  |  +254 709 208 000</div>
        </div>
        <div class="text-right">
          <div class="text-2xl font-black tracking-widest uppercase">QUOTATION</div>
          <div class="text-xs text-blue-200 mt-1">{{ __('Quote No') }}: <strong class="text-white">{{ quoteName || __('Draft') }}</strong></div>
          <div class="text-xs text-blue-200">{{ __('Date') }}: {{ today }}</div>
          <div class="text-xs text-blue-200">{{ __('Valid Until') }}: {{ validUntil }}</div>
        </div>
      </div>

      <!-- Customer -->
      <div class="border-b border-outline-elevation-2 px-6 py-3">
        <div class="text-xs font-semibold uppercase tracking-wide text-ink-gray-4">{{ __('Quote To') }}</div>
        <div class="mt-0.5 text-base font-bold text-ink-gray-9">{{ context.customer || dealId }}</div>
        <div v-if="context.partner" class="text-xs text-ink-gray-5">{{ __('Partner') }}: {{ context.partner }}</div>
      </div>

      <!-- Pricing title -->
      <div class="border-b border-l-4 border-blue-600 bg-blue-50 px-6 py-2.5 dark:bg-blue-900/20">
        <span class="text-xs font-bold uppercase tracking-wide text-blue-800 dark:text-blue-300">
          {{ __('Pricing for Tiberbu CareVerse HIMS Solution') }} — {{ quoteData.payment_terms }}
        </span>
      </div>

      <!-- Line items -->
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead class="bg-blue-900 text-xs text-white uppercase tracking-wide">
            <tr>
              <th class="px-4 py-2.5 text-center w-10">{{ __('No.') }}</th>
              <th class="px-4 py-2.5 text-left">{{ __('Category') }}</th>
              <th class="px-4 py-2.5 text-left">{{ __('Item') }}</th>
              <th class="px-4 py-2.5 text-center w-16">{{ __('Pkg') }}</th>
              <th class="px-4 py-2.5 text-right w-12">{{ __('Qty') }}</th>
              <th class="px-4 py-2.5 text-right">{{ __('Unit Price (KES)') }}</th>
              <th class="px-4 py-2.5 text-right">{{ __('Total (KES)') }}</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-outline-elevation-2">
            <!-- CareVerse system section header -->
            <tr class="bg-blue-800"><td colspan="7" class="px-4 py-1.5 text-xs font-bold uppercase text-white tracking-wide">{{ __('CareverseHIMS System') }}</td></tr>
            <template v-for="(f, fi) in quoteData.facilities" :key="'f'+fi">
              <tr class="even:bg-surface-gray-1/30">
                <td class="px-4 py-2.5 text-center text-ink-gray-5">{{ lineIdx++ }}</td>
                <td class="px-4 py-2.5 text-ink-gray-7">{{ __('Hosted HIMS Software Solution') }}</td>
                <td class="px-4 py-2.5 text-ink-gray-9">{{ __('CareVerse SaaS Subscription') }} — {{ f.facility_name }}</td>
                <td class="px-4 py-2.5 text-center"><span :class="tierPill(f.package_tier)">{{ f.package_tier }}</span></td>
                <td class="px-4 py-2.5 text-right">1</td>
                <td class="px-4 py-2.5 text-right text-ink-gray-6">{{ fmt(tierSub(f)) }}</td>
                <td class="px-4 py-2.5 text-right font-medium text-ink-gray-9">{{ fmt(tierSub(f)) }}</td>
              </tr>
              <tr class="even:bg-surface-gray-1/30">
                <td class="px-4 py-2.5 text-center text-ink-gray-5">{{ lineIdx++ }}</td>
                <td class="px-4 py-2.5 text-ink-gray-7">{{ __('Professional Services') }}</td>
                <td class="px-4 py-2.5 text-ink-gray-9">{{ __('Implementation & Training') }} — {{ f.facility_name }}</td>
                <td class="px-4 py-2.5 text-center"><span :class="tierPill(f.package_tier)">{{ f.package_tier }}</span></td>
                <td class="px-4 py-2.5 text-right">1</td>
                <td class="px-4 py-2.5 text-right text-ink-gray-6">{{ fmt(tierImpl(f)) }}</td>
                <td class="px-4 py-2.5 text-right font-medium text-ink-gray-9">{{ fmt(tierImpl(f)) }}</td>
              </tr>
            </template>
            <!-- Add-ons -->
            <template v-if="quoteData.addons.length">
              <tr class="bg-blue-800"><td colspan="7" class="px-4 py-1.5 text-xs font-bold uppercase text-white tracking-wide">{{ __('Other Optional Costs') }}</td></tr>
              <tr v-for="(a, ai) in quoteData.addons" :key="'a'+ai" class="even:bg-surface-gray-1/30">
                <td class="px-4 py-2.5 text-center text-ink-gray-5">{{ lineIdx++ }}</td>
                <td class="px-4 py-2.5 text-ink-gray-7">{{ addonCategory(a.product_sku) }}</td>
                <td class="px-4 py-2.5 text-ink-gray-9">{{ addonName(a.product_sku) }}</td>
                <td class="px-4 py-2.5"></td>
                <td class="px-4 py-2.5 text-right">{{ a.qty }}</td>
                <td class="px-4 py-2.5 text-right text-ink-gray-6">{{ fmt(addonPrice(a.product_sku)) }}</td>
                <td class="px-4 py-2.5 text-right font-medium">{{ fmt(addonPrice(a.product_sku) * a.qty) }}</td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>

      <!-- Totals -->
      <div class="flex justify-end border-t border-outline-elevation-2 px-6 py-4">
        <div class="w-64 space-y-1.5 text-sm">
          <div class="flex justify-between"><span class="text-ink-gray-6">{{ __('Sub Total Excl. VAT') }}</span><span>{{ fmt(computed_pricing.net_subtotal) }}</span></div>
          <div v-if="computed_pricing.discount > 0" class="flex justify-between text-red-500"><span>{{ __('Discount Applied') }}</span><span>-{{ fmt(computed_pricing.discount) }}</span></div>
          <div class="flex justify-between"><span class="text-ink-gray-6">{{ __('VAT 16%') }}</span><span>{{ fmt(computed_pricing.vat) }}</span></div>
          <div class="my-2 border-t border-outline-elevation-2" />
          <div class="flex justify-between rounded-lg bg-blue-900 px-3 py-2 text-white font-bold">
            <span>{{ __('Grand Total Year 1 (Incl. VAT)') }}</span>
            <span>{{ fmt(computed_pricing.grand_total) }}</span>
          </div>
        </div>
      </div>

      <!-- Renewal table -->
      <div v-if="quoteData.contract_term_yrs > 1" class="border-t border-outline-elevation-2 px-6 py-4">
        <div class="mb-2 text-xs font-semibold uppercase tracking-wide text-ink-gray-5">{{ __('Discounted Annual Subscription Renewal') }}</div>
        <table class="w-full text-xs">
          <thead class="bg-gray-600 text-white"><tr>
            <th class="px-3 py-1.5 text-left">{{ __('Year') }}</th>
            <th class="px-3 py-1.5 text-right">{{ __('Excl. VAT (KES)') }}</th>
            <th class="px-3 py-1.5 text-right">{{ __('Incl. VAT (KES)') }}</th>
            <th v-if="quoteData.payment_terms === 'Monthly'" class="px-3 py-1.5 text-right">{{ __('Monthly (KES)') }}</th>
          </tr></thead>
          <tbody class="divide-y divide-outline-elevation-2">
            <tr v-for="r in renewalRows" :key="r.year" class="even:bg-surface-gray-1/30">
              <td class="px-3 py-1.5 font-medium">{{ __('Year') }} {{ r.year }}</td>
              <td class="px-3 py-1.5 text-right text-ink-gray-6">{{ fmt(r.subscription_excl_vat) }}</td>
              <td class="px-3 py-1.5 text-right font-medium">{{ fmt(r.grand_total_incl_vat) }}</td>
              <td v-if="quoteData.payment_terms === 'Monthly'" class="px-3 py-1.5 text-right text-ink-gray-6">{{ fmt(r.monthly_equivalent) }}/mo</td>
            </tr>
            <tr class="bg-blue-900 text-white font-bold">
              <td class="px-3 py-2">{{ __('5-Year TCO') }}</td>
              <td class="px-3 py-2 text-right">{{ fmt(tcoExcl) }}</td>
              <td class="px-3 py-2 text-right">{{ fmt(tcoIncl) }}</td>
              <td v-if="quoteData.payment_terms === 'Monthly'" class="px-3 py-2"></td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Notes / T&C -->
      <div class="border-t border-outline-elevation-2 px-6 py-4 text-xs text-ink-gray-6 space-y-1">
        <div class="font-semibold uppercase tracking-wide text-ink-gray-5 mb-1.5">{{ __('Notes') }}</div>
        <div>1. {{ __('Price validity is 30 days from the date of this quotation/proposal.') }}</div>
        <div>2. {{ __('All prices are in KES. Payment shall be made in KES.') }}</div>
        <div>3. {{ __('All on-site services will be delivered within Kenya.') }}</div>
        <div>4. {{ __('All payments are invoiced in advance.') }}</div>
      </div>

      <!-- Signature block -->
      <div class="border-t border-outline-elevation-2 px-6 py-4">
        <div class="text-xs font-semibold uppercase tracking-wide text-ink-gray-5 mb-3">{{ __('Customer Quotation Approval') }}</div>
        <div class="grid grid-cols-2 gap-6 text-xs">
          <div><div class="text-ink-gray-4 mb-4">{{ __('Full Name') }}</div><div class="border-t border-gray-400 pt-1 text-ink-gray-3">__________________________</div></div>
          <div><div class="text-ink-gray-4 mb-4">{{ __('Role / Title') }}</div><div class="border-t border-gray-400 pt-1 text-ink-gray-3">__________________________</div></div>
          <div><div class="text-ink-gray-4 mb-4">{{ __('Signature') }}</div><div class="border-t border-gray-400 pt-1 text-ink-gray-3">__________________________</div></div>
          <div><div class="text-ink-gray-4 mb-4">{{ __('Date') }}</div><div class="border-t border-gray-400 pt-1 text-ink-gray-3">__________________________</div></div>
        </div>
        <div class="mt-4 text-center text-xs font-bold uppercase tracking-widest text-ink-gray-3">PRIVATE & CONFIDENTIAL</div>
      </div>
    </div>
    <!-- end preview -->

    <!-- Action buttons -->
    <div class="flex flex-wrap items-center justify-between gap-2">
      <Button variant="ghost" @click="emit('back')">{{ __('← Back') }}</Button>
      <div class="flex flex-wrap gap-2">
        <Button v-if="!isReadOnly" variant="subtle" :loading="actionLoading === 'draft'" @click="doSaveDraft">{{ __('Save as Draft') }}</Button>
        <Button variant="outline" @click="downloadPdf">{{ __('Download PDF') }}</Button>

        <!-- Draft state: Send to Customer -->
        <Button
          v-if="!isReadOnly && (!currentStatus || currentStatus === 'Draft')"
          variant="solid"
          :loading="actionLoading === 'send'"
          @click="doSend"
        >{{ __('Send to Customer →') }}</Button>

        <!-- Sent state: Accept + Reject + Re-send -->
        <template v-if="currentStatus === 'Sent'">
          <Button variant="subtle" :loading="actionLoading === 'send'" @click="doSend">{{ __('Re-send') }}</Button>
          <Button variant="solid" class="!bg-green-600 hover:!bg-green-700" :loading="actionLoading === 'accept'" @click="doAccept">{{ __('Accept ✓') }}</Button>
          <Button variant="subtle" class="!text-red-600" :loading="actionLoading === 'reject'" @click="confirmRejectVisible = true">{{ __('Reject ✗') }}</Button>
        </template>
      </div>
    </div>

    <Dialog v-model="confirmRejectVisible" :options="{ title: __('Reject this quote?'), size: 'sm' }">
      <template #body-content>
        <p class="text-sm text-ink-gray-6">{{ __('This will set the quote to Rejected. The customer will need a new version.') }}</p>
      </template>
      <template #actions>
        <Button variant="subtle" @click="confirmRejectVisible = false">{{ __('Cancel') }}</Button>
        <Button variant="solid" theme="red" :loading="actionLoading === 'reject'" @click="doReject">{{ __('Confirm Reject') }}</Button>
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { createResource } from 'frappe-ui'
import { Button, Dialog } from 'frappe-ui'

const TIERS = {
  Core:       { subscription: 605149.06,  impl: 620000.00  },
  Advanced:   { subscription: 1821349.83, impl: 1870000.00 },
  Enterprise: { subscription: 6044783.95, impl: 6180000.00 },
}
const ADDON_META = {
  'CV-HW-OPTIPLEX-7010':       { name: 'Dell OptiPlex 7010 Workstation',      price: 84000,  cat: 'Hardware' },
  'CV-HW-LATITUDE-5440':       { name: 'Dell Latitude 5440 Laptop',            price: 126000, cat: 'Hardware' },
  'CV-HW-TAB-10':              { name: 'Tablet 10.1" Android',                 price: 38889,  cat: 'Hardware' },
  'CV-SW-ENDPOINT-SEC':        { name: 'Endpoint Security Subscription',       price: 8100,   cat: 'Software' },
  'CV-SW-OFFICE-MGMT':         { name: 'Office Management Suite',              price: 13886,  cat: 'Software' },
  'CV-SVC-OUT-NAIROBI':        { name: 'Implementation Outside Nairobi',       price: 14500,  cat: 'Professional Services' },
  'CV-SVC-REFRESHER-VIRT':     { name: 'Refresher Training (Virtual)',          price: 2500,   cat: 'Professional Services' },
  'CV-SVC-ONSITE-ENGINEER':    { name: 'On-Site Support Engineer',             price: 220000, cat: 'Professional Services' },
  'CV-SVC-PARTTIME-ENGINEER':  { name: 'Part-Time Support Engineer',           price: 100000, cat: 'Professional Services' },
}
const VAT = 0.16
const MONTHLY_SURCHARGE = 0.15
const TRUEUP = 0.05

const props = defineProps({
  quoteData:   { type: Object,  required: true },
  quoteName:   { type: String,  default: null  },
  dealId:      { type: String,  required: true },
  context:     { type: Object,  default: () => ({}) },
})
const emit = defineEmits(['back', 'saved', 'sent', 'accepted', 'rejected'])

const actionLoading = ref(null)
const confirmRejectVisible = ref(false)
const currentQuoteName = ref(props.quoteName)
const currentStatus = ref(null) // set after save/send

const isReadOnly = computed(() => ['Accepted', 'Rejected'].includes(currentStatus.value))

let lineIdxCounter = 0
const lineIdx = computed({
  get: () => { lineIdxCounter = 0; return { valueOf: () => ++lineIdxCounter } },
  set: () => {},
})
// Simple counter reset each render
let _lineIdx = 0

function tierSub(f) {
  const p = TIERS[f.package_tier] || TIERS.Core
  return p.subscription * (1 - (props.quoteData.saas_discount || 0) / 100)
}
function tierImpl(f) {
  const p = TIERS[f.package_tier] || TIERS.Core
  return p.impl * (1 - (props.quoteData.services_discount || 0) / 100)
}
function addonName(sku) { return ADDON_META[sku]?.name || sku }
function addonPrice(sku) { return ADDON_META[sku]?.price || 0 }
function addonCategory(sku) { return ADDON_META[sku]?.cat || '' }
function tierPill(tier) {
  const map = {
    Core:       'rounded-full bg-green-100 px-1.5 py-0.5 text-xs font-bold text-green-700',
    Advanced:   'rounded-full bg-blue-100 px-1.5 py-0.5 text-xs font-bold text-blue-700',
    Enterprise: 'rounded-full bg-purple-100 px-1.5 py-0.5 text-xs font-bold text-purple-700',
  }
  return map[tier] || map.Core
}

const today = new Date().toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
const validUntil = new Date(Date.now() + 30 * 86400000).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })

const computed_pricing = computed(() => {
  let sub_total = 0, impl_total = 0
  for (const f of props.quoteData.facilities || []) {
    let sub = tierSub(f)
    let impl = tierImpl(f)
    if (props.quoteData.payment_terms === 'Monthly') sub *= (1 + MONTHLY_SURCHARGE)
    sub_total += sub
    impl_total += impl
  }
  const addon_total = (props.quoteData.addons || []).reduce((s, a) => s + addonPrice(a.product_sku) * (a.qty || 0), 0)
  const raw_sub = props.quoteData.facilities.reduce((s, f) => s + (TIERS[f.package_tier]?.subscription || 0), 0)
  const raw_impl = props.quoteData.facilities.reduce((s, f) => s + (TIERS[f.package_tier]?.impl || 0), 0)
  const discount = (raw_sub - props.quoteData.facilities.reduce((s, f) => s + tierSub(f), 0)) +
                   (raw_impl - props.quoteData.facilities.reduce((s, f) => s + tierImpl(f), 0))
  const net_subtotal = sub_total + impl_total + addon_total
  const vat = net_subtotal * VAT
  return { sub_total, impl_total, addon_total, discount, net_subtotal, vat, grand_total: net_subtotal + vat }
})

const renewalRows = computed(() => {
  const rows = []
  const monthly_flag = props.quoteData.payment_terms === 'Monthly'
  let base_sub = props.quoteData.facilities.reduce((s, f) => {
    const sub = TIERS[f.package_tier]?.subscription || 0
    return s + sub * (1 - (props.quoteData.saas_discount || 0) / 100)
  }, 0)
  if (monthly_flag) base_sub /= (1 + MONTHLY_SURCHARGE)
  const impl_yr1 = props.quoteData.facilities.reduce((s, f) => s + tierImpl(f), 0)
  const addon_yr1 = (props.quoteData.addons || []).reduce((s, a) => s + addonPrice(a.product_sku) * (a.qty || 0), 0)
  for (let yr = 1; yr <= (props.quoteData.contract_term_yrs || 1); yr++) {
    const sub_yr = base_sub * Math.pow(1 + TRUEUP, yr - 1)
    const gt = (sub_yr + (yr === 1 ? impl_yr1 : 0) + (yr === 1 ? addon_yr1 : 0)) * (1 + VAT)
    rows.push({ year: yr, subscription_excl_vat: sub_yr, grand_total_incl_vat: gt, monthly_equivalent: monthly_flag ? gt / 12 : 0 })
  }
  return rows
})
const tcoExcl = computed(() => renewalRows.value.reduce((s, r) => s + r.subscription_excl_vat, 0))
const tcoIncl = computed(() => renewalRows.value.reduce((s, r) => s + r.grand_total_incl_vat, 0))

function fmt(v) {
  if (!v && v !== 0) return '0'
  return Math.round(parseFloat(v)).toLocaleString()
}

const saveRes   = createResource({ url: 'crm.api.quotes.save_quote' })
const sendRes   = createResource({ url: 'crm.api.quotes.send_quote' })
const acceptRes = createResource({ url: 'crm.api.quotes.accept_quote' })
const rejectRes = createResource({ url: 'crm.api.quotes.reject_quote' })

async function doSaveDraft() {
  actionLoading.value = 'draft'
  try {
    const payload = { ...props.quoteData, name: currentQuoteName.value, status: 'Draft' }
    const r = await saveRes.submit({ quote_data: JSON.stringify(payload) })
    currentQuoteName.value = r.name
    currentStatus.value = 'Draft'
    emit('saved')
  } finally { actionLoading.value = null }
}

async function doSend() {
  actionLoading.value = 'send'
  try {
    // Save first if no name
    if (!currentQuoteName.value) await doSaveDraft()
    await sendRes.submit({ quote_name: currentQuoteName.value })
    currentStatus.value = 'Sent'
    emit('sent')
  } finally { actionLoading.value = null }
}

async function doAccept() {
  actionLoading.value = 'accept'
  try {
    await acceptRes.submit({ quote_name: currentQuoteName.value })
    currentStatus.value = 'Accepted'
    emit('accepted')
  } finally { actionLoading.value = null }
}

async function doReject() {
  actionLoading.value = 'reject'
  try {
    await rejectRes.submit({ quote_name: currentQuoteName.value })
    currentStatus.value = 'Rejected'
    confirmRejectVisible.value = false
    emit('rejected')
  } finally { actionLoading.value = null }
}

function downloadPdf() {
  if (!currentQuoteName.value) { alert('Save the quote first'); return }
  window.open(
    `/api/method/frappe.utils.print_format.download_pdf?doctype=CRM+Quote&name=${encodeURIComponent(currentQuoteName.value)}&format=CRM+Quote+Standard`,
    '_blank'
  )
}
</script>
