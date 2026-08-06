import { ref } from 'vue'

// Module-level singleton so index.vue and Sidebar.vue share the same state
const isOpen = ref(false)

export function useSidebar() {
  function toggle() { isOpen.value = !isOpen.value }
  function close() { isOpen.value = false }
  return { isOpen, toggle, close }
}
