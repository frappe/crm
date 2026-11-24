import { defineAsyncComponent, shallowRef } from 'vue'

const loaders = {
  desktop: () => import('./DesktopLayout.vue'),
  mobile: () => import('./MobileLayout.vue'),
}
const lazy = {
  desktop: defineAsyncComponent(loaders.desktop),
  mobile: defineAsyncComponent(loaders.mobile),
}
const loaded = shallowRef({})

/** The app shell for this screen. A shell loaded ahead with `preloadLayout` draws at once. */
export function layoutFor(width) {
  const kind = width < 640 ? 'mobile' : 'desktop'
  return loaded.value[kind] ?? lazy[kind]
}

/** Loads the shell before the first page that needs it, such as the one setup hands over to. */
export async function preloadLayout(width) {
  const kind = width < 640 ? 'mobile' : 'desktop'
  const { default: layout } = await loaders[kind]()
  loaded.value = { ...loaded.value, [kind]: layout }
}
