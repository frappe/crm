// What desk v2 does after the settings dialog saves FCRM Settings.
import { askReload, registerAfterSave } from '@shell'

// Both write Property Setters (and forecasting the deal layouts), which open pages read only on load.
const RELOAD_FIELDS = ['enable_forecasting', 'currency']

registerAfterSave('FCRM Settings', (saved) => askReload(saved, RELOAD_FIELDS))
