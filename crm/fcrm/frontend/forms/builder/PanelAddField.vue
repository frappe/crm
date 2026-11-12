<!-- Nothing selected: search and an alphabetical list of the doctype's fields, to click or drag onto the form. -->
<template>
	<div class="flex min-h-[42px] items-center px-4 py-2">
		<p class="text-p-sm text-ink-gray-5">
			{{ __("Select a field or a section heading to edit it here.") }}
		</p>
	</div>
	<PanelSection :label="__('Add a field')">
		<TextInput v-model="query" :placeholder="__('Search {0} fields', [doctypeLabel])">
			<template #prefix>
				<span class="lucide-search size-4 text-ink-gray-5" aria-hidden="true" />
			</template>
		</TextInput>
		<Draggable
			:list="rows"
			:group="{ name: 'wf-fields', pull: 'clone', put: false }"
			:sort="false"
			:clone="cloneField"
			item-key="value"
			class="flex flex-col"
			:force-fallback="true"
			:fallback-on-body="false"
			fallback-class="wf-drag-fallback"
			ghost-class="editor-drop-line"
			@start="$emit('drag-start')"
			@end="$emit('drag-end')"
		>
			<template #item="{ element: o }">
				<ItemListRow
					as="button"
					type="button"
					class="!min-h-8 cursor-grab text-left hover:bg-surface-gray-2 active:cursor-grabbing"
					data-editor-palette-row
					:title="__('Click to add, or drag onto the form')"
					@click="$emit('add', o)"
				>
					<template #prefix>
						<span class="size-4 text-ink-gray-5" :class="fieldTypeIcon(o.af)" aria-hidden="true" />
					</template>
					<span class="block truncate text-ink-gray-8">{{ o.label }}</span>
				</ItemListRow>
			</template>
		</Draggable>
		<p v-if="!rows.length" class="text-p-sm text-ink-gray-5">
			{{ query ? __("No field matches.") : __("Every field is on the form.") }}
		</p>
	</PanelSection>
</template>

<script setup>
import { computed, ref } from "vue";
import { ItemListRow, TextInput } from "frappe-ui";
import { __ } from "frappe/i18n";
import Draggable from "vuedraggable";
import { fieldTypeIcon } from "../fieldTypeIcon";
import { newFieldFromCatalog } from "./formModel";
import PanelSection from "./PanelSection.vue";

const props = defineProps({
	options: { type: Array, default: () => [] }, // { label, value, af } of fields not on the form
	doctypeLabel: { type: String, default: "" },
});
defineEmits(["add", "drag-start", "drag-end"]);

const query = ref("");
const rows = computed(() => {
	const q = query.value.trim().toLowerCase();
	const list = q ? props.options.filter((o) => o.label.toLowerCase().includes(q)) : props.options;
	return [...list].sort((a, b) => a.label.localeCompare(b.label));
});

// a drop onto the form receives a new field object, never the palette row
const cloneField = (o) => newFieldFromCatalog(o.af);
</script>
