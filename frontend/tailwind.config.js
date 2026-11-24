import frappeUIPreset, { content as frappeUIContent } from 'frappe-ui/tailwind'

export default {
  presets: [frappeUIPreset],
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}',
    ...frappeUIContent,
    // @whatsapp/ui source, beside CRM or the pinned release whatsapp-ui.js clones — its icons
    // are `lucide-*` utility classes, and unscanned source fails silently as blank icons
    '../../whatsapp/ui/src/**/*.{vue,js,ts,jsx,tsx}',
    './.cache/whatsapp/*/ui/src/**/*.{vue,js,ts,jsx,tsx}',
    // linked @framework/ui source, for the Grid and Link the account form uses
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
