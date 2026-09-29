<template>
  <div class="flex-1 flex flex-col overflow-y-auto">
    <div class="flex gap-4 items-center justify-between py-3 px-2">
      <div class="flex flex-col">
        <div class="text-p-base-medium text-ink-gray-7 truncate">
          {{ __('Enrich') }}
        </div>
        <div class="text-p-sm text-ink-gray-5">
          {{ __('Master switch for the Domain Enrichment feature.') }}
        </div>
      </div>
      <div>
        <Switch
          :model-value="Boolean(doc.enabled)"
          size="sm"
          @update:model-value="(value) => emit('toggle', 'enabled', value)"
        />
      </div>
    </div>

    <div class="h-px border-t mx-2 border-outline-elevation-2" />

    <div
      class="flex items-center justify-between text-lg-semibold mt-4 py-3 px-2"
      :class="headingClass"
    >
      {{ __('Crawl settings') }}
    </div>
    <div class="flex gap-4 items-start justify-between py-3 px-2">
      <div class="flex flex-col">
        <div class="text-p-base-medium truncate" :class="labelClass">
          {{ __('Maximum pages') }}
        </div>
        <div class="text-p-sm" :class="descriptionClass">
          {{
            __(
              'Maximum number of pages that can be crawled during a single enrichment run.',
            )
          }}
        </div>
      </div>
      <div class="flex flex-col items-end">
        <FormControl
          :model-value="maxPages ?? doc.max_pages"
          type="number"
          min="1"
          :max="maxPagesLimit"
          class="w-24"
          :disabled="enrichmentOff"
          @update:model-value="(value) => emit('update:maxPages', value)"
        />
        <ErrorMessage
          v-if="maxPagesError"
          class="mt-1 max-w-60 text-right"
          :message="maxPagesError"
        />
      </div>
    </div>

    <div class="h-px border-t mx-2 border-outline-elevation-2" />

    <div
      class="flex items-center justify-between text-lg-semibold mt-4 py-3 px-2"
      :class="headingClass"
    >
      {{ __('Automation') }}
    </div>
    <div class="flex gap-4 items-center justify-between py-3 px-2">
      <div class="flex flex-col">
        <div class="text-p-base-medium truncate" :class="labelClass">
          {{ __('Auto-enrich new Organizations') }}
        </div>
        <div class="text-p-sm" :class="descriptionClass">
          {{
            __(
              'Automatically enrich a CRM Organization in the background as soon as it is created (requires a website). When off, enrichment is triggered manually via the Enrich button.',
            )
          }}
        </div>
      </div>
      <div>
        <Switch
          :model-value="Boolean(doc.auto_enrich)"
          size="sm"
          :disabled="enrichmentOff"
          @update:model-value="(value) => emit('toggle', 'auto_enrich', value)"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ErrorMessage, FormControl, Switch } from 'frappe-ui'
import { computed } from 'vue'

// The General tab's fields. Nothing here saves: every change goes up to
// EnrichmentSettings.vue, which holds it until the header Save.
const props = defineProps({
  doc: { type: Object, required: true },
  // The typed Max pages value, held apart from the doc until Save so a
  // half-typed number never counts as the stored one.
  maxPages: { type: [String, Number], default: undefined },
  maxPagesError: { type: String, default: '' },
  maxPagesLimit: { type: Number, required: true },
})

const emit = defineEmits(['toggle', 'update:maxPages'])

// The master switch gates everything under it, so those rows read as disabled
// until enrichment is on: still visible, so you can see what turning it on would
// give you, but greyed and non-interactive. The three classes below are the
// greyed-or-normal text colours for those rows' headings, titles and descriptions.
const enrichmentOff = computed(() => !props.doc.enabled)
const headingClass = computed(() =>
  enrichmentOff.value ? 'text-ink-gray-4' : 'text-ink-gray-8',
)
const labelClass = computed(() =>
  enrichmentOff.value ? 'text-ink-gray-4' : 'text-ink-gray-7',
)
const descriptionClass = computed(() =>
  enrichmentOff.value ? 'text-ink-gray-4' : 'text-ink-gray-5',
)
</script>
