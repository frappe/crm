import js from '@eslint/js'
import ts from 'typescript-eslint'
import pluginVue from 'eslint-plugin-vue'
import configPrettier from 'eslint-config-prettier'
import vueParser from 'vue-eslint-parser'
import globals from 'globals'
import importX, { createNodeResolver } from 'eslint-plugin-import-x'
import path from 'node:path'

export default [
  {
    ignores: ['**/dist/**', '**/node_modules/**', '**/public/dist/**'],
  },
  js.configs.recommended,
  ...ts.configs.recommended,
  ...pluginVue.configs['flat/recommended'],
  {
    files: ['**/*.vue', '**/*.js', '**/*.ts'],
    languageOptions: {
      parser: vueParser,
      parserOptions: {
        parser: ts.parser,
        sourceType: 'module',
        ecmaVersion: 'latest',
      },
      globals: {
        ...globals.browser,
        ...globals.node,
        frappe: 'readonly',
        __: 'readonly',
      },
    },
  },
  {
    plugins: { 'import-x': importX },
    settings: {
      'import-x/resolver-next': [
        createNodeResolver({
          alias: { '@': [path.resolve(import.meta.dirname, 'src')] },
          extensions: ['.js', '.ts', '.jsx', '.tsx', '.vue', '.json'],
        }),
      ],
    },
    rules: {
      'import-x/no-unresolved': ['error', { ignore: ['^~icons/'] }],
      'vue/multi-word-component-names': 'off',
      'vue/prop-name-casing': 'off',
      'vue/attribute-hyphenation': 'off',
      'vue/v-on-event-hyphenation': 'off',
      '@typescript-eslint/no-explicit-any': 'warn',
      '@typescript-eslint/no-unused-vars': 'warn',
      'no-undef': 'error',
    },
  },
  configPrettier,
]
