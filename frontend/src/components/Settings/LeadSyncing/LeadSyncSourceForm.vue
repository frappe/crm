<template>
	<div class="flex h-full flex-col text-ink-gray-8">
		<!-- Header -->
		<div class="flex justify-between px-2 pt-2">
			<div class="flex gap-1 -ml-4 w-9/12">
				<Button variant="ghost" icon-left="chevron-left"
					:label="isLocal ? __('New lead sync source') : syncSource.name" size="md"
					@click="() => emit('updateStep', 'source-list')"
					class="cursor-pointer hover:bg-transparent focus:bg-transparent focus:outline-none focus:ring-0 focus:ring-offset-0 focus-visible:none active:bg-transparent active:outline-none active:ring-0 active:ring-offset-0 active:text-ink-gray-5 font-semibold text-xl hover:opacity-70 !pr-0 !max-w-96 !justify-start" />
			</div>
			<div class="flex item-center space-x-4 w-3/12 justify-end">
				<div class="flex items-center space-x-2">
					<Switch size="sm" v-model="syncSource.enabled" />
					<span class="text-sm text-ink-gray-7">{{ __('Enabled') }}</span>
				</div>

				<Button v-if="!isLocal && docResource?.document?.syncLeads" :label="__('Sync now')" variant="outline"
					:loading="docResource?.document?.syncLeads.loading"
					@click="docResource?.document?.syncLeads.submit()" />

				<Button :label="isLocal ? __('Create') : __('Update')" icon-left="plus" variant="solid"
					:loading="sources.setValue.loading || sources.insert.loading || docResource?.loading"
					@click="createOrUpdateSource" />
			</div>
		</div>

		<Tabs as="div" v-model="tabIndex" :tabs="tabs" class="mt-2">
			<template #tab-panel="{ tab }">
				<div v-if="tab.label == 'Details'" class="overflow-hidden flex h-full flex-col gap-6 mt-4">
					<!-- Form -->
					<div class="grid grid-cols-2 gap-4">
						<FormControl type="autocomplete" required="true" v-model="syncSource.type"
							:options="supportedSourceTypes" :label="__('Source type')"
							:placeholder="__('Select source type')">
							<template v-if="syncSource.type" #prefix>
								<component class="mr-2 size-4" :is="syncSource.type.icon" />
							</template>

							<template #item-prefix="{ option }">
								<component class="size-4" :is="option.icon" />
							</template>
						</FormControl>

						<FormControl type="text" v-if="isLocal" required="true" v-model="syncSource.name"
							:label="__('Source name')" :placeholder="__('Enter source name')" />


						<FormControl v-if="fieldsMap.background_sync_frequency" type="select" required="true"
							:options="fieldsMap.background_sync_frequency.options"
							v-model="syncSource.background_sync_frequency" :label="__('Background sync frequency')" />

						<FormControl type="password" required="true" v-model="syncSource.access_token"
							:label="__('Access token')" :placeholder="__('Enter access token')">
							<template #suffix>
								<a target="_blank"
									href="https://developers.facebook.com/docs/facebook-login/guides/access-tokens/">
									<LucideCircleQuestionMark class="w-4" />
								</a>
							</template>
						</FormControl>

						<FormControl v-if="!isLocal && sourceDoc && sourceDoc.last_synced_at"
							:modelValue="formatDate(sourceDoc.last_synced_at)" disabled type="datetime" :label="__('Last synced at')" />

						<Link v-if="!isLocal" label="Facebook Page" v-model="syncSource.facebook_page"
							doctype="Facebook Page" />

						<Link v-if="!isLocal && syncSource.facebook_page" label="Lead Form"
							v-model="syncSource.facebook_lead_form" doctype="Facebook Lead Form" :filters="{
								'page': syncSource.facebook_page
							}" />
					</div>

					<!-- Mapping Grid -->
					<div
						v-if="syncSource.facebook_lead_form && mappingFormDocResource && mappingFormDocResource.document?.doc">
						<Grid v-model="mappingFormDocResource.document.doc.questions"
							v-model:parent="mappingFormDocResource.document.doc" doctype="Facebook Lead Form Question"
							parentDoctype="Facebook Lead Form" parentFieldname="questions" :overrides="{
								fields: [
									{ 'fieldname': 'mapped_to_crm_field', 'options': getCRMLeadFields, 'placeholder': __('Not synced') }
								]
							}" />
					</div>
				</div>

				<div class="mt-4" v-if="tab.label == 'Failure Logs'">
					<FailureLogs :source="syncSource.name" />
				</div>
			</template>
		</Tabs>

		<ErrorMessage :message="docResource?.document?.syncLeads.error" />
	</div>
</template>

<script setup>
import { useDocument } from "@/data/document";
import { onMounted, inject, ref, computed, watch } from "vue";
import { supportedSourceTypes } from "./leadSyncSourceConfig";
import {
	Button,
	FormControl,
	Switch,
	toast,
	createResource,
	ErrorMessage,
	Tabs
} from "frappe-ui";

