<!-- CRM Organization's Deals tab: the deals whose organization it is. -->
<template>
	<LinkedList
		:page="page"
		:source="DEALS"
		:columns="columns"
		:empty="__('No deals')"
	>
		<template #default="{ row }">
			<ListCell><span class="truncate text-base font-medium text-ink-gray-8">{{ row.name }}</span></ListCell>
			<ListCell class="gap-1.5">
				<span class="flex size-4 shrink-0 items-center justify-center" :class="ink(row.status)">
					<span class="size-2 rounded-full bg-current" />
				</span>
				<span class="truncate text-base text-ink-gray-8">{{ __(row.status) }}</span>
			</ListCell>
			<ListCell class="justify-end"><span class="truncate text-base text-ink-gray-8">{{ amount(row) }}</span></ListCell>
			<ListCell><span class="truncate text-base text-ink-gray-7">{{ row.deal_owner_name }}</span></ListCell>
			<ListCell><TimeAgo :timestamp="row.modified" class="truncate text-base text-ink-gray-5" /></ListCell>
		</template>
	</LinkedList>
</template>

<script setup>
import { ListCell } from 'frappe-ui/list'
import { TimeAgo } from '@framework/ui/ActivityTimeline'
import { useFieldDisplay } from '@framework/ui/FormLayout'
import { __ } from 'frappe/i18n'
import { findStatus, statusInk } from '../status/statusChange.js'
import LinkedList from './LinkedList.vue'
import { DEALS } from './organizationTabs.js'

const props = defineProps({
	page: { type: Object, required: true },
	statuses: { type: Array, default: undefined },
})

const columns = [
	{ label: __('Deal'), width: 'minmax(0, 1.4fr)' },
	{ label: __('Status'), width: 'minmax(0, 1.4fr)' },
	{ label: __('Amount'), width: 'minmax(0, 1.1fr)', align: 'right' },
	{ label: __('Deal Owner'), width: 'minmax(0, 1.2fr)' },
	{ label: __('Last Modified'), width: 'minmax(0, 1fr)' },
]

const DEAL_VALUE = { fieldname: 'deal_value', fieldtype: 'Currency', options: 'currency' }
const display = useFieldDisplay()

function ink(status) {
	return statusInk(findStatus(props.statuses, status)?.color)
}

function amount(row) {
	return display(DEAL_VALUE, row.deal_value, { doc: row })
}
</script>
