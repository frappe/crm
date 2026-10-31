<!-- Gives existing system users a CRM role, through crm.api.user.add_existing_users. -->
<template>
	<Dialog v-model="open" :title="__('Add existing users')">
		<div class="flex flex-col gap-4">
			<TableMultiSelect
				v-model="picked"
				doctype="User"
				:filters="filters"
				:label="__('Users')"
				:placeholder="__('Search users')"
			/>
			<Select v-model="role" :label="__('Role')" :options="roleOptions" />
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
import { computed, ref } from "vue";
import { Button, Dialog, ErrorMessage, Select, toast } from "frappe-ui";
import { TableMultiSelect } from "@framework/ui";
import { runMethod } from "@framework/ui/api";
import { __ } from "frappe/i18n";

const props = defineProps<{ roles: string[]; existing: string[] }>();
const emit = defineEmits<{ added: [] }>();
const open = defineModel<boolean>({ required: true });

const picked = ref<string[]>([]);
const role = ref("Sales User");
const saving = ref(false);
const error = ref("");

const roleOptions = computed(() => props.roles.map((value) => ({ label: __(value), value })));
const filters = computed(() => ({
	enabled: 1,
	user_type: "System User",
	name: ["not in", [...props.existing, "Administrator", "Guest"]],
}));

async function add() {
	saving.value = true;
	error.value = "";
	try {
		await runMethod(
			"crm.api.user.add_existing_users",
			{ users: picked.value, role: role.value },
			{ nullable: true }
		);
		const count = picked.value.length;
		toast.success(count === 1 ? __("1 user added to CRM") : __("{0} users added to CRM", [count]));
		picked.value = [];
		open.value = false;
		emit("added");
	} catch (failure) {
		error.value = (failure as Error).message;
	} finally {
		saving.value = false;
	}
}
</script>
