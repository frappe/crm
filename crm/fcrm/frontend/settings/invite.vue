<!-- Invites people to CRM by email on frappe's User Invitation; CRM's user_invitation hook limits the roles. -->
<template>
	<div class="mt-3">
		<InviteUser
			v-bind="invitations"
			:roles="roleOptions"
			:email-props="emailProps"
			:roles-props="{ label: __('Roles'), placeholder: __('Select roles') }"
			:show-result-toasts="false"
			@invited="announce"
		>
			<template #submit="{ canSubmit, inviting }">
				<Button
					type="submit"
					variant="solid"
					class="w-fit"
					:label="__('Send invites')"
					:loading="inviting"
					:disabled="!canSubmit"
				/>
			</template>
		</InviteUser>
	</div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { Button, toast } from "frappe-ui";
import { InviteUser, useInviteUser } from "@framework/ui/InviteUser";
import type { InviteResult } from "@framework/ui/InviteUser";
import { useUserRoles } from "@framework/ui/useUserRoles";
import { __ } from "frappe/i18n";
import { crmRole, givenRoles } from "./users/crmUsers.js";

defineProps<{ bindings: Record<string, never> }>();

const invitations = useInviteUser({ appName: "crm", redirectPath: "/apps/crm" });

const { roles } = useUserRoles();
const roleOptions = computed(() =>
	givenRoles({ role: crmRole(roles.value ?? []) }).map((role: string) => ({
		label: __(role),
		value: role,
	}))
);

const emailProps = {
	label: __("Email addresses"),
	placeholder: __("Search users or type an email…"),
	emptyText: __("No matching users"),
	createLabel: (email: string) => __('Invite "{0}"', [email]),
};

function announce(result: InviteResult) {
	const list = (emails: string[]) => emails.join(", ");
	if (result.invited_emails.length)
		toast.success(__("Invitation sent to {0}", [list(result.invited_emails)]));
	if (result.pending_invite_emails.length)
		toast.info(__("Already invited: {0}", [list(result.pending_invite_emails)]));
	if (result.accepted_invite_emails.length)
		toast.info(__("Already accepted: {0}", [list(result.accepted_invite_emails)]));
	if (result.disabled_user_emails.length)
		toast.info(__("Not invited, disabled users: {0}", [list(result.disabled_user_emails)]));
}
</script>
