<template>
  <div class="flex h-full flex-col">
    <MobileHeader>
      <template #left>
        <router-link
          :to="{ name: 'Customers' }"
          class="flex items-center gap-2 text-base font-medium text-gray-600"
        >
          <FeatherIcon name="arrow-left" class="h-4" />
        </router-link>
      </template>
      <template #title>
        {{ customer?.customer_name || __('Customer') }}
      </template>
    </MobileHeader>

    <div v-if="customer" class="flex-1 overflow-auto">
      <div class="space-y-6 p-4">
        <div class="flex items-center gap-4">
          <div
            v-if="customer.image"
            class="h-16 w-16 overflow-hidden rounded-lg"
          >
            <img
              :src="customer.image"
              :alt="customer.customer_name"
              class="h-full w-full object-cover"
            />
          </div>
          <div v-else class="flex h-16 w-16 items-center justify-center rounded-lg bg-gray-100">
            <span class="text-2xl font-medium text-gray-600">
              {{ customer.customer_name[0] }}
            </span>
          </div>
          <div>
            <h1 class="text-xl font-bold text-gray-900">
              {{ customer.customer_name }}
            </h1>
            <p v-if="customer.customer_type" class="text-sm text-gray-500">
              {{ customer.customer_type }}
            </p>
          </div>
        </div>

        <div class="space-y-4">
          <div v-if="customer.tax_id" class="space-y-1">
            <label class="text-sm font-medium text-gray-500">{{ __('Tax ID') }}</label>
            <p class="text-base text-gray-900">{{ customer.tax_id }}</p>
          </div>
          <div v-if="customer.customer_group" class="space-y-1">
            <label class="text-sm font-medium text-gray-500">{{ __('Customer Group') }}</label>
            <p class="text-base text-gray-900">{{ customer.customer_group }}</p>
          </div>
          <div v-if="customer.territory" class="space-y-1">
            <label class="text-sm font-medium text-gray-500">{{ __('Territory') }}</label>
            <p class="text-base text-gray-900">{{ customer.territory }}</p>
          </div>
          <div v-if="customer.default_currency" class="space-y-1">
            <label class="text-sm font-medium text-gray-500">{{ __('Default Currency') }}</label>
            <p class="text-base text-gray-900">{{ customer.default_currency }}</p>
          </div>
          <div v-if="customer.default_price_list" class="space-y-1">
            <label class="text-sm font-medium text-gray-500">{{ __('Default Price List') }}</label>
            <p class="text-base text-gray-900">{{ customer.default_price_list }}</p>
          </div>
          <div v-if="customer.payment_terms" class="space-y-1">
            <label class="text-sm font-medium text-gray-500">{{ __('Payment Terms') }}</label>
            <p class="text-base text-gray-900">{{ customer.payment_terms }}</p>
          </div>
        </div>

        <div v-if="customer.credit_limits && customer.credit_limits.length" class="space-y-2">
          <h3 class="text-lg font-medium text-gray-900">{{ __('Credit Limits') }}</h3>
          <div class="space-y-4">
            <div
              v-for="limit in customer.credit_limits"
              :key="limit.name"
              class="rounded-lg border p-4"
            >
              <div class="space-y-2">
                <div class="space-y-1">
                  <label class="text-sm font-medium text-gray-500">{{ __('Company') }}</label>
                  <p class="text-base text-gray-900">{{ limit.company }}</p>
                </div>
                <div class="space-y-1">
                  <label class="text-sm font-medium text-gray-500">{{ __('Credit Limit') }}</label>
                  <p class="text-base text-gray-900">{{ formatCurrency(limit.credit_limit) }}</p>
                </div>
              </div>
            </div>
          </div>
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
const customer = ref(null)

onMounted(async () => {
  try {
    const result = await call('frappe.client.get', {
      doctype: 'Customer',
      name: route.params.customerId,
    })
    customer.value = result.message
  } catch (error) {
    console.error('Error fetching customer:', error)
  }
})

function formatCurrency(value) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: customer.value?.default_currency || 'USD',
  }).format(value)
}
</script> 