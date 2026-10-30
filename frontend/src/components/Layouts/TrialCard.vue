<template>
  <SidebarCard
    v-if="content"
    :theme="content.theme"
    :title="content.title"
    :description="content.description"
    :dismissible="content.dismissible"
    :action="{ label: content.action, loading: opening, onClick: open }"
    @dismiss="dismiss"
  />
</template>

<script setup>
import { useCloudSettings } from '@/composables/cloudSettings'
import { useTrialCard } from '@/composables/trialCard'
import { trialCardContent } from '@/utils/trialCard'
import { SidebarCard } from 'frappe-ui'
import { computed } from 'vue'

const { trial, dismiss } = useTrialCard()
const { opening, open } = useCloudSettings()

const content = computed(() => trial.value && trialCardContent(trial.value))
</script>
