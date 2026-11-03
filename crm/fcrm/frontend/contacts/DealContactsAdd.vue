<!-- The "+" on the Contacts header: picks a contact for the deal, or creates one in Quick Entry. -->
<template>
	<Link
		v-if="editor.editable"
		:modelValue="null"
		doctype="Contact"
		creatable
		align="end"
		:disabled="editor.busy.value"
		@update:modelValue="add"
		@create="create"
	>
		<template #trigger>
			<Button
				variant="ghost"
				icon="lucide-plus"
				:label="__('Add contact')"
				:tooltip="__('Add contact')"
				:disabled="editor.busy.value"
			/>
		</template>
	</Link>
</template>

<script setup>
import { Button } from 'frappe-ui'
import { Link } from '@framework/ui'
import { __ } from 'frappe/i18n'

const props = defineProps({
	page: { type: Object, required: true },
	editor: { type: Object, required: true },
})

function add(contact) {
	if (contact) props.editor.add(contact)
}

function create(query) {
	props.editor.create({
		first_name: query,
		company_name: props.page.doc.organization,
	})
}
</script>
