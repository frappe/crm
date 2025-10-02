<template>
    <div class="flex flex-col h-full gap-4">
        <div role="heading" aria-level="1" class="flex flex-col gap-1">
            <h2 class="text-xl font-semibold text-ink-gray-8">
                {{ __('Setup Lead Syncing Source') }}
            </h2>
            <p class="text-sm text-ink-gray-5">
                {{ __('Choose the type of source you want to configure.') }}
            </p>
        </div>

        <!-- supported sources -->
        <div class="flex flex-wrap items-center">
            <div v-for="s in supportedSourceTypes" :key="s.name" class="flex flex-col items-center gap-1 mt-4 w-[70px]"
                @click="handleSelect(s)">
                <EmailProviderIcon :label="s.name" :logo="s.icon" :selected="selectedSourceType?.name === s?.name" />
            </div>
        </div>

        <div v-if="selectedSourceType" class="flex flex-col gap-4">
            <!-- docs -->
            <div class="flex items-center gap-2 p-2 rounded-md ring-1 ring-outline-gray-3 text-ink-gray-6">
                <CircleAlert class="w-5 h-6 w-min-5 w-max-5 min-h-5 max-w-5" />
                <div class="text-xs text-wrap">
                    {{ selectedSourceType.info }}
                    <a :href="selectedSourceType.link" target="_blank" class="underline">
                        {{ __('here') }}
                    </a>.
                </div>
            </div>

            <!-- Form -->
            <div v-if="selectedSourceType.name === 'Facebook'" class="flex flex-col gap-4">
                <div class="grid grid-cols-1 gap-4">
                    <div v-for="field in fbSourceFields" :key="field.name" class="flex flex-col gap-1">
                        <FormControl v-model="syncSource[field.name]" :label="field.label" :name="field.name"
                            :type="field.type" :placeholder="field.placeholder" />
                    </div>
                </div>
            </div>
        </div>

        <!-- action button -->
        <div v-if="selectedSourceType" class="flex justify-between mt-auto">
            <Button :label="__('Back')" variant="outline" :disabled="sources.insert.loading"
                @click="emit('updateStep', 'source-list')" />
            <Button :label="__('Create')" variant="solid" :loading="sources.insert.loading"
                @click="createLeadSyncSource" />
        </div>
    </div>
</template>


<script setup>
import { ref, inject, onMounted } from "vue";
import { FormControl, toast } from "frappe-ui";
import CircleAlert from "~icons/lucide/circle-alert";
import { supportedSourceTypes } from "./leadSyncSourceConfig";
import EmailProviderIcon from "../EmailProviderIcon.vue";

const syncSource = ref({
    name: "",
    type: "",
    access_token: "",
});

const emit = defineEmits()

const props = defineProps({
  sourceData: {
    type: Object,
    default: () => ({}),
  },
})

const selectedSourceType = ref(supportedSourceTypes[0]);
syncSource.value.type = selectedSourceType.value.name;

const sources = inject("sources");
const fbSourceFields = [
    {
        name: "name",
        label: __("Name"),
        type: "text",
        placeholder: __("Add a name for your source"),
    },
    {
        name: "access_token",
        label: __("Access Token"),
        type: "password",
        placeholder: __("Enter your Facebook Access Token"),
    },
];

function handleSelect(sourceType) {
    selectedSourceType.value = sourceType;
    syncSource.value.type = sourceType.name;
}

function createLeadSyncSource() {
    sources.insert.submit({
        ...syncSource.value
    }, {
        onSuccess: () => {
            toast.success(__('New Lead Syncing Source created successfully'))
            emit('updateStep', 'edit-source', { ...syncSource.value })
        },
        onError: (error) => {
            toast.error(error.messages[0] || __('Failed to create source'))
        },
    })
}


onMounted(() => {
  if (props.sourceData?.name) {
    Object.assign(syncSource.value, props.sourceData)
    syncSource.value.name = `${syncSource.value.name} - Copy`
    syncSource.value.enabled = false // Default to disabled
  }
})
</script>