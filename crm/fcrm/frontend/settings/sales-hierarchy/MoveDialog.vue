<!-- Changes who one node of the sales hierarchy reports to. -->
<template>
	<Dialog v-model="open" :title="__('Move {0}', [row.full_name])">
		<div class="flex flex-col gap-4">
			<Select v-model="manager" :label="__('Reports to')" :options="managerOptions" />
			<ErrorMessage v-if="error" :message="error" />
		</div>
		<template #actions>
			<div class="flex justify-end">
				<Button
					variant="solid"
					:label="__('Move')"
					:disabled="manager === (row.reports_to || '')"
					:loading="saving"
					@click="move"
				/>
			</div>
		</template>
	</Dialog>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { Button, Dialog, ErrorMessage, Select, toast } from "frappe-ui";
import { updateDocument } from "@framework/ui/api";
import { __ } from "frappe/i18n";
import { managerChoices } from "./hierarchyTree.js";
import type { HierarchyNode, HierarchyRow, HierarchyUser } from "./types";

const props = defineProps<{ row: HierarchyRow; nodes: HierarchyNode[]; users: HierarchyUser[] }>();
const emit = defineEmits<{ changed: [] }>();
const open = defineModel<boolean>({ required: true });

const manager = ref(props.row.reports_to || "");
const saving = ref(false);
const error = ref("");

const managerOptions = computed(() => [
	{ label: __("No one (top level)"), value: "" },
	...managerChoices(props.nodes, props.row, props.users).map((node: HierarchyNode) => ({
		label: node.full_name || node.user,
		value: node.name,
	})),
]);

async function move() {
	saving.value = true;
	error.value = "";
	try {
		const { name, modified } = props.row;
		await updateDocument("CRM Sales Hierarchy", name, {
			name,
			modified,
			reports_to: manager.value || null,
		});
		toast.success(__("{0} moved", [props.row.full_name]));
		emit("changed");
		open.value = false;
	} catch (failure) {
		error.value = (failure as Error).message;
	} finally {
		saving.value = false;
	}
}
</script>
