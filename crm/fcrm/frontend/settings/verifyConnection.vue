<!-- ERPNext connection check: asks ERPNext, on this site or the saved one, and names the URL, key or company that is wrong. -->
<template>
	<div v-if="settings.loading" aria-hidden="true">
		<div class="flex items-center gap-8 py-3.5">
			<Skeleton class="h-4 w-36 rounded-1" />
			<Skeleton class="ml-auto h-7 w-28 rounded-4" />
		</div>
	</div>
	<p v-else-if="!settings.meta" class="py-3.5 text-base text-ink-red-7">
		{{ __("{0} could not load: {1}", [__(DOCTYPE), settings.error]) }}
	</p>
	<template v-else>
		<SettingsRow
			:title="__('Saved connection')"
			:description="
				__('Checks ERPNext on this site, or the URL, keys and company of the other site.')
			"
		>
			<Button
				:label="__('Verify connection')"
				icon-left="lucide-plug-zap"
				:disabled="unsaved"
				:tooltip="unsaved ? __('Save the change first') : undefined"
				:loading="checking"
				@click="verify"
			/>
		</SettingsRow>
		<Alert
			v-if="result"
			class="mt-2"
			:theme="result.state === 'verified' ? 'green' : 'red'"
			:title="result.title"
			:description="result.description || undefined"
		/>
		<ul v-if="result?.companies" class="mt-2" data-test="found-companies">
			<li
				v-for="company in result.companies"
				:key="company"
				class="border-b border-outline-gray-1 py-2 text-base text-ink-gray-8 last:border-b-0"
			>
				{{ company }}
			</li>
		</ul>
	</template>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { Alert, Button, SettingsRow, Skeleton } from "frappe-ui";
import { runDocumentMethod } from "@framework/ui/api";
import type { DoctypeMeta } from "@framework/ui/useDoctypeMeta";
import { __ } from "frappe/i18n";
import { verifyConnection } from "./verifyConnection/outcome.js";

/** The part of the settings dialog's binding this block reads; the full shape is `ComponentBinding`. */
interface Binding {
	readonly doc: Record<string, any>;
	readonly saved: Record<string, any>;
	readonly meta: DoctypeMeta | null;
	readonly loading: boolean;
	readonly error: string;
}

const DOCTYPE = "ERPNext CRM Settings";
const CONNECTION_FIELDS = [
	"is_erpnext_in_different_site",
	"erpnext_site_url",
	"api_key",
	"api_secret",
	"erpnext_company",
];

const props = defineProps<{ bindings: { settings: Binding } }>();
const settings = props.bindings.settings;

const result = ref<Awaited<ReturnType<typeof verifyConnection>> | null>(null);
const checking = ref(false);

// The methods read the saved document, so a changed field would be checked against its old value.
const unsaved = computed(() =>
	CONNECTION_FIELDS.some((field) => (settings.doc[field] || "") !== (settings.saved[field] || ""))
);
const savedConnection = () => CONNECTION_FIELDS.map((field) => settings.saved[field]).join("\n");
watch(savedConnection, () => (result.value = null));

/** A remote site that never answers would hold the button and a server worker. */
const ANSWER_WITHIN_MS = 30_000;

async function verify() {
	const before = savedConnection();
	const controller = new AbortController();
	const timer = setTimeout(() => controller.abort(), ANSWER_WITHIN_MS);
	const callMethod = async <T,>(method: string) =>
		(await runDocumentMethod<T>(DOCTYPE, DOCTYPE, method, {}, { signal: controller.signal })).data;
	checking.value = true;
	try {
		const outcome = await verifyConnection(settings.saved, {
			isInstalled: () => callMethod<boolean>("is_erpnext_installed"),
			companies: () => callMethod<{ company_name: string }[]>("get_external_companies"),
		});
		// A save made while the site was answering leaves this outcome about the old connection.
		if (savedConnection() === before) result.value = outcome;
	} finally {
		clearTimeout(timer);
		checking.value = false;
	}
}
</script>
