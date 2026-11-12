<template>
	<div class="flex items-center justify-between py-3">
		<div class="flex items-center gap-2">
			<Button
				variant="ghost"
				icon-left="lucide-chevron-left"
				:label="form.title || __('Untitled')"
				size="md"
				class="-ml-4 cursor-pointer !max-w-96 !justify-start !pr-0 text-lg-semibold text-ink-gray-7 no-underline hover:bg-transparent hover:no-underline hover:opacity-70 focus:bg-transparent focus:outline-none focus:ring-0"
				@click="emit('back')"
			/>
			<Badge v-if="dirty" variant="subtle" theme="amber" size="sm" :label="__('Not Saved')" />
		</div>
		<div v-if="loaded" class="flex items-center gap-4">
			<div class="flex items-center justify-between gap-2 h-7" @click="togglePublish">
				<Switch size="sm" :model-value="Boolean(form.published)" />
				<span class="text-sm text-ink-gray-7">{{ __("Publish") }}</span>
			</div>
			<Button
				:label="mode === 'edit' ? __('Preview') : __('Edit')"
				@click="emit('update:mode', mode === 'edit' ? 'preview' : 'edit')"
			>
				<template #prefix>
					<span class="lucide-eye h-4 w-4" aria-hidden="true" v-if="mode === 'edit'" />
					<span class="lucide-pencil h-4 w-4" aria-hidden="true" v-else />
				</template>
			</Button>
			<Button
				:disabled="!dirty"
				:label="__('Save')"
				theme="gray"
				variant="solid"
				:loading="saving"
				@click="saveNow"
			/>
		</div>
	</div>
</template>

<script setup>
import { Badge, Button, Switch } from "frappe-ui";
import { __ } from "frappe/i18n";

const props = defineProps({
	draft: { type: Object, required: true },
	mode: { type: String, required: true }, // edit | preview
});
const emit = defineEmits(["back", "update:mode"]);

const { form, loaded, saving, dirty, togglePublish, saveNow } = props.draft;
</script>
