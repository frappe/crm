<!-- A field on the canvas, as a visitor sees it. A click selects it (its settings open in the panel), a drag moves it. -->
<template>
	<div
		data-editor-select
		:data-fieldname="field.fieldname"
		class="editor-field group/field relative -m-2 cursor-grab rounded-6 p-2 transition-shadow active:cursor-grabbing"
		:class="selected ? 'ring-1 ring-outline-gray-4' : 'hover:ring-1 hover:ring-outline-gray-2'"
	>
		<div
			v-if="field.fieldtype !== 'Check'"
			class="mb-1.5 flex items-center gap-1 text-sm text-ink-gray-6"
		>
			<span class="truncate">{{ field.label || field.fieldname }}</span>
			<span v-if="required" class="-ml-0.5 text-ink-red-4">*</span>
			<Tooltip
				v-if="guestSelectMissing"
				:text="__('Guests can\'t see {0} records.', [field.options])"
			>
				<span class="lucide-triangle-alert size-3.5 shrink-0 text-ink-gray-5" aria-hidden="true" />
			</Tooltip>
			<span
				class="lucide-grip-vertical -my-1 ml-auto size-4 shrink-0 text-ink-gray-4 opacity-0 transition-opacity group-hover/field:opacity-100"
				:class="{ '!opacity-100': selected }"
				aria-hidden="true"
			/>
		</div>
		<div class="pointer-events-none" tabindex="-1" inert>
			<div v-if="field.fieldtype === 'Check'" class="flex h-7 items-center gap-2">
				<FormControl type="checkbox" :model-value="false" />
				<span class="text-sm text-ink-gray-6">
					{{ field.label }}<span v-if="required" class="text-ink-red-4">*</span>
				</span>
			</div>
			<FormControl
				v-else-if="isTextarea"
				type="textarea"
				size="md"
				:rows="3"
				:model-value="''"
				:placeholder="field.placeholder"
			/>
			<FormControl
				v-else-if="field.fieldtype === 'Select' || field.fieldtype === 'Link'"
				type="select"
				size="md"
				:model-value="''"
				:options="[{ label: field.placeholder || __('Select an option'), value: '' }]"
			/>
			<FormControl
				v-else
				type="text"
				size="md"
				:model-value="''"
				:placeholder="field.placeholder"
			/>
		</div>
		<p v-if="field.field_description" class="mt-1.5 text-p-sm text-ink-gray-5">
			{{ field.field_description }}
		</p>
	</div>
</template>

<script setup>
import { computed } from "vue";
import { FormControl, Tooltip } from "frappe-ui";
import { __ } from "frappe/i18n";
import { TEXTAREA_TYPES } from "./formModel";

const props = defineProps({
	field: { type: Object, required: true },
	selected: { type: Boolean, default: false },
	locked: { type: Boolean, default: false },
	guestSelectMissing: { type: Boolean, default: false },
});

const isTextarea = computed(() => TEXTAREA_TYPES.includes(props.field.fieldtype));
const required = computed(() => props.locked || props.field.reqd);
</script>
