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
            <div
                v-for="s in supportedSourceTypes"
                :key="s.name"
                class="flex flex-col items-center gap-1 mt-4 w-[70px]"
                @click="handleSelect(s)"
            >
                <EmailProviderIcon
                    :label="s.name"
                    :logo="s.icon"
                    :selected="selectedSourceType?.name === s?.name"
                />
            </div>
        </div>
    </div>
</template>


<script setup>
 import { computed, reactive, ref } from 'vue'
import { createResource, toast } from 'frappe-ui'
import CircleAlert from '~icons/lucide/circle-alert'
// import {
//   customProviderFields,
//   popularProviderFields,
//   services,
//   validateInputs,
//   incomingOutgoingFields,
// } from './emailConfig'
import { supportedSourceTypes } from './leadSyncSourceConfig'
import EmailProviderIcon from '../EmailProviderIcon.vue'


const selectedSourceType = ref(null)

function handleSelect(sourceType) {
  selectedSourceType.value = sourceType
//   state.service = service.name
}
</script>