<template>
  <div class="flex h-full flex-col gap-6 py-8 px-6 text-ink-gray-8">
    <div class="flex flex-col gap-1 px-2">
      <h2 class="flex gap-2 text-2xl-semibold leading-none h-5">
        {{ __('Enrichment') }}
      </h2>
      <p class="text-p-base text-ink-gray-6">
        {{ __('Fill in company details from a record’s website') }}
      </p>
    </div>

    <div
      v-if="settings.get.loading"
      class="flex flex-1 items-center justify-center"
    >
      <LoadingIndicator class="size-8" />
    </div>
    <div v-else class="flex-1 flex flex-col overflow-y-auto">
      <div class="flex gap-4 items-center justify-between py-3 px-2">
        <div class="flex flex-col">
          <div class="text-p-base-medium text-ink-gray-7 truncate">
            {{ __('Enable enrichment') }}
          </div>
          <div class="text-p-sm text-ink-gray-5">
            {{
              __(
                'Turn on enrichment for this site. When off, the Enrich button is hidden and no record is enriched',
              )
            }}
          </div>
        </div>
        <div>
          <Switch
            :model-value="Boolean(settings.doc.enabled)"
            size="sm"
            @update:model-value="(value) => update('enabled', value)"
          />
        </div>
      </div>
      <div class="flex gap-4 items-center justify-between py-3 px-2">
        <div class="flex flex-col">
          <div class="text-p-base-medium text-ink-gray-7 truncate">
            {{ __('Auto-enrich new records') }}
          </div>
          <div class="text-p-sm text-ink-gray-5">
            {{ __('Enrich a new record as soon as it is created') }}
          </div>
        </div>
        <div>
          <Switch
            :model-value="Boolean(settings.doc.auto_enrich)"
            size="sm"
            :disabled="!settings.doc.enabled"
            @update:model-value="(value) => update('auto_enrich', value)"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import {
  createDocumentResource,
  LoadingIndicator,
  Switch,
  toast,
} from 'frappe-ui'

const settings = createDocumentResource({
  doctype: 'CRM Enrichment Settings',
  name: 'CRM Enrichment Settings',
  auto: true,
})

// Check fields come back as 0/1, so write the same shape back -- a Boolean would
// leave the doc differing from originalDoc on every load.
function update(fieldname, value) {
  settings.doc[fieldname] = value ? 1 : 0
  settings.save.submit(null, {
    onSuccess: () =>
      toast.success(
        value
          ? __('Setting enabled successfully')
          : __('Setting disabled successfully'),
      ),
    onError: (err) => toast.error(err.messages?.[0] || __('Could not save')),
  })
}
</script>
