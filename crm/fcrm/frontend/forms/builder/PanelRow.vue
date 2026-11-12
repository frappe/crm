<!-- A label-left row of the field panel. `box` wraps a ghost control the way desk's FieldBox does. -->
<template>
	<div class="grid grid-cols-[130px_1fr] items-start gap-2">
		<span class="h-7 text-base leading-7 text-ink-gray-5">{{ label }}</span>
		<div class="min-w-0">
			<div
				v-if="box"
				class="min-h-7 w-full min-w-0 rounded-4 hover:bg-surface-gray-2 focus-within:bg-surface-gray-2 focus-within:ring-1 focus-within:ring-inset focus-within:ring-outline-gray-3"
			>
				<slot />
			</div>
			<slot v-else />
		</div>
	</div>
</template>

<script setup>
defineProps({
	label: { type: String, required: true },
	box: { type: Boolean, default: true },
});
</script>
