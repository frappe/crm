<!-- CRM Sales Hierarchy as a tree: add users under a manager, move a user, remove a node. -->
<template>
	<p
		v-if="hierarchyOff"
		class="mt-3 rounded-4 bg-surface-gray-2 px-3 py-2 text-base text-ink-gray-6"
	>
		{{
			__(
				"Sales hierarchy permissions are off, so the tree does not limit who sees which leads and deals. Turn them on under General › Deals."
			)
		}}
	</p>
	<div class="mt-3 flex items-center gap-2">
		<TextInput
			v-model="query"
			class="flex-1"
			type="text"
			:placeholder="__('Search the hierarchy')"
			:aria-label="__('Search the hierarchy')"
		>
			<template #prefix>
				<span class="lucide-search size-4 text-ink-gray-5" aria-hidden="true" />
			</template>
		</TextInput>
		<Button
			v-if="perms.holds('create')"
			:label="__('Add to hierarchy')"
			icon-left="lucide-plus"
			:disabled="!nodes"
			@click="adding = true"
		/>
	</div>
	<div v-if="!nodes && !error" aria-hidden="true" class="mt-2">
		<div v-for="row in 3" :key="row" class="flex items-center gap-3 py-2.5">
			<Skeleton class="size-8 rounded-full" />
			<Skeleton class="h-4 w-48 rounded-1" />
		</div>
	</div>
	<ErrorMessage v-else-if="!nodes" class="py-3.5" :message="error" />
	<template v-else>
		<p v-if="!rows.length" class="py-3.5 text-base text-ink-gray-5">
			{{ query ? __("No one matches {0}", [query]) : __("No one is in the hierarchy yet") }}
		</p>
		<ul class="mt-2">
			<li
				v-for="row in rows"
				:key="row.name"
				:data-node="row.user"
				class="flex items-center gap-3 border-b border-outline-gray-1 py-2.5 last:border-b-0"
				:style="{ paddingInlineStart: `${row.depth * 1.75}rem` }"
			>
				<Avatar :image="row.user_image" :label="row.full_name" size="lg" />
				<div class="min-w-0 flex-1">
					<p class="truncate text-base text-ink-gray-8">{{ row.full_name }}</p>
					<p class="truncate text-sm text-ink-gray-5">{{ row.user }}</p>
				</div>
				<span class="shrink-0 text-base text-ink-gray-6">{{ row.role ? __(row.role) : "" }}</span>
				<Dropdown v-if="actions.length" :options="actions.map((act) => act(row))" align="end">
					<Button
						icon="lucide-ellipsis"
						variant="ghost"
						:label="__('Actions for {0}', [row.full_name])"
					/>
				</Dropdown>
			</li>
		</ul>
		<ErrorMessage v-if="error" class="py-3.5" :message="error" />
	</template>
	<AddToHierarchyDialog
		v-if="adding && nodes"
		v-model="adding"
		:nodes="nodes"
		:users="users"
		@changed="load"
	/>
	<MoveDialog
		v-if="moving && nodes"
		:key="moving.name"
		v-model="movingOpen"
		:row="moving"
		:nodes="nodes"
		:users="users"
		@changed="load"
	/>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import {
	Avatar,
	Button,
	Dropdown,
	ErrorMessage,
	Skeleton,
	TextInput,
	dialog,
	toast,
} from "frappe-ui";
import {
	deleteDocument,
	getDocument,
	listDocuments,
	runMethod,
	updateDocument,
} from "@framework/ui/api";
import { useDocPermissions } from "@framework/ui/useDocPermissions";
import { __ } from "frappe/i18n";
import AddToHierarchyDialog from "./sales-hierarchy/AddToHierarchyDialog.vue";
import MoveDialog from "./sales-hierarchy/MoveDialog.vue";
import { reportsOf, treeRows } from "./sales-hierarchy/hierarchyTree.js";
import type { HierarchyNode, HierarchyRow, HierarchyUser } from "./sales-hierarchy/types";

defineProps<{ bindings: Record<string, never> }>();

const DOCTYPE = "CRM Sales Hierarchy";
const PAGE = 500;

const perms = useDocPermissions(DOCTYPE);
const nodes = ref<HierarchyNode[] | null>(null);
const users = ref<HierarchyUser[]>([]);
const hierarchyOff = ref(false);
const error = ref("");
const query = ref("");
const adding = ref(false);
const moving = ref<HierarchyRow | null>(null);

const rows = computed(() => treeRows(nodes.value ?? [], users.value, query.value));
const actions = computed(() => [
	...(perms.holds("write") ? [moveAction] : []),
	...(perms.holds("write") && perms.holds("delete") ? [removeAction] : []),
]);
const movingOpen = computed({
	get: () => !!moving.value,
	set: (open) => !open && (moving.value = null),
});

load();
readSwitch();

async function load() {
	try {
		const [list, crmUsers] = await Promise.all([
			listNodes(),
			runMethod<[HierarchyUser[], HierarchyUser[]]>(
				"crm.api.session.get_users",
				{},
				{ http: "GET" }
			),
		]);
		nodes.value = list;
		users.value = crmUsers.data[1];
		error.value = "";
	} catch (failure) {
		error.value = (failure as Error).message;
	}
}

async function listNodes() {
	const all: HierarchyNode[] = [];
	for (let more = true; more; ) {
		const page = await listDocuments<HierarchyNode>(DOCTYPE, {
			fields: ["name", "user", "full_name", "reports_to", "modified"],
			order_by: "lft asc",
			start: all.length,
			limit: PAGE,
		});
		all.push(...page.data);
		more = page.has_next_page;
	}
	return all;
}

async function readSwitch() {
	try {
		const { data } = await getDocument("FCRM Settings", "FCRM Settings");
		hierarchyOff.value = !data.enable_sales_hierarchy;
	} catch {
		hierarchyOff.value = false;
	}
}

function moveAction(row: HierarchyRow) {
	return { label: __("Move"), icon: "lucide-move", onClick: () => (moving.value = row) };
}

function removeAction(row: HierarchyRow) {
	return {
		label: __("Remove from hierarchy"),
		icon: "lucide-trash-2",
		onClick: () => confirmRemove(row),
	};
}

function confirmRemove(row: HierarchyRow) {
	const manager = nodes.value?.find((node) => node.name === row.reports_to);
	const message = !row.reports
		? __("They keep their CRM role.")
		: manager
		? __("Their direct reports will report to {0}.", [manager.full_name || manager.user])
		: __("Their direct reports move to the top level.");
	dialog.confirm({
		title: __("Remove {0} from the hierarchy?", [row.full_name]),
		message,
		confirmLabel: __("Remove"),
		theme: "red",
		onConfirm: () => remove(row),
	});
}

async function remove(row: HierarchyRow) {
	try {
		// A node with reports cannot be deleted, so its reports move up first.
		for (const child of reportsOf(nodes.value ?? [], row)) {
			const { name, modified } = child;
			await updateDocument(DOCTYPE, name, { name, modified, reports_to: row.reports_to || null });
		}
		await deleteDocument(DOCTYPE, row.name);
		toast.success(__("{0} was removed from the hierarchy", [row.full_name]));
	} catch (failure) {
		toast.error((failure as Error).message);
	}
	await load();
}
</script>
