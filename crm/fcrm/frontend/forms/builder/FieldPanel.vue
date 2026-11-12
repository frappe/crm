<!-- The editor's right panel: 380px, always present. Field settings, section settings, or "Add a field". -->
<template>
	<aside
		class="flex h-full w-[380px] shrink-0 flex-col overflow-y-auto border-l border-outline-gray-1"
		data-editor-panel
	>
		<PanelFieldSettings
			v-if="selection.field"
			:field="selection.field"
			:locked="draft.isMandatory(selection.field.fieldname)"
			:guest-select-missing="guestMissing(selection.field)"
			:granting="!!draft.linkMeta.grantingSelect[selection.field.options]"
			:grant-refused="!!draft.linkMeta.grantRefused[selection.field.options]"
			:doctype-label="draft.doctypeLabel"
			@update="(patch) => draft.updateField(selection.field, patch)"
			@remove="selection.removeSelected()"
			@close="selection.clear()"
			@grant-guest="draft.linkMeta.grantGuestSelect(selection.field.options)"
		/>
		<PanelSectionSettings
			v-else-if="selection.section"
			:section="selection.section"
			:field-count="selection.sectionFieldCount"
			@heading="(v) => ((selection.section.secField.label = v), draft.markDirty())"
			@columns="(n) => draft.setColumns(selection.section, n)"
			@remove="selection.removeSelectedSection()"
			@close="selection.clear()"
		/>
		<PanelAddField
			v-else
			:options="draft.availableFieldOptions"
			:doctype-label="draft.doctypeLabel"
			@add="(o) => $emit('add', o)"
			@drag-start="(evt) => $emit('drag-start', evt)"
			@drag-end="$emit('drag-end')"
		/>
	</aside>
</template>

<script setup>
import PanelAddField from "./PanelAddField.vue";
import PanelFieldSettings from "./PanelFieldSettings.vue";
import PanelSectionSettings from "./PanelSectionSettings.vue";

const props = defineProps({
	draft: { type: Object, required: true },
	selection: { type: Object, required: true },
});
defineEmits(["add", "drag-start", "drag-end"]);

const guestMissing = (f) =>
	f.fieldtype === "Link" && props.draft.linkMeta.guestSelect[f.options] === false;
</script>
