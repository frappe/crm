<!-- CRM Organization's Contacts tab: the contacts whose company it is. -->
<template>
	<LinkedList
		:page="page"
		doctype="Contact"
		field="company_name"
		:fields="CONTACT_FIELDS"
		:columns="columns"
		:empty="__('No contacts')"
	>
		<template #default="{ row }">
			<ListCell class="gap-2">
				<Avatar :label="row.full_name || row.name" :image="row.image" size="sm" />
				<span class="truncate text-base font-medium text-ink-gray-8">{{ row.full_name || row.name }}</span>
			</ListCell>
			<ListCell><span class="truncate text-base text-ink-gray-7">{{ row.email_id }}</span></ListCell>
			<ListCell><span class="truncate text-base text-ink-gray-7">{{ row.mobile_no }}</span></ListCell>
			<ListCell><TimeAgo :timestamp="row.modified" class="truncate text-base text-ink-gray-5" /></ListCell>
		</template>
	</LinkedList>
</template>

<script setup>
import { Avatar } from 'frappe-ui'
import { ListCell } from 'frappe-ui/list'
import { TimeAgo } from '@framework/ui/ActivityTimeline'
import { __ } from 'frappe/i18n'
import LinkedList from './LinkedList.vue'
import { CONTACT_FIELDS } from './organizationTabs.js'

defineProps({
	page: { type: Object, required: true },
})

const columns = [
	{ label: __('Name'), width: 'minmax(10rem, 1fr)' },
	{ label: __('Email'), width: 'minmax(10rem, 1fr)' },
	{ label: __('Mobile No'), width: '10rem' },
	{ label: __('Last Modified'), width: '8rem' },
]
</script>
