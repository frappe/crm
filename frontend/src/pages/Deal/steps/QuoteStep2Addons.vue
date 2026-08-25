<template>
  <div class="mx-auto max-w-3xl px-5 py-6">
    <div class="mb-6">
      <h2 class="text-lg font-semibold text-ink-gray-9">{{ __('Add-ons') }} <span class="text-sm font-normal text-ink-gray-4">({{ __('Optional') }})</span></h2>
      <p class="mt-1 text-sm text-ink-gray-5">{{ __('Select additional products to include in this quote.') }}</p>
    </div>

    <div v-for="group in GROUPS" :key="group.key" class="mb-6">
      <h3 class="mb-3 text-xs font-semibold uppercase tracking-wide text-ink-gray-5">{{ __(group.label) }}</h3>
      <div class="overflow-hidden rounded-xl border border-outline-gray-2">
        <table class="w-full text-sm">
          <thead class="bg-surface-gray-1 text-xs text-ink-gray-5">
            <tr>
              <th class="w-8 px-3 py-2"></th>
              <th class="px-4 py-2 text-left font-medium">{{ __('Product') }}</th>
              <th class="px-4 py-2 text-center font-medium w-24">{{ __('Qty') }}</th>
              <th class="px-4 py-2 text-right font-medium">{{ __('Unit Price') }}</th>
              <th class="px-4 py-2 text-right font-medium">{{ __('Total') }}</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-outline-gray-2">
            <tr v-for="product in group.products" :key="product.sku" class="transition-colors" :class="isChecked(product.sku) ? 'bg-surface-blue-1/50 dark:bg-surface-blue-2/20' : ''">
              <td class="px-3 py-2.5 text-center">
                <input type="checkbox" :checked="isChecked(product.sku)" @change="toggleAddon(product)" class="h-4 w-4 rounded accent-[var(--blue-6)] cursor-pointer" />
              </td>
              <td class="px-4 py-2.5 font-medium text-ink-gray-9">
                {{ product.name }}
                <span class="ml-1 text-xs text-ink-gray-4">{{ product.unit }}</span>
              </td>
              <td class="px-4 py-2.5 text-center">
                <input
                  v-if="isChecked(product.sku)"
                  v-model.number="getAddon(product.sku).qty"
                  type="number"
                  min="1"
                  class="w-20 rounded-lg border border-outline-gray-2 bg-surface-white px-2 py-1 text-center text-sm dark:bg-surface-gray-2 focus:outline-none focus:ring-2 focus:ring-outline-blue-4"
                  @input="emit('dirty')"
                />
                <span v-else class="text-ink-gray-3">—</span>
              </td>
              <td class="px-4 py-2.5 text-right text-ink-gray-6">{{ fmtKes(product.price) }}</td>
              <td class="px-4 py-2.5 text-right font-medium text-ink-gray-9">
                {{ isChecked(product.sku) ? fmtKes(product.price * (getAddon(product.sku).qty || 0)) : '—' }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-if="addonsTotal > 0" class="flex items-center justify-end text-sm font-semibold text-ink-gray-9">
      {{ __('Add-ons Subtotal') }}: {{ fmtKes(addonsTotal) }}
    </div>

    <div class="mt-6 flex items-center justify-between">
      <Button variant="ghost" @click="emit('back')">{{ __('← Back') }}</Button>
      <div class="flex gap-2">
        <Button variant="subtle" @click="emit('next')">{{ __('Skip') }}</Button>
        <Button variant="solid" @click="emit('next')">{{ __('Continue → Pricing') }}</Button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Button } from 'frappe-ui'

const props = defineProps({
  addons: { type: Array, default: () => [] },
})
const emit = defineEmits(['update:addons', 'next', 'back', 'dirty'])

const GROUPS = [
  {
    key: 'hardware',
    label: 'Hardware',
    products: [
      { sku: 'CV-HW-OPTIPLEX-7010',  name: 'Dell OptiPlex 7010 MT Workstation', price: 84000,  unit: '/unit' },
      { sku: 'CV-HW-LATITUDE-5440',  name: 'Dell Latitude 5440 Laptop',          price: 126000, unit: '/unit' },
      { sku: 'CV-HW-TAB-10',         name: 'Tablet 10.1" Android',               price: 38889,  unit: '/unit' },
    ],
  },
  {
    key: 'software',
    label: 'Software',
    products: [
      { sku: 'CV-SW-ENDPOINT-SEC',  name: 'Endpoint Security Subscription',  price: 8100,  unit: '/user/yr' },
      { sku: 'CV-SW-OFFICE-MGMT',   name: 'Office Management Suite',         price: 13886, unit: '/user/yr' },
    ],
  },
  {
    key: 'services',
    label: 'Professional Services',
    products: [
      { sku: 'CV-SVC-OUT-NAIROBI',        name: 'Implementation Outside Nairobi',       price: 14500,  unit: '/day/implementor' },
      { sku: 'CV-SVC-REFRESHER-VIRT',     name: 'Refresher Training (Virtual)',          price: 2500,   unit: '/session' },
      { sku: 'CV-SVC-ONSITE-ENGINEER',    name: 'On-Site Support Engineer (5 days/wk)', price: 220000, unit: '/month' },
      { sku: 'CV-SVC-PARTTIME-ENGINEER',  name: 'Part-Time Support Engineer (2 days/wk)', price: 100000, unit: '/month' },
    ],
  },
]

function isChecked(sku) { return props.addons.some(a => a.product_sku === sku) }
function getAddon(sku)  { return props.addons.find(a => a.product_sku === sku) || { qty: 1 } }

function toggleAddon(product) {
  if (isChecked(product.sku)) {
    emit('update:addons', props.addons.filter(a => a.product_sku !== product.sku))
  } else {
    emit('update:addons', [...props.addons, { product_sku: product.sku, qty: 1 }])
  }
  emit('dirty')
}

const addonsTotal = computed(() => {
  return GROUPS.flatMap(g => g.products).reduce((sum, p) => {
    const a = getAddon(p.sku)
    return sum + (isChecked(p.sku) ? p.price * (a.qty || 0) : 0)
  }, 0)
})

function fmtKes(v) {
  if (!v && v !== 0) return 'KES 0'
  const n = parseFloat(v)
  if (n >= 1_000_000) return 'KES ' + (n / 1_000_000).toFixed(1) + 'M'
  if (n >= 1_000)     return 'KES ' + Math.round(n / 1_000) + 'K'
  return 'KES ' + n.toLocaleString()
}
</script>
