// The `System Manager DocType` kind: a doctype's list, offered only to a System Manager.
import { routeFor } from '@shell'

export default {
	icon: 'list',

	render(item) {
		return { to: routeFor(item.link_to) }
	},

	label(item) {
		return item.link_to
	},
}
