// CRM's global acts on desk v2's shell surface, run from the palette as `shell.crm.<name>`.
import { __ } from 'frappe/i18n'

export default [
	{
		name: 'log_a_call',
		get label() {
			return __('Log a call')
		},
		icon: 'lucide-phone',
		right: { doctype: 'CRM Call Log', ptype: 'create' },
		run: (shell) => shell.create('CRM Call Log'),
	},
]
