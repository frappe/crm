<!-- The person's CRM Telephony Agent, with each provider's rows only while that provider is on. -->
<template>
	<div v-if="loading" aria-hidden="true">
		<div
			v-for="row in rows.length"
			:key="row"
			class="flex items-center gap-8 border-b border-outline-gray-1 py-3.5 last:border-b-0"
		>
			<Skeleton class="h-4 w-36 rounded-1" />
			<Skeleton class="ml-auto h-7 w-56 rounded-4" />
		</div>
	</div>
	<p v-else-if="!agent.meta" class="py-3.5 text-base text-ink-red-7">
		{{ __("{0} could not load: {1}", [__(DOCTYPE), agent.error]) }}
	</p>
	<template v-else>
		<p
			v-if="agent.isNew"
			class="mt-3 rounded-4 bg-surface-gray-2 px-3 py-2 text-base text-ink-gray-6"
		>
			{{ __("No {0} for you yet. The first change creates it.", [__(DOCTYPE)]) }}
		</p>
		<div
			v-for="field in fields"
			:key="field.fieldname"
			:data-fieldname="field.fieldname"
			class="border-b border-outline-gray-1 last:border-b-0"
		>
			<SettingsRow
				:title="__(field.label || field.fieldname)"
				:description="field.description && __(field.description)"
			>
				<component
					:is="getFieldComponent(field.fieldtype)"
					class="w-56"
					:field="{ ...field, label: '', description: '' }"
					:model-value="agent.doc[field.fieldname]"
					@update:model-value="(value: unknown) => (agent.doc[field.fieldname] = value)"
					@change="agent.commit()"
				/>
			</SettingsRow>
		</div>
		<ErrorMessage v-if="agent.error" class="py-3.5" :message="agent.error" />
	</template>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { ErrorMessage, SettingsRow, Skeleton } from "frappe-ui";
import { runMethod } from "@framework/ui/api";
import { buildLayoutFromMeta, getFieldComponent, layoutFields } from "@framework/ui/FormLayout";
import { useDocPermissions } from "@framework/ui/useDocPermissions";
import type { FieldNode } from "@framework/ui/FormLayout/types";
import type { DoctypeMeta } from "@framework/ui/useDoctypeMeta";
import { __ } from "frappe/i18n";
import { telephonyRows } from "./telephonyRows.js";

/** The part of the settings dialog's binding this block reads; the full shape is `ComponentBinding`. */
interface Binding {
	readonly doc: Record<string, any>;
	readonly meta: DoctypeMeta | null;
	readonly loading: boolean;
	readonly error: string;
	readonly isNew: boolean;
	commit(): Promise<void>;
}

const DOCTYPE = "CRM Telephony Agent";

const props = defineProps<{ bindings: { agent: Binding } }>();
const agent = props.bindings.agent;
const perms = useDocPermissions(DOCTYPE);

const providers = ref<Record<string, boolean> | null>(null);
// A failed read shows no provider's rows.
runMethod<{ integrations: Record<string, boolean> }>(
	"crm.integrations.api.is_call_integration_enabled",
	{},
	{ http: "GET" }
).then(
	({ data }) => (providers.value = data.integrations),
	() => (providers.value = {})
);

const loading = computed(() => agent.loading || !providers.value);
const rows = computed(() => telephonyRows(providers.value ?? {}));

/** Generated rows' rules: hidden and unreadable fields are left out, unwritable ones read-only. */
const fields = computed(() => {
	const byName = new Map(
		layoutFields(buildLayoutFromMeta(agent.meta?.fields ?? [])).map((field) => [
			field.fieldname,
			field,
		])
	);
	const writes = perms.loading.value || perms.holds("write");
	return rows.value
		.map((fieldname) => byName.get(fieldname))
		.filter((field): field is FieldNode => !!field && !field.hidden)
		.filter((field) => perms.fieldAccess(field) !== "none")
		.map((field) => ({
			...field,
			readOnly: field.readOnly || !writes || perms.fieldAccess(field) === "read",
		}));
});
</script>
