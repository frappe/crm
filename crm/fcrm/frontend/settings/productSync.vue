<!-- ERPNext product sync: the two-way switch, the sync status read on open and after a sync, and Sync now. -->
<template>
	<div v-if="settings.loading" aria-hidden="true">
		<div
			v-for="row in 2"
			:key="row"
			class="flex items-center gap-8 border-b border-outline-gray-1 py-3.5 last:border-b-0"
		>
			<Skeleton class="h-4 w-36 rounded-1" />
			<Skeleton class="ml-auto h-7 w-24 rounded-4" />
		</div>
	</div>
	<p v-else-if="!settings.meta" class="py-3.5 text-base text-ink-red-7">
		{{ __("{0} could not load: {1}", [__(DOCTYPE), settings.error]) }}
	</p>
	<p v-else-if="!available" class="py-3.5 text-base text-ink-gray-5">
		{{ __("Product sync runs once the integration is on and ERPNext is on this site.") }}
	</p>
	<template v-else>
		<div
			v-if="twoWay"
			data-fieldname="sync_products"
			class="border-b border-outline-gray-1"
		>
			<SettingsRow
				:title="__('Bidirectional product sync')"
				:description="
					__(
						'ERPNext items always sync into CRM products. Turn this on to also sync CRM product changes back to ERPNext items.'
					)
				"
			>
				<Switch
					:model-value="!!settings.doc.sync_products"
					:disabled="twoWay.readOnly"
					@update:model-value="toggle"
				/>
			</SettingsRow>
		</div>
		<SettingsRow
			:title="__('Products')"
			:description="error || countsLine(status) || __('Reading the sync status…')"
		>
			<div class="flex items-center gap-2">
				<Button
					icon="lucide-rotate-cw"
					variant="ghost"
					:label="__('Read again')"
					:tooltip="__('Read again')"
					:loading="reading"
					@click="read"
				/>
				<Button
					:label="__('Sync now')"
					icon-left="lucide-refresh-cw"
					:disabled="unsaved"
					:tooltip="unsaved ? __('Save the change first') : undefined"
					:loading="syncing"
					@click="syncNow"
				/>
			</div>
		</SettingsRow>
		<p v-if="unsynced" class="rounded-4 bg-surface-gray-2 px-3 py-2 text-base text-ink-gray-6">
			{{ unsynced }}
		</p>
		<template v-if="status?.failed?.length">
			<h4 class="mt-4 text-base font-medium text-ink-gray-8">{{ __("Failed syncs") }}</h4>
			<ul class="mt-1">
				<li
					v-for="issue in status.failed"
					:key="issue.name"
					class="border-b border-outline-gray-1 py-2.5 last:border-b-0"
				>
					<p class="truncate text-base text-ink-gray-8">{{ issue.product }}</p>
					<p class="text-sm text-ink-gray-5">{{ issue.detail }}</p>
				</li>
			</ul>
		</template>
		<ErrorMessage v-if="settings.error" class="py-3.5" :message="settings.error" />
	</template>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { Button, ErrorMessage, SettingsRow, Skeleton, Switch, toast } from "frappe-ui";
import { runDocumentMethod, runMethod } from "@framework/ui/api";
import { buildLayoutFromMeta, layoutFields } from "@framework/ui/FormLayout";
import { useDocPermissions } from "@framework/ui/useDocPermissions";
import type { DoctypeMeta } from "@framework/ui/useDoctypeMeta";
import { __ } from "frappe/i18n";
import { canSync, countsLine, unsyncedLine } from "./productSync/syncStatus.js";

/** The part of the settings dialog's binding this block reads; the full shape is `ComponentBinding`. */
interface Binding {
	readonly doc: Record<string, any>;
	readonly saved: Record<string, any>;
	readonly meta: DoctypeMeta | null;
	readonly loading: boolean;
	readonly error: string;
	commit(): Promise<void>;
}

interface SyncStatus {
	products?: { count: number };
	items?: { count: number };
	failed?: { name: string; product: string; detail: string }[];
	unsynced?: { items: number; products: number; sync_products: boolean };
}

const DOCTYPE = "ERPNext CRM Settings";
const STATUS_METHOD =
	"crm.fcrm.doctype.erpnext_crm_settings.erpnext_crm_settings.get_product_sync_status";

const props = defineProps<{ bindings: { settings: Binding } }>();
const settings = props.bindings.settings;
const perms = useDocPermissions(DOCTYPE);

const status = ref<SyncStatus | null>(null);
const error = ref("");
const reading = ref(false);
const syncing = ref(false);

const available = computed(() => canSync(settings.saved));
const unsynced = computed(() => unsyncedLine(status.value));
const unsaved = computed(() => !!settings.doc.sync_products !== !!settings.saved.sync_products);

const twoWay = computed(() => {
	const field = layoutFields(buildLayoutFromMeta(settings.meta?.fields ?? [])).find(
		(field) => field.fieldname === "sync_products"
	);
	if (!field || perms.fieldAccess(field) === "none") return null;
	const writes = perms.loading.value || perms.holds("write");
	return { ...field, readOnly: !writes || perms.fieldAccess(field) === "read" };
});

// Enabling the integration starts a sync on the server, so the status is read again then.
watch(available, (on) => on && read(), { immediate: true });

function toggle(on: boolean) {
	settings.doc.sync_products = on ? 1 : 0;
	settings.commit();
}

async function read() {
	reading.value = true;
	try {
		const { data } = await runMethod<SyncStatus>(STATUS_METHOD, {}, { http: "GET" });
		status.value = data;
		error.value = data.products ? "" : __("You cannot read CRM products.");
	} catch (failure) {
		error.value = (failure as Error).message;
	} finally {
		reading.value = false;
	}
}

async function syncNow() {
	syncing.value = true;
	try {
		await runDocumentMethod(DOCTYPE, DOCTYPE, "run_product_sync");
		toast.success(__("Product sync started"));
	} catch (failure) {
		toast.error((failure as Error).message);
	} finally {
		syncing.value = false;
	}
	await read();
}
</script>
