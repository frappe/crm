<template>
  <div class="flex flex-1 flex-col overflow-y-auto">
    <div
      v-if="quotations.loading && !quotations.data?.length"
      class="flex flex-1 items-center justify-center gap-3 text-base text-ink-gray-4"
    >
      <LoadingIndicator class="h-4 w-4" />
      <span>{{ __('Loading...') }}</span>
    </div>

    <div
      v-else-if="!quotations.data?.length"
      class="flex flex-1 flex-col items-center justify-center gap-2 text-ink-gray-4"
    >
      <DetailsIcon class="h-8 w-8" />
      <div class="text-base">{{ __('No Quotations Found') }}</div>
    </div>

    <div v-else class="flex flex-col gap-2 p-5">
      <div
        v-for="q in quotations.data"
        :key="q.name"
        class="flex items-center justify-between rounded-lg border p-3 hover:bg-surface-gray-1 cursor-pointer"
        @click="openInERPNext(q.name)"
      >
        <div class="flex flex-col gap-1 truncate">
          <div class="flex items-center gap-2">
            <div class="text-base font-medium text-ink-gray-9">
              {{ q.name }}
            </div>
            <Badge :label="q.status" :theme="statusTheme(q.status)" />
          </div>
          <div class="text-sm text-ink-gray-5">
            {{ q.customer_name || '' }}
            <span v-if="q.transaction_date"> · {{ formatDate(q.transaction_date) }}</span>
            <span v-if="q.valid_till"> · {{ __('Valid till') }} {{ formatDate(q.valid_till) }}</span>
          </div>
        </div>
        <div class="flex items-center gap-3 shrink-0">
          <div class="text-base font-medium text-ink-gray-9">
            {{ formatAmount(q.grand_total, q.currency) }}
          </div>
          <Tooltip :text="__('Open in ERPNext')">
            <Button
              variant="ghost"
              :icon="ArrowUpRightIcon"
              @click.stop="openInERPNext(q.name)"
            />
          </Tooltip>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import DetailsIcon from '@/components/Icons/DetailsIcon.vue'
import LoadingIndicator from '@/components/Icons/LoadingIndicator.vue'
import ArrowUpRightIcon from '@/components/Icons/ArrowUpRightIcon.vue'
import { createResource, Badge, Button, Tooltip } from 'frappe-ui'

const props = defineProps({
  dealId: { type: String, required: true },
})

const quotations = createResource({
  url: 'crm.fcrm.doctype.crm_deal.api.get_deal_quotations',
  params: { name: props.dealId },
  cache: ['deal_quotations', props.dealId],
  auto: true,
})

function statusTheme(status) {
  const map = {
    Draft: 'gray',
    Open: 'blue',
    Replied: 'orange',
    Ordered: 'green',
    Submitted: 'green',
    Lost: 'red',
    Cancelled: 'red',
    Expired: 'red',
  }
  return map[status] || 'gray'
}

function formatDate(date) {
  return new Date(date).toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
}

function formatAmount(amount, currency) {
  if (!amount) return ''
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: currency || 'INR',
    maximumFractionDigits: 0,
  }).format(amount)
}

function openInERPNext(name) {
  window.open(`/app/quotation/${name}`, '_blank')
}
</script>