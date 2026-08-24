import frappeUIPreset from 'frappe-ui/tailwind'

export default {
  presets: [frappeUIPreset],
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}',
    './node_modules/frappe-ui/src/**/*.{vue,js,ts,jsx,tsx}',
    '../node_modules/frappe-ui/src/**/*.{vue,js,ts,jsx,tsx}',
    './node_modules/frappe-ui/frappe/**/*.{vue,js,ts,jsx,tsx}',
    '../node_modules/frappe-ui/frappe/**/*.{vue,js,ts,jsx,tsx}',
    // linked @framework/ui source (apps/frappe/ui/src) — scan so its utility and
    // arbitrary-variant classes (e.g. Notifications TabButtons overrides) are generated
    '../../frappe/ui/src/**/*.{vue,js,ts,jsx,tsx}',
  ],
  safelist: [
    '!text-gray-700',
    '!text-blue-600',
    '!text-green-700',
    '!text-red-600',
    '!text-pink-600',
    '!text-orange-600',
    '!text-amber-600',
    '!text-yellow-600',
    '!text-cyan-600',
    '!text-teal-600',
    '!text-violet-600',
    '!text-purple-600',
    '!text-ink-gray-9',
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
