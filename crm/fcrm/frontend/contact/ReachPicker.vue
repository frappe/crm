<!-- Contact's email or mobile on `/apps/crm`: picks the primary from the contact's own, or adds one, as CRM v1 does. -->
<template>
	<Combobox
		class="w-full"
		:modelValue="modelValue || null"
		:label="field.label"
		:options="options"
		:placeholder="text.placeholder"
		:emptyText="text.empty"
		:error="error"
		:disabled="busy"
		openOnFocus
		@update:modelValue="choose"
	>
		<template #item-add="{ query }">
			<span class="truncate">{{ __('Add {0}', [query.trim()]) }}</span>
		</template>
	</Combobox>
</template>

<script setup>
import { computed } from 'vue'
import { Combobox } from 'frappe-ui'
import { __ } from 'frappe/i18n'
import { reachEditor } from './contactReach.js'

const props = defineProps({
	page: { type: Object, required: true },
	field: { type: Object, required: true },
	modelValue: { type: String, default: null },
	error: { type: [String, Array], default: null },
})

// A `change` closes the panel's inline editor once the write is done; the pick never reaches the draft.
const emit = defineEmits(['change'])

const STALE = __('This contact changed while you were editing. Reload it to see the change; unsaved edits will be lost.')

const TEXT = {
	email_id: {
		placeholder: __('Add an email…'),
		empty: __('No emails'),
		primary: __('Primary email address updated'),
		added: __('Email address added'),
	},
	mobile_no: {
		placeholder: __('Add a mobile number…'),
		empty: __('No mobile numbers'),
		primary: __('Primary mobile number updated'),
		added: __('Mobile number added'),
	},
}

const text = TEXT[props.field.fieldname]
const editor = reachEditor(props.page, props.field.fieldname, { ...text, stale: STALE })
const busy = editor.busy

const options = computed(() => [
	...editor.values().map((value) => ({ label: value, value })),
	{
		type: 'custom',
		key: 'add',
		label: __('Add'),
		slot: 'add',
		icon: 'lucide-plus',
		condition: ({ query }) => editor.canAdd(query),
		onClick: ({ query }) => settle(editor.add(query)),
	},
])

function choose(value) {
	settle(editor.setPrimary(value))
}

async function settle(write) {
	if (await write) emit('change', props.page.doc[props.field.fieldname])
}
</script>
