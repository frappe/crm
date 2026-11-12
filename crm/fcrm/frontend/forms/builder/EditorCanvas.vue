<template>
	<!-- native-style layout: draggable section boxes → dashed columns → field cards -->
	<div class="flex flex-col gap-3" :class="{ 'select-none': dragging }">
		<Draggable
			:list="sections"
			:item-key="sectionKey"
			handle=".section-handle"
			group="wf-sections"
			class="flex flex-col gap-3"
			ghost-class="opacity-40"
			:force-fallback="true"
			:fallback-on-body="false"
			fallback-class="wf-drag-fallback"
			:animation="120"
			@start="dragging = true"
			@end="onSortEnd"
		>
			<template #item="{ element: sec }">
				<div class="flex flex-col gap-1.5 rounded-4 bg-surface-gray-2 p-2.5">
					<div class="flex h-7 items-center justify-between">
						<div class="flex items-center gap-2 text-base-medium text-ink-gray-9">
							<span
								class="lucide-grip-vertical section-handle h-3.5 shrink-0 cursor-grab text-ink-gray-3"
								aria-hidden="true"
							/>
							<input
								v-if="sec.editingLabel"
								:ref="(el) => el && el.focus()"
								v-model="sec.secField.label"
								:placeholder="__('Section title')"
								class="min-w-0 flex-1 border-0 bg-transparent p-0 text-base-medium text-ink-gray-9 placeholder:font-normal placeholder:italic placeholder:text-ink-gray-4 focus:outline-none focus:ring-0"
								@blur="sec.editingLabel = false"
								@keydown.enter="sec.editingLabel = false"
								@input="markDirty"
							/>
							<span
								v-else
								class="cursor-text truncate"
								:class="{
									'italic text-ink-gray-4': !sec.secField.label,
								}"
								@click="sec.editingLabel = true"
							>
								{{ sec.secField.label || __("Section title") }}
							</span>
						</div>
						<div class="flex items-center gap-1.5">
							<span
								v-if="sectionFieldCount(sec)"
								class="rounded-4 bg-surface-gray-3 px-1.5 py-0.5 text-xs leading-none text-ink-gray-4"
							>
								{{ sectionFieldCount(sec) }}
								{{ sectionFieldCount(sec) === 1 ? __("field") : __("fields") }}
							</span>
							<Dropdown :options="sectionMenu(sec)">
								<template #default>
									<Button variant="ghost">
										<span class="lucide-more-horizontal h-4" aria-hidden="true" />
									</Button>
								</template>
							</Dropdown>
						</div>
					</div>
					<div class="flex gap-2">
						<div
							v-for="col in sec.columns"
							:key="columnKey(col)"
							class="flex min-w-0 flex-1 flex-col gap-1.5 rounded-4 border border-dashed border-outline-gray-2 bg-surface-elevation-2 p-2"
						>
							<Draggable
								:list="col.items"
								group="wf-fields"
								item-key="fieldname"
								handle=".drag-handle"
								class="flex min-h-[34px] min-w-0 flex-1 flex-col gap-1.5"
								ghost-class="opacity-40"
								:force-fallback="true"
								:fallback-on-body="false"
								fallback-class="wf-drag-fallback"
								:animation="120"
								@start="dragging = true"
								@end="onSortEnd"
							>
								<template #item="{ element: f }">
									<FieldCard
										:field="f"
										:expanded="expanded === f.fieldname"
										:locked="isMandatory(f.fieldname)"
										:guest-select-missing="
											f.fieldtype === 'Link' && guestSelect[f.options] === false
										"
										:granting="!!grantingSelect[f.options]"
										:grant-refused="!!grantRefused[f.options]"
										@open="open(f)"
										@toggle="toggle(f)"
										@remove="removeField(f)"
										@update="(patch) => updateField(f, patch)"
										@grant-guest="grantGuestSelect(f.options)"
									/>
								</template>
							</Draggable>
							<Combobox
								:options="availableFieldOptions"
								:model-value="null"
								:placeholder="__('Search fields…')"
								@update:selected-option="(e) => addFieldToColumn(col, e)"
							>
								<template #trigger="{ open, setOpen }">
									<Button
										class="!h-8 w-full !bg-surface-elevation-2"
										variant="outline"
										:label="__('Add Field')"
										icon-left="lucide-plus"
										@click="openFieldPicker(open, setOpen)"
									/>
								</template>
							</Combobox>
						</div>
					</div>
				</div>
			</template>
		</Draggable>

		<Button
			class="!h-8 w-full"
			variant="subtle"
			:label="__('Add Section')"
			icon-left="lucide-plus"
			@click="addBreak('Section Break')"
		/>
	</div>
</template>

<script setup>
import { Button, Combobox, Dropdown } from "frappe-ui";
import { __ } from "frappe/i18n";
import Draggable from "vuedraggable";
import { ref } from "vue";
import FieldCard from "../FieldCard.vue";
import { MAX_COLUMNS } from "./formModel";

const props = defineProps({ draft: { type: Object, required: true } });
const {
	sections,
	expanded,
	hiddenFields,
	availableFieldOptions,
	linkMeta,
	isMandatory,
	markDirty,
	syncFromModel,
	updateField,
	removeField,
	removeBreak,
	addBreak,
	toggle,
	open,
	addFieldToColumn,
	addColumn,
	removeLastColumn,
} = props.draft;
const { guestSelect, grantingSelect, grantRefused, grantGuestSelect } = linkMeta;

const dragging = ref(false);

// vuedraggable item-keys
const sectionKey = (sec) => sec.secField?.fieldname || "sec";
const columnKey = (col) => col.colField?.fieldname || "col0";

function onSortEnd() {
	dragging.value = false;
	syncFromModel();
}

// field counts shown in section headers
function sectionFieldCount(sec) {
	return sec.columns.reduce((n, c) => n + c.items.length, 0);
}

// opening the Add Field picker collapses any open field editor
function openFieldPicker(isOpen, setOpen) {
	if (!isOpen) expanded.value = null;
	setOpen(!isOpen);
}

// ⋯ menu for a section: rename / remove + column ops
function sectionMenu(sec) {
	return [
		{
			group: __("Section"),
			options: [
				{
					label: __("Rename"),
					icon: "lucide-edit",
					onClick: () => (sec.editingLabel = true),
				},
				{
					label: __("Remove Section"),
					icon: "lucide-trash-2",
					onClick: () => removeBreak(sec.secField),
				},
			],
		},
		{ group: __("Column"), options: columnOps(sec.columns) },
	];
}

function columnOps(cols) {
	return [
		{
			label: __("Add Column"),
			icon: "lucide-columns",
			onClick: () => addColumn(cols),
			condition: () => cols.length < MAX_COLUMNS,
		},
		{
			label: __("Remove Last Column"),
			icon: "lucide-trash-2",
			onClick: () => removeLastColumn(cols),
			condition: () => cols.length > 1,
		},
	];
}
</script>

<style>
/* Hide Sortable's floating drag clone so reordering stays contained to the
   fields list — only the in-list placeholder moves, never a copy that can
   drift outside the section/modal. */
.wf-drag-fallback {
	opacity: 0 !important;
}
</style>
