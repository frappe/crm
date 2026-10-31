<!-- CRM Deal's contacts section: the deal's contacts, each opening its record, and a picker that adds one. -->
<template>
	<div class="flex flex-col gap-2.5">
		<div v-for="row in contacts" :key="row.contact" class="flex min-w-0 items-center gap-2">
			<Avatar :label="row.full_name || row.contact" size="lg" />
			<div class="flex min-w-0 flex-1 flex-col gap-0.5">
				<div class="flex min-w-0 items-center gap-1.5">
					<RecordAnchor
						:href="href(row.contact)"
						class="truncate text-base font-medium text-ink-gray-8 hover:underline"
						@open="open(row.contact)"
					>
						{{ row.full_name || row.contact }}
					</RecordAnchor>
					<Badge v-if="row.is_primary" :label="__('Primary')" theme="gray" variant="subtle" />
				</div>
				<span v-if="reach(row)" class="truncate text-sm text-ink-gray-5">{{ reach(row) }}</span>
			</div>
			<div v-if="editor.editable" class="flex w-7 shrink-0 justify-end">
				<Dropdown :options="options(row)" align="end">
					<Button
						variant="ghost"
						icon="lucide-more-horizontal"
						:label="__('Contact actions')"
						:disabled="busy"
					/>
				</Dropdown>
			</div>
		</div>
		<span v-if="!contacts.length" class="text-base text-ink-gray-5">{{ __('No contacts added') }}</span>
		<Link
			v-if="editor.editable"
			:modelValue="null"
			doctype="Contact"
			creatable
			:disabled="busy"
			:placeholder="__('Add a contact…')"
			@update:modelValue="add"
			@create="create"
		/>
	</div>
</template>

<script setup>
import { computed } from 'vue'
import { Avatar, Badge, Button, Dropdown } from 'frappe-ui'
import { Link, RecordAnchor } from '@framework/ui'
import { routeFor } from '@shell'
import { __ } from 'frappe/i18n'
import { ContactsEditor, dealContacts } from './dealContacts.js'

const props = defineProps({
	page: { type: Object, required: true },
})

const editor = new ContactsEditor(props.page, {
	duplicate: __('Contact already added'),
	added: __('Contact added'),
	removed: __('Contact removed'),
	primary: __('Primary contact set'),
	stale: __('Contacts changed while you were editing. Reload the deal to see them; unsaved edits will be lost.'),
})

const busy = editor.busy

const contacts = computed(() => dealContacts(props.page.doc))

function options(row) {
	return [
		{
			label: __('Set as primary'),
			icon: 'lucide-star',
			condition: () => !row.is_primary,
			onClick: () => editor.setPrimary(row.contact),
		},
		{
			label: __('Remove'),
			icon: 'lucide-trash-2',
			theme: 'red',
			onClick: () => editor.remove(row.contact),
		},
	]
}

function add(contact) {
	if (contact) editor.add(contact)
}

function create(query) {
	editor.create({ first_name: query, company_name: props.page.doc.organization })
}

function reach(row) {
	return [row.email, row.mobile_no].filter(Boolean).join(' · ')
}

function href(contact) {
	return props.page.router.resolve(routeFor('Contact', contact)).href
}

function open(contact) {
	props.page.router.push(routeFor('Contact', contact))
}
</script>
