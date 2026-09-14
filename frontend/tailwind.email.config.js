import frappeUIPreset from 'frappe-ui/tailwind'

export default {
  presets: [frappeUIPreset],
  content: [{ raw: '<div class="prose-f"></div>', extension: 'html' }],
  theme: {
    extend: {},
  },
  plugins: [],
}
