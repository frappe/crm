<template>
  <div
    :class="[
      'flex flex-col md:flex-row md:items-center gap-3 px-3 py-3 hover:bg-gray-50 dark:hover:bg-gray-800/60 transition-colors',
      'border-l-4',
      urgencyBorderClass,
    ]"
  >
    <!-- Icon chip -->
    <div
      :class="[
        'w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0',
        urgencyBgClass,
      ]"
      v-html="typeIconSvg"
    />

    <!-- Main info -->
    <div class="flex-1 min-w-0">
      <div class="flex flex-wrap items-baseline gap-1.5">
        <span class="text-xs text-gray-400 dark:text-gray-500 uppercase tracking-wide">{{ item.doctype }}</span>
        <span class="text-xs text-gray-500 dark:text-gray-400">{{ item.docname }}</span>
      </div>
      <p class="font-medium text-gray-800 dark:text-gray-200 truncate">{{ item.party_name || item.party_type }}</p>
      <div class="flex items-center gap-2 mt-0.5">
        <span
          v-if="item.amount > 0"
          class="text-sm font-semibold text-gray-700 dark:text-gray-300"
        >
          {{ formatCurrency(item.amount, item.currency) }}
        </span>
        <span class="text-xs bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400 rounded px-1.5 py-0.5">
          {{ item.age_days }}d
        </span>
      </div>
    </div>

    <!-- Actions -->
    <div class="flex flex-col md:flex-row items-stretch md:items-center gap-2 md:flex-shrink-0 w-full md:w-auto">
      <a
        :href="item.erpnext_url"
        target="_blank"
        class="text-xs px-3 py-1.5 rounded bg-blue-600 text-white hover:bg-blue-700 transition-colors text-center font-medium"
        @click.stop
      >{{ item.primary_action_label }}</a>
      <button
        v-if="item.secondary_actions && item.secondary_actions.length"
        class="text-xs px-2 py-1.5 rounded border border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
        @click.stop="showMenu = !showMenu"
      >
        &hellip;
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useCurrency } from '../composables/useCurrency.js'

const props = defineProps({
  item: { type: Object, required: true },
})

const showMenu = ref(false)

const URGENCY_BORDER = {
  critical: 'border-red-500',
  warning: 'border-amber-500',
  normal: 'border-gray-300 dark:border-gray-600',
}
const URGENCY_BG = {
  critical: 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400',
  warning: 'bg-amber-100 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400',
  normal: 'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400',
}

const TYPE_ICONS = {
  overdue_invoice: '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 2v20l2-1 2 1 2-1 2 1 2-1 2 1 2-1 2 1V2l-2 1-2-1-2 1-2-1-2 1-2-1-2 1Z"/><path d="M16 8h-6a2 2 0 1 0 0 4h4a2 2 0 1 1 0 4H8"/><path d="M12 17.5v-11"/></svg>',
  unapplied_payment: '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="20" height="14" x="2" y="5" rx="2"/><line x1="2" x2="22" y1="10" y2="10"/></svg>',
  pending_rebate: '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/><line x1="3" x2="21" y1="6" y2="6"/><path d="M16 10a4 4 0 0 1-8 0"/></svg>',
  approved_rebate_unpaid: '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 12 20 22 4 22 4 12"/><rect width="20" height="5" x="2" y="7"/><line x1="12" x2="12" y1="22" y2="7"/><path d="M12 7H7.5a2.5 2.5 0 0 1 0-5C11 2 12 7 12 7z"/><path d="M12 7h4.5a2.5 2.5 0 0 0 0-5C13 2 12 7 12 7z"/></svg>',
  unconfirmed_commission: '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 7H4a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="2"/><path d="M6 12h.01M18 12h.01"/></svg>',
  confirmed_commission_unpaid: '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m9 12 2 2 4-4"/><path d="M5 7H4a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-1"/><rect width="10" height="5" x="7" y="2" rx="1"/></svg>',
  expense_claim_pending_payment: '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12V7H5a2 2 0 0 1 0-4h14v4"/><path d="M3 5v14a2 2 0 0 0 2 2h16v-5"/><path d="M18 12a2 2 0 0 0 0 4h4v-4Z"/></svg>',
  employee_advance_unclaimed: '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
  overdue_purchase_invoice: '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="20" height="14" x="2" y="5" rx="2"/><line x1="2" x2="22" y1="10" y2="10"/></svg>',
  purchase_invoice_pending_approval: '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" x2="8" y1="13" y2="13"/><line x1="16" x2="8" y1="17" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>',
  bank_transaction_unmatched: '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="3" x2="21" y1="22" y2="22"/><line x1="6" x2="6" y1="18" y2="11"/><line x1="10" x2="10" y1="18" y2="11"/><line x1="14" x2="14" y1="18" y2="11"/><line x1="18" x2="18" y1="18" y2="11"/><polygon points="12 2 20 7 4 7"/></svg>',
  period_closing_due: '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="4" rx="2" ry="2"/><line x1="16" x2="16" y1="2" y2="6"/><line x1="8" x2="8" y1="2" y2="6"/><line x1="3" x2="21" y1="10" y2="10"/></svg>',
  subscription_invoice_due: '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 7.5V6a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h3.5"/><path d="M16 2v4"/><path d="M8 2v4"/><path d="M3 10h5"/><path d="m17.5 17.5 1.5 1.5 3-3"/><circle cx="19" cy="19" r="3"/></svg>',
}

const urgencyBorderClass = URGENCY_BORDER[props.item.urgency] || URGENCY_BORDER.normal
const urgencyBgClass = URGENCY_BG[props.item.urgency] || URGENCY_BG.normal
const typeIconSvg = TYPE_ICONS[props.item.type] || TYPE_ICONS.overdue_invoice

const { formatCurrency } = useCurrency()
</script>
