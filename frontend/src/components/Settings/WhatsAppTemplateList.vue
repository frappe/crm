<template>
  <div class="flex h-full flex-col">
    <div
      v-if="templates.loading && !templates.data"
      class="flex items-center justify-center mt-12"
    >
      <LoadingIndicator class="w-4" />
    </div>
    <div v-else class="flex min-h-0 w-full flex-col">
      <div class="mb-4 flex items-center justify-between gap-2">
        <TextInput
          v-if="templates.data?.length > 10"
          v-model="search"
          class="w-full"
          :placeholder="__('Search Template')"
          :debounce="300"
        >
          <template #prefix>
            <span
              class="lucide-search h-4 w-4 text-ink-gray-6"
              aria-hidden="true"
            />
          </template>
        </TextInput>
        <!-- Meta owns approval, so a template's status only moves on a sync
             or a webhook; a button covers the wait for the webhook. -->
        <Button
          class="ml-auto shrink-0"
          :label="__('Sync')"
          icon-left="lucide-refresh-cw"
          :loading="syncing"
          @click="syncTemplates"
        />
      </div>
      <EmptyState
        v-if="!templates.data?.length"
        name="WhatsApp Templates"
        :title="__('No WhatsApp templates yet')"
        :description="
          __('Create one, or sync the templates already on your Meta account.')
        "
        :icon="WhatsAppIcon"
      />
      <div v-else class="overflow-y-auto">
        <template
          v-for="(template, i) in filteredTemplates"
          :key="template.name"
        >
          <div
            class="flex w-full items-center justify-between rounded px-2 py-3 hover:bg-surface-gray-2"
          >
            <div
              class="min-w-0 cursor-pointer"
              @click="emit('edit', template.name)"
            >
              <div class="truncate text-base-medium text-ink-gray-7">
                {{ template.template_label || template.template_name }}
              </div>
              <div class="mt-0.5 truncate text-p-base text-ink-gray-5">
                {{ details(template) }}
              </div>
            </div>
            <div class="flex items-center gap-2">
              <Badge
                variant="subtle"
                :theme="templateStatusTheme(template.status)"
                :label="__(template.status)"
              />
              <Dropdown placement="right" :options="rowOptions(template)">
                <Button
                  icon="lucide-more-horizontal"
                  variant="ghost"
                  @click="confirmDelete = false"
                />
              </Dropdown>
            </div>
          </div>
          <hr v-if="filteredTemplates.length !== i + 1" class="mx-2" />
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'
import EmptyState from '@/components/ListViews/EmptyState.vue'
import { templateStatusTheme } from '@/composables/whatsapp'
import { ConfirmDelete } from '@/utils'
import {
  call,
  createListResource,
  Dropdown,
  LoadingIndicator,
  TextInput,
  toast,
} from 'frappe-ui'
import { computed, onMounted, ref } from 'vue'

const emit = defineEmits(['edit'])

const search = ref('')
const confirmDelete = ref(false)
const syncing = ref(false)

const TEMPLATE_API =
  'whatsapp.whatsapp.doctype.whatsapp_template.whatsapp_template'

const templates = createListResource({
  doctype: 'WhatsApp Template',
  cache: 'WhatsApp Templates',
  fields: [
    'name',
    'template_label',
    'template_name',
    'template_type',
    'language',
    'status',
    'whatsapp_account',
  ],
  orderBy: 'creation desc',
  pageLength: 99,
  auto: true,
})

// The list resource is cached, and this panel is unmounted whenever the tab
// changes, so refresh on the way back in to pick up templates added since.
onMounted(() => {
  if (templates.data) templates.reload()
})

const filteredTemplates = computed(() => {
  const query = search.value.toLowerCase()
  if (!query) return templates.data
  return templates.data.filter((template) =>
    [template.template_label, template.template_name, template.language].some(
      (field) => field?.toLowerCase().includes(query),
    ),
  )
})

function details(template) {
  return [template.template_type, template.language, template.whatsapp_account]
    .filter(Boolean)
    .join(' · ')
}

// One account at a time rather than the app's `sync_all`, which stops to ask
// which account when there are several.
async function syncTemplates() {
  syncing.value = true
  try {
    const accounts = await call(`${TEMPLATE_API}.get_active_accounts`)
    if (!accounts?.length) {
      toast.error(__('No active WhatsApp account to sync from'))
      return
    }
    let created = 0
    let updated = 0
    for (const account of accounts) {
      const result = await call(`${TEMPLATE_API}.sync_from_account`, {
        account_name: account.name,
      })
      created += result.total_synced || 0
      updated += result.total_skipped || 0
    }
    toast.success(__('{0} new, {1} updated', [created, updated]))
    templates.reload()
  } catch (error) {
    toast.error(error.messages?.[0] || __('Sync failed'))
  } finally {
    syncing.value = false
  }
}

function deleteTemplate(template) {
  templates.delete.submit(template.name, {
    onSuccess: () => {
      toast.success(__('Template deleted'))
    },
    onError: (error) => {
      toast.error(error.messages?.[0] || __('Failed to delete template'))
    },
  })
}

function rowOptions(template) {
  return [
    {
      label: __('Edit'),
      icon: 'edit-2',
      onClick: () => emit('edit', template.name),
    },
    ...ConfirmDelete({
      onConfirmDelete: () => deleteTemplate(template),
      isConfirmingDelete: confirmDelete,
    }),
  ]
}
</script>
