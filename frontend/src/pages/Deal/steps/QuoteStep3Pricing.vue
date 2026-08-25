<template>
  <div class="mx-auto max-w-4xl px-5 py-6">
    <div class="mb-6">
      <h2 class="text-lg font-semibold text-ink-gray-9">{{ __('Discount & Pricing') }}</h2>
    </div>

    <div class="grid gap-6 lg:grid-cols-[1fr_320px]">
      <!-- Controls -->
      <div class="space-y-6">
        <!-- Partner context -->
        <div class="rounded-xl border border-outline-gray-2 bg-surface-gray-1 px-4 py-3 dark:bg-surface-gray-2">
          <div class="flex flex-wrap gap-4 text-sm">
            <span><span class="text-ink-gray-5">{{ __('Partner Tier') }}:</span> <strong class="text-ink-gray-9 ml-1">{{ context.partner_tier || 'No Partner' }}</strong></span>
            <span><span class="text-ink-gray-5">{{ __('Max SaaS Discount') }}:</span> <strong class="text-ink-gray-9 ml-1">{{ context.max_saas_discount ?? 45 }}%</strong></span>
            <span><span class="text-ink-gray-5">{{ __('Max Services Discount') }}:</span> <strong class="text-ink-gray-9 ml-1">{{ context.max_services_discount ?? 65 }}%</strong></span>
          </div>
          <!-- Margin info for Sales Manager / Finance Manager -->
          <div v-if="context.partner_buy_saas_pct > 0" class="mt-2 flex gap-4 text-xs text-ink-gray-4">
            <span>{{ __('Partner buy-price SaaS') }}: {{ context.partner_buy_saas_pct }}%</span>
            <span>{{ __('Partner buy-price Services') }}: {{ context.partner_buy_services_pct }}%</span>
          </div>
        </div>

        <!-- Discount inputs -->
        <div class="space-y-4">
          <div>
            <label class="mb-2 block text-sm font-medium text-ink-gray-7">
              {{ __('SaaS Discount') }} — <span :class="saasDiscount > maxSaas ? 'text-red-500' : 'text-ink-gray-5'">{{ __('max') }} {{ maxSaas }}%</span>
            </label>
            <div class="flex items-center gap-3">
              <input type="range" :min="0" :max="maxSaas" :value="saasDiscount" class="flex-1 accent-[var(--blue-6)]" @input="onSaasInput" />
              <input
                type="number"
                :min="0"
                :max="maxSaas"
                :value="saasDiscount"
                class="w-20 rounded-lg border border-outline-gray-2 bg-surface-white px-2 py-1 text-center text-sm dark:bg-surface-gray-2 focus:outline-none focus:ring-2 focus:ring-outline-blue-4"
                @input="onSaasInput"
              />
              <span class="text-sm text-ink-gray-6">%</span>
            </div>
            <p v-if="saasDiscount > maxSaas" class="mt-1 text-xs text-red-500 dark:text-red-400">{{ __('Capped at {0}% ({1} tier max)', [maxSaas, context.partner_tier]) }}</p>
          </div>
          <div>
            <label class="mb-2 block text-sm font-medium text-ink-gray-7">
              {{ __('Services Discount') }} — <span :class="servicesDiscount > maxServices ? 'text-red-500' : 'text-ink-gray-5'">{{ __('max') }} {{ maxServices }}%</span>
            </label>
            <div class="flex items-center gap-3">
              <input type="range" :min="0" :max="maxServices" :value="servicesDiscount" class="flex-1 accent-[var(--blue-6)]" @input="onServicesInput" />
              <input
                type="number"
                :min="0"
                :max="maxServices"
                :value="servicesDiscount"
                class="w-20 rounded-lg border border-outline-gray-2 bg-surface-white px-2 py-1 text-center text-sm dark:bg-surface-gray-2 focus:outline-none focus:ring-2 focus:ring-outline-blue-4"
                @input="onServicesInput"
              />
              <span class="text-sm text-ink-gray-6">%</span>
            </div>
          </div>
        </div>

        <!-- Payment terms -->
        <div>
          <label class="mb-2 block text-sm font-medium text-ink-gray-7">{{ __('Payment Terms') }}</label>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="pt in PAYMENT_TERMS"
              :key="pt.value"
              :class="[
                'rounded-lg border-2 px-3 py-2 text-sm font-medium transition-all',
                paymentTerms === pt.value
                  ? 'border-outline-blue-5 bg-surface-blue-1 text-ink-blue-7 dark:bg-surface-blue-2/20 dark:text-ink-blue-6'
                  : 'border-outline-gray-2 bg-surface-white text-ink-gray-7 hover:border-outline-blue-3 dark:bg-surface-gray-2',
              ]"
              :title="pt.value === 'Monthly' ? __('Monthly billing adds a 15% surcharge') : ''"
              @click="emit('update:paymentTerms', pt.value)"
            >
              {{ __(pt.label) }}
              <span v-if="pt.value === 'Monthly'" class="ml-1 text-xs text-ink-gray-4">(+15%)</span>
            </button>
          </div>
        </div>

        <!-- Contract term -->
        <div>
          <label class="mb-2 block text-sm font-medium text-ink-gray-7">{{ __('Contract Term') }}</label>
          <div class="flex gap-2">
            <button
              v-for="yr in [1,2,3,4,5]"
              :key="yr"
              :class="[
                'rounded-lg border-2 px-3 py-1.5 text-sm font-medium transition-all',
                contractTermYrs === yr
                  ? 'border-outline-blue-5 bg-surface-blue-1 text-ink-blue-7 dark:bg-surface-blue-2/20 dark:text-ink-blue-6'
                  : 'border-outline-gray-2 bg-surface-white text-ink-gray-7 hover:border-outline-blue-3 dark:bg-surface-gray-2',
              ]"
              @click="emit('update:contractTermYrs', yr)"
            >{{ yr }}{{ __('yr') }}</button>
          </div>
        </div>
      </div>

      <!-- Live price summary -->
      <div class="space-y-4">
        <div class="rounded-xl border border-outline-gray-2 bg-surface-white p-4 dark:bg-surface-gray-1">
          <h3 class="mb-3 text-xs font-semibold uppercase tracking-wide text-ink-gray-5">{{ __('Price Summary') }}</h3>
          <div class="space-y-2 text-sm">
            <div class="flex justify-between"><span class="text-ink-gray-6">{{ __('Subscription') }}</span><span>{{ fmtKes(pricing.sub_total) }}</span></div>
            <div class="flex justify-between"><span class="text-ink-gray-6">{{ __('Implementation') }}</span><span>{{ fmtKes(pricing.impl_total) }}</span></div>
            <div v-if="pricing.addon_total > 0" class="flex justify-between"><span class="text-ink-gray-6">{{ __('Add-ons') }}</span><span>{{ fmtKes(pricing.addon_total) }}</span></div>
            <div v-if="pricing.discount > 0" class="flex justify-between text-red-500"><span>{{ __('Discount') }}</span><span>-{{ fmtKes(pricing.discount) }}</span></div>
            <div class="my-2 border-t border-outline-gray-2" />
            <div class="flex justify-between"><span class="text-ink-gray-6">{{ __('Net Subtotal (excl. VAT)') }}</span><span class="font-medium">{{ fmtKes(pricing.net_subtotal) }}</span></div>
            <div class="flex justify-between"><span class="text-ink-gray-6">{{ __('VAT 16%') }}</span><span>{{ fmtKes(pricing.vat) }}</span></div>
            <div class="my-2 border-t border-outline-gray-2" />
            <div class="flex justify-between font-bold text-base"><span>{{ __('Grand Total Year 1') }}</span><span class="text-ink-gray-9">{{ fmtKes(pricing.grand_total) }}</span></div>
            <div v-if="paymentTerms === 'Monthly'" class="flex justify-between text-xs text-ink-gray-5"><span>{{ __('Monthly Equivalent') }}</span><span>{{ fmtKes(pricing.monthly) }}/mo</span></div>
          </div>
        </div>

        <!-- Renewal table -->
        <div v-if="contractTermYrs > 1" class="rounded-xl border border-outline-gray-2 overflow-hidden">
          <div class="bg-surface-gray-1 px-4 py-2.5 text-xs font-semibold uppercase tracking-wide text-ink-gray-5">{{ __('5-Year Renewal Schedule') }}</div>
          <table class="w-full text-xs">
            <thead class="bg-surface-gray-1/50 text-ink-gray-5">
              <tr>
                <th class="px-3 py-2 text-left font-medium">{{ __('Year') }}</th>
                <th class="px-3 py-2 text-right font-medium">{{ __('Excl. VAT') }}</th>
                <th class="px-3 py-2 text-right font-medium">{{ __('Incl. VAT') }}</th>
                <th v-if="paymentTerms === 'Monthly'" class="px-3 py-2 text-right font-medium">/mo</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-outline-elevation-2">
              <tr v-for="row in renewalSchedule" :key="row.year">
                <td class="px-3 py-1.5 font-medium text-ink-gray-9">{{ __('Year') }} {{ row.year }}</td>
                <td class="px-3 py-1.5 text-right text-ink-gray-6">{{ fmtKes(row.subscription_excl_vat) }}</td>
                <td class="px-3 py-1.5 text-right font-medium text-ink-gray-9">{{ fmtKes(row.grand_total_incl_vat) }}</td>
                <td v-if="paymentTerms === 'Monthly'" class="px-3 py-1.5 text-right text-ink-gray-6">{{ fmtKes(row.monthly_equivalent) }}</td>
              </tr>
              <tr class="bg-surface-blue-1 dark:bg-surface-blue-2/20 font-bold">
                <td class="px-3 py-2 text-ink-gray-9">{{ __('5-Year TCO') }}</td>
                <td class="px-3 py-2 text-right text-ink-gray-9">{{ fmtKes(tcoExcl) }}</td>
                <td class="px-3 py-2 text-right text-ink-blue-7 dark:text-ink-blue-6">{{ fmtKes(tcoIncl) }}</td>
                <td v-if="paymentTerms === 'Monthly'" class="px-3 py-2"></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <div class="mt-6 flex items-center justify-between">
      <Button variant="ghost" @click="emit('back')">{{ __('← Back') }}</Button>
      <Button variant="solid" @click="emit('next')">{{ __('Continue → Review') }}</Button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Button } from 'frappe-ui'

