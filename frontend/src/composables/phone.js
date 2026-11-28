import { useMediaQuery } from '@vueuse/core'
import { computed, inject, onBeforeUnmount, provide, watch } from 'vue'

/** True below Tailwind's `sm` breakpoint, where CRM draws its phone layout. */
export const isPhone = useMediaQuery('(max-width: 639.98px)')

const phonePickersKey = Symbol('phonePickers')

/** Select and Link controls below this component pick from a bottom sheet on a phone. */
export function providePhonePickers() {
  provide(phonePickersKey, true)
}

export function usePhonePickers() {
  const enabled = inject(phonePickersKey, false)
  return computed(() => enabled && isPhone.value)
}

// Phone Back closes the top layer (a sheet, a settings page) before it leaves the page.
// Opening a layer pushes a history entry on the same URL, with the router's own state kept
// and the open layers' ids added, so Back pops that entry and closes the layer. Entries
// whose layers have closed any other way are popped back off, unless a navigation has
// put another entry on top of them since.
const layers = []
// ids stay unique across reloads, since history keeps entries from earlier loads
const loadId = Date.now().toString(36)
let nextLayerId = 0
let ownBacks = 0
let unwindScheduled = false

const openIds = () => history.state?.backClose || []
const isLive = (id) => layers.some((layer) => layer.id === id)

window.addEventListener('popstate', () => {
  if (ownBacks) return void ownBacks--
  const stillOpen = openIds()
  const closing = layers.filter((layer) => !stillOpen.includes(layer.id))
  closing.reverse().forEach((layer) => layer.close())
  setTimeout(() => {
    // a layer that asked first (Discard changes?) keeps its entry
    closing.filter((layer) => isLive(layer.id)).forEach(restoreEntry)
    scheduleUnwind()
  }, 0)
})

/**
 * Ties a layer to a history entry while `isOpen()` is true.
 * `close` should make `isOpen()` false; a layer that stays open keeps its entry.
 */
export function useBackClose(isOpen, close) {
  const layer = {
    id: `${loadId}-${++nextLayerId}`,
    closedByBack: false,
    close: () => {
      layer.closedByBack = true
      close()
    },
  }

  watch(
    isOpen,
    (open, wasOpen) => {
      if (open) return pushLayer()
      if (!wasOpen) return
      dropLayer()
      if (layer.closedByBack) return void (layer.closedByBack = false)
      scheduleUnwind()
    },
    { immediate: true },
  )

  onBeforeUnmount(() => dropLayer() && scheduleUnwind())

  // A layer that opens as another closes (a menu item that opens a dialog)
  // takes over the closed layer's entry instead of stacking on top of it.
  function pushLayer() {
    const ids = openIds()
    const top = ids[ids.length - 1]
    if (top && !isLive(top)) {
      history.replaceState(
        { ...history.state, backClose: [...ids.slice(0, -1), layer.id] },
        '',
      )
    } else {
      history.pushState({ ...history.state, backClose: [...ids, layer.id] }, '')
    }
    layers.push(layer)
  }

  function dropLayer() {
    const index = layers.indexOf(layer)
    if (index >= 0) layers.splice(index, 1)
    return index >= 0
  }
}

function restoreEntry(layer) {
  layer.closedByBack = false
  history.pushState(
    { ...history.state, backClose: [...openIds(), layer.id] },
    '',
  )
}

// Runs after the click that closed the layers, so a navigation it started stays on top.
function scheduleUnwind() {
  if (unwindScheduled) return
  unwindScheduled = true
  setTimeout(unwind, 0)
}

function unwind() {
  unwindScheduled = false
  const ids = openIds()
  let count = 0
  while (count < ids.length && !isLive(ids[ids.length - 1 - count])) count++
  if (!count) return
  ownBacks++
  history.go(-count)
}
