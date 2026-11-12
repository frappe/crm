<!-- The bin: 24px above the canvas's bottom edge, only while a canvas field is dragged. Not a drop
     list: DragLayer hit-tests the pointer against `el`, so a release elsewhere never removes. -->
<template>
	<div class="pointer-events-none sticky bottom-6 z-10 flex h-0 justify-center">
		<div
			ref="el"
			class="flex h-9 -translate-y-full items-center gap-2 rounded-8 border px-4 text-base shadow-xl transition-[opacity,background-color,border-color,color] duration-150"
			:class="[
				visible ? 'opacity-100' : 'opacity-0',
				over
					? 'border-outline-red-3 bg-surface-red-2 text-ink-red-5'
					: 'border-outline-gray-2 bg-surface-white text-ink-gray-6',
			]"
			data-editor-bin
		>
			<span class="lucide-trash-2 size-4" aria-hidden="true" />
			{{ over ? __("Release to remove") : __("Drop here to remove") }}
		</div>
	</div>
</template>

<script setup>
import { ref } from "vue";
import { __ } from "frappe/i18n";

defineProps({
	visible: { type: Boolean, default: false },
	over: { type: Boolean, default: false },
});
const el = ref(null);
defineExpose({ el });
</script>
