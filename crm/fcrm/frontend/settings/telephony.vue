<!-- The person's CRM Telephony Agent. A provider's number shows only while that provider is on,
     as in CRM's own Telephony pane. -->
<template>
	<div v-if="loading" aria-hidden="true">
		<div
			v-for="row in 3"
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
					@change="commit(field.fieldname)"
				/>
			</SettingsRow>
			<ErrorMessage
				v-if="refused[field.fieldname]"
				class="-mt-1.5 pb-3.5"
				:message="refused[field.fieldname]"
			/>
		</div>
	</template>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from "vue";
import { ErrorMessage, SettingsRow, Skeleton } from "frappe-ui";
import { runMethod } from "@framework/ui/api";
import { buildLayoutFromMeta, getFieldComponent, layoutFields } from "@framework/ui/FormLayout";
import type { DoctypeMeta } from "@framework/ui/useDoctypeMeta";
import { __ } from "frappe/i18n";

/** The part of the settings dialog's binding this block reads; the full shape is `ComponentBinding`. */
interface Binding {
	readonly doc: Record<string, any>;
	readonly meta: DoctypeMeta | null;
	readonly loading: boolean;
	readonly error: string;
	readonly isNew: boolean;
	commit(): Promise<void>;
}

type Providers = Record<string, boolean>;

const DOCTYPE = "CRM Telephony Agent";

/** The rows in order, each with when it shows. */
const SHOWN_WHEN: Record<string, (on: Providers) => boolean> = {
	mobile_no: () => true,
	default_medium: (on) => Object.values(on).some(Boolean),
	call_receiving_device: () => true,
	twilio_number: (on) => !!on.twilio,
	exotel_number: (on) => !!on.exotel,
};

const props = defineProps<{ bindings: { agent: Binding } }>();
const agent = props.bindings.agent;

const providers = ref<Providers | null>(null);
// CRM's own pane treats a failed read as no provider on.
runMethod<{ integrations: Providers }>(
	"crm.integrations.api.is_call_integration_enabled",
	{},
	{ http: "GET" }
).then(
	({ data }) => (providers.value = data.integrations),
	() => (providers.value = {})
);

const loading = computed(() => agent.loading || !providers.value);

const fields = computed(() => {
	const byName = new Map(
		layoutFields(buildLayoutFromMeta(agent.meta?.fields ?? [])).map((field) => [
			field.fieldname,
			field,
		])
	);
	return Object.entries(SHOWN_WHEN)
		.filter(([, shown]) => shown(providers.value ?? {}))
		.map(([fieldname]) => byName.get(fieldname))
		.filter((field) => !!field);
});

const refused = reactive<Record<string, string>>({});

/** The binding's error is shared by every component on this draft, so it is read right after this block's save. */
async function commit(fieldname: string) {
	await agent.commit();
	refused[fieldname] = agent.error;
}
</script>
