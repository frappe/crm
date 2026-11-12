<!-- Fields the form does not ask for. Every new record gets their values; a row drags up onto the
     form, a field drags down into here. A record-required field with no value shows as a missing row. -->
<template>
	<div class="mt-10 border-t border-outline-gray-1 pt-10" data-editor-hidden>
		<h3 class="text-lg font-semibold text-ink-gray-6">{{ __("Hidden fields") }}</h3>
		<p class="mt-1.5 text-p-base text-ink-gray-5">
			{{
				__(
					"Not shown to visitors. Every new {0} gets these values — or drag a field onto the form to ask for it.",
					[draft.doctypeLabel]
				)
			}}
		</p>
		<Draggable
			:model-value="draft.hiddenRows"
			:group="{ name: 'wf-fields', pull: 'clone', put: true }"
			:clone="draft.cloneHidden"
			:sort="false"
			:move="canLeaveHidden"
			item-key="fieldname"
			filter="input, select, textarea, button"
			:prevent-on-filter="false"
			class="mt-5 flex min-h-8 flex-col gap-3"
			ghost-class="editor-drop-line"
			:force-fallback="true"
			:fallback-on-body="false"
			fallback-class="wf-drag-fallback"
			data-editor-hidden-list
			@start="drag.startHidden"
			@end="$emit('clone-end')"
			@change="draft.onHiddenChange"
		>
			<template #item="{ element: h }">
				<div
					class="group/hidden flex min-h-8 cursor-grab select-none items-center gap-3 active:cursor-grabbing"
					:data-hidden-fieldname="h.fieldname"
				>
					<span class="w-36 shrink-0 truncate text-sm text-ink-gray-6">
						{{ h.label || h.fieldname
						}}<span v-if="draft.isMandatory(h.fieldname)" class="text-ink-red-4"> *</span>
					</span>
					<div v-if="draft.isMissingRow(h)" class="flex min-w-0 flex-1 items-center gap-3">
						<span class="flex min-w-0 flex-1 items-center gap-1.5 text-sm text-ink-red-5">
							<span class="lucide-circle-alert size-4 shrink-0" aria-hidden="true" />
							<span class="truncate">{{ __("Every {0} needs this", [draft.doctypeLabel]) }}</span>
						</span>
						<Button
							variant="subtle"
							size="sm"
							:label="__('Set a value')"
							@click.stop="draft.setHiddenValue(h)"
						/>
					</div>
					<div
						v-else-if="valueControl(h.fieldtype) === 'checkbox'"
						class="flex h-7 min-w-0 flex-1 items-center"
					>
						<FormControl
							type="checkbox"
							size="sm"
							:model-value="isChecked(h.default)"
							:data-hidden-value="h.fieldname"
							@update:model-value="(v) => draft.setHiddenDefault(h, v)"
						/>
					</div>
					<FormControl
						v-else
						class="min-w-0 flex-1"
						:type="valueControl(h.fieldtype)"
						size="sm"
						:model-value="h.default"
						:options="valueControl(h.fieldtype) === 'select' ? selectOptions(h) : undefined"
						:placeholder="placeholder(h)"
						:data-hidden-value="h.fieldname"
						@update:model-value="(v) => draft.setHiddenDefault(h, v)"
					/>
					<Button
						v-if="draft.canAddToForm(h)"
						variant="subtle"
						size="sm"
						:label="__('Add to form')"
						@click.stop="addToForm(h)"
					/>
					<span
						class="lucide-grip-vertical size-4 shrink-0 text-ink-gray-4 group-hover/hidden:text-ink-gray-6"
						:title="__('Drag onto the form')"
						aria-hidden="true"
					/>
				</div>
			</template>
		</Draggable>
		<Combobox
			:options="draft.hiddenPickerOptions"
			:model-value="null"
			:placeholder="__('Search fields…')"
			@update:selected-option="draft.addHiddenField"
		>
			<template #trigger="{ open, setOpen }">
				<div class="mt-4 flex w-fit" data-editor-add-hidden>
					<Button
						variant="subtle"
						size="sm"
						icon-left="lucide-plus"
						:class="{ '!bg-surface-gray-3': open }"
						:label="__('Add hidden field')"
						@click.stop="setOpen(!open)"
					/>
				</div>
			</template>
		</Combobox>
	</div>
</template>

<script setup>
import { Button, Combobox, FormControl } from "frappe-ui";
import { __ } from "frappe/i18n";
import Draggable from "vuedraggable";
import { optionList } from "./formModel";
import { isChecked, valueControl } from "./hiddenValue";

const props = defineProps({
	draft: { type: Object, required: true },
	selection: { type: Object, required: true },
	drag: { type: Object, required: true },
});
defineEmits(["clone-end"]);

// Sortable asks the list a drag started in, so this list guards drops onto the form
const canLeaveHidden = (evt) =>
	evt.to === evt.from || props.draft.canAddToForm(evt.draggedContext.element);

const PLACEHOLDERS = {
	select: () => __("Select a value"),
	date: () => __("Select a date"),
	datetime: () => __("Select a date and time"),
	time: () => __("Select a time"),
};
const placeholder = (h) => PLACEHOLDERS[valueControl(h.fieldtype)]?.() || __("Add a value");

function selectOptions(h) {
	const options =
		h.fieldtype === "Select"
			? optionList(h.options)
			: (props.draft.linkMeta.linkOptions[h.options] || []).slice();
	if (h.default && !options.includes(h.default)) options.unshift(h.default);
	return options.map((o) => ({ label: o, value: o }));
}

function addToForm(h) {
	const f = props.draft.addHiddenToForm(h);
	if (!f) return;
	props.selection.selectField(f);
	requestAnimationFrame(() =>
		document
			.querySelector(`[data-editor-canvas] [data-fieldname="${f.fieldname}"]`)
			?.scrollIntoView({ block: "center", behavior: "smooth" })
	);
}
</script>
