<template>
  <div class="fc-setup space-y-6">
    <div>
      <h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100">Setup</h2>
      <p class="mt-1 text-xs text-gray-400">Finance Manager configuration links. Opens ERPNext in a new tab.</p>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      <a
        v-for="link in setupLinks"
        :key="link.label"
        :href="resolveUrl(link.url)"
        target="_blank"
        rel="noopener noreferrer"
        class="group flex items-start gap-3 p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg hover:border-blue-400 dark:hover:border-blue-500 hover:shadow-sm transition-all"
      >
        <component
          :is="link.icon"
          class="w-5 h-5 mt-0.5 text-gray-400 group-hover:text-blue-500 shrink-0 transition-colors"
        />
        <div class="min-w-0">
          <div class="text-sm font-medium text-gray-800 dark:text-gray-200 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors truncate">
            {{ link.label }}
          </div>
          <div class="text-xs text-gray-500 dark:text-gray-400 mt-0.5 line-clamp-2">{{ link.description }}</div>
        </div>
      </a>
    </div>
  </div>
</template>

<script setup>
import { useCompanyContext } from '../composables/useCompanyContext.js'
import LucideBuilding2 from '~icons/lucide/building-2'
import LucideGitBranch from '~icons/lucide/git-branch'
import LucideSliders from '~icons/lucide/sliders'
import LucideReceipt from '~icons/lucide/receipt'
import LucideClock from '~icons/lucide/clock'
import LucideCreditCard from '~icons/lucide/credit-card'
import LucideCalendar from '~icons/lucide/calendar'
import LucideRefreshCw from '~icons/lucide/refresh-cw'

const { company } = useCompanyContext()

const setupLinks = [
  {
    label: 'Chart of Accounts',
    description: 'View and manage the company account tree.',
    icon: LucideBuilding2,
    url: '/app/account?is_tree=1&company=__COMPANY__',
  },
  {
    label: 'Cost Centres',
    description: 'Manage cost centre hierarchy for expense tracking.',
    icon: LucideGitBranch,
    url: '/app/cost-center?is_tree=1',
  },
  {
    label: 'Accounting Dimensions',
    description: 'Define custom dimensions for granular reporting.',
    icon: LucideSliders,
    url: '/app/accounting-dimension',
  },
  {
    label: 'Tax Templates',
    description: 'Configure sales taxes and charge templates.',
    icon: LucideReceipt,
    url: '/app/sales-taxes-and-charges-template',
  },
  {
    label: 'Payment Terms',
    description: 'Set up payment term schedules for invoices.',
    icon: LucideClock,
    url: '/app/payment-terms-template',
  },
  {
    label: 'Payment Methods',
    description: 'Manage accepted modes of payment.',
    icon: LucideCreditCard,
    url: '/app/mode-of-payment',
  },
  {
    label: 'Fiscal Year',
    description: 'Configure fiscal year dates for reporting periods.',
    icon: LucideCalendar,
    url: '/app/fiscal-year',
  },
  {
    label: 'Currency Exchange',
    description: 'Set currency exchange rates and settings.',
    icon: LucideRefreshCw,
    url: '/app/currency-exchange-settings',
  },
]

function resolveUrl(url) {
  return url.replace('__COMPANY__', encodeURIComponent(company.value || ''))
}
</script>
