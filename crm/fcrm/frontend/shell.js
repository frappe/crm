// CRM's shell hook: desk v2 runs `setup` once per tab at idle, for people CRM admits.
import { askReload } from '@shell'

// Both write Property Setters (and forecasting the deal layouts), which open pages read only on load.
const RELOAD_FIELDS = ['enable_forecasting', 'currency']

export function setup(shell) {
	shell.afterSave('FCRM Settings', (saved) => askReload(saved, RELOAD_FIELDS))
}
