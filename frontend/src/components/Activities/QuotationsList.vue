<template>
  <div class="flex h-full flex-col">
    <div
      v-if="quotations.loading && !quotations.fetched"
      class="flex flex-1 flex-col items-center justify-center gap-3 text-2xl-medium text-ink-gray-4"
    >
      <LoadingIndicator class="h-6 w-6" />
      <span>{{ __('Loading...') }}</span>
    </div>
    <EmptyState
      v-else-if="!rows.length"
      name="Quotations"
      :title="__('No quotations yet')"
      :description="__('Create a quotation from this deal to see it here.')"
      icon="file-text"
      top="30%"
    />
    <div v-else class="flex flex-col px-3 pb-3 sm:px-10 sm:pb-5">
      <div v-for="(quotation, i) in rows" :key="quotation.name">
        <a
          :href="quotation.url"
          target="_blank"
          rel="noopener noreferrer"
          class="group flex cursor-pointer items-center gap-4 rounded p-3 duration-300 ease-in-out hover:bg-surface-gray-1"
        >
          <div class="flex min-w-0 flex-1 flex-col gap-2 truncate text-base">
            <div class="flex items-center gap-2">
              <span class="truncate font-medium text-ink-gray-9">
                {{ quotation.name }}
              </span>
              <Badge
                :label="quotation.status"
                :theme="statusTheme(quotation.status)"
                variant="subtle"
                size="sm"
              />
            </div>
            <div class="flex items-center gap-2 text-ink-gray-6">
              <span class="tabular-nums text-ink-gray-8">
                {{
                  formatCurrency(quotation.grand_total, '', quotation.currency)
                }}
              </span>
              <span class="text-ink-gray-4">·</span>
              <span>{{ dateLabel(quotation) }}</span>
            </div>
          </div>
          <ArrowUpRightIcon
            class="h-4 w-4 shrink-0 text-ink-gray-4 opacity-0 duration-200 group-hover:opacity-100"
          />
        </a>
        <div
          v-if="i < rows.length - 1"
          class="mx-2 h-px border-t border-outline-elevation-2"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import EmptyState from '@/components/ListViews/EmptyState.vue'
import ArrowUpRightIcon from '@/components/Icons/ArrowUpRightIcon.vue'
import LoadingIndicator from '@/components/Icons/LoadingIndicator.vue'
import { formatDate } from '@/utils'
import { formatCurrency } from '@/utils/numberFormat.js'
import { globalStore } from '@/stores/global'
import { Badge, createResource } from 'frappe-ui'
import { computed, onBeforeUnmount, onMounted } from 'vue'

const { $socket } = globalStore()

const props = defineProps({
  deal: { type: String, required: true },
})

const quotations = createResource({
  url: 'crm.fcrm.doctype.erpnext_crm_settings.erpnext_crm_settings.get_deal_quotations',
  params: { crm_deal: props.deal },
  auto: true,
})

const rows = computed(() => quotations.data || [])

// live-refresh when a quotation for this deal is created/updated/deleted (same-site)
function onQuotationUpdate(data) {
  if (data?.crm_deal === props.deal) quotations.reload()
}
onMounted(() => $socket.on('crm_quotation_update', onQuotationUpdate))
onBeforeUnmount(() => $socket.off('crm_quotation_update', onQuotationUpdate))

// ERPNext Quotation statuses → frappe-ui Badge themes
const STATUS_THEME = {
  Draft: 'gray',
  Open: 'orange',
  Ordered: 'green',
  Lost: 'red',
  Expired: 'gray',
  Cancelled: 'red',
}
function statusTheme(status) {
  return STATUS_THEME[status] || 'gray'
}

function dateLabel(quotation) {
  if (quotation.valid_till) {
    return __('Valid till {0}', [formatDate(quotation.valid_till, '', true)])
  }
  return formatDate(quotation.transaction_date, '', true)
}
</script>
