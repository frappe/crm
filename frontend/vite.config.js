import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueJsx from '@vitejs/plugin-vue-jsx'
import path from 'path'
import { VitePWA } from 'vite-plugin-pwa'
import frappeui from 'frappe-ui/vite'

// https://vitejs.dev/config/
export default defineConfig(() => {
  const config = {
    plugins: [
      vue(),
      vueJsx(),
      VitePWA({
        registerType: 'autoUpdate',
        workbox: {
          maximumFileSizeToCacheInBytes: 8 * 1024 * 1024,
        },
        devOptions: {
          enabled: true,
        },
        manifest: {
          display: 'standalone',
          name: 'Frappe CRM',
          short_name: 'Frappe CRM',
          start_url: '/crm',
          description:
            'Modern & 100% Open-source CRM tool to supercharge your sales operations',
          icons: [
            {
              src: '/assets/crm/manifest/manifest-icon-192.maskable.png',
              sizes: '192x192',
              type: 'image/png',
              purpose: 'any',
            },
            {
              src: '/assets/crm/manifest/manifest-icon-192.maskable.png',
              sizes: '192x192',
              type: 'image/png',
              purpose: 'maskable',
            },
            {
              src: '/assets/crm/manifest/manifest-icon-512.maskable.png',
              sizes: '512x512',
              type: 'image/png',
              purpose: 'any',
            },
            {
              src: '/assets/crm/manifest/manifest-icon-512.maskable.png',
              sizes: '512x512',
              type: 'image/png',
              purpose: 'maskable',
            },
          ],
        },
      }),
    ],
    resolve: {
      alias: {
        '@': path.resolve(import.meta.dirname, 'src'),
        // point at the package src dir (not index.ts) so subpath imports like
        // `@whatsapp/ui/components/Messages` resolve to a real file
        '@whatsapp/ui': path.resolve(
          import.meta.dirname,
          '../../whatsapp/ui/src',
        ),
        // same shape for @framework/ui: its account form pieces (Grid, Link) are
        // what @whatsapp/ui's AccountForm is built on
        '@framework/ui': path.resolve(
          import.meta.dirname,
          '../../frappe/ui/src',
        ),
      },
      // ensure the linked @whatsapp/ui package reuses the host app's single copy of each peer:
      // the symlinked source has no node_modules of its own, so dedupe resolves its imports
      // (`dompurify`, and the peers below) to the host's copy.
      // `reka-ui` is what frappe-ui builds on and it passes state through provide/inject,
      // so a second copy silently breaks context across a linked package's components.
      // the editor packages must resolve to one copy each: tiptap imports
      // `@tiptap/pm/model` while prosemirror-state/transform/tables import bare
      // `prosemirror-model`, so a nested install of either throws "multiple
      // versions of prosemirror-model were loaded" on mention insert. Unlike
      // optimizeDeps (dev-only) this also applies to the production build.
      // @framework/ui is aliased to frappe's ui/src, so its own direct deps
      // (leaflet, cropperjs, vuedraggable) must also come from here: a bench
      // build never installs apps/frappe/ui/node_modules.
      dedupe: [
        'vue',
        'vue-router',
        'frappe-ui',
        'reka-ui',
        'dompurify',
        'cropperjs',
        'leaflet',
        'leaflet-draw',
        'leaflet.locatecontrol',
        // ConditionBuilder's drag handles; resolved from the host for the same reason
        'vuedraggable',
        '@tiptap/core',
        '@tiptap/pm',
        '@tiptap/vue-3',
        'prosemirror-model',
        'prosemirror-state',
        'prosemirror-view',
        'prosemirror-transform',
      ],
    },
    optimizeDeps: {
      include: [
        'tailwind.config.js',
        'prosemirror-state',
        'prosemirror-view',
        'lowlight',
        'interactjs',
      ],
    },
    server: {
      fs: {
        // allow the bench `apps/` dir so Vite can serve linked local packages
        // (@whatsapp/ui, @framework/ui) that live in sibling app repos
        allow: [path.resolve(import.meta.dirname, '../..')],
      },
    },
  }

  config.plugins.unshift(
    frappeui({
      frappeProxy: true,
      lucideIcons: true,
      jinjaBootData: true,
      // its esbuild helper breaks Vite 8's dependency scan
      codeLanguages: false,
      buildConfig: {
        indexHtmlPath: '../crm/www/crm.html',
        emptyOutDir: true,
        sourcemap: true,
      },
    }),
  )

  return config
})
