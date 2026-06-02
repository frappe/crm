import { onMounted, onUnmounted } from 'vue'

const STORAGE_KEY = 'app_broadcasts'

const activeListeners = new Map()

function hasActiveListener(event) {
  const set = activeListeners.get(event)
  return Boolean(set && set.size)
}

function trackListener(event, wrapped) {
  if (!activeListeners.has(event)) activeListeners.set(event, new Set())
  activeListeners.get(event).add(wrapped)
}

function untrackListener(event, wrapped) {
  const set = activeListeners.get(event)
  if (!set) return
  set.delete(wrapped)
  if (!set.size) activeListeners.delete(event)
}

function drainStoredBroadcasts(event, handler) {
  const broadcasts = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]')
  const missed = broadcasts.filter((b) => b.event === event)
  if (!missed.length) return
  missed.forEach((b) => handler(b.payload))
  const remaining = broadcasts.filter((b) => b.event !== event)
  localStorage.setItem(STORAGE_KEY, JSON.stringify(remaining))
}

const bus = {
  send(event, payload) {
    window.dispatchEvent(new CustomEvent(event, { detail: payload }))

    // Only persist for replay if no listener consumed it live in this tab.
    // Otherwise the entry would be stranded in localStorage and replayed on
    // every future mount of a listener for this event.
    if (hasActiveListener(event)) return

    const broadcasts = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]')
    broadcasts.push({ event, payload, timestamp: Date.now() })
    localStorage.setItem(STORAGE_KEY, JSON.stringify(broadcasts))
  },
  on(event, wrapped) {
    window.addEventListener(event, wrapped)
    trackListener(event, wrapped)
  },
  off(event, wrapped) {
    window.removeEventListener(event, wrapped)
    untrackListener(event, wrapped)
  },
}

export function useBroadcast() {
  const listeners = []

  function on(event, handler) {
    const wrapped = (e) => handler(e.detail)
    bus.on(event, wrapped)
    listeners.push({ event, wrapped })

    // Drain any missed broadcasts persisted before this listener existed.
    onMounted(() => drainStoredBroadcasts(event, handler))
  }

  onUnmounted(() => {
    listeners.forEach(({ event, wrapped }) => bus.off(event, wrapped))
  })

  return { on, send: bus.send }
}
