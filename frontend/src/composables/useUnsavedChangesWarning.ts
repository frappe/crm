import { onMounted, onUnmounted } from 'vue'

export function useUnsavedChangesWarning(hasUnsavedChanges: () => boolean) {
  function beforeUnloadHandler(event: BeforeUnloadEvent) {
    if (!hasUnsavedChanges()) return
    event.preventDefault()
    event.returnValue = true
  }

  onMounted(() => addEventListener('beforeunload', beforeUnloadHandler))
  onUnmounted(() => removeEventListener('beforeunload', beforeUnloadHandler))
}
