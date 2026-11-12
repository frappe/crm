<template>
	<div class="mx-auto flex w-full max-w-[640px] flex-col gap-8 pt-6">
		<section class="flex flex-col gap-4">
			<div class="flex flex-col gap-1">
				<h3 class="text-base-medium text-ink-gray-8">{{ __("Form details") }}</h3>
				<p class="text-p-sm text-ink-gray-5">
					{{ __("Where submissions go and how the form is reached.") }}
				</p>
			</div>
			<FormControl
				v-model="doctypeModel"
				type="select"
				:label="__('Maps to')"
				:options="targetOptions"
			/>
			<div class="space-y-1.5">
				<FormLabel :label="__('Route')" />
				<div
					class="flex h-7 cursor-text items-center rounded-4 border border-transparent bg-surface-gray-2 px-2 text-base transition-colors hover:bg-surface-gray-3 focus-within:border-outline-gray-4 focus-within:bg-surface-base"
					@click="focusRouteEnd"
				>
					<span class="shrink-0 text-ink-gray-4">/crm-form/</span>
					<input
						v-model="form.route"
						class="min-w-0 flex-1 border-0 bg-transparent p-0 text-base text-ink-gray-8 placeholder:text-ink-gray-4 focus:outline-none focus:ring-0"
						@input="(routeEdited = true), markDirty()"
						@blur="form.route = slugify(form.route)"
					/>
				</div>
			</div>
			<FormControl
				v-model="form.submit_button_label"
				type="text"
				:label="__('Submit button label')"
				@input="markDirty"
			/>
			<div class="flex flex-col gap-2">
				<div class="space-y-1.5">
					<FormLabel :label="__('After submit')" />
					<TabButtons v-model="afterSubmit" :options="afterSubmitOptions" fluid />
				</div>
				<FormControl
					v-if="afterSubmit === 'message'"
					v-model="form.success_message"
					type="textarea"
					:rows="3"
					:placeholder="__('Thank you! We will be in touch soon.')"
					@input="markDirty"
				/>
				<FormControl
					v-else
					v-model="form.redirect_url"
					type="text"
					:placeholder="__('https://example.com/thank-you')"
					@input="markDirty"
				/>
			</div>
		</section>
	</div>
</template>

<script setup>
import { FormControl, FormLabel, TabButtons } from "frappe-ui";
import { computed } from "vue";
import { __ } from "frappe/i18n";
import { slugify } from "./formModel";

const props = defineProps({ draft: { type: Object, required: true } });
const { form, routeEdited, doctypeModel, targetOptions, markDirty } = props.draft;

const afterSubmitOptions = [
	{ value: "message", label: __("Show a message") },
	{ value: "url", label: __("Go to a URL") },
];
// both values stay in the form while editing; save clears the one not selected
const afterSubmit = computed({
	get: () => form.after_submit,
	set(value) {
		form.after_submit = value;
		markDirty();
	},
});

// clicking the /crm-form/ prefix or the box padding focuses the slug input with
// the caret at the end (not the start)
function focusRouteEnd(e) {
	if (e.target.tagName === "INPUT") return;
	const input = e.currentTarget.querySelector("input");
	if (!input) return;
	input.focus();
	input.setSelectionRange(input.value.length, input.value.length);
}
</script>
