<template>
  <Dialog v-model:open="show" size="lg" bare>
    <template #default>
      <div class="px-4 pb-6 pt-5 sm:px-6">
        <div class="mb-4 flex items-start justify-between gap-4">
          <div>
            <Dialog.Title as-child>
              <h3 class="text-2xl-semibold leading-6 text-ink-gray-9">
                {{ __('Select lead') }}
              </h3>
            </Dialog.Title>
            <p class="mt-1.5 text-p-base text-ink-gray-5">
              {{ __('Select the lead you want to merge into this one') }}
            </p>
          </div>
          <Dialog.Close as-child>
            <Button
              :aria-label="__('Close')"
              variant="ghost"
              class="w-7 shrink-0"
              icon="lucide-x"
            />
          </Dialog.Close>
        </div>
        <TextInput
          v-model="search"
          type="text"
          class="w-full"
          autofocus
          :placeholder="__('Search by name, email, organization or ID')"
        >
          <template #prefix>
            <span
              class="lucide-search h-4 w-4 text-ink-gray-4"
              aria-hidden="true"
            />
          </template>
        </TextInput>
        <div class="mt-3 h-[340px] overflow-y-auto">
          <div
            v-if="loading && !rowCount"
            class="flex h-full items-center justify-center text-p-base text-ink-gray-5"
          >
            {{ __('Loading...') }}
          </div>
          <div
            v-else-if="!rowCount"
            class="flex h-full items-center justify-center text-p-base text-ink-gray-5"
          >
            {{ __('No leads found') }}
          </div>
          <template v-else>
            <template v-for="group in groups" :key="group.key">
              <div
                v-if="showGroupLabels"
                class="px-2 pb-1 pt-2 text-sm text-ink-gray-5"
              >
                {{ group.label }}
              </div>
              <button
                v-for="l in group.rows"
                :key="l.name"
                type="button"
                class="flex w-full items-center gap-3 rounded-4 px-2 py-1.5 text-left hover:bg-surface-gray-2 focus-visible:bg-surface-gray-2 focus-visible:outline-none"
                @click="emit('select', l)"
              >
                <Avatar
                  :label="l.lead_name || l.name"
                  size="md"
                  class="shrink-0"
                />
                <div class="flex min-w-0 flex-1 flex-col gap-1">
                  <span class="truncate text-base-medium text-ink-gray-8">
                    {{ l.lead_name || l.name }}
                  </span>
                  <span class="truncate text-p-sm text-ink-gray-5">
                    {{ l.name }} ·
                    {{
                      group.key === 'duplicates'
                        ? matchedValue(l)
                        : l.email || __('No email')
                    }}
                  </span>
                </div>
                <Badge
                  v-if="group.key === 'duplicates'"
                  theme="gray"
                  size="sm"
                  class="shrink-0"
                  :label="
                    matchedOnEmail(l) ? __('Same email') : __('Same phone')
                  "
                />
              </button>
            </template>
          </template>
        </div>
      </div>
    </template>
  </Dialog>
</template>
<script setup lang="ts">
import { Avatar, Badge, Dialog, TextInput, createResource } from 'frappe-ui'
import { useDebounceFn } from '@vueuse/core'
import { computed, ref, watch } from 'vue'

export interface SelectableLead {
  name: string
  lead_name: string
  email: string
  mobile_no: string
  phone: string
  organization: string
}

interface DuplicateLead extends SelectableLead {
  // fields the backend matched on, e.g. ['email'] or ['mobile_no']
  matched_fields: string[]
}

const SEARCH_FIELDS = [
  'name',
  'lead_name',
  'email',
  'organization',
  'mobile_no',
  'phone',
] as const

const props = defineProps<{ lead: string }>()

const emit = defineEmits<{ select: [lead: SelectableLead] }>()

const show = defineModel<boolean>({ default: false })

const search = ref('')
let lastQuery: string | null = null

const duplicates = createResource({
  url: 'crm.api.lead.find_duplicate_leads',
  makeParams: () => ({ lead_name: props.lead }),
})

const duplicateNames = computed<string[]>(() =>
  (duplicates.data || []).map((d: DuplicateLead) => d.name),
)

const leads = createResource({
  url: 'frappe.client.get_list',
  makeParams() {
    const txt = search.value.trim()
    lastQuery = txt
    return {
      doctype: 'CRM Lead',
      fields: [
        'name',
        'lead_name',
        'email',
        'mobile_no',
        'phone',
        'organization',
      ],
      filters: [
        ['name', '!=', props.lead],
        ['converted', '=', 0],
        ['is_duplicate', '=', 0],
      ],
      or_filters: txt
        ? SEARCH_FIELDS.map((f) => [f, 'like', `%${txt}%`])
        : undefined,
      order_by: 'modified desc',
      limit_page_length: 20,
    }
  },
})

const filteredDuplicates = computed<DuplicateLead[]>(() => {
  const txt = search.value.trim().toLowerCase()
  const rows: DuplicateLead[] = duplicates.data || []
  if (!txt) return rows
  return rows.filter((d) =>
    SEARCH_FIELDS.some((f) => (d[f] || '').toLowerCase().includes(txt)),
  )
})

// duplicates are listed in their own group
const otherLeads = computed<SelectableLead[]>(() =>
  (leads.data || []).filter(
    (l: SelectableLead) => !duplicateNames.value.includes(l.name),
  ),
)

const groups = computed(() =>
  [
    {
      key: 'duplicates',
      label: __('Possible duplicates'),
      rows: filteredDuplicates.value,
    },
    { key: 'others', label: __('Other leads'), rows: otherLeads.value },
  ].filter((g) => g.rows.length),
)

const showGroupLabels = computed(() => duplicateNames.value.length > 0)
const rowCount = computed(() =>
  groups.value.reduce((n, g) => n + g.rows.length, 0),
)
const loading = computed(() => duplicates.loading || leads.loading)

function matchedOnEmail(l: DuplicateLead) {
  return l.matched_fields.includes('email')
}

// the value the lead matched on, so the row shows why it's a possible duplicate
function matchedValue(l: DuplicateLead) {
  if (matchedOnEmail(l)) return l.email
  return l.matched_fields.includes('mobile_no') ? l.mobile_no : l.phone
}

// skip when the open-reset already fetched this term
const reloadDebounced = useDebounceFn(() => {
  if (search.value.trim() !== lastQuery) leads.reload()
}, 300)

watch(search, () => reloadDebounced())

watch(
  show,
  (open) => {
    if (!open) return
    search.value = ''
    // the picker still works as a plain search if this fails
    duplicates.reload().catch(() => {})
    leads.reload()
  },
  { immediate: true },
)
</script>
