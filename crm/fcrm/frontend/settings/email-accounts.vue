<!-- The person's own email accounts, read-only: they are linked from each Email Account record. -->
<template>
	<ErrorMessage
		v-if="error !== null"
		class="py-3.5"
		:message="__('Email accounts could not load: {0}', [error])"
	/>
	<div v-else-if="!accounts" aria-hidden="true" class="mt-2">
		<div class="flex items-center gap-3 py-2.5">
			<div class="flex-1 space-y-1.5">
				<Skeleton class="h-4 w-40 rounded-1" />
				<Skeleton class="h-3.5 w-56 rounded-1" />
			</div>
			<Skeleton class="h-5 w-16 rounded-4" />
		</div>
	</div>
	<p v-else-if="!accounts.length" class="py-3.5 text-base text-ink-gray-6">
		{{ __("No email account is linked to you yet.") }}
	</p>
	<ul v-else class="mt-2">
		<li
			v-for="account in accounts"
			:key="account.email_account"
			:data-email-account="account.email_account"
			class="flex items-center gap-3 border-b border-outline-gray-1 py-2.5 last:border-b-0"
		>
			<div class="min-w-0 flex-1">
				<p class="truncate text-base text-ink-gray-8">{{ account.email_account }}</p>
				<p class="truncate text-sm text-ink-gray-5">{{ account.email_id }}</p>
			</div>
			<Badge v-if="account.awaiting_password" :label="__('Awaiting password')" theme="amber" />
			<Badge v-if="account.enable_outgoing" :label="__('Outgoing')" theme="gray" />
		</li>
	</ul>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { Badge, ErrorMessage, Skeleton } from "frappe-ui";
import { runMethod } from "@framework/ui/api";
import { __ } from "frappe/i18n";

/** A block with no binding is handed an empty `bindings`. */
defineProps<{ bindings: Record<string, never> }>();

interface EmailAccountRow {
	email_account: string;
	email_id: string;
	enable_outgoing: 0 | 1;
	awaiting_password: 0 | 1;
}

const accounts = ref<EmailAccountRow[] | null>(null);
const error = ref<string | null>(null);

// User's `user_emails` is permlevel 1, so the person's own rows come from this read, not the User doc.
runMethod<EmailAccountRow[]>(
	"frappe.email.inbox.get_own_email_accounts",
	{},
	{ http: "GET" }
).then(
	({ data }) => (accounts.value = data),
	(failure: Error) => (error.value = failure.message)
);
</script>
