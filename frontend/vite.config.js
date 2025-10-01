import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueJsx from '@vitejs/plugin-vue-jsx'
import path from 'path'
import { VitePWA } from 'vite-plugin-pwa'

// https://vitejs.dev/config/
export default defineConfig(async ({ mode }) => {
  const isDev = mode === 'development'
  const frappeui = await importFrappeUIPlugin(isDev)

  const config = {
    plugins: [
      frappeui({
        frappeProxy: true,
        lucideIcons: true,
        jinjaBootData: true,
        buildConfig: {
          indexHtmlPath: '../crm/www/crm.html',
          emptyOutDir: true,
          sourcemap: true,
        },
      }),
      vue(),
      vueJsx(),
      VitePWA({
        registerType: 'autoUpdate',
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
        '@': path.resolve(__dirname, 'src'),
      },
    },
    optimizeDeps: {
      include: [
        'feather-icons',
        'showdown',
        'tailwind.config.js',
        'prosemirror-state',
        'prosemirror-view',
        'lowlight',
        'interactjs',
      ],
    },
  }

  // Add local frappe-ui alias only in development if the local frappe-ui exists
  if (isDev) {
    try {
      // Check if the local frappe-ui directory exists
      const fs = await import('node:fs')
      const localFrappeUIPath = path.resolve(__dirname, '../frappe-ui')
      const vitePluginPath = path.resolve(localFrappeUIPath, 'vite.js')
      
      if (fs.existsSync(localFrappeUIPath) && fs.existsSync(vitePluginPath)) {
        config.resolve.alias['frappe-ui'] = localFrappeUIPath
      } else {
        console.warn('Local frappe-ui directory not found or incomplete, using npm package')
      }
    } catch (error) {
      console.warn(
        'Error checking for local frappe-ui, using npm package:',
        error.message,
      )
    }
  }

  return config
})

async function importFrappeUIPlugin(isDev) {
  if (isDev) {
    try {
      // Check if local frappe-ui has the vite plugin file
      const fs = await import('node:fs')
      const localVitePluginPath = path.resolve(__dirname, '../frappe-ui/vite.js')
      
      if (fs.existsSync(localVitePluginPath)) {
        const module = await import('../frappe-ui/vite')
        return module.default
      } else {
        console.warn('Local frappe-ui vite plugin not found, using npm package')
      }
    } catch (error) {
      console.warn(
        'Local frappe-ui not found, falling back to npm package:',
        error.message,
      )
    }
  }
  // Fall back to npm package if local import fails
  const module = await import('frappe-ui/vite')
  return module.default
}