import { getMeta } from "@/stores/meta";
import Link from "@/components/Controls/Link.vue";
import Grid from "@/components/Controls/Grid.vue";
import LucideCircleQuestionMark from '~icons/lucide/circle-question-mark';
import FailureLogs from "./FailureLogs.vue";
import DetailsIcon from '@/components/Icons/DetailsIcon.vue'
import RefreshIcon from '@/components/Icons/RefreshIcon.vue'
import {formatDate} from "@/utils";

const props = defineProps({
	sourceData: {
		type: Object,
		default: () => ({}),
	},
});
const emit = defineEmits(["updateStep"]);

const tabs = computed(() => {
	const tabList = [
		{
			label: __('Details'),
			icon: DetailsIcon
		}
	]

	if (!isLocal.value) {
		tabList.push({
			label: __('Failure logs'),
			icon: RefreshIcon
		})
	}

	return tabList;
})

const tabIndex = ref(0);

const docResource = ref(null);
const mappingFormDocResource = ref(null);

const sourceDoc = computed(() => {
	if (!docResource.value) return;
	return docResource.value?.document?.doc;
});

const { meta, getFields } = getMeta("Lead Sync Source");
const fields = ref(getFields());

watch(
	() => meta.data,
	() => {
		fields.value = getFields();
	},
);

const fieldsMap = computed(() => {
	if (!fields.value) return {};

	const map = {};
	for (const field of fields.value) {
		map[field.fieldname] = field;
	}
	return map;
});

const sources = inject("sources");
const syncSource = ref({
	name: "",
	type: "",
	access_token: "",
	facebook_page: "",
	facebook_lead_form: "",
	enabled: true,
	background_sync_frequency:
		fieldsMap.value.background_sync_frequency?.default || "Hourly",
});

const isLocal = ref(true);

function updateSource(data) {
	sources.setValue.submit(
		{
			name: syncSource.value.name,
			...data,
		},
		{
			onSuccess: () => {
				if (docResource.value) {
					docResource.value.document.reload();
				}

				mappingFormDocResource.value.document.save.submit();
			},
			onError(e) {
				toast.error(e.messages[0] || __("Error updating Lead sync source"));
			},
		},
	);
}

function createSource() {
	sources.insert.submit(
		{
			...syncSource.value,
			type: syncSource.value.type.value,
		},
		{
			onSuccess: (newDoc) => {
				toast.success(__("Lead sync source created successfully"));
				isLocal.value = false;
				docResource.value = getSourceDocResource(newDoc.name);
			},
			onError(error) {
				toast.error(error.messages[0] || __("Error creating lead sync source"));
			},
		},
	);
}

function createOrUpdateSource() {
	if (isLocal.value) {
		createSource();
	} else {
		updateSource({
			...syncSource.value,
			type: syncSource.value.type.value,
		});
	}
}

onMounted(() => {
	if (props.sourceData?.name) {
		Object.assign(syncSource.value, props.sourceData);
		isLocal.value = false; // edit form
		docResource.value = getSourceDocResource(props.sourceData.name);
	}

	if (syncSource.value.facebook_lead_form) {
		mappingFormDocResource.value = useDocument(
			"Facebook Lead Form",
			syncSource.value.facebook_lead_form,
		);
	}
});

watch(
	() => sourceDoc.value,
	(newDoc) => {
		if (newDoc) {
			Object.assign(syncSource.value, {
				...newDoc,
				type:
					supportedSourceTypes.find((type) => type.value === newDoc.type) ||
					newDoc.type,
			});

			mappingFormDocResource.value = useDocument(
				"Facebook Lead Form",
				syncSource.value.facebook_lead_form,
			);
		}
	},
);

watch(
	() => syncSource.value.facebook_page,
	(_, oldValue) => {
		if (!oldValue) return; // on mount, the value changes from empty
		syncSource.value.facebook_lead_form = "";
	},
);

watch(
	() => syncSource.value.facebook_lead_form,
	(newVal) => {
		if (newVal) {
			mappingFormDocResource.value = useDocument(
				"Facebook Lead Form",
				newVal,
			);
		} else {
			mappingFormDocResource.value = null;
		}
	},
);

const leadFields = createResource({
	url: "crm.api.doc.get_fields_meta",
	params: {
		doctype: "CRM Lead",
		as_array: true,
	},
	cache: ["fieldsMeta", "CRM Lead"],
	auto: true,
	transform: (data) => {
		let restrictedFields = [
			"name",
			"owner",
			"creation",
			"modified",
			"modified_by",
			"docstatus",
			"_comments",
			"_user_tags",
			"_assign",
			"_liked_by",
		];
		return data.filter((field) => !restrictedFields.includes(field.fieldname));
	},
});

const getCRMLeadFields = computed(() => {
	if (leadFields.data) {
		return leadFields.data.map((field) => ({
			label: field.label,
			value: field.fieldname,
		}));
	}
	return [];
});

function getSourceDocResource(name) {
	return useDocument("Lead Sync Source", name, {
		whitelistedMethods: {
			syncLeads: {
				method: 'sync_leads',
				onSuccess() {
					toast.success(__("Syncing started in background"))
				},
				onError(e) {
					toast.error((e.messages ?? e.messages[0]) || __("Error syncing leads"))
				}
			}
		}
	})
}
</script>