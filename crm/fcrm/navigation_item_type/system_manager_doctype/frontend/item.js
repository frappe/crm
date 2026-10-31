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
