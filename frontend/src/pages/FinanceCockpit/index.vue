<template>
  <FrappeUIProvider>
    <div class="flex h-screen w-full">

      <!-- Sidebar — mirrors CRM AppSidebar structure.
           bg-surface-gray-1 is required: Sidebar's own bg-surface-sidebar is
           transparent in dark mode, so without this the column falls through
           to the white page canvas (same fix as CRM AppSidebar). -->
      <div class="relative flex h-full bg-surface-gray-1 fc-sidebar-wrap">
        <Sidebar
          v-model:collapsed="sidebarCollapsed"
          width="15rem"
          class="border-r border-outline-gray-1"
        >
          <div class="flex h-full flex-col p-2">

            <!-- Brand / config dropdown — mirrors CRM UserDropdown.
                 Holds context switch (company), Preferences, Logout. -->
            <Dropdown :options="brandDropdownOptions">
              <template #default="{ open }">
                <button
                  class="flex h-12 items-center rounded-md py-2 duration-300 ease-in-out"
                  :class="
                    sidebarCollapsed
                      ? 'w-auto px-0'
                      : open
                        ? 'w-full px-2 bg-surface-elevation-3 shadow-sm'
                        : 'w-full px-2 hover:bg-surface-gray-2'
                  "
                >
                  <div class="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-blue-600 text-white text-sm font-bold select-none">
                    FC
                  </div>
                  <div
                    class="flex flex-1 flex-col text-left duration-300 ease-in-out truncate"
                    :class="sidebarCollapsed ? 'ml-0 w-0 overflow-hidden opacity-0' : 'ml-2 w-auto opacity-100'"
                  >
                    <div class="text-base-medium leading-none text-ink-gray-9 truncate">Finance</div>
                    <div class="mt-1 text-sm leading-none text-ink-gray-7 truncate">{{ company || 'Select company' }}</div>
                  </div>
                  <div
                    class="duration-300 ease-in-out"
                    :class="sidebarCollapsed ? 'ml-0 w-0 overflow-hidden opacity-0' : 'ml-2 w-auto opacity-100'"
                  >
                    <span class="lucide-chevron-down size-4 text-ink-gray-5" aria-hidden="true" />
                  </div>
                </button>
              </template>
            </Dropdown>

            <!-- Nav items -->
            <div class="-mx-2 mt-2 flex flex-1 flex-col gap-1 overflow-y-auto px-2">
              <SidebarItem
                v-for="section in SIDEBAR_SECTIONS"
                :key="section.key"
                :label="section.label"
                :active="activeSection === section.key"
                @click="onNavigate(section.key)"
              >
                <template #prefix>
                  <span :class="[section.iconClass, 'size-4 text-ink-gray-7']" aria-hidden="true" />
                </template>
                <Tooltip
                  :text="section.label"
                  placement="right"
                  :hover-delay="1.5"
                  :disabled="!sidebarCollapsed"
                >
                  <span class="truncate text-sm">{{ section.label }}</span>
                </Tooltip>
              </SidebarItem>
            </div>

            <!-- Footer — collapse toggle (mirrors CRM) -->
            <div class="mt-auto flex flex-col gap-1 pt-2">
              <SidebarItem
                :label="sidebarCollapsed ? 'Expand' : 'Collapse'"
                @click="sidebarCollapsed = !sidebarCollapsed"
              >
                <template #prefix>
                  <span
                    class="lucide-panel-left-close size-4 text-ink-gray-7 duration-300 ease-in-out"
                    :class="{ '[transform:rotateY(180deg)]': sidebarCollapsed }"
                    aria-hidden="true"
                  />
                </template>
              </SidebarItem>
            </div>

          </div>
        </Sidebar>
      </div>

      <!-- Content column — mirrors CRM crm-content-col -->
      <div class="fc-content-col flex-1 flex flex-col h-full overflow-auto bg-surface-base">

        <!-- Sticky glass header — mirrors CRM AppHeader (breadcrumb strip) -->
        <div class="fc-app-header flex items-center px-5">
          <Breadcrumbs :items="breadcrumbs" />
        </div>

        <!-- Page body -->
        <div class="flex-1 overflow-auto">
          <div class="mx-auto w-full max-w-screen-2xl px-6 py-5">
            <template v-if="activeSection === 'dashboard'"><CrmDashboard @navigate="onNavigate" /></template>
            <template v-else-if="activeSection === 'quotes'"><Quotes /></template>
            <template v-else-if="activeSection === 'orders'"><Orders /></template>
            <template v-else-if="activeSection === 'invoices'"><Invoices /></template>
            <template v-else-if="activeSection === 'payments'"><Payments /></template>
            <template v-else-if="activeSection === 'partner_commission'"><PartnerCommission /></template>
            <template v-else-if="activeSection === 'reports'"><CrmReports /></template>

            <!-- Preferences — full-page view (no modal), hosts the ported CRM ThemeSwitcher -->
            <template v-else-if="activeSection === 'settings'">
              <div class="max-w-2xl space-y-8">
                <div>
                  <h2 class="text-lg font-semibold text-ink-gray-9">Preferences</h2>
                  <p class="mt-0.5 text-sm text-ink-gray-5">Manage how the Finance Cockpit looks and behaves.</p>
                </div>
                <div class="space-y-3">
                  <div>
                    <h3 class="text-sm font-medium text-ink-gray-8">Theme</h3>
                    <p class="text-xs text-ink-gray-5">Choose a light, dark, or system-matched appearance.</p>
                  </div>
                  <ThemeSwitcher :logo="fcLogo" name="Finance" />
                </div>
              </div>
            </template>
          </div>
        </div>

      </div>
    </div>

    <FinanceCommandPalette
      v-model:show="searchOpen"
      :user-roles="userRoles"
      @navigate="onNavigate"
    />
  </FrappeUIProvider>
