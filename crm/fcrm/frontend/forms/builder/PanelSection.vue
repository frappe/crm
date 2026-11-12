<!-- One collapsible section of the field panel, as in the record panel: 42px header, bold label, chevron, a rule above. -->
<template>
	<div
		class="flex h-[42px] shrink-0 cursor-pointer select-none items-center gap-1.5 px-4"
		:class="{ 'border-t border-outline-gray-1': divided }"
		@click="open = !open"
	>
		<button
			type="button"
			class="flex items-center gap-1 py-1 text-base font-semibold text-ink-gray-8"
			:aria-expanded="open"
			@click.stop="open = !open"
		>
			{{ label }}
			<span
				class="size-4 text-ink-gray-5"
				:class="open ? 'lucide-chevron-up' : 'lucide-chevron-down'"
				aria-hidden="true"
			/>
		</button>
		<div v-if="$slots.actions" class="ml-auto flex cursor-default items-center gap-1" @click.stop>
			<slot name="actions" />
		</div>
	</div>
	<div v-if="open" class="flex flex-col gap-2.5 px-4 pb-3 pt-1">
		<slot />
	</div>
</template>

<script setup>
import { ref } from "vue";

defineProps({
	label: { type: String, required: true },
	divided: { type: Boolean, default: true },
});
const open = ref(true);
</script>
