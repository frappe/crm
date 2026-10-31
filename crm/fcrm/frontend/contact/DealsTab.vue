<!-- Contact's Deals tab: the deals that list the contact, each row opening its deal. -->
<template>
	<div class="flex flex-col gap-3 px-6 pb-8 pt-4">
		<List v-if="deals?.length" :columns="columns.map((column) => column.width)" class="list-row-px-3">
			<ListHeader>
				<ListHeaderCell
					v-for="column in columns"
					:key="column.label"
					:class="{ 'justify-end': column.align === 'right' }"
				>
					{{ column.label }}
				</ListHeaderCell>
			</ListHeader>
			<ListRow v-for="row in deals" :key="row.name" :route="routeFor('CRM Deal', row.name)">
				<ListCell class="gap-2">
					<Avatar
						:label="row.organization || row.name"
						:image="row.organization_logo"
						shape="square"
						size="sm"
					/>
					<span class="truncate text-base font-medium text-ink-gray-8">
						{{ row.organization || row.name }}
					</span>
				</ListCell>
				<ListCell class="gap-1.5">
					<span class="flex size-4 shrink-0 items-center justify-center" :class="ink(row.status)">
						<span class="size-2 rounded-full bg-current" />
					</span>
					<span class="truncate text-base text-ink-gray-8">{{ __(row.status) }}</span>
				</ListCell>
				<ListCell class="justify-end">
					<span class="truncate text-base text-ink-gray-8">{{ amount(row) }}</span>
				</ListCell>
				<ListCell><span class="truncate text-base text-ink-gray-7">{{ row.email }}</span></ListCell>
				<ListCell><span class="truncate text-base text-ink-gray-7">{{ row.mobile_no }}</span></ListCell>
				<ListCell>
					<span class="truncate text-base text-ink-gray-7">{{ row.deal_owner_name || row.deal_owner }}</span>
				</ListCell>
				<ListCell><TimeAgo :timestamp="row.modified" class="truncate text-base text-ink-gray-5" /></ListCell>
			</ListRow>
		</List>
		<div v-else-if="deals === undefined" class="flex flex-col gap-3 py-2">
			<Skeleton v-for="index in 3" :key="index" class="h-4 w-full rounded-2" />
		</div>
		<p v-else-if="deals === null" class="py-10 text-center text-base text-ink-gray-5">
			{{ __('Could not load the deals.') }}
		</p>
		<p v-else class="py-10 text-center text-base text-ink-gray-5">{{ __('No deals') }}</p>
	</div>
</template>

<script setup>
import { Avatar, Skeleton } from 'frappe-ui'
import { List, ListCell, ListHeader, ListHeaderCell, ListRow } from 'frappe-ui/list'
import { TimeAgo } from '@framework/ui/ActivityTimeline'
import { formatCurrency, getFormatDefaults } from '@framework/ui/FormLayout'
import { routeFor } from '@shell'
import { __ } from 'frappe/i18n'
import { findStatus, statusInk } from '../status/statusChange.js'

const props = defineProps({
	page: { type: Object, required: true },
	deals: { type: Array, default: undefined },
	statuses: { type: Array, default: undefined },
})

const columns = [
	{ label: __('Organization'), width: 'minmax(9rem, 1fr)' },
	{ label: __('Status'), width: '8rem' },
	{ label: __('Amount'), width: '7rem', align: 'right' },
	{ label: __('Email'), width: 'minmax(8rem, 1fr)' },
	{ label: __('Mobile No'), width: '8rem' },
	{ label: __('Deal Owner'), width: '8rem' },
	{ label: __('Last Modified'), width: '6.5rem' },
]

function ink(status) {
	return statusInk(findStatus(props.statuses, status)?.color)
}

function amount(row) {
	const defaults = getFormatDefaults()
	return formatCurrency(row.deal_value || 0, {
		numberFormat: defaults.number_format,
		currency: row.currency || defaults.currency,
	})
}
</script>
