<!-- Settings of the selected section heading: its heading text and column count. -->
<template>
	<PanelHeader
		icon="lucide-rows-3"
		:title="section.secField.label || __('Untitled section')"
		:subtitle="__('Section · {0} fields', [fieldCount])"
		:remove-label="__('Remove section, keep its fields')"
		@remove="$emit('remove')"
		@close="$emit('close')"
	/>
	<PanelSection :label="__('Section')">
		<PanelRow :label="__('Heading')">
			<TextInput
				variant="ghost"
				:model-value="section.secField.label"
				:placeholder="__('Add heading…')"
				@update:model-value="(v) => $emit('heading', v)"
			/>
		</PanelRow>
		<PanelRow :label="__('Columns')" :box="false">
			<TabButtons
				:options="COLUMN_OPTIONS"
				:model-value="section.columns.length"
				@update:model-value="(n) => $emit('columns', n)"
			/>
		</PanelRow>
	</PanelSection>
</template>

<script setup>
import { TabButtons, TextInput } from "frappe-ui";
import { __ } from "frappe/i18n";
import PanelHeader from "./PanelHeader.vue";
import PanelRow from "./PanelRow.vue";
import PanelSection from "./PanelSection.vue";

defineProps({
	section: { type: Object, required: true },
	fieldCount: { type: Number, default: 0 },
});
defineEmits(["heading", "columns", "remove", "close"]);

const COLUMN_OPTIONS = [1, 2, 3].map((n) => ({ label: String(n), value: n }));
</script>
