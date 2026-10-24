import { computed, ref } from 'vue'

export const mobileSidebarOpened = ref(false)

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
