<template>
  <SetupImport
    v-if="importing"
    @imported="onImported"
    @cancel="importing = false"
  />
  <div v-else class="flex flex-col">
    <h1 class="text-2xl-semibold text-ink-gray-9">
      {{ __('Bring in your leads') }}
    </h1>
    <p class="mt-2 text-p-base text-ink-gray-6">
      {{
        __(
          'Start with the leads you already have, or explore the CRM with sample data first.',
        )
      }}
    </p>
    <div class="mt-8 grid gap-3 sm:grid-cols-2">
      <button
        v-for="option in options"
        :key="option.name"
        type="button"
        class="flex flex-col items-start gap-2 rounded-7 border p-4 text-left transition-colors hover:bg-surface-gray-1"
        :class="
          selected === option.name
            ? 'border-outline-gray-4 bg-surface-gray-1'
            : 'border-outline-gray-2'
        "
        :aria-pressed="
          option.name === 'sample' ? selected === 'sample' : undefined
        "
        @click="option.onClick"
      >
        <component :is="option.icon" class="size-5 text-ink-gray-7" />
        <span class="text-base font-medium text-ink-gray-9">
          {{ option.title }}
        </span>
        <span class="text-p-sm text-ink-gray-6">{{ option.description }}</span>
      </button>
    </div>
    <div class="mt-auto flex items-center justify-between pt-8">
      <Button
        variant="ghost"
        :label="__('I\'ll add leads later')"
        @click="emit('skip')"
      />
      <Button
        variant="solid"
        :label="__('Continue')"
        :disabled="selected !== 'sample'"
        @click="continueWithSample"
      />
    </div>
  </div>
</template>

<script setup>
import LucideFileUp from '~icons/lucide/file-up'
import LucideSparkles from '~icons/lucide/sparkles'
import SetupImport from '@/components/Setup/SetupImport.vue'
import { useCrmOnboarding } from '@/composables/onboarding'
import { useDemoData } from '@/composables/demoData'
import { Button, call, toast } from 'frappe-ui'
import { ref } from 'vue'

const emit = defineEmits(['done', 'skip'])

const { completeStep } = useCrmOnboarding()
const { isDemoDataCreated } = useDemoData()

const importing = ref(false)
const selected = ref(null)

const options = [
  {
    name: 'csv',
    icon: LucideFileUp,
    title: __('Import from CSV'),
    description: __('Upload a spreadsheet of your existing leads.'),
    onClick: () => (importing.value = true),
  },
  {
    name: 'sample',
    icon: LucideSparkles,
    title: __('Try with sample data'),
    description: __(
      'Explore with sample leads, deals and tasks. Clear them anytime.',
    ),
    onClick: () =>
      (selected.value = selected.value === 'sample' ? null : 'sample'),
  },
]

function continueWithSample() {
  loadSampleData()
  emit('done', { source: 'sample_data' })
}

// Runs in the background so the user isn't held on this step.
async function loadSampleData() {
  try {
    await call('run_doc_method', {
      dt: 'FCRM Settings',
      dn: 'FCRM Settings',
      method: 'restore_demo_data',
    })
    isDemoDataCreated.value = true
  } catch (error) {
    toast.error(error.messages?.[0] || __('Could not load sample data'))
  }
}

function onImported(result) {
  completeStep('create_first_lead')
  emit('done', { source: 'csv', imported: result.imported })
}
</script>
