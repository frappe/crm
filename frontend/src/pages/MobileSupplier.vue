<template>
  <div class="flex h-full flex-col">
    <MobileHeader>
      <template #left>
        <router-link
          :to="{ name: 'Suppliers' }"
          class="flex items-center gap-2 text-base font-medium text-gray-600"
        >
          <FeatherIcon name="arrow-left" class="h-4" />
        </router-link>
      </template>
      <template #title>
        {{ supplier?.supplier_name || __('Supplier') }}
      </template>
    </MobileHeader>

    <div v-if="supplier" class="flex-1 overflow-auto">
      <div class="space-y-6 p-4">
        <div class="flex items-center gap-4">
          <div
            v-if="supplier.image"
            class="h-16 w-16 overflow-hidden rounded-lg"
          >
            <img
              :src="supplier.image"
              :alt="supplier.supplier_name"
              class="h-full w-full object-cover"
            />
          </div>
          <div v-else class="flex h-16 w-16 items-center justify-center rounded-lg bg-gray-100">
            <span class="text-2xl font-medium text-gray-600">
              {{ supplier.supplier_name[0] }}
            </span>
          </div>
          <div>
            <h1 class="text-xl font-bold text-gray-900">
              {{ supplier.supplier_name }}
            </h1>
            <p v-if="supplier.supplier_type" class="text-sm text-gray-500">
              {{ supplier.supplier_type }}
            </p>
          </div>
        </div>

        <div class="space-y-4">
          <div v-if="supplier.tax_id" class="space-y-1">
            <label class="text-sm font-medium text-gray-500">{{ __('Tax ID') }}</label>
            <p class="text-base text-gray-900">{{ supplier.tax_id }}</p>
          </div>
          <div v-if="supplier.supplier_group" class="space-y-1">
            <label class="text-sm font-medium text-gray-500">{{ __('Supplier Group') }}</label>
            <p class="text-base text-gray-900">{{ supplier.supplier_group }}</p>
          </div>
          <div v-if="supplier.country" class="space-y-1">
            <label class="text-sm font-medium text-gray-500">{{ __('Country') }}</label>
            <p class="text-base text-gray-900">{{ supplier.country }}</p>
          </div>
          <div v-if="supplier.default_currency" class="space-y-1">
            <label class="text-sm font-medium text-gray-500">{{ __('Default Currency') }}</label>
            <p class="text-base text-gray-900">{{ supplier.default_currency }}</p>
          </div>
          <div v-if="supplier.default_price_list" class="space-y-1">
            <label class="text-sm font-medium text-gray-500">{{ __('Default Price List') }}</label>
            <p class="text-base text-gray-900">{{ supplier.default_price_list }}</p>
          </div>
          <div v-if="supplier.payment_terms" class="space-y-1">
            <label class="text-sm font-medium text-gray-500">{{ __('Payment Terms') }}</label>
            <p class="text-base text-gray-900">{{ supplier.payment_terms }}</p>
          </div>
          <div v-if="supplier.website" class="space-y-1">
            <label class="text-sm font-medium text-gray-500">{{ __('Website') }}</label>
            <p class="text-base text-blue-600">
              <a :href="supplier.website" target="_blank" rel="noopener noreferrer">
                {{ supplier.website }}
              </a>
            </p>
          </div>
        </div>

        <div v-if="supplier.is_frozen" class="rounded-lg bg-red-50 p-4">
          <p class="text-sm text-red-700">
            {{ __('This supplier is frozen. Transactions with this supplier cannot be created.') }}
          </p>
        </div>
      </div>
    </div>
    <div
      v-else
      class="flex h-full items-center justify-center text-lg text-gray-500"
    >
      {{ __('Loading...') }}
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { call } from 'frappe-ui'
import { FeatherIcon } from 'frappe-ui'
import MobileHeader from '@/components/Mobile/MobileHeader.vue'

const route = useRoute()
const supplier = ref(null)

onMounted(async () => {
  try {
    const result = await call('frappe.client.get', {
      doctype: 'Supplier',
      name: route.params.supplierId,
    })
    supplier.value = result.message
  } catch (error) {
    console.error('Error fetching supplier:', error)
  }
})

function formatCurrency(value) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: supplier.value?.default_currency || 'USD',
  }).format(value)
}
</script> 