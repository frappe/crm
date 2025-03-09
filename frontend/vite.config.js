import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueJsx from '@vitejs/plugin-vue-jsx'
import path from 'path'
import frappeui from 'frappe-ui/vite'
import { VitePWA } from 'vite-plugin-pwa'

// https://vitejs.dev/config/

export default defineConfig(({  mode }) => {
  const env = loadEnv(mode,process.cwd())
  let proxyConfig = {}
  
  if (env.VITE_SITE_NAME && env.VITE_SITE_PORT) {
    proxyConfig = {
      '^/(app|api|assets|files|private)': {
        target: `http://${env.VITE_SITE_NAME}:${env.VITE_SITE_PORT}`,
        ws: true,
        changeOrigin: true,
        secure: false,
      },
    }
  }
  return {
    server: {
      port: 8080,
      proxy: proxyConfig,
    },
    plugins: [
      frappeui(),
      vue({
        script: {
          propsDestructure: true,
        },
      }),
      vueJsx(),
      VitePWA({
        registerType: 'autoUpdate',
        devOptions: {
          enabled: true,
        },
        manifest: {
          display: 'standalone',
          name: 'Next CRM',
          short_name: 'Next CRM',
          start_url: '/next-crm',
          description: 'Modern & 100% Open-source CRM tool to supercharge your sales operations',
          icons: [
            {
              src: '/assets/next_crm/manifest/manifest-icon-192.maskable.png',
              sizes: '192x192',
              type: 'image/png',
              purpose: 'any',
            },
            {
              src: '/assets/next_crm/manifest/manifest-icon-192.maskable.png',
              sizes: '192x192',
              type: 'image/png',
              purpose: 'maskable',
            },
            {
              src: '/assets/next_crm/manifest/manifest-icon-512.maskable.png',
              sizes: '512x512',
              type: 'image/png',
              purpose: 'any',
            },
            {
              src: '/assets/next_crm/manifest/manifest-icon-512.maskable.png',
              sizes: '512x512',
              type: 'image/png',
              purpose: 'maskable',
            },
          ],
        },
      }),
      {
        name: 'transform-index.html',
        transformIndexHtml(html, context) {
          if (!context.server) {
            return html.replace(
              /<\/body>/,
              `
                  <script>
                      {% for key in boot %}
                      window["{{ key }}"] = {{ boot[key] | tojson }};
                      {% endfor %}
                  </script>
                  </body>
                  `,
            )
          }
          return html
        },
      },
    ],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, 'src'),
      },
    },
    build: {
      outDir: '../next_crm/public/frontend',
      emptyOutDir: true,
      commonjsOptions: {
        include: [/tailwind.config.js/, /node_modules/],
      },
      sourcemap: true,
    },
    optimizeDeps: {
      include: ['feather-icons', 'showdown', 'tailwind.config.js', 'engine.io-client', 'prosemirror-state'],
    },
  }
})
