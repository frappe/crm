<!-- Public lead and deal capture forms: the list, and the builder for one form at `?form=<name>`. Server logic stays in crm.api.form. -->
<template>
	<PageHeader v-if="!activeName">
		<Breadcrumbs class="-ml-0.5" :items="[{ label: __('Forms') }]" />
		<div class="flex items-center gap-2">
			<Button
				variant="ghost"
				size="sm"
				icon="lucide-circle-question-mark"
				:href="DOCS_URL"
				:aria-label="__('Documentation')"
			/>
			<Button
				variant="solid"
				icon-left="lucide-plus"
				:label="__('Create')"
				@click="list.openCreate()"
			/>
		</div>
	</PageHeader>
	<div class="flex h-full flex-col overflow-y-auto">
		<div class="px-3 pb-6 sm:px-5">
			<FormBuilder
				v-if="activeName"
				:key="activeName"
				:name="activeName"
				:router="router"
				@back="router.push({ query: {} })"
			/>
			<FormsList v-else ref="list" @open="(name) => router.push({ query: { form: name } })" />
		</div>
	</div>
</template>

<script setup>
import { computed, useTemplateRef } from "vue";
import { useRoute, useRouter } from "vue-router";
import { Breadcrumbs, Button, PageHeader } from "frappe-ui";
import { __ } from "frappe/i18n";
import FormBuilder from "./FormBuilder.vue";
import FormsList from "./FormsList.vue";

const DOCS_URL = "https://docs.frappe.io/crm/capturing-leads/web-form";

const router = useRouter();
const list = useTemplateRef("list");
const route = useRoute();
const activeName = computed(() => [route.query.form].flat()[0] || null);
</script>
