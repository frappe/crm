<!-- CRM Deal's contacts section: a row per contact that opens to its email and mobile, as v1 draws it. -->
<template>
	<div v-if="contacts.length" class="flex flex-col divide-y divide-outline-gray-1">
		<div v-for="row in contacts" :key="row.contact" class="py-2.5 first:pt-0 last:pb-0">
			<div class="flex h-7 min-w-0 items-center gap-2">
				<button
					type="button"
					class="flex min-w-0 flex-1 items-center gap-2 text-base text-ink-gray-7"
					:aria-expanded="isOpen(row)"
					@click="toggle(row)"
				>
					<Avatar :label="row.full_name || row.contact" size="md" />
					<span class="truncate">{{ row.full_name || row.contact }}</span>
					<Badge
						v-if="row.is_primary"
						class="ml-1 shrink-0"
						:label="__('Primary')"
						theme="green"
						variant="outline"
					/>
				</button>
				<div class="flex shrink-0 items-center">
					<Dropdown v-if="editor.editable" :options="options(row)" align="end">
						<Button
							variant="ghost"
							icon="lucide-more-horizontal"
							:label="__('Contact actions')"
							:disabled="editor.busy.value"
						/>
					</Dropdown>
					<Button
						variant="ghost"
						icon="lucide-arrow-up-right"
						:label="__('Open contact')"
						:tooltip="__('Open contact')"
						:route="routeFor('Contact', row.contact)"
					/>
					<Button
						variant="ghost"
						icon="lucide-chevron-right"
						class="transition-transform"
						:class="{ 'rotate-90': isOpen(row) }"
						:label="isOpen(row) ? __('Collapse') : __('Expand')"
						:aria-expanded="isOpen(row)"
						@click="toggle(row)"
					/>
				</div>
			</div>
			<div v-if="isOpen(row)" class="flex flex-col gap-1.5 pt-2 text-base text-ink-gray-8">
				<DealContactLine
					v-if="row.email"
					icon="lucide-mail"
					:value="row.email"
					:tooltip="__('Send email to {0}', [row.email])"
					:action="canEmail(page) ? () => emailContact(page, row.email) : null"
				/>
				<DealContactLine
					v-if="row.mobile_no"
					icon="lucide-phone"
					:value="row.mobile_no"
					:tooltip="__('Call {0}', [row.mobile_no])"
					:action="canCall() ? () => callContact(page, row.mobile_no) : null"
				/>
				<span v-if="!row.email && !row.mobile_no" class="py-3 text-center text-sm text-ink-gray-4">
					{{ __('No details added') }}
				</span>
			</div>
		</div>
	</div>
	<span v-else class="flex h-20 items-center justify-center text-base text-ink-gray-5">
		{{ __('No contacts added') }}
	</span>
</template>

<script setup>
import { computed, reactive } from 'vue'
import { Avatar, Badge, Button, Dropdown } from 'frappe-ui'
import { routeFor } from '@shell'
import { __ } from 'frappe/i18n'
import DealContactLine from './DealContactLine.vue'
import { callContact, canCall, canEmail, dealContacts, emailContact } from './dealContacts.js'

const props = defineProps({
	page: { type: Object, required: true },
	editor: { type: Object, required: true },
})

const contacts = computed(() => dealContacts(props.page.doc))

// By contact, not row: a save hands back new row objects.
const opened = reactive(new Set())

function isOpen(row) {
	return opened.has(row.contact)
}

function toggle(row) {
	if (!opened.delete(row.contact)) opened.add(row.contact)
}

function options(row) {
	return [
		{
			label: __('Set as primary'),
			icon: 'lucide-star',
			condition: () => !row.is_primary,
			onClick: () => props.editor.setPrimary(row.contact),
		},
		{
			label: __('Remove'),
			icon: 'lucide-trash-2',
			theme: 'red',
			onClick: () => props.editor.remove(row.contact),
		},
	]
}
</script>