const TIERS = {
  Core:       { subscription: 605149.06,  impl: 620000.00  },
  Advanced:   { subscription: 1821349.83, impl: 1870000.00 },
  Enterprise: { subscription: 6044783.95, impl: 6180000.00 },
}
const ADDON_PRICES = {
  'CV-HW-OPTIPLEX-7010':       84000,
  'CV-HW-LATITUDE-5440':      126000,
  'CV-HW-TAB-10':              38889,
  'CV-SW-ENDPOINT-SEC':         8100,
  'CV-SW-OFFICE-MGMT':         13886,
  'CV-SVC-OUT-NAIROBI':        14500,
  'CV-SVC-REFRESHER-VIRT':      2500,
  'CV-SVC-ONSITE-ENGINEER':   220000,
  'CV-SVC-PARTTIME-ENGINEER': 100000,
}
const PAYMENT_TERMS = [
  { value: 'Annual Upfront',    label: 'Annual Upfront' },
  { value: 'Quarterly Advance', label: 'Quarterly Advance' },
  { value: 'Monthly',           label: 'Monthly' },
]
const VAT = 0.16
const MONTHLY_SURCHARGE = 0.15
const TRUEUP = 0.05

const props = defineProps({
  facilities:       { type: Array,  default: () => [] },
  addons:           { type: Array,  default: () => [] },
  paymentTerms:     { type: String, default: 'Annual Upfront' },
  contractTermYrs:  { type: Number, default: 1 },
  saasDiscount:     { type: Number, default: 0 },
  servicesDiscount: { type: Number, default: 0 },
  context:          { type: Object, default: () => ({}) },
})
const emit = defineEmits([
  'update:paymentTerms', 'update:contractTermYrs',
  'update:saasDiscount', 'update:servicesDiscount',
  'next', 'back', 'dirty',
])

