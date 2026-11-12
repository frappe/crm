<template>
	<div class="mx-auto max-w-2xl pt-8">
		<div class="rounded-7 border bg-surface-white p-7">
			<!-- simulated success screen -->
			<div v-if="previewSubmitted" class="flex flex-col items-center gap-3 py-10 text-center">
				<div
					class="flex h-12 w-12 items-center justify-center rounded-full bg-surface-green-2 text-ink-green-2"
				>
					<span class="lucide-check h-6 w-6" aria-hidden="true" />
				</div>
				<div class="text-lg font-semibold text-ink-gray-9">
					{{ form.success_message || __("Thank you!") }}
				</div>
				<Button :label="__('Preview again')" @click="resetPreview" />
			</div>

			<template v-else>
				<!-- mirror the public page (crm_form.html): 20px title, ~14px gap -->
				<div class="text-xl font-semibold text-ink-gray-9">
					{{ form.title || __("Form title") }}
				</div>
				<div v-if="form.description" class="mt-3.5 whitespace-pre-wrap text-sm text-ink-gray-6">
					{{ form.description }}
				</div>
				<div class="mt-5 flex flex-col gap-5">
					<div v-for="(section, si) in layout" :key="si">
						<div v-if="section.label" class="mb-3 text-sm font-semibold text-ink-gray-8">
							{{ section.label }}
						</div>
						<div
							class="grid gap-x-5"
							:style="{
								gridTemplateColumns: `repeat(${section.columns.length}, minmax(0,1fr))`,
							}"
						>
							<div v-for="(col, ci) in section.columns" :key="ci" class="flex flex-col gap-4">
								<div v-show="fieldVisible(f)" v-for="f in col" :key="f.fieldname">
									<div v-if="f.fieldtype !== 'Check'" class="mb-1.5 text-sm text-ink-gray-5">
										{{ f.label }}<span v-if="fieldRequired(f)" class="text-ink-red-4">*</span>
									</div>
									<FormControl
										v-if="TEXTAREA_TYPES.includes(f.fieldtype)"
										v-model="previewModel[f.fieldname]"
										type="textarea"
										:placeholder="f.placeholder"
										:disabled="fieldReadOnly(f)"
									/>
									<FormControl
										v-else-if="f.fieldtype === 'Select'"
										v-model="previewModel[f.fieldname]"
										type="select"
										:options="selectOptions(f)"
										:placeholder="f.placeholder || __('Select an option')"
										:disabled="fieldReadOnly(f)"
									/>
									<FormControl
										v-else-if="f.fieldtype === 'Link'"
										v-model="previewModel[f.fieldname]"
										type="select"
										:options="linkSelectOptions(f)"
										:placeholder="f.placeholder || __('Select an option')"
										:disabled="fieldReadOnly(f)"
									/>
									<div v-else-if="f.fieldtype === 'Check'" class="flex items-center gap-2">
										<FormControl
											v-model="previewModel[f.fieldname]"
											type="checkbox"
											:disabled="fieldReadOnly(f)"
										/>
										<span class="text-sm text-ink-gray-5"
											>{{ f.label
											}}<span v-if="fieldRequired(f)" class="text-ink-red-4">*</span></span
										>
									</div>
									<FormControl
										v-else
										v-model="previewModel[f.fieldname]"
										:type="inputType(f)"
										:placeholder="f.placeholder"
										:disabled="fieldReadOnly(f)"
									/>
									<div v-if="f.field_description" class="mt-1 text-sm text-ink-gray-4">
										{{ f.field_description }}
									</div>
								</div>
							</div>
						</div>
					</div>
					<div v-if="!inputFieldCount" class="text-sm text-ink-gray-4">
						{{ __("Add fields to see them here.") }}
					</div>
					<div class="mt-1 flex justify-end gap-2.5">
						<Button
							variant="solid"
							size="md"
							:label="form.submit_button_label || __('Submit')"
							@click="previewSubmitted = true"
						/>
					</div>
				</div>
			</template>
		</div>
	</div>
</template>

<script setup>
import { Button, FormControl } from "frappe-ui";
import { ref, reactive, computed } from "vue";
import { __ } from "frappe/i18n";
import { evaluateRule } from "../conditionalRule";
import { BREAK_TYPES, TEXTAREA_TYPES, groupLayout, inputType, optionList } from "./formModel";

const props = defineProps({ draft: { type: Object, required: true } });
const { form, linkMeta } = props.draft;

const previewModel = reactive({}); // throwaway values so the preview is interactive
const previewSubmitted = ref(false);

const layout = computed(() => groupLayout(form.fields));
const inputFieldCount = computed(
	() => form.fields.filter((f) => !BREAK_TYPES.includes(f.fieldtype)).length
);

// the public page's fallbacks: a rule that does not parse shows the field, and does not require or lock it
const fieldVisible = (f) => evaluateRule(f.depends_on, previewModel, true);
const fieldRequired = (f) =>
	f.reqd ? true : evaluateRule(f.mandatory_depends_on, previewModel, false);
const fieldReadOnly = (f) => evaluateRule(f.read_only_depends_on, previewModel, false);

function resetPreview() {
	previewSubmitted.value = false;
	Object.keys(previewModel).forEach((k) => delete previewModel[k]);
}

function selectOptions(f) {
	const opts = optionList(f.options).map((o) => ({ label: o, value: o }));
	return [{ label: __("Select an option"), value: "" }, ...opts];
}

// preview dropdown for a Link field — the target doctype's records, fetched lazily
// into `linkOptions`; mirrors the public form's server-populated <select>.
function linkSelectOptions(f) {
	linkMeta.ensureLinkMeta(f.options);
	const opts = (linkMeta.linkOptions[f.options] || []).map((o) => ({
		label: o,
		value: o,
	}));
	return [{ label: __("Select an option"), value: "" }, ...opts];
}
</script>
