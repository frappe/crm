// Published as `crm/lib` through the import_map hook; a stored Client Script imports it by name.
import { h } from 'vue'

/** One line for a deal: its name and its raw status. The desk publishes no translation function yet. */
export function formatDeal(doc) {
	return `${doc.name} · ${doc.status}`
}

/** A grey chip that prefixes `label` with `crm/lib:`; takes one prop, `label`. */
export const DealBadge = {
	props: { label: { type: String, required: true } },
	setup(props) {
		return () =>
			h('div', { class: 'rounded-1 bg-surface-gray-2 px-2 py-1 text-base text-ink-gray-8', 'data-crm-lib': '' }, [
				h('span', { class: 'font-medium' }, 'crm/lib: '),
				props.label,
			])
	},
}
