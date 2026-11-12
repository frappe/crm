<template>
	<div class="pt-5">
		<EditorMasthead :draft="draft" />
		<EditorCanvas :draft="draft" />
		<HiddenFieldsBlock :draft="draft" />
	</div>
</template>

<script setup>
import EditorCanvas from "./EditorCanvas.vue";
import EditorMasthead from "./EditorMasthead.vue";
import HiddenFieldsBlock from "./HiddenFieldsBlock.vue";

defineProps({ draft: { type: Object, required: true } });
</script>
