// CRM's global acts on desk v2's shell surface, run from the palette as `shell.crm.<name>`.
import { routeFor } from '@shell'
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
	{
		name: 'form_scripts_to_rewrite',
		get label() {
			return __('Form Scripts to rewrite')
		},
		icon: 'lucide-file-code',
		// Only a System Manager writes Client Scripts, so only they are offered the report.
		right: { doctype: 'Client Script', ptype: 'create' },
		run: (shell) => shell.router.push(routeFor('CRM Form Script')),
	},
]