</template>

<script setup>
import { ref, computed, h, markRaw, onMounted } from 'vue'
import {
  FrappeUIProvider,
  Sidebar,
  SidebarItem,
  Dropdown,
  Breadcrumbs,
  Tooltip,
  createResource,
  useTheme,
} from 'frappe-ui'
import { useStorage } from '@vueuse/core'
import ThemeSwitcher from '@/components/Settings/ThemeSwitcher.vue'
import FinanceCommandPalette from './components/FinanceCommandPalette.vue'
import CrmDashboard from './sections/CrmDashboard.vue'
import Quotes from './sections/Quotes.vue'
import Orders from './sections/Orders.vue'
import Invoices from './sections/Invoices.vue'
import Payments from './sections/Payments.vue'
import PartnerCommission from './sections/PartnerCommission.vue'
import CrmReports from './sections/CrmReports.vue'
import { SIDEBAR_SECTIONS } from './constants/sidebarConfig.js'
import { provideCompanyContext } from './composables/useCompanyContext.js'
import { useBoot } from './composables/useBoot.js'

const { company, setCompany, companiesResource } = provideCompanyContext()
const { getRoles } = useBoot()

// Restore the persisted theme on boot. useTheme()'s lazy initializer only runs
// on its first call; ThemeSwitcher (the only other consumer) mounts solely on
// the Preferences page, so without this call a reload onto any other section
// never re-applies the stored data-theme and the app reverts to light.
useTheme()

const sidebarCollapsed = useStorage('fc_sidebar_collapsed', false)

// Ported CRM logo slot for ThemeSwitcher preview cards (component branch,
// avoids the broken-<img> path when logo is an empty string).
const fcLogo = markRaw({
  render: () =>
    h(
      'div',
      { class: 'flex h-5 w-5 items-center justify-center rounded bg-blue-600 text-white text-[8px] font-bold' },
      'FC',
    ),
})

const activeSection = ref('dashboard')
const ALL_SECTION_KEYS = [...SIDEBAR_SECTIONS.map((s) => s.key), 'settings']

function onNavigate(key) {
  activeSection.value = key
  window.location.hash = '#/' + key.replace(/_/g, '-')
}
onMounted(() => {
  const hash = window.location.hash
  if (hash?.startsWith('#/')) {
    const key = hash.slice(2).replace(/-/g, '_')
    if (ALL_SECTION_KEYS.includes(key)) activeSection.value = key
  }
})

const userRoles = computed(() => getRoles())

const headerTitle = computed(() => {
  if (activeSection.value === 'settings') return 'Preferences'
  return SIDEBAR_SECTIONS.find((s) => s.key === activeSection.value)?.label ?? 'Finance'
})
const breadcrumbs = computed(() => [
  { label: 'Finance', onClick: () => onNavigate('dashboard') },
  { label: headerTitle.value },
])

// Logout — POST-only in Frappe; frappe-ui call() issues POST with CSRF.
const logoutResource = createResource({
  url: 'logout',
  onSuccess: () => (window.location.href = '/login'),
})

// Brand dropdown — context switch (company) + Preferences + Logout,
// grouped like CRM UserDropdown.
const brandDropdownOptions = computed(() => {
  const companies = companiesResource?.data || []
  const groups = []
  if (companies.length) {
    groups.push({
      group: 'Company',
      items: companies.map((c) => ({
        label: c.name,
        icon: c.name === company.value ? 'check' : '',
        onClick: () => setCompany(c.name),
      })),
    })
  }
  groups.push({
    group: '',
    hideLabel: true,
    items: [
      { label: 'Preferences', icon: 'settings', onClick: () => onNavigate('settings') },
      { label: 'Logout', icon: 'log-out', onClick: () => logoutResource.submit() },
    ],
  })
  return groups
})

const searchOpen = ref(false)
</script>

<style scoped>
.fc-sidebar-wrap {
  isolation: isolate;
}
.fc-sidebar-wrap::before {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  background: radial-gradient(70% 28% at 50% 0%, var(--brand-tint-07) 0%, transparent 55%);
}
.fc-sidebar-wrap > * { position: relative; z-index: 1; }

.fc-content-col {
  position: relative;
  isolation: isolate;
}
.fc-content-col::before {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  background: radial-gradient(55% 40% at 15% 0%, var(--brand-tint-07) 0%, transparent 60%);
}
.fc-content-col > * { position: relative; z-index: 1; }

/* Identical to CRM AppHeader */
.fc-app-header {
  position: sticky;
  top: 0;
  z-index: 10;
  height: 3rem;
  background: var(--glass-bg);
  -webkit-backdrop-filter: blur(12px) saturate(140%);
  backdrop-filter: blur(12px) saturate(140%);
  border-bottom: 1px solid var(--glass-border-color);
}
@supports not ((backdrop-filter: blur(1px)) or (-webkit-backdrop-filter: blur(1px))) {
  .fc-app-header { background: var(--surface-gray-1); }
}
</style>
