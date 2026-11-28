import { inject, onBeforeUnmount, onMounted, provide, shallowRef } from 'vue'

// What a settings page tells the phone shell: a view inside it (an account, a
// template) that takes the header's title and Back, and its unsaved edits for
// the Discard / Save bar. On a computer nothing provides this, and both calls
// do nothing: the page keeps its own header and Save button.
const settingsPhoneKey = Symbol('settingsPhone')

export function provideSettingsPhone() {
  const state = { subpage: shallowRef(null), saveBar: shallowRef(null) }
  provide(settingsPhoneKey, state)
  return state
}

/**
 * A view inside a settings page, shown full screen on a phone.
 * `title` is a getter; `back` returns to the page.
 */
export function useSettingsSubpage({ title, back }) {
  useShellSlot('subpage', { title, back })
}

/**
 * The page's unsaved edits, for the phone's Discard / Save bar.
 * `isDirty`, `saving` and `count` are getters.
 */
export function useSettingsSaveBar({ isDirty, saving, count, save, discard }) {
  useShellSlot('saveBar', { isDirty, saving, count, save, discard })
}

function useShellSlot(name, entry) {
  const shell = inject(settingsPhoneKey, null)
  if (!shell) return
  // a view inside a page hands the slot back to the page when it closes
  let previous = null
  onMounted(() => {
    previous = shell[name].value
    shell[name].value = entry
  })
  onBeforeUnmount(() => {
    entry.unmounted = true
    if (shell[name].value !== entry) return
    shell[name].value = previous?.unmounted ? null : previous
  })
}
