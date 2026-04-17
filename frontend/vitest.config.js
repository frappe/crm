import { defineConfig } from 'vitest/config'
import path from 'path'

export default defineConfig({
  test: {
    globals: true,
    environment: 'happy-dom',
    root: __dirname,
    setupFiles: ['./tests/setup.js'],
    include: ['tests/**/*.test.js', 'src/**/*.test.js'],
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
})
