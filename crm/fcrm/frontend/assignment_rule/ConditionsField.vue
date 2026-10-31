<!-- The builder opens in a dialog: a form column is too narrow for its rows. -->
<template>
	<div>
		<InputLabel v-if="field.label" :label="field.label" :required="required" />
		<div class="mt-1 flex flex-col items-start gap-2">
			<code
				v-if="expression"
				class="w-full whitespace-pre-wrap break-words rounded-5 bg-surface-gray-2 px-2 py-1.5 text-p-sm text-ink-gray-8"
			>{{ expression }}</code>
			<span v-else class="text-p-sm text-ink-gray-5">{{ __('No conditions') }}</span>
			<Button
				v-if="!field.readOnly"
				:label="expression ? __('Edit conditions') : __('Add conditions')"
				:disabled="!doctype"
				@click="open = true"
			/>
		</div>
		<InputDescription v-if="field.description && !error" class="mt-1" :description="field.description" />
		<ErrorMessage class="mt-1" :message="error" />
		<Dialog v-model="open" :title="field.label" size="3xl">
			<ConditionBuilder
				:key="doctype"
				:modelValue="tree"
				:doctype="doctype"
				:description="field.description"
				@update:modelValue="edit"
			/>
			<template #actions>
				<div class="flex justify-end">
					<Button variant="solid" :label="__('Done')" @click="open = false" />
				</div>
			</template>
		</Dialog>
	</div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { Button, Dialog, ErrorMessage } from 'frappe-ui'
import { InputDescription, InputLabel } from 'frappe-ui/experimental'
import { __ } from 'frappe/i18n'
import {
	ConditionBuilder,
	fromFrappeConditions,
	toFrappeConditions,
} from '@framework/ui/ConditionBuilder'
import { parseConditions } from './assignmentRule.js'

const props = defineProps({
	page: { type: Object, required: true },
	field: { type: Object, required: true },
	modelValue: { type: String, default: null },
	error: { type: [String, Array], default: null },
	python: { type: String, required: true },
	required: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue', 'change'])

const open = ref(false)
const doctype = computed(() => props.page.doc.document_type || '')
const expression = computed(() => props.page.doc[props.python])

// The tree lives here: the JSON drops a row with no field yet, so reading it back would lose the row.
const tree = ref(read(props.modelValue))
let written = props.modelValue

watch(
	() => props.modelValue,
	(value) => {
		if (value === written) return
		written = value
		tree.value = read(value)
	},
)

function edit(next) {
	tree.value = next
	const json = JSON.stringify(toFrappeConditions(next))
	if (json === written) return
	written = json
	emit('update:modelValue', json)
	emit('change', json)
}

function read(json) {
	return fromFrappeConditions(parseConditions(json))
}
</script>
