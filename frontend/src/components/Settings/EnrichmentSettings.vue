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
    <div v-else class="flex-1 flex flex-col gap-4 overflow-hidden">
      <div class="px-2">
        <TabButtons v-model="tab" :options="tabOptions" />
      </div>

      <div
        v-if="tab === 'general'"
        class="flex-1 flex flex-col overflow-y-auto"
      >
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

        <div
          class="flex items-center justify-between text-lg-semibold text-ink-gray-8 mt-4 py-3 px-2"
        >
          {{ __('Crawl') }}
        </div>
        <div class="flex gap-4 items-center justify-between py-3 px-2">
          <div class="flex flex-col">
            <div class="text-p-base-medium text-ink-gray-7 truncate">
              {{ __('Max pages') }}
            </div>
            <div class="text-p-sm text-ink-gray-5">
              {{ __('Maximum number of pages crawled per enrichment') }}
            </div>
          </div>
          <div>
            <FormControl
              :model-value="settings.doc.max_pages"
              type="number"
              min="1"
              class="w-24"
              @change="(e) => updateMaxPages(e.target)"
            />
          </div>
        </div>
      </div>

      <div
        v-else
        class="flex flex-1 items-center justify-center text-p-sm text-ink-gray-5"
      >
        {{ __('Rules coming soon') }}
      </div>
    </div>
  </div>
</template>

<script setup>
import {
  createDocumentResource,
  FormControl,
  LoadingIndicator,
  Switch,
  TabButtons,
  toast,
} from 'frappe-ui'
import { ref } from 'vue'

const settings = createDocumentResource({
  doctype: 'CRM Enrichment Settings',
  name: 'CRM Enrichment Settings',
  auto: true,
})

const tab = ref('general')

const tabOptions = [
  { label: __('General'), value: 'general' },
  { label: __('Rules'), value: 'rules' },
]

// A Switch hands us a Boolean, but Check fields come back from the server as
// 0/1 -- so write that shape back, or the doc would differ from originalDoc on
// every load. Every other fieldtype (max_pages is an Int) is saved as given.
function update(fieldname, value) {
  const isCheck = typeof value === 'boolean'
  settings.doc[fieldname] = isCheck ? (value ? 1 : 0) : value

  const message = isCheck
    ? value
      ? __('Setting enabled successfully')
      : __('Setting disabled successfully')
    : __('Setting updated successfully')

  settings.save.submit(null, {
    onSuccess: () => toast.success(message),
    onError: (err) => toast.error(err.messages?.[0] || __('Could not save')),
  })
}

// The number input reports a string, and an emptied box reports ''. Anything
// that isn't a positive whole number is refused: saving 0 would leave the
// crawler fetching no pages at all. The box is put back to the stored value so
// it never shows a number that wasn't saved -- the bound doc value hasn't
// changed, so Vue won't re-render the input for us.
//
// No upper bound: nothing in crm/domain_enrichment clamps max_pages, so the UI
// doesn't invent a ceiling the backend doesn't have.
function updateMaxPages(input) {
  const pages = Number(input.value)

  if (!Number.isInteger(pages) || pages < 1) {
    toast.error(__('Max pages must be a whole number of 1 or more'))
    input.value = settings.doc.max_pages ?? ''
    return
  }

  if (pages === settings.doc.max_pages) return
  update('max_pages', pages)
}
</script>