const maxSaas     = computed(() => props.context.max_saas_discount ?? 45)
const maxServices = computed(() => props.context.max_services_discount ?? 65)

function onSaasInput(e) {
  const v = Math.min(Math.max(0, parseFloat(e.target.value) || 0), maxSaas.value)
  emit('update:saasDiscount', v)
  emit('dirty')
}
function onServicesInput(e) {
  const v = Math.min(Math.max(0, parseFloat(e.target.value) || 0), maxServices.value)
  emit('update:servicesDiscount', v)
  emit('dirty')
}

const pricing = computed(() => {
  let sub_total = 0, impl_total = 0
  for (const f of props.facilities) {
    const p = TIERS[f.package_tier] || TIERS.Core
    let sub = p.subscription * (1 - (props.saasDiscount || 0) / 100)
    let impl = p.impl * (1 - (props.servicesDiscount || 0) / 100)
    if (props.paymentTerms === 'Monthly') sub *= (1 + MONTHLY_SURCHARGE)
    sub_total  += sub
    impl_total += impl
  }
  let addon_total = 0
  for (const a of props.addons) {
    addon_total += (ADDON_PRICES[a.product_sku] || 0) * (a.qty || 0)
  }
  const raw_sub_total  = props.facilities.reduce((s, f) => s + (TIERS[f.package_tier]?.subscription || 0), 0)
  const raw_impl_total = props.facilities.reduce((s, f) => s + (TIERS[f.package_tier]?.impl || 0), 0)
  const discount = (raw_sub_total - sub_total) + (raw_impl_total - impl_total)
  const net_subtotal = sub_total + impl_total + addon_total
  const vat = net_subtotal * VAT
  const grand_total = net_subtotal + vat
  const monthly = grand_total / 12
  return { sub_total, impl_total, addon_total, discount, net_subtotal, vat, grand_total, monthly, base_sub: sub_total }
})

