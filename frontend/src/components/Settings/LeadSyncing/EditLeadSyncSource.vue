<template>
    <div class="flex h-full flex-col gap-6 p-8 text-ink-gray-8">
        <!-- Header -->
        <div class="flex justify-between">
            <div class="flex gap-1 -ml-4 w-9/12">
                <Button variant="ghost" icon-left="chevron-left" :label="__(source.name)" size="md"
                    @click="() => emit('updateStep', 'source-list')"
                    class="cursor-pointer hover:bg-transparent focus:bg-transparent focus:outline-none focus:ring-0 focus:ring-offset-0 focus-visible:none active:bg-transparent active:outline-none active:ring-0 active:ring-offset-0 active:text-ink-gray-5 font-semibold text-xl hover:opacity-70 !pr-0 !max-w-96 !justify-start" />

                <div class="w-fit ml-1">
                    <EmailProviderIcon :logo="sourceIcon[source.type]" />
                </div>
            </div>
            <div class="flex item-center space-x-4 w-3/12 justify-end">
                <div v-if="leadSyncSourceDoc.doc" class="flex items-center space-x-2">
                    <Switch size="sm" v-model="leadSyncSourceDoc.doc.enabled" />
                    <span class="text-sm text-ink-gray-7">{{ __('Enabled') }}</span>
                </div>
                <Button :label="__('Update')" icon-left="edit" variant="solid" :loading="sources.setValue.loading"
                    @click="updateSource" />
            </div>
        </div>

        <!-- Form -->
        <div v-if="leadSyncSourceDoc.doc">
            <div class="grid grid-cols-1 gap-4">
                <div v-for="field in fbSourceFields" :key="field.name" class="flex flex-col gap-1">
                    <FormControl v-model="leadSyncSourceDoc.doc[field.name]" :label="field.label" :name="field.name"
                        :type="field.type" :placeholder="field.placeholder" />
                </div>
            </div>
        </div>

        <div class="grid sm:grid-cols-2 gap-4">
            <Link
                label="Facebook Page"
                doctype="Facebook Page"
                v-model="leadSyncSourceDoc.doc.facebook_page" 
            />

             <Link
                label="Facebook Lead Form"
                doctype="Facebook Lead Form"
                v-model="leadSyncSourceDoc.doc.facebook_lead_form" 
                :filters="{
                    page: leadSyncSourceDoc.doc.facebook_page
                }"
            />
        </div>

        <!-- Mapping Table -->
         <div v-if="formDoc.doc">
             <Grid
                 v-model="formDoc.doc.questions"
                 v-model:parent="formDoc.doc"
                 doctype="Facebook Lead Form Question"
                 parentDoctype="Facebook Lead Form"
                 parentFieldname="questions"
                 :overrides="{
                    fields: [
                        {'fieldname': 'mapped_to_crm_field', 'options': getCRMLeadFields, 'placeholder': __('Not Synced')}
                    ]
                 }"
              />
         </div>
    </div>
</template>
<script setup>
import { Switch, createResource } from "frappe-ui";
import { useDocument } from "@/data/document";
import { computed, inject, onMounted, ref } from "vue";
import Grid from "@/components/Controls/Grid.vue";
import { fbSourceFields } from "./leadSyncSourceConfig";
import { sourceIcon } from "./leadSyncSourceConfig";
import EmailProviderIcon from "../EmailProviderIcon.vue";
import Link from "@/components/Controls/Link.vue";

const emit = defineEmits();
const props = defineProps({
	sourceData: {
		type: Object,
		required: true,
	},
});

const sources = inject("sources");
const source = ref({});

onMounted(() => {
	source.value = { ...props.sourceData };
});

const { document: leadSyncSourceDoc } = useDocument(
	"Lead Sync Source",
	props.sourceData.name,
);
const { document: formDoc } = useDocument(
	"Facebook Lead Form",
	props.sourceData.facebook_lead_form,
);

function updateSource() {
	leadSyncSourceDoc.save.submit();
	formDoc.save.submit();
}

const fields = createResource({
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
		console.log("data", data);
		return data.filter((field) => !restrictedFields.includes(field.fieldname));
	},
});

const getCRMLeadFields = computed(() => {
	if (fields.data) {
		return fields.data.map((field) => ({
			label: field.label,
			value: field.fieldname,
		}));
	}
	return [];
});
</script>