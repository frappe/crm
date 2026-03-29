import { onMounted, onUnmounted } from 'vue'

const STORAGE_KEY = 'app_broadcasts'
const bus = {
  send(event, payload) {
    window.dispatchEvent(new CustomEvent(event, { detail: payload }))

    const broadcasts = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]')
    broadcasts.push({ event, payload, timestamp: Date.now() })
    localStorage.setItem(STORAGE_KEY, JSON.stringify(broadcasts))
  },
  on(event, handler) {
    window.addEventListener(event, (e) => handler(e.detail))
  },
  off(event, handler) {
    window.removeEventListener(event, handler)
  },
}

export function useBroadcast() {
  const listeners = []

  function on(event, handler) {
    bus.on(event, handler)
    listeners.push({ event, handler })

    // check localStorage for missed broadcasts on init
    onMounted(() => {
      const broadcasts = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]')
      const missed = broadcasts.filter((b) => b.event === event)
      if (missed.length) {
        missed.forEach((b) => handler(b.payload))
        // clear handled broadcasts
        const remaining = broadcasts.filter((b) => b.event !== event)
        localStorage.setItem(STORAGE_KEY, JSON.stringify(remaining))
      }
    })
  }

  onUnmounted(() => {
    listeners.forEach(({ event, handler }) => bus.off(event, handler))
  })

  return { on, send: bus.send }
}
