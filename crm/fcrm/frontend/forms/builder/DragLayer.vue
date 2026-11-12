<!-- The drag preview card and the bin. Pointer state stays in here: a re-render of the editor
     mid-drag makes vuedraggable patch DOM that Sortable has moved. -->
<template>
	<RemoveBin ref="bin" :visible="withBin" :over="overBin" />
	<!-- the card under the pointer; Sortable's own clone stays hidden. Over the bin it lifts above the
	     pointer, so "Release to remove" stays readable. -->
	<div
		v-if="card"
		class="pointer-events-none fixed left-0 top-0 z-50 flex h-9 max-w-[240px] items-center gap-2 rounded-6 border px-3 text-base opacity-95 shadow-xl"
		:class="
			overBin
				? 'border-outline-red-3 bg-surface-red-2 text-ink-red-5'
				: 'border-outline-gray-2 bg-surface-white text-ink-gray-8'
		"
		:style="{ transform: `translate(${pos.x - 20}px, ${pos.y - (overBin ? 62 : 18)}px)` }"
		data-editor-drag-card
	>
		<span
			class="size-4 shrink-0"
			:class="[card.icon, overBin ? '' : 'text-ink-gray-5']"
			aria-hidden="true"
		/>
		<span class="truncate">{{ card.label }}</span>
	</div>
</template>

<script setup>
import { onBeforeUnmount, reactive, ref } from "vue";
import RemoveBin from "./RemoveBin.vue";

const card = ref(null);
const withBin = ref(false);
const overBin = ref(false);
const pos = reactive({ x: 0, y: 0 });
const bin = ref(null);

function track(e) {
	pos.x = e.clientX;
	pos.y = e.clientY;
	if (!withBin.value || !bin.value?.el) return;
	const r = bin.value.el.getBoundingClientRect();
	overBin.value =
		e.clientX >= r.left - 8 &&
		e.clientX <= r.right + 8 &&
		e.clientY >= r.top - 8 &&
		e.clientY <= r.bottom + 8;
}
window.addEventListener("pointerdown", track, true);
window.addEventListener("pointermove", track, true);
onBeforeUnmount(() => {
	window.removeEventListener("pointerdown", track, true);
	window.removeEventListener("pointermove", track, true);
});

function start(next, withRemoveBin) {
	card.value = next;
	withBin.value = withRemoveBin;
	overBin.value = false;
}

// ends the drag; true when it was released over the bin
function end() {
	const wasOverBin = withBin.value && overBin.value;
	card.value = null;
	withBin.value = false;
	overBin.value = false;
	return wasOverBin;
}

defineExpose({ start, end, pos });
</script>
