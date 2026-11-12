<!-- The form as a visitor sees it, one size up: sections 40px apart, fields that select and drag. -->
<template>
	<Draggable
		:list="draft.sections"
		:item-key="sectionKey"
		handle=".section-handle"
		group="wf-sections"
		class="flex flex-col gap-10"
		ghost-class="opacity-40"
		:force-fallback="true"
		:fallback-on-body="false"
		fallback-class="wf-drag-fallback"
		:animation="120"
		@end="onSortEnd"
	>
		<template #item="{ element: sec }">
			<div class="section-block relative">
				<div
					class="relative -m-4 rounded-7 p-4"
					:class="{ 'ring-1 ring-outline-gray-4': selection.isSectionSelected(sec) }"
				>
					<div class="group/section relative mb-5 flex h-6 items-center">
						<input
							v-model="sec.secField.label"
							data-editor-select
							:placeholder="__('Untitled section')"
							class="min-w-0 flex-1 border-0 bg-transparent p-0 text-lg font-semibold text-ink-gray-9 placeholder:font-normal placeholder:text-ink-gray-4 focus:outline-none focus:ring-0"
							@focus="selection.selectSection(sec)"
							@click.stop="selection.selectSection(sec)"
							@input="draft.markDirty"
						/>
						<span
							class="section-handle flex size-6 shrink-0 cursor-grab items-center justify-center text-ink-gray-4 opacity-0 transition-opacity hover:text-ink-gray-7 group-hover/section:opacity-100"
							:class="{ '!opacity-100': selection.isSectionSelected(sec) }"
							:title="__('Drag to move the section')"
						>
							<span class="lucide-grip-vertical size-4" aria-hidden="true" />
						</span>
					</div>
					<div
						class="grid gap-x-8"
						:style="{ gridTemplateColumns: `repeat(${sec.columns.length}, minmax(0,1fr))` }"
					>
						<div
							v-for="col in sec.columns"
							:key="columnKey(col)"
							class="relative flex min-w-0 flex-col"
						>
							<Draggable
								:list="col.items"
								group="wf-fields"
								item-key="fieldname"
								handle=".editor-field"
								class="flex min-w-0 flex-1 flex-col gap-6 pb-4"
								:class="{ 'min-h-[60px]': !col.items.length }"
								:data-editor-empty="!col.items.length || null"
								ghost-class="editor-drop-line"
								:force-fallback="true"
								:fallback-on-body="false"
								fallback-class="wf-drag-fallback"
								:animation="120"
								@start="drag.startField"
								@end="onSortEnd"
							>
								<template #item="{ element: f }">
									<EditorField
										:field="f"
										:selected="selection.field === f"
										:locked="draft.isMandatory(f.fieldname)"
										:guest-select-missing="
											f.fieldtype === 'Link' && guestSelect[f.options] === false
										"
										@click.stop="selection.selectField(f)"
									/>
								</template>
							</Draggable>
							<div
								v-if="!col.items.length"
								class="pointer-events-none absolute inset-x-0 top-0 flex h-[60px] items-center justify-center rounded-4 border border-dashed border-outline-gray-2 text-base text-ink-gray-4"
							>
								{{ __("Drop a field here") }}
							</div>
						</div>
					</div>
					<Combobox
						:options="draft.availableFieldOptions"
						:model-value="null"
						:placeholder="__('Search fields…')"
						@update:selected-option="(o) => addToSection(sec, o)"
					>
						<template #trigger="{ open, setOpen }">
							<div class="flex w-fit" data-editor-add-field>
								<Button
									variant="subtle"
									size="sm"
									icon-left="lucide-plus"
									:class="{ '!bg-surface-gray-3': open }"
									:label="__('Add field')"
									@click.stop="setOpen(!open)"
								/>
							</div>
						</template>
					</Combobox>
				</div>
			</div>
		</template>
	</Draggable>

	<div class="mt-10 flex border-t border-outline-gray-1 pt-4" data-editor-add-section>
		<Button
			variant="subtle"
			size="sm"
			icon-left="lucide-plus"
			:label="__('Add section')"
			@click.stop="selection.selectSection(draft.addSection())"
		/>
	</div>
	<div class="mt-8 flex justify-end">
		<Button
			variant="solid"
			size="md"
			class="pointer-events-none"
			tabindex="-1"
			:label="draft.form.submit_button_label || __('Submit')"
		/>
	</div>
</template>

<script setup>
import { Button, Combobox } from "frappe-ui";
import { __ } from "frappe/i18n";
import Draggable from "vuedraggable";
import EditorField from "./EditorField.vue";

const props = defineProps({
	draft: { type: Object, required: true },
	selection: { type: Object, required: true },
	drag: { type: Object, required: true },
});
const guestSelect = props.draft.linkMeta.guestSelect;

const sectionKey = (sec) => sec.secField?.fieldname || "sec";
const columnKey = (col) => col.colField?.fieldname || "col0";

function onSortEnd() {
	const { cancelled, removed } = props.drag.end();
	if (cancelled) return;
	if (removed) {
		props.draft.sections.forEach((sec) =>
			sec.columns.forEach((c) => {
				const i = c.items.indexOf(removed);
				if (i > -1) c.items.splice(i, 1);
			})
		);
	}
	props.draft.syncFromModel();
	if (!props.draft.form.fields.includes(props.selection.field)) props.selection.clear();
}

// a field enters the form after the selected one in that section, else in its shortest column
function addToSection(sec, option) {
	const f = props.draft.addFieldToSection(sec, option, props.selection.field);
	if (f) props.selection.selectField(f);
}
</script>

<style>
/* Sortable's floating clone stays hidden: DragLayer draws the preview card instead. */
.wf-drag-fallback {
	opacity: 0 !important;
}
/* Sortable's ghost is drawn as a 2px line centred in the 24px field gap. */
.editor-drop-line {
	height: 2px !important;
	min-height: 0 !important;
	margin: -13px 0 !important;
	padding: 0 !important;
	border: 0 !important;
	border-radius: 1px;
	overflow: hidden;
	box-shadow: none !important;
	background-color: var(--outline-gray-4) !important;
	opacity: 1 !important;
}
[data-editor-empty] > .editor-drop-line {
	margin: 29px 0 0 !important;
}
[data-editor-hidden-list] > .editor-drop-line {
	margin: -7px 0 !important;
}
.editor-drop-line > * {
	display: none !important;
}
</style>
