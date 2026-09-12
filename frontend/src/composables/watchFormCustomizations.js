import { watch } from 'vue'

export function watchFormCustomizations(document, scripts, callback) {
  const readyDocument = () =>
    document.doc && scripts.data ? document.doc : null

  // Do not consume the one-shot watcher while either resource is still loading.
  return watch(readyDocument, callback, {
    once: true,
    immediate: Boolean(readyDocument()),
  })
}
