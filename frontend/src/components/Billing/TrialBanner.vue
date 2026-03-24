<template>
  <div
    v-if="!isSidebarCollapsed && showBanner"
    class="flex flex-col gap-3 shadow-sm rounded-lg py-2.5 px-3 bg-surface-modal text-base"
  >
    <div class="flex flex-col gap-1">
      <div class="inline-flex text-ink-gray-9 gap-2 items-center font-medium">
        <FeatherIcon class="h-4" name="info" />
        {{ trialTitle }}
      </div>
      <div class="text-ink-gray-7 text-p-sm">
        {{ trialMessage }}
      </div>
    </div>
    <Button :label="__('Upgrade plan')" theme="blue" @click="upgradePlan">
      <template #prefix>
        <LightningIcon class="size-4" />
      </template>
    </Button>
  </div>
  <Button v-else-if="isSidebarCollapsed && showBanner" @click="upgradePlan">
    <LightningIcon class="h-4 my-0.5 shrink-0" />
  </Button>
</template>

<script setup>
import LightningIcon from '@/components/Icons/LightningIcon.vue'
import { Button, FeatherIcon, createResource } from 'frappe-ui'
import { computed, ref } from 'vue'

const props = defineProps({
  isSidebarCollapsed: {
    type: Boolean,
    default: false,
  },
  afterUpgrade: {
    type: Function,
    default: () => {},
  },
})

const trialEndDays = ref(0)
const showBanner = ref(false)
const baseEndpoint = ref('https://frappecloud.com')
const siteName = ref('')

const trialTitle = computed(() => {
  if (trialEndDays.value > 1) {
    return __('Trial ends in {0} days', [trialEndDays.value])
  }
  return __('Trial ends tomorrow')
})

const trialMessage = computed(() => {
  return __('Upgrade to a paid plan for uninterrupted services')
})

createResource({
  url: 'frappe.integrations.frappe_providers.frappecloud_billing.current_site_info',
  cache: 'current_site_info_data',
  auto: true,
  onSuccess: (data) => {
    trialEndDays.value = calculateTrialEndDays(data.trial_end_date)
    baseEndpoint.value = data.base_url
    siteName.value = data.site_name
    showBanner.value = data.plan.is_trial_plan && trialEndDays.value > 0
  },
})

function calculateTrialEndDays(trialEndDate) {
  if (!trialEndDate) return 0

  const parsedTrialEndDate = new Date(trialEndDate)
  const today = new Date()
  const diffTime = parsedTrialEndDate - today
  return Math.ceil(diffTime / (1000 * 60 * 60 * 24))
}

function upgradePlan() {
  window.open(
    `${baseEndpoint.value}/dashboard/sites/${siteName.value}`,
    '_blank',
  )
  props.afterUpgrade?.()
}
</script>