const renewalSchedule = computed(() => {
  const rows = []
  const monthly_flag = props.paymentTerms === 'Monthly'
  let base_sub = props.facilities.reduce((s, f) => {
    const p = TIERS[f.package_tier] || TIERS.Core
    return s + p.subscription * (1 - (props.saasDiscount || 0) / 100)
  }, 0)
  if (monthly_flag) base_sub /= (1 + MONTHLY_SURCHARGE)

  const impl_yr1 = props.facilities.reduce((s, f) => {
    const p = TIERS[f.package_tier] || TIERS.Core
    return s + p.impl * (1 - (props.servicesDiscount || 0) / 100)
  }, 0)
  const addon_yr1 = props.addons.reduce((s, a) => s + (ADDON_PRICES[a.product_sku] || 0) * (a.qty || 0), 0)

  for (let yr = 1; yr <= props.contractTermYrs; yr++) {
    const sub_yr = base_sub * Math.pow(1 + TRUEUP, yr - 1)
    const impl_yr = yr === 1 ? impl_yr1 : 0
    const addon_yr = yr === 1 ? addon_yr1 : 0
    const gt = (sub_yr + impl_yr + addon_yr) * (1 + VAT)
    rows.push({
      year: yr,
      subscription_excl_vat: sub_yr,
      grand_total_incl_vat: gt,
      monthly_equivalent: monthly_flag ? gt / 12 : 0,
    })
  }
  return rows
})

const tcoExcl = computed(() => renewalSchedule.value.reduce((s, r) => s + r.subscription_excl_vat, 0))
const tcoIncl = computed(() => renewalSchedule.value.reduce((s, r) => s + r.grand_total_incl_vat, 0))

function fmtKes(v) {
  if (!v && v !== 0) return 'KES 0'
  const n = parseFloat(v)
  if (n >= 1_000_000) return 'KES ' + (n / 1_000_000).toFixed(1) + 'M'
  if (n >= 1_000)     return 'KES ' + Math.round(n / 1_000) + 'K'
  return 'KES ' + Math.round(n).toLocaleString()
}
</script>
