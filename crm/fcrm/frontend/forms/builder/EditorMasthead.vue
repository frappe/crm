<template>
	<!-- form masthead (title + description) — typed right on the canvas -->
	<div class="mb-5 px-1">
		<input
			v-model="form.title"
			:placeholder="__('Form title')"
			class="w-full border-0 bg-transparent p-0 text-2xl font-semibold leading-tight text-ink-gray-9 placeholder:text-ink-gray-4 focus:outline-none focus:ring-0"
			@input="onTitleInput"
		/>
		<textarea
			ref="descInput"
			v-model="form.description"
			:placeholder="__('Add a description to help people fill out this form')"
			rows="1"
			class="mt-2 w-full resize-none border-0 bg-transparent p-0 text-base leading-relaxed text-ink-gray-6 placeholder:text-ink-gray-4 focus:outline-none focus:ring-0"
			@input="(e) => (autoGrow(e.target), markDirty())"
		/>
		<hr class="mt-5 border-outline-gray-2" />
	</div>
</template>

<script setup>
import { ref, watch, onMounted } from "vue";
import { __ } from "frappe/i18n";

const props = defineProps({ draft: { type: Object, required: true } });
const { form, markDirty, onTitleInput } = props.draft;

const descInput = ref(null);

// Keep the description box sized to its text. flush:'post' runs after the DOM
// settles, so it fires whenever the textarea actually mounts (initial load, or
// re-entering Edit — it lives inside a lazily-rendered Tabs panel) or its content
// changes — no more 1-row box scrolled to the last line.
watch([descInput, () => form.description], () => sizeDescription(), {
	flush: "post",
});
// re-measure once web fonts load: scrollHeight with the fallback font wraps wrong
onMounted(() => document.fonts?.ready?.then(() => sizeDescription()));

// Robustly size the description box: measure on an animation frame (after layout),
// and if the box isn't laid out yet — it lives in a lazily-rendered Tabs panel, so
// on re-navigation it can be briefly zero-width/hidden — retry on the next frame.
// Without this, opening a saved multi-line description shows only the first line.
function sizeDescription(tries = 0) {
	requestAnimationFrame(() => {
		const el = descInput.value;
		if (!el) return;
		if (!el.clientWidth && tries < 20) return sizeDescription(tries + 1);
		autoGrow(el);
	});
}

// keep the description textarea sized to its content
function autoGrow(el) {
	if (!el) return;
	el.style.height = "auto";
	el.style.height = el.scrollHeight + "px";
}
</script>
