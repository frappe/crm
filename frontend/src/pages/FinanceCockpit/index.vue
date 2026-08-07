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
      :badge-count="0"
      :user-roles="userRoles"
      @navigate="onNavigate"
    />
    <!-- Main content -->
    <div class="flex flex-col flex-1 min-w-0 overflow-hidden">
      <Topbar @toggle-sidebar="sidebarToggle" />
      <main class="flex-1 overflow-y-auto p-4">
        <template v-if="activeSection === 'dashboard'">
          <KpiStrip :user-roles="userRoles" @navigate="onNavigate" />
        </template>
        <template v-else>
          <p class="font-medium text-gray-700 dark:text-gray-300 capitalize">
            {{ activeSection.replace(/_/g, ' ') }}
          </p>
          <p class="text-xs mt-1 text-gray-400">Section content coming in sprint 2.</p>
        </template>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import Sidebar from './components/Sidebar.vue'
import Topbar from './components/Topbar.vue'
import KpiStrip from './components/KpiStrip.vue'
import { provideCompanyContext } from './composables/useCompanyContext.js'
import { useSidebar } from './composables/useSidebar.js'
import { useBreakpoint } from './composables/useBreakpoint.js'

// Provide company context to all child components
provideCompanyContext()

const { isOpen: sidebarIsOpen, toggle: sidebarToggle, close: sidebarClose } = useSidebar()
const { isMobile } = useBreakpoint()

// Hash-based routing
const activeSection = ref('dashboard')

function onNavigate(sectionKey) {
  activeSection.value = sectionKey
  window.location.hash = '#/' + sectionKey.replace(/_/g, '-')
}

onMounted(() => {
  // Read section from hash on load
  const hash = window.location.hash
  if (hash && hash.startsWith('#/')) {
    const section = hash.slice(2).replace(/-/g, '_')
    activeSection.value = section
  }
})

// Read user roles from frappe.boot
const userRoles = computed(() => {
  try {
    return window.frappe?.boot?.user?.roles || []
  } catch {
    return []
  }
})
</script>
