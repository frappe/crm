import { computed, ref, watch } from 'vue'

export const mobileSidebarOpened = ref(false)

let afterMobileSidebarClosed = null

// A callback whose close never finished (drawer unmounted mid-transition)
// must not fire on a later, unrelated close.
watch(mobileSidebarOpened, (opened) => {
  if (opened) afterMobileSidebarClosed = null
})

// The drawer traps focus until its leave transition ends, so anything that
// needs focus (like a dialog) must wait for it to be gone.
export function closeMobileSidebar(then) {
  if (!mobileSidebarOpened.value) return then?.()
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

// a record to open on the Settings page, such as the automation the assistant just added
export const settingsRecord = ref('')

// true while a Settings editor has unsaved edits, so the assistant doesn't open another page over them
export const unsavedSettings = ref(false)

// bumped when a link opens Settings, so the page reloads what something else just changed
export const settingsOpenCount = ref(0)
