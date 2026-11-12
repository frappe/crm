<template>
	<!-- hidden required fields: kept off the form, a default is applied
       on submission so the record can still be created -->
	<div v-if="hiddenFields.length" class="mt-6">
		<div class="mb-2 flex items-center gap-1.5 text-base-medium text-ink-gray-7">
			<span class="lucide-eye-off h-3.5 w-3.5 text-ink-gray-5" aria-hidden="true" />
			{{ __("Hidden required fields") }}
		</div>
		<div class="rounded-4 bg-surface-gray-2 p-2.5">
			<p class="mb-2.5 text-p-sm text-ink-gray-5">
				{{
					__(
						"These fields aren't shown to users. Default values are used when the form is submitted."
					)
				}}
			</p>
			<div class="flex flex-col gap-2">
				<div
					v-for="h in hiddenFields"
					:key="h.fieldname"
					class="flex items-center gap-2.5 rounded-4 border border-outline-gray-2 bg-surface-elevation-2 px-2.5 py-2"
				>
					<span
						:class="[fieldTypeIcon(h), 'h-4 w-4 shrink-0 text-ink-gray-5']"
						aria-hidden="true"
					/>
					<span class="flex-1 truncate text-base text-ink-gray-8" :title="h.label">{{
						h.label
					}}</span>
					<div class="w-52 shrink-0">
						<FormControl
							v-if="hiddenIsSelect(h)"
							type="select"
							size="sm"
							:modelValue="h.default"
							:options="hiddenSelectOptions(h)"
							@update:modelValue="(v) => ((h.default = v), markDirty())"
						/>
						<FormControl
							v-else
							type="text"
							size="sm"
							:modelValue="h.default"
							:placeholder="__('Default value')"
							@update:modelValue="(v) => ((h.default = v), markDirty())"
						/>
					</div>
				</div>
			</div>
			<ErrorMessage
				v-if="hiddenMissingDefault"
				class="mt-2"
				:message="__('Set a default value for each field to publish this form.')"
			/>
		</div>
	</div>
</template>

<script setup>
import { ErrorMessage, FormControl } from "frappe-ui";
import { __ } from "frappe/i18n";
import { fieldTypeIcon } from "../fieldTypeIcon";
import { optionList } from "./formModel";

const props = defineProps({ draft: { type: Object, required: true } });
const { hiddenFields, hiddenMissingDefault, markDirty, linkMeta } = props.draft;

function hiddenIsSelect(h) {
	return h.fieldtype === "Select" || h.fieldtype === "Link";
}

function hiddenSelectOptions(h) {
	let opts = [];
	if (h.fieldtype === "Select") {
		opts = optionList(h.options);
	} else if (h.fieldtype === "Link") {
		opts = linkMeta.linkOptions[h.options] || [];
	}
	opts = opts.slice();
	if (h.default && !opts.includes(h.default)) opts.unshift(h.default);
	return opts.map((o) => ({ label: o, value: o }));
}
</script>
