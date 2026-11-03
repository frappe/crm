<!-- An email or mobile line of an open contact row: a button when it acts, plain text otherwise. -->
<template>
	<Tooltip :text="tooltip" :disabled="!action">
		<component
			:is="action ? 'button' : 'div'"
			:type="action ? 'button' : undefined"
			class="-mx-2 flex min-w-0 items-center gap-3 rounded-2 py-1 pl-3 pr-2 text-left"
			:class="
				action
					? 'cursor-pointer hover:bg-surface-gray-2 focus-visible:bg-surface-gray-2 focus-visible:outline-none'
					: ''
			"
			@click="action?.()"
		>
			<span class="size-4 shrink-0 text-ink-gray-6" :class="icon" aria-hidden="true" />
			<span class="truncate">{{ value }}</span>
		</component>
	</Tooltip>
</template>

<script setup>
import { Tooltip } from 'frappe-ui'

defineProps({
	icon: { type: String, required: true },
	value: { type: String, required: true },
	tooltip: { type: String, default: '' },
	action: { type: Function, default: null },
})
</script>
