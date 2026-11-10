<!-- Public lead and deal capture forms: the list, and the builder for one form. Server logic stays in crm.api.form. -->
<template>
	<FormsList v-if="screen === 'list'" @open="openBuilder" />
	<FormBuilder v-else :key="activeName" :name="activeName" @back="screen = 'list'" />
</template>

<script setup>
import { ref } from "vue";
import FormBuilder from "./forms/FormBuilder.vue";
import FormsList from "./forms/FormsList.vue";

defineProps({ bindings: { type: Object, default: () => ({}) } });

const screen = ref("list");
const activeName = ref(null);

function openBuilder(name) {
	activeName.value = name;
	screen.value = "builder";
}
</script>
