<template>
	<div class="flex flex-col pt-5">
		<!-- form details -->
		<div>
			<div class="flex flex-col gap-1">
				<span class="text-lg-semibold text-ink-gray-8">{{ __("Form details") }}</span>
				<span class="text-p-sm text-ink-gray-6">{{ __("Basic settings for this form.") }}</span>
			</div>
			<div class="mt-3.5 flex flex-col gap-4">
				<div class="grid grid-cols-2 gap-4">
					<div>
						<div class="mb-1.5 text-sm text-ink-gray-5">
							{{ __("Route") }}
						</div>
						<div
							class="flex h-7 cursor-text items-center rounded-4 border border-transparent bg-surface-gray-2 px-2.5 text-base transition-colors hover:bg-surface-gray-3 focus-within:border-outline-gray-4 focus-within:bg-surface-base"
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
						v-model="doctypeModel"
						type="select"
						:label="__('Maps to')"
						:options="targetOptions"
					/>
					<FormControl
						v-model="form.submit_button_label"
						type="text"
						:label="__('Submit button label')"
						@input="markDirty"
					/>
				</div>
				<FormControl
					v-model="form.success_message"
					type="textarea"
					:label="__('Success message')"
					:rows="4"
					:placeholder="__('Shown after a successful submission')"
					@input="markDirty"
				/>
				<div>
					<FormControl
						v-model="form.redirect_url"
						type="text"
						:label="__('Redirect URL')"
						:placeholder="__('https://example.com/thank-you')"
						@input="markDirty"
					/>
					<p class="mt-1.5 text-p-sm text-ink-gray-5">
						{{
							__("Send visitors here after they submit. Leave blank to show the success message.")
						}}
					</p>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import { FormControl } from "frappe-ui";
import { __ } from "frappe/i18n";
import { slugify } from "./formModel";

const props = defineProps({ draft: { type: Object, required: true } });
const { form, routeEdited, doctypeModel, targetOptions, markDirty } = props.draft;

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
