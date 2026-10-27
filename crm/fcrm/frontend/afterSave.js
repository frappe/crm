// What desk v2 does after the settings dialog saves FCRM Settings.
import { toast } from 'frappe-ui'
import { __ } from 'frappe/i18n'
import { registerAfterSave } from '@shell'

// Both write Property Setters and layouts, so open pages keep the old meta until a reload.
const RELOAD_FIELDS = ['enable_forecasting', 'currency']

registerAfterSave('FCRM Settings', (saved) => {
	if (!saved.changed.some((field) => RELOAD_FIELDS.includes(field))) return
	// Desk's own reload toast has this id, so one toast shows however many saves ask.
	toast(__('Reload to apply'), {
		id: 'settings-reload',
		duration: Infinity,
		action: { label: __('Reload'), onClick: () => window.location.reload() },
	})
})
