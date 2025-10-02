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
                <div class="flex items-center space-x-2">
                    <Switch size="sm" v-model="source.enabled" />
                    <span class="text-sm text-ink-gray-7">{{ __('Enabled') }}</span>
                </div>
                <Button :label="__('Update')" icon-left="edit" variant="solid" :loading="sources.setValue.loading"
                    @click="updateSource" />
            </div>
        </div>
    </div>
</template>

<script setup>
import { Switch } from "frappe-ui";
import { inject, onMounted, ref } from "vue";

import { sourceIcon } from "./leadSyncSourceConfig";
import EmailProviderIcon from "../EmailProviderIcon.vue";

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

function updateSource() {}
</script>