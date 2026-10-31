<!-- Places CRM users in the sales hierarchy under one manager, or at its top level. -->
<template>
	<Dialog v-model="open" :title="__('Add to hierarchy')">
		<div class="flex flex-col gap-4">
			<Select v-model="manager" :label="__('Reports to')" :options="managerOptions" />
			<TableMultiSelect
				v-if="candidates.length"
				v-model="picked"
				doctype="User"
				:filters="{ name: ['in', candidates.map((user) => user.name)] }"
				:label="__('Users')"
				:placeholder="__('Search users')"
			/>
			<p v-else class="text-base text-ink-gray-5">
				{{ __("Every CRM user who can be placed here is already in the hierarchy.") }}
			</p>
			<ErrorMessage v-if="error" :message="error" />
		</div>
		<template #actions>
			<div class="flex justify-end">
				<Button
					variant="solid"
					:label="__('Add')"
					:disabled="!picked.length"
					:loading="saving"
					@click="add"
				/>
			</div>
		</template>
	</Dialog>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { Button, Dialog, ErrorMessage, Select, toast } from "frappe-ui";
import { TableMultiSelect } from "@framework/ui";
import { createDocument } from "@framework/ui/api";
import { __ } from "frappe/i18n";
import { addCandidates } from "./hierarchyTree.js";
import type { HierarchyNode, HierarchyUser } from "./types";

const props = defineProps<{ nodes: HierarchyNode[]; users: HierarchyUser[] }>();
const emit = defineEmits<{ changed: [] }>();
const open = defineModel<boolean>({ required: true });

const manager = ref("");
const picked = ref<string[]>([]);
const saving = ref(false);
const error = ref("");

const managerNode = computed(
	() => props.nodes.find((node) => node.name === manager.value) ?? null
);
const candidates = computed(() => addCandidates(props.users, props.nodes, managerNode.value));
const managerOptions = computed(() => [
	{ label: __("No one (top level)"), value: "" },
	...props.nodes.map((node) => ({ label: node.full_name || node.user, value: node.name })),
]);

watch(candidates, (allowed) => {
	picked.value = picked.value.filter((name) => allowed.some((user) => user.name === name));
});

async function add() {
	saving.value = true;
	error.value = "";
	let added = 0;
	try {
		// One at a time: each insert renumbers the tree's lft/rgt.
		for (const user of picked.value) {
			await createDocument("CRM Sales Hierarchy", { user, reports_to: manager.value || null });
			picked.value = picked.value.filter((name) => name !== user);
			added++;
		}
		toast.success(added === 1 ? __("1 user added") : __("{0} users added", [added]));
		emit("changed");
		open.value = false;
	} catch (failure) {
		error.value = (failure as Error).message;
		if (added) emit("changed");
	} finally {
		saving.value = false;
	}
}
</script>
