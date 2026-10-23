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
            v-if="leads.loading && !leads.data?.length"
            class="flex h-full items-center justify-center text-p-base text-ink-gray-5"
          >
            {{ __('Loading...') }}
          </div>
          <div
            v-else-if="!leads.data?.length"
            class="flex h-full items-center justify-center text-p-base text-ink-gray-5"
          >
            {{ __('No leads found') }}
          </div>
          <template v-else>
            <button
              v-for="l in leads.data"
              :key="l.name"
              type="button"
              class="flex w-full items-center gap-3 rounded px-2 py-2 text-left hover:bg-surface-gray-2 focus-visible:bg-surface-gray-2 focus-visible:outline-none"
              @click="emit('select', l)"
            >
              <Avatar
                :label="l.lead_name || l.name"
                size="lg"
                class="shrink-0"
              />
              <div class="flex min-w-0 flex-col gap-1">
                <span class="truncate text-base-medium text-ink-gray-8">
                  {{ l.lead_name || l.name }}
                </span>
                <span class="truncate text-p-sm text-ink-gray-5">
                  {{ l.name }} · {{ l.email || __('No email') }}
                </span>
              </div>
            </button>
          </template>
        </div>
      </div>
    </template>
  </Dialog>
</template>
<script setup lang="ts">
import { Avatar, Dialog, TextInput, createResource } from 'frappe-ui'
import { useDebounceFn } from '@vueuse/core'
import { ref, watch } from 'vue'

export interface SelectableLead {
  name: string
  lead_name: string
  email: string
  organization: string
}

const props = defineProps<{ lead: string }>()

const emit = defineEmits<{ select: [lead: SelectableLead] }>()

const show = defineModel<boolean>({ default: false })

const search = ref('')
let lastQuery: string | null = null

const leads = createResource({
  url: 'frappe.client.get_list',
  makeParams() {
    const txt = search.value.trim()
    lastQuery = txt
    return {
      doctype: 'CRM Lead',
      fields: ['name', 'lead_name', 'email', 'organization'],
      filters: [
        ['name', '!=', props.lead],
        ['converted', '=', 0],
      ],
      or_filters: txt
        ? ['name', 'lead_name', 'email', 'organization'].map((f) => [
            f,
            'like',
            `%${txt}%`,
          ])
        : undefined,
      order_by: 'modified desc',
      limit_page_length: 20,
    }
  },
})

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
    leads.reload()
  },
  { immediate: true },
)
</script>
