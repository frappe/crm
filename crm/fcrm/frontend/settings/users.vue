<!-- CRM's users with their role: change a role, remove a user's CRM roles, add existing users. -->
<template>
	<div class="mt-3 flex items-center gap-2">
		<TextInput
			v-model="query"
			class="flex-1"
			type="text"
			:placeholder="__('Search users')"
			:aria-label="__('Search users')"
		>
			<template #prefix>
				<span class="lucide-search size-4 text-ink-gray-5" aria-hidden="true" />
			</template>
		</TextInput>
		<Button
			:label="__('Add existing users')"
			icon-left="lucide-plus"
			:disabled="!users"
			@click="adding = true"
		/>
	</div>
	<div v-if="!users && !error" aria-hidden="true" class="mt-2">
		<div
			v-for="row in 3"
			:key="row"
			class="flex items-center gap-3 border-b border-outline-gray-1 py-2.5 last:border-b-0"
		>
			<Skeleton class="size-8 rounded-full" />
			<Skeleton class="h-4 w-48 rounded-1" />
			<Skeleton class="ml-auto h-7 w-32 rounded-4" />
		</div>
	</div>
	<ErrorMessage v-else-if="!users" class="py-3.5" :message="error" />
	<template v-else>
		<p v-if="!shown.length" class="py-3.5 text-base text-ink-gray-5">
			{{ query ? __("No user matches {0}", [query]) : __("No CRM users yet") }}
		</p>
		<ul class="mt-2">
			<li
				v-for="user in shown"
				:key="user.name"
				:data-user="user.name"
				class="flex items-center gap-3 border-b border-outline-gray-1 py-2.5 last:border-b-0"
			>
				<Avatar :image="user.user_image" :label="user.full_name || user.name" size="lg" />
				<div class="min-w-0 flex-1">
					<p class="truncate text-base text-ink-gray-8">{{ user.full_name || user.name }}</p>
					<p class="truncate text-sm text-ink-gray-5">{{ user.name }}</p>
				</div>
				<div class="w-40 shrink-0">
					<Dropdown
						v-if="roleChoices(viewer, user).length > 1"
						:options="roleOptions(user)"
						:button="{ label: __(user.role), iconRight: 'lucide-chevron-down' }"
						align="end"
					/>
					<span v-else class="px-2 text-base text-ink-gray-6">{{ __(user.role) }}</span>
				</div>
				<Button
					v-if="removable(viewer, user)"
					icon="lucide-user-minus"
					variant="ghost"
					:label="__('Remove from CRM')"
					:tooltip="__('Remove from CRM')"
					@click="confirmRemove(user)"
				/>
				<span v-else class="w-7 shrink-0" aria-hidden="true" />
			</li>
		</ul>
		<ErrorMessage v-if="error" class="py-3.5" :message="error" />
	</template>
	<AddUsersDialog
		v-if="users"
		v-model="adding"
		:roles="givenRoles(viewer)"
		:existing="users.map((user) => user.name)"
		@added="load"
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
import { runMethod } from "@framework/ui/api";
import { __ } from "frappe/i18n";
import AddUsersDialog from "./users/AddUsersDialog.vue";
import { givenRoles, listedUsers, removable, roleChoices } from "./users/crmUsers.js";

defineProps<{ bindings: Record<string, never> }>();

interface CrmUser {
	name: string;
	full_name?: string;
	user_image?: string;
	role: string;
	session_user?: boolean;
}

const users = ref<CrmUser[] | null>(null);
const error = ref("");
const query = ref("");
const adding = ref(false);

const viewer = computed(
	() => users.value?.find((user) => user.session_user) ?? { name: "", role: "" }
);
const shown = computed(() => listedUsers(users.value ?? [], query.value));

load();

async function load() {
	try {
		const { data } = await runMethod<[CrmUser[], CrmUser[]]>(
			"crm.api.session.get_users",
			{},
			{ http: "GET" }
		);
		users.value = data[1];
		error.value = "";
	} catch (failure) {
		error.value = (failure as Error).message;
	}
}

function roleOptions(user: CrmUser) {
	return roleChoices(viewer.value, user).map((role: string) => ({
		label: __(role),
		selected: role === user.role,
		onClick: () => changeRole(user, role),
	}));
}

async function changeRole(user: CrmUser, role: string) {
	if (role === user.role) return;
	try {
		await runMethod(
			"crm.api.user.update_user_role",
			{ user: user.name, new_role: role },
			{ nullable: true }
		);
		toast.success(__("{0} is now {1}", [user.full_name || user.name, __(role)]));
	} catch (failure) {
		toast.error((failure as Error).message);
	}
	await load();
}

function confirmRemove(user: CrmUser) {
	dialog.confirm({
		title: __("Remove {0} from CRM?", [user.full_name || user.name]),
		message: __("They lose their CRM roles and their place in the sales hierarchy."),
		confirmLabel: __("Remove"),
		theme: "red",
		onConfirm: async () => {
			await runMethod(
				"crm.api.user.remove_crm_roles_from_user",
				{ user: user.name },
				{ nullable: true }
			);
			toast.success(__("{0} was removed from CRM", [user.full_name || user.name]));
			await load();
		},
	});
}
</script>
