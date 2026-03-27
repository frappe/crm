import { onUnmounted } from 'vue'

const bus = {
  send(event, payload) {
    window.dispatchEvent(new CustomEvent(event, { detail: payload }))
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
  }

  onUnmounted(() => {
    listeners.forEach(({ event, handler }) => bus.off(event, handler))
  })

  return { on, send: bus.send }
}
