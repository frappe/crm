<template>
  <SettingsLayoutBase
    v-if="screen === 'list'"
    :title="__('Workflow Automations')"
    :description="__('Create workflow automations for CRM documents')"
  >
    <template #header-actions>
      <Button
        :label="__('New')"
        variant="solid"
        icon-left="lucide-plus"
        @click="newAutomation"
      />
    </template>
    <template v-if="showSearch" #header-bottom>
      <div class="relative">
        <Input
          :model-value="search"
          :placeholder="__('Search')"
          icon-left="search"
          debounce="300"
          class="rounded border-outline-gray-2 bg-surface-gray-2"
          @input="search = $event"
        />
        <Button
          v-if="search"
          icon="lucide-x"
          variant="ghost"
          class="absolute right-1 top-1/2 -translate-y-1/2"
          @click="search = ''"
        />
      </div>
    </template>
    <template #content>
      <div v-if="automations.list.loading" class="mt-10 flex justify-center">
        <LoadingIndicator class="w-4" />
      </div>
      <EmptyState
        v-else-if="!filteredAutomations.length"
        name="Workflow Automations"
        :icon="WorkflowIcon"
        :title="__('No workflow automations yet')"
        :description="__('Add one to get started.')"
        width="lg"
      />
      <List
        v-else
        class="workflow-automation-list"
        :columns="listColumns"
        :row-height="56"
        divider="full"
      >
        <ListHeader class="sticky top-0 z-10 mx-3 bg-surface-elevation-2">
          <ListHeaderCell>{{ __('Name') }}</ListHeaderCell>
          <ListHeaderCell>{{ __('Document Type') }}</ListHeaderCell>
          <ListHeaderCell>{{ __('Created By') }}</ListHeaderCell>
          <ListHeaderCell>{{ __('Enabled') }}</ListHeaderCell>
        </ListHeader>
        <ListRows
          v-slot="{ item: row }"
          :items="filteredAutomations"
          row-key="name"
        >
          <ListRow :value="row.name" @click="openAutomation(row)">
            <ListCell>
              <span class="truncate text-base-medium text-ink-gray-7">
                {{ row.title || row.name }}
              </span>
            </ListCell>
            <ListCell>
              <span class="truncate text-sm">
                {{ row.document_type || __('Any document') }}
              </span>
            </ListCell>
            <ListCell>
              <Tooltip :text="getUser(row.owner).full_name">
                <UserAvatar :user="row.owner" size="sm" />
              </Tooltip>
            </ListCell>
            <ListCell>
              <div
                class="flex w-full items-center justify-between pr-1"
                @click.stop
              >
                <Badge
                  :label="row.enabled ? __('Enabled') : __('Draft')"
                  :theme="row.enabled ? 'green' : 'orange'"
                  variant="subtle"
                />
                <Dropdown placement="right" :options="rowOptions(row)">
                  <Button
                    icon="lucide-more-horizontal"
                    variant="ghost"
                    @click="confirmingDelete = ''"
                  />
                </Dropdown>
              </div>
            </ListCell>
          </ListRow>
        </ListRows>
      </List>
    </template>
  </SettingsLayoutBase>
  <WorkflowAutomationDetail
    v-else
    :automation-name="selectedAutomation"
    @edit="showBuilder = true"
    @back="backToList"
  />

  <!-- The builder overlays the settings dialog: wider, taller, and dismissable only
       through its own close button so a stray click can't drop unsaved steps. -->
  <Dialog v-model:open="showBuilder" size="6xl" bare :dismissible="false">
    <template #default>
      <div class="h-[calc(100vh_-_6rem)]">
        <WorkflowAutomationBuilder
          v-if="showBuilder"
          :automation-name="selectedAutomation"
          @update:dirty="dirty = $event"
          @close="requestClose"
          @saved="onSaved"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import SettingsLayoutBase from '@/components/Layouts/SettingsLayoutBase.vue'
import EmptyState from '@/components/ListViews/EmptyState.vue'
import WorkflowAutomationBuilder from './WorkflowAutomationBuilder.vue'
import WorkflowAutomationDetail from './WorkflowAutomationDetail.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import WorkflowIcon from '~icons/lucide/workflow'
import { ConfirmDelete } from '@/utils'
import { createDialog } from '@/utils/dialogs'
import { usersStore } from '@/stores/users'
import { disableSettingModalOutsideClick } from '@/composables/settings'
import {
  List,
  ListCell,
  ListHeader,
  ListHeaderCell,
  ListRow,
  ListRows,
} from 'frappe-ui/list'
import {
  Badge,
  Button,
  Dialog,
  Dropdown,
  LoadingIndicator,
  Tooltip,
  call,
  createListResource,
  toast,
} from 'frappe-ui'
import { computed, onUnmounted, reactive, ref, watch } from 'vue'

const { getUser } = usersStore()

const screen = ref('list')
const search = ref('')
const selectedAutomation = ref('')
const confirmingDelete = ref('')
const showBuilder = ref(false)
const dirty = ref(false)
const toggling = reactive(new Set())

const listColumns = [
  'minmax(0, 4fr)',
  'minmax(0, 2fr)',
  'minmax(0, 2fr)',
  'minmax(0, 2fr)',
]

// While the builder is up, a click outside must not take the settings dialog with it.
watch(showBuilder, (open) => (disableSettingModalOutsideClick.value = open))
onUnmounted(() => (disableSettingModalOutsideClick.value = false))

