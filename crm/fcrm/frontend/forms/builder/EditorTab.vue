<!-- The Editor tab: the form canvas (scrolls) and the 380px panel side by side, under the tab strip. -->
<template>
	<div class="flex min-h-0 flex-1">
		<div
			class="relative min-w-0 flex-1 overflow-y-auto"
			:class="{ 'select-none': drag.dragging }"
			data-editor-canvas
			@click="selection.onCanvasClick"
		>
			<div class="mx-auto w-full max-w-[640px] px-10 pb-[40vh] pt-10">
				<EditorMasthead :draft="draft" />
				<EditorCanvas :draft="draft" :selection="selection" :drag="drag" />
				<HiddenFieldsBlock
					:draft="draft"
					:selection="selection"
					:drag="drag"
					@clone-end="onCloneEnd"
				/>
			</div>
			<DragLayer ref="layer" />
		</div>
		<FieldPanel
			:draft="draft"
			:selection="selection"
			@add="addFromPanel"
			@drag-start="drag.startPalette"
			@drag-end="onCloneEnd"
		/>
	</div>
</template>

<script setup>
import { reactive, useTemplateRef } from "vue";
import DragLayer from "./DragLayer.vue";
import EditorCanvas from "./EditorCanvas.vue";
import EditorMasthead from "./EditorMasthead.vue";
import FieldPanel from "./FieldPanel.vue";
import HiddenFieldsBlock from "./HiddenFieldsBlock.vue";
import { useEditorDrag } from "./useEditorDrag";
import { useEditorSelection } from "./useEditorSelection";

const props = defineProps({ draft: { type: Object, required: true } });

const layer = useTemplateRef("layer");
const drag = reactive(useEditorDrag({ draft: props.draft, layer }));
const selection = reactive(useEditorSelection({ draft: props.draft, drag }));

// a click on the panel's list adds to the form's last column
function addFromPanel(option) {
	const col = props.draft.sections.at(-1).columns.at(-1);
	const f = props.draft.addFieldToColumn(col, option);
	requestAnimationFrame(() =>
		document
			.querySelector(`[data-editor-canvas] [data-fieldname="${f?.fieldname}"]`)
			?.scrollIntoView({ block: "nearest", behavior: "smooth" })
	);
}

function onCloneEnd() {
	if (!drag.end().cancelled) props.draft.settleCloneDrop();
}
</script>
