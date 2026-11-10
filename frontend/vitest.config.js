import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  test: {
    globals: true,
    environment: 'happy-dom',
    root: import.meta.dirname,
    setupFiles: ['./tests/setup.js'],
    include: ['tests/**/*.test.{js,ts}', 'src/**/*.test.{js,ts}'],
    server: {
      deps: {
        inline: ['frappe-ui'],
      },
    },
    coverage: {
      provider: 'v8',
      reporter: ['text', 'lcov', 'json-summary'],
      reportsDirectory: './coverage',
      include: [
        'src/utils/fieldTransforms.js',
        'src/utils/scriptHelpers.js',
        'src/utils/expressions.js',
        'src/utils/renderFieldLayoutDialog.js',
      ],
    },
  },
  resolve: {
    alias: [
      { find: '@', replacement: path.resolve(import.meta.dirname, 'src') },
      // The desk resolves these for `crm/fcrm/frontend/`, which sits outside this package.
      {
        find: /^frappe-ui$/,
        replacement: path.resolve(
          import.meta.dirname,
          'node_modules/frappe-ui/src/index.ts',
        ),
      },
      {
        find: '@framework/ui/api',
        replacement: path.resolve(
          import.meta.dirname,
          'tests/fixtures/frameworkApi.js',
        ),
      },
      // The desk resolves it from the framework's node_modules, where `crm/desk.package.json` declares it.
      {
        find: '@twilio/voice-sdk',
        replacement: path.resolve(
          import.meta.dirname,
          'node_modules/@twilio/voice-sdk',
        ),
      },
      {
        find: '@shell',
        replacement: path.resolve(
          import.meta.dirname,
          'tests/fixtures/shell.js',
        ),
      },
      {
        find: 'frappe/i18n',
        replacement: path.resolve(
          import.meta.dirname,
          'tests/fixtures/frappeI18n.js',
        ),
      },
      {
        find: /^~icons\/.*/,
        replacement: path.resolve(import.meta.dirname, 'tests/stubs/icon.js'),
      },
      {
        find: /^@framework\/ui\/(.*)$/,
        replacement: path.resolve(
          import.meta.dirname,
          'tests/stubs/framework/$1',
        ),
      },
    ],
  },
})