const automations = createListResource({
  doctype: 'Automation Flow',
  fields: [
    'name',
    'title',
    'document_type',
    'owner',
    'enabled',
    'creation',
    'modified',
  ],
  cache: ['workflowAutomations'],
  orderBy: 'creation desc',
  pageLength: 999,
  auto: true,
})

// On the template, not the div inside it: a declared slot still renders the layout's padded
// wrapper, which leaves a gap where the search box would have been.
const showSearch = computed(() => search.value || automations.data?.length > 9)

const filteredAutomations = computed(() => {
  const rows = automations.data || []
  const matches = search.value ? rows.filter((row) => matchesSearch(row)) : rows
  return sortByNewestCreated(matches)
})

function matchesSearch(row) {
  const query = search.value.toLowerCase()
  return [row.title, row.name, row.document_type, getUser(row.owner).full_name]
    .filter(Boolean)
    .some((value) => value.toLowerCase().includes(query))
}

function sortByNewestCreated(rows) {
  return [...rows].sort(compareCreatedDesc)
}

function compareCreatedDesc(a, b) {
  return compareDesc(a.creation, b.creation) || compareDesc(a.name, b.name)
}

function compareDesc(a, b) {
  return String(b || '').localeCompare(String(a || ''))
}

function newAutomation() {
  selectedAutomation.value = ''
  showBuilder.value = true
}

function openAutomation(automation) {
  selectedAutomation.value = automation.name
  screen.value = 'detail'
}

/** Closing the builder always lands back on the list, warning first about unsaved edits. */
function requestClose() {
  if (!dirty.value) return closeBuilder()
  createDialog({
    title: __('Unsaved changes'),
    message: __('You have unsaved changes. Do you wish to exit?'),
    size: 'sm',
    actions: [
      { label: __('Keep editing'), onClick: ({ close }) => close() },
      {
        label: __('Discard and exit'),
        variant: 'solid',
        theme: 'red',
        onClick: closeBuilder,
      },
    ],
  })
}

function closeBuilder({ close } = {}) {
  close?.()
  showBuilder.value = false
  dirty.value = false
  backToList()
}

function backToList() {
  selectedAutomation.value = ''
  screen.value = 'list'
  reloadList()
}

function onSaved(saved) {
  selectedAutomation.value = saved?.name || selectedAutomation.value
  reloadList()
}

function reloadList() {
  automations.reload()
}

async function toggleAutomation(automation, enabled) {
  if (toggling.has(automation.name)) return
  const previous = automation.enabled
  automation.enabled = enabled ? 1 : 0
  toggling.add(automation.name)
  try {
    await updateEnabled(automation)
    toast.success(__('Automation updated'))
  } catch (error) {
    automation.enabled = previous
    toast.error(error?.message || __('Could not update automation'))
  } finally {
    toggling.delete(automation.name)
  }
}

function updateEnabled(automation) {
  return call('frappe.client.set_value', {
    doctype: 'Automation Flow',
    name: automation.name,
    fieldname: 'enabled',
    value: automation.enabled,
  })
}

function rowOptions(automation) {
  return [
    {
      label: automation.enabled ? __('Disable') : __('Enable'),
      icon: automation.enabled ? 'toggle-left' : 'toggle-right',
      onClick: () => toggleAutomation(automation, !automation.enabled),
    },
    {
      label: __('Duplicate'),
      icon: 'copy',
      onClick: () => duplicateAutomation(automation),
    },
    ...ConfirmDelete({
      isConfirmingDelete: computed({
        get: () => confirmingDelete.value === automation.name,
        set: (value) => (confirmingDelete.value = value ? automation.name : ''),
      }),
      onConfirmDelete: () => deleteAutomation(automation),
    }),
  ]
}

async function duplicateAutomation(automation) {
  try {
    const source = await call('frappe.client.get', {
      doctype: 'Automation Flow',
      name: automation.name,
    })
    await call('frappe.client.insert', { doc: copyOf(source) })
    toast.success(__('Automation duplicated'))
    reloadList()
  } catch (error) {
    toast.error(error.messages?.[0] || __('Could not duplicate automation'))
  }
}

/** A copy starts disabled, so a half-reviewed flow never runs the moment it is saved. */
function copyOf(source) {
  return {
    ...withoutIdentity(source),
    doctype: 'Automation Flow',
    title: nextCopyTitle(source.title),
    enabled: 0,
    actions: (source.actions || []).map(withoutIdentity),
  }
}

const IDENTITY_FIELDS = [
  'name',
  'creation',
  'modified',
  'owner',
  'modified_by',
  'idx',
  'parent',
  'parentfield',
  'parenttype',
]

function withoutIdentity(row) {
  const copy = { ...row }
  IDENTITY_FIELDS.forEach((field) => delete copy[field])
  return copy
}

/** "Welcome lead sequence" -> "Welcome lead sequence (1)", skipping names already taken. */
function nextCopyTitle(title) {
  const taken = new Set((automations.data || []).map((row) => row.title))
  let index = 1
  while (taken.has(`${title} (${index})`)) index += 1
  return `${title} (${index})`
}

async function deleteAutomation(automation) {
  await call('frappe.client.delete', {
    doctype: 'Automation Flow',
    name: automation.name,
  })
  toast.success(__('Automation deleted'))
  confirmingDelete.value = ''
  reloadList()
}
</script>

<style scoped>
/* Match the header's rule so rows read as one table. */
.workflow-automation-list :deep([data-slot='list-divider']) {
  border-color: var(--outline-gray-2);
}
</style>
