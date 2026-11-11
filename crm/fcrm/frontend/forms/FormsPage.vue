<!-- Public lead and deal capture forms: the list, and the builder for one form at `?form=<name>`. Server logic stays in crm.api.form. -->
<template>
	<div class="flex h-full flex-col overflow-y-auto">
		<header
			v-if="!activeName"
			class="flex h-12 shrink-0 items-center border-b border-outline-gray-1 px-5"
		>
			<h1 class="text-xl-semibold text-ink-gray-9">{{ __("Forms") }}</h1>
		</header>
		<div class="px-5 pb-6">
			<FormBuilder
				v-if="activeName"
				:key="activeName"
				:name="activeName"
				:router="router"
				@back="router.push({ query: {} })"
			/>
			<FormsList v-else @open="(name) => router.push({ query: { form: name } })" />
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { __ } from "frappe/i18n";
import FormBuilder from "./FormBuilder.vue";
import FormsList from "./FormsList.vue";

const router = useRouter();
const route = useRoute();
const activeName = computed(() => route.query.form || null);
</script>
