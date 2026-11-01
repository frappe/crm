// CRM v1's standard form script rows: a port runs only while its row is enabled, as `/crm` runs only enabled rows.
import { getDocumentFields } from '@framework/ui/api'

/** Whether the standard row `name` is enabled; a missing row reads as disabled. */
export function standardScriptEnabled(name) {
	return getDocumentFields('CRM Form Script', name, ['enabled']).then((reply) => Boolean(reply.data?.enabled))
}
