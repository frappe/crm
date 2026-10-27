import { computed, ref } from 'vue'

export const mobileSidebarOpened = ref(false)

let afterMobileSidebarClosed = null

// The drawer traps focus until its leave transition ends, so anything that
// needs focus (like a dialog) must wait for it to be gone.
export function closeMobileSidebar(then) {
  afterMobileSidebarClosed = then
  mobileSidebarOpened.value = false
}

export function onMobileSidebarClosed() {
  afterMobileSidebarClosed?.()
  afterMobileSidebarClosed = null
}

export const isMobileView = computed(() => window.innerWidth < 768)

export const showSettings = ref(false)

export const disableSettingModalOutsideClick = ref(false)

export const activeSettingsPage = ref('')
