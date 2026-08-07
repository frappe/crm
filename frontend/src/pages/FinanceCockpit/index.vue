<template>
  <div class="fc-root flex h-screen overflow-hidden bg-gray-50 dark:bg-gray-950">
    <!-- Sidebar overlay backdrop for mobile -->
    <div
      v-if="isMobile && sidebarIsOpen"
      class="fixed inset-0 bg-black/40 z-40"
      @click="sidebarClose"
    />
    <!-- Sidebar -->
    <Sidebar
      :active-section="activeSection"
      :badge-count="inboxBadgeCount"
      :user-roles="userRoles"
      @navigate="onNavigate"
    />
    <!-- Main content -->
    <div class="flex flex-col flex-1 min-w-0 overflow-hidden">
      <Topbar @toggle-sidebar="sidebarToggle" />
      <main class="flex-1 overflow-y-auto p-4">
        <template v-if="activeSection === 'dashboard'">
          <KpiStrip :user-roles="userRoles" @navigate="onNavigate" @update:period="kpiPeriod = $event" />
          <!-- Charts lazy-loaded after KPI strip — only shown once company context exists -->
          <Suspense>
            <DashboardCharts v-if="company" :period="kpiPeriod" />
            <template #fallback>
              <div class="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
                <div v-for="n in 4" :key="n" class="bg-gray-100 dark:bg-gray-800 rounded-lg p-4 h-48 animate-pulse" />
              </div>
            </template>
          </Suspense>
        </template>
        <template v-else-if="activeSection === 'inbox'">
          <Inbox ref="inboxRef" />
        </template>
        <template v-else-if="activeSection === 'receivables'">
          <Receivables />
        </template>
        <template v-else-if="activeSection === 'payables'">
          <Payables />
        </template>
        <template v-else-if="activeSection === 'expenses'">
          <Expenses />
        </template>
        <template v-else-if="activeSection === 'partner_commission'">
          <PartnerCommission />
        </template>
        <template v-else-if="activeSection === 'banking'">
          <Banking />
        </template>
        <template v-else-if="activeSection === 'reports'">
          <Reports />
        </template>
        <template v-else-if="activeSection === 'general_ledger' && isFinanceManager">
          <GeneralLedger />
        </template>
        <template v-else-if="activeSection === 'liabilities' && isFinanceManager">
          <Liabilities />
        </template>
        <template v-else-if="activeSection === 'assets' && isFinanceManager">
          <Assets />
        </template>
        <template v-else>
          <p class="font-medium text-gray-700 dark:text-gray-300 capitalize">
            {{ activeSection.replace(/_/g, ' ') }}
          </p>
          <p class="text-xs mt-1 text-gray-400">Section content coming in a future sprint.</p>
        </template>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, defineAsyncComponent, onMounted } from 'vue'
import Sidebar from './components/Sidebar.vue'
import Topbar from './components/Topbar.vue'
import KpiStrip from './components/KpiStrip.vue'
import Inbox from './components/Inbox.vue'
import Receivables from './sections/Receivables.vue'
import Payables from './sections/Payables.vue'
import Expenses from './sections/Expenses.vue'
import PartnerCommission from './sections/PartnerCommission.vue'
import Banking from './sections/Banking.vue'
import Reports from './sections/Reports.vue'
import GeneralLedger from './sections/GeneralLedger.vue'
import Liabilities from './sections/Liabilities.vue'
import Assets from './sections/Assets.vue'
import { provideCompanyContext } from './composables/useCompanyContext.js'
import { useSidebar } from './composables/useSidebar.js'
import { useBreakpoint } from './composables/useBreakpoint.js'

// DashboardCharts lazy-loaded so KPI strip renders immediately
const DashboardCharts = defineAsyncComponent(() =>
  import('./components/DashboardCharts.vue')
)

// Provide company context to all child components
const { company } = provideCompanyContext()

const { isOpen: sidebarIsOpen, toggle: sidebarToggle, close: sidebarClose } = useSidebar()
const { isMobile } = useBreakpoint()

// Hash-based routing
const activeSection = ref('dashboard')

function onNavigate(sectionKey) {
  activeSection.value = sectionKey
  window.location.hash = '#/' + sectionKey.replace(/_/g, '-')
}

onMounted(() => {
  const hash = window.location.hash
  if (hash && hash.startsWith('#/')) {
    const section = hash.slice(2).replace(/-/g, '_')
    activeSection.value = section
  }
})

const userRoles = computed(() => {
  try {
    return window.frappe?.boot?.user?.roles || []
  } catch {
    return []
  }
})

const isFinanceManager = computed(() =>
  userRoles.value.includes('Finance Manager') ||
  userRoles.value.includes('System Manager') ||
  window.frappe?.session?.user === 'Administrator'
)

// Period state: driven by KpiStrip's update:period event so DashboardCharts stays in sync
const kpiPeriod = ref(localStorage.getItem('fc_period') || 'month')

// Inbox badge count for sidebar
const inboxRef = ref(null)
const inboxBadgeCount = computed(() => inboxRef.value?.totalCount ?? 0)
</script>
