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

      <div v-else class="flex-1 flex flex-col overflow-y-auto">
        <div class="text-lg-semibold text-ink-gray-8 py-3 px-2">
          {{ __('Social profile rules') }}
        </div>

        <div
          v-if="rulesLoading"
          class="flex flex-1 items-center justify-center"
        >
          <LoadingIndicator class="size-4" />
        </div>
        <div
          v-else-if="socialRules.list.error"
          class="flex flex-1 flex-col items-center justify-center gap-3"
        >
          <div class="text-p-base text-ink-gray-6 text-center">
            {{
              socialRules.list.error.messages?.[0] ||
              __('Could not load social rules')
            }}
          </div>
          <Button :label="__('Retry')" @click="retry" />
        </div>
        <EmptyState
          v-else-if="!socialRules.data?.length"
          class="flex-1"
          name="Social Rules"
          :title="__('No social rules found')"
          :description="
            __('Social rules are created when enrichment is installed.')
          "
          icon="share-2"
        />
        <div v-else>
          <div class="flex items-center p-2 text-sm text-ink-gray-5">
            <div class="w-3/12">{{ __('Platform') }}</div>
            <div class="w-7/12">{{ __('Patterns') }}</div>
            <div class="w-2/12">{{ __('Status') }}</div>
          </div>
          <div class="h-px border-t mx-2 border-outline-elevation-2" />
          <template v-for="(rule, i) in socialRules.data" :key="rule.name">
            <div class="flex items-start py-3 px-2">
              <div
                class="w-3/12 pr-4 text-p-base-medium text-ink-gray-7 truncate"
              >
                {{ rule.target_value || rule.rule_name }}
              </div>
              <div class="w-7/12 pr-4 flex flex-col gap-1">
                <div
                  v-for="(pattern, index) in patterns[rule.name]"
                  :key="index"
                  class="break-all font-mono text-xs text-ink-gray-5"
                >
                  {{ pattern }}
                </div>
                <div
                  v-if="!patterns[rule.name]?.length"
                  class="text-p-sm text-ink-gray-4"
                >
                  {{ __('No patterns') }}
                </div>
              </div>
              <div class="w-2/12">
                <Badge
                  :label="rule.enabled ? __('Enabled') : __('Disabled')"
                  :theme="rule.enabled ? 'green' : 'gray'"
                  variant="subtle"
                  size="sm"
                />
              </div>
            </div>
            <hr v-if="socialRules.data.length !== i + 1" class="mx-2" />
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import {
  Badge,
  Button,
  call,
  createDocumentResource,
  createListResource,
  FormControl,
  LoadingIndicator,
  Switch,
  TabButtons,
  toast,
} from 'frappe-ui'
import EmptyState from '@/components/ListViews/EmptyState.vue'
import { computed, reactive, ref } from 'vue'

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

// Only Social rules for now -- Industry rules score a classification and read
// nothing like a platform/pattern pair, so they get their own list later.
// order_by matches the doctype's own sort (modified desc), so the list reads the
// same here as it does in Desk.
const socialRules = createListResource({
  doctype: 'CRM Enrichment Rule',
  filters: { rule_type: 'Social' },
  fields: ['name', 'rule_name', 'target_value', 'enabled'],
  orderBy: 'modified desc',
  pageLength: 99,
  auto: true,
  onSuccess: (rules) => loadPatterns(rules),
})

// rule name -> list of pattern strings
const patterns = reactive({})
const patternsLoading = ref(false)

// createListResource keeps its fetch state on `.list`, not on the resource
// itself -- the patterns land after it, so the spinner has to cover both.
const rulesLoading = computed(
  () => socialRules.list.loading || patternsLoading.value,
)

// reload() rethrows on a second failure, and an unguarded rejection here would
// only show up as console noise -- the error state already renders the message.
function retry() {
  socialRules.reload().catch(() => {})
}

// get_list never returns child tables, so the patterns have to be fetched
// separately: one frappe.client.get per rule, which is what the rest of Settings
// already does for a single doc (see WorkflowAutomationDetail.vue). A handful of
// Social rules means a handful of parallel requests -- cheaper than adding a
// backend endpoint for a read-only list. createDocumentResource per rule was the
// other option, but a resource can't be created inside v-for: it would have to
// be built and cached outside the render, and its save/setValue machinery is
// dead weight in a list nothing can edit yet.
async function loadPatterns(rules) {
  if (!rules?.length) return

  patternsLoading.value = true
  try {
    const docs = await Promise.all(
      rules.map((rule) =>
        call('frappe.client.get', {
          doctype: 'CRM Enrichment Rule',
          name: rule.name,
        }),
      ),
    )
    docs.forEach((doc) => {
      patterns[doc.name] = (doc.patterns || []).map((row) => row.pattern)
    })
  } catch (err) {
    // A row with no patterns loaded reads as "No patterns", so say out loud that
    // the fetch failed rather than letting it look like an empty rule.
    toast.error(err.messages?.[0] || __('Could not load rule patterns'))
  } finally {
    patternsLoading.value = false
  }
}

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
