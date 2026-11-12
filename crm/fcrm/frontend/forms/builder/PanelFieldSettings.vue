<!-- Settings of the selected field: label, required, placeholder, help text and its conditions. -->
<template>
	<PanelHeader
		:icon="fieldTypeIcon(field)"
		:title="field.label || field.fieldname"
		:subtitle="`${fieldTypeLabel(field)} · ${field.fieldname}`"
		:remove-label="__('Remove from the form')"
		@remove="$emit('remove')"
		@close="$emit('close')"
	/>
	<div
		v-if="guestSelectMissing"
		class="mx-4 mb-3 flex items-start gap-2 rounded-4 bg-surface-gray-2 p-2.5"
	>
		<span
			class="lucide-triangle-alert mt-0.5 size-3.5 shrink-0 text-ink-gray-6"
			aria-hidden="true"
		/>
		<div class="flex min-w-0 flex-col items-start gap-2">
			<p class="text-p-sm text-ink-gray-7">{{ guestNote }}</p>
			<Button
				v-if="!grantRefused"
				size="sm"
				:loading="granting"
				:label="__('Grant access')"
				@click="$emit('grant-guest')"
			/>
		</div>
	</div>
	<PanelSection :label="__('Field')">
		<PanelRow :label="__('Label')">
			<TextInput
				variant="ghost"
				:model-value="field.label"
				:placeholder="field.fieldname"
				@update:model-value="(v) => $emit('update', { label: v })"
			/>
		</PanelRow>
		<PanelRow :label="__('Required')" :box="false">
			<div class="flex min-h-7 flex-col justify-center px-2">
				<div class="flex h-7 items-center">
					<Switch
						:model-value="locked || !!field.reqd"
						:disabled="locked"
						size="sm"
						@update:model-value="(v) => $emit('update', { reqd: v })"
					/>
				</div>
				<p v-if="locked" class="pb-1 text-p-sm text-ink-gray-5">
					{{ __("Every {0} needs it, so it stays required.", [doctypeLabel]) }}
				</p>
			</div>
		</PanelRow>
		<PanelRow v-if="field.fieldtype !== 'Check'" :label="__('Placeholder')">
			<TextInput
				variant="ghost"
				:model-value="field.placeholder"
				:placeholder="__('Add placeholder…')"
				@update:model-value="(v) => $emit('update', { placeholder: v })"
			/>
		</PanelRow>
		<PanelRow :label="__('Help text')">
			<Textarea
				variant="ghost"
				:rows="1"
				class="!min-h-7 !resize-none !py-1"
				:model-value="field.field_description"
				:placeholder="__('Add help text…')"
				@update:model-value="(v) => $emit('update', { field_description: v })"
			/>
		</PanelRow>
	</PanelSection>
	<PanelSection :label="__('Conditions')">
		<template #actions>
			<Tooltip :text="conditionHint">
				<span class="lucide-info size-4 text-ink-gray-4" aria-hidden="true" />
			</Tooltip>
		</template>
		<PanelRow v-for="rule in RULES" :key="rule.key" :label="rule.label" :box="false">
			<div
				class="min-h-7 w-full rounded-4 hover:bg-surface-gray-2 focus-within:bg-surface-gray-2 focus-within:ring-1 focus-within:ring-inset focus-within:ring-outline-gray-3"
			>
				<TextInput
					variant="ghost"
					:model-value="field[rule.key]"
					:placeholder="rule.empty"
					@update:model-value="(v) => $emit('update', { [rule.key]: v })"
				/>
			</div>
			<p v-if="ruleError(field[rule.key])" class="px-2 pt-1 text-p-sm text-ink-red-4">
				{{ __("This rule does not work: {0}", [ruleError(field[rule.key])]) }}
			</p>
		</PanelRow>
	</PanelSection>
</template>

<script setup>
import { computed } from "vue";
import { Button, Switch, TextInput, Textarea, Tooltip } from "frappe-ui";
import { __ } from "frappe/i18n";
import { ruleError } from "../conditionalRule";
import { fieldTypeIcon, fieldTypeLabel } from "../fieldTypeIcon";
import PanelHeader from "./PanelHeader.vue";
import PanelRow from "./PanelRow.vue";
import PanelSection from "./PanelSection.vue";

const props = defineProps({
	field: { type: Object, required: true },
	locked: { type: Boolean, default: false },
	guestSelectMissing: { type: Boolean, default: false },
	granting: { type: Boolean, default: false },
	grantRefused: { type: Boolean, default: false },
	doctypeLabel: { type: String, default: "" },
});
defineEmits(["update", "remove", "close", "grant-guest"]);

const RULES = [
	{ key: "depends_on", label: __("Visible if"), empty: __("Always") },
	{ key: "mandatory_depends_on", label: __("Mandatory if"), empty: __("Never") },
	{ key: "read_only_depends_on", label: __("Read-only if"), empty: __("Never") },
];
const conditionHint = __(
	"A field name, or eval: with doc.<fieldname>, e.g. eval:doc.country == 'India'. Leave blank for no condition."
);

const guestNote = computed(() =>
	props.grantRefused
		? __(
				"Guests can't see {0} records, and access can't be granted: they hold personal data. The public dropdown stays empty.",
				[props.field.options]
		  )
		: __("Guests can't see {0} records. Grant select access to list them publicly.", [
				props.field.options,
		  ])
);
</script>
