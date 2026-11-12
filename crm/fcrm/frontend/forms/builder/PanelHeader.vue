<!-- Icon tile, title, subtitle and the remove / close buttons that head a field or section panel. -->
<template>
	<div class="flex items-start gap-2.5 px-4 pb-3 pt-4">
		<div
			class="grid size-9 shrink-0 place-items-center rounded-4 bg-surface-gray-2 text-ink-gray-6"
		>
			<span class="size-4" :class="icon" aria-hidden="true" />
		</div>
		<div class="min-w-0 flex-1">
			<p class="truncate text-lg font-semibold text-ink-gray-9">{{ title }}</p>
			<p class="mt-0.5 truncate text-sm text-ink-gray-5">{{ subtitle }}</p>
		</div>
		<div class="-mr-1 flex shrink-0 items-center">
			<Button
				variant="ghost"
				icon="lucide-trash-2"
				:tooltip="removeLabel"
				:aria-label="removeLabel"
				@click="$emit('remove')"
			/>
			<Button variant="ghost" icon="lucide-x" :tooltip="__('Close')" @click="$emit('close')" />
		</div>
	</div>
</template>

<script setup>
import { Button } from "frappe-ui";
import { __ } from "frappe/i18n";

defineProps({
	icon: { type: String, required: true },
	title: { type: String, required: true },
	subtitle: { type: String, required: true },
	removeLabel: { type: String, required: true },
});
defineEmits(["remove", "close"]);
</script>
