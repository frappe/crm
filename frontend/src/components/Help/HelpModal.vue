<template>
  <div
    v-show="show"
    class="fixed z-50 right-0 w-80 h-[calc(100%_-_80px)] text-ink-gray-9 m-5 mt-[62px] p-3 flex gap-2 flex-col justify-between rounded-lg bg-surface-modal shadow-2xl"
    :class="{ 'top-[calc(100%_-_120px)] border': minimize }"
    @click.stop
  >
    <div class="flex items-center justify-between px-2 py-1.5">
      <div class="text-base font-medium">
        {{ headingTitle }}
      </div>
      <div class="flex gap-1">
        <Dropdown v-if="options.length" :options="options">
          <Button variant="ghost" icon="more-horizontal" />
        </Dropdown>
        <Button variant="ghost" @click="minimize = !minimize">
          <component
            :is="minimize ? MaximizeIcon : MinimizeIcon"
            class="h-3.5"
          />
        </Button>
        <Button variant="ghost" @click="show = false">
          <FeatherIcon name="x" class="h-3.5" />
        </Button>
      </div>
    </div>
    <div class="h-full overflow-hidden flex flex-col">
      <OnboardingSteps
        v-if="!isOnboardingStepsCompleted && !showHelpCenter"
        :title="title"
        :logo="logo"
        :afterSkip="afterSkip"
        :afterSkipAll="afterSkipAll"
        :afterReset="afterReset"
        :afterResetAll="afterResetAll"
        :appName="appName"
      />
      <HelpCenter
        v-else-if="showHelpCenter"
        v-model="articles"
        :docsLink="docsLink"
      />
    </div>
    <div
      v-for="item in footerItems"
      :key="item.label"
      class="flex flex-col gap-1.5"
    >
      <div
        class="w-full flex gap-2 items-center hover:bg-surface-gray-1 text-ink-gray-8 rounded px-2 py-1.5 cursor-pointer"
        @click="item.onClick"
      >
        <component :is="item.icon" class="h-4" />
        <div class="text-base">{{ item.label }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import Dropdown from '@/components/frappe-ui/Dropdown.vue'
import HelpCenter from '@/components/Help/HelpCenter.vue'
import HelpIcon from '@/components/Icons/HelpIcon.vue'
import MaximizeIcon from '@/components/Icons/MaximizeIcon.vue'
import MinimizeIcon from '@/components/Icons/MinimizeIcon.vue'
import StepsIcon from '@/components/Icons/StepsIcon.vue'
import OnboardingSteps from '@/components/Onboarding/OnboardingSteps.vue'
import { Button, FeatherIcon } from 'frappe-ui'
import { minimize, showHelpCenter, useOnboarding } from 'frappe-ui/frappe'
import { computed, onMounted } from 'vue'

const props = defineProps({
  appName: {
    type: String,
    default: 'frappecrm',
  },
  title: {
    type: String,
    default: 'Frappe CRM',
  },
  logo: {
    type: Object,
    required: true,
  },
  afterSkip: {
    type: Function,
    default: () => {},
  },
  afterSkipAll: {
    type: Function,
    default: () => {},
  },
  afterReset: {
    type: Function,
    default: () => {},
  },
  afterResetAll: {
    type: Function,
    default: () => {},
  },
  docsLink: {
    type: String,
    default: 'https://docs.frappe.io/crm',
  },
})

const { syncStatus, resetAll, isOnboardingStepsCompleted } = useOnboarding(
  props.appName,
)

const show = defineModel({
  type: Boolean,
  default: false,
})
const articles = defineModel('articles', {
  type: Array,
  default: () => [],
})

const headingTitle = computed(() => {
  if (!isOnboardingStepsCompleted.value && !showHelpCenter.value) {
    return __('Getting started')
  }
  if (showHelpCenter.value) {
    return __('Help center')
  }
  return ''
})

const options = computed(() => {
  const items = [
    {
      icon: StepsIcon,
      label: __('Reset onboarding steps'),
      onClick: resetOnboardingSteps,
      condition: () => showHelpCenter.value && isOnboardingStepsCompleted.value,
    },
  ]

  return items.filter((item) => item.condition())
})

const footerItems = computed(() => {
  const items = [
    {
      icon: HelpIcon,
      label: __('Help centre'),
      onClick: () => {
        syncStatus()
        showHelpCenter.value = true
      },
      condition: !isOnboardingStepsCompleted.value && !showHelpCenter.value,
    },
    {
      icon: StepsIcon,
      label: __('Getting started'),
      onClick: () => {
        showHelpCenter.value = false
      },
      condition: showHelpCenter.value && !isOnboardingStepsCompleted.value,
    },
  ]

  return items.filter((item) => item.condition)
})

function resetOnboardingSteps() {
  resetAll()
  isOnboardingStepsCompleted.value = false
  showHelpCenter.value = false
}

onMounted(() => {
  if (isOnboardingStepsCompleted.value) {
    showHelpCenter.value = true
  }
})
</script>
