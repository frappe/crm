<template>
  <div class="flex-1 flex flex-col">
    <div class="flex gap-4 items-center justify-between py-3">
      <div class="flex flex-col">
        <div class="text-p-base-medium text-ink-gray-7 truncate">
          {{ __('Enable enrichment') }}
        </div>
        <div class="text-p-sm text-ink-gray-5">
          {{
            __(
              'Fill in company details on Leads, Deals and Organizations from their website.',
            )
          }}
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

    <template v-if="doc.enabled">
      <div class="h-px border-t border-outline-elevation-2" />

      <div
        class="flex items-center justify-between text-lg-semibold text-ink-gray-8 mt-4 py-3"
      >
        {{ __('Crawl settings') }}
      </div>
      <div class="flex gap-4 items-start justify-between py-3">
        <div class="flex flex-col">
          <div class="text-p-base-medium text-ink-gray-7 truncate">
            {{ __('Maximum pages') }}
          </div>
          <div class="text-p-sm text-ink-gray-5">
            {{
              __(
                'Maximum number of pages that can be crawled during a single enrichment run.',
              )
            }}
          </div>
        </div>
        <div class="flex flex-col items-end">
          <!-- Not :error: it renders inside the w-24 box and gets squeezed. -->
          <FormControl
            :model-value="maxPages ?? doc.max_pages"
            type="number"
            min="1"
            :max="maxPagesLimit"
            class="w-24"
            @update:model-value="
              (value: string | number) => emit('update:maxPages', value)
            "
          />
          <ErrorMessage
            v-if="maxPagesError"
            class="mt-1 max-w-60 text-right"
            :message="maxPagesError"
          />
        </div>
      </div>

      <div class="h-px border-t border-outline-elevation-2" />

      <div
        class="flex items-center justify-between text-lg-semibold text-ink-gray-8 mt-4 py-3"
      >
        {{ __('Automation') }}
      </div>
      <div class="flex gap-4 items-center justify-between py-3">
        <div class="flex flex-col">
          <div class="text-p-base-medium text-ink-gray-7 truncate">
            {{ __('Auto-enrich new records') }}
          </div>
          <div class="text-p-sm text-ink-gray-5">
            {{
              __(
                'Automatically enrich new Leads, Deals and Organizations in the background when they have a website. When off, use the Enrich button on the record.',
              )
            }}
          </div>
        </div>
        <div>
          <Switch
            :model-value="Boolean(doc.auto_enrich)"
            size="sm"
            @update:model-value="
              (value) => emit('toggle', 'auto_enrich', value)
            "
          />
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ErrorMessage, FormControl, Switch } from 'frappe-ui'
import type { EnrichmentSettingsDoc } from './types'

// Nothing saves here: the parent holds every change (even hidden ones) until
// the header Update.
withDefaults(
  defineProps<{
    doc: EnrichmentSettingsDoc
    // Held apart from doc until Update, so half-typed input isn't stored.
    maxPages?: string | number
    maxPagesError?: string
    maxPagesLimit: number
  }>(),
  {
    maxPages: undefined,
    maxPagesError: '',
  },
)

const emit = defineEmits<{
  toggle: [fieldname: 'enabled' | 'auto_enrich', value: boolean]
  'update:maxPages': [value: string | number]
}>()
</script>
