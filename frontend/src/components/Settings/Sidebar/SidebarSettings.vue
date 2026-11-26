<!-- Settings › Sidebar: order, hide, rename and add the items of CRM's sidebar. -->
<template>
  <div class="flex h-full flex-col gap-6 p-8 text-ink-gray-8">
    <div class="flex items-start justify-between gap-6">
      <div class="flex flex-col gap-1">
        <div class="flex h-5 items-center gap-2">
          <h2 class="text-2xl-semibold leading-none">{{ __('Sidebar') }}</h2>
          <Badge
            v-if="isDirty"
            :label="__('Not Saved')"
            variant="subtle"
            theme="amber"
          />
        </div>
        <p class="text-p-base text-ink-gray-6">
          {{
            __(
              'Choose what shows in the sidebar for everyone. Drag rows to reorder.',
            )
          }}
        </p>
      </div>
      <div v-if="isDirty" class="flex shrink-0 gap-2">
        <Button :label="__('Discard')" @click="discard" />
        <Button
          variant="solid"
          :label="__('Save')"
          :loading="settings.setValue.loading"
          @click="save"
        />
      </div>
    </div>

    <div class="flex min-h-0 flex-1 flex-col gap-3">
      <Draggable
        v-model="rows"
        tag="ul"
        item-key="name"
        handle=".drag-handle"
        :aria-label="__('Sidebar items')"
        class="min-h-0 select-none overflow-y-auto rounded-6 border border-outline-gray-2 p-1"
      >
        <template #item="{ element }">
          <li>
            <SidebarItemRow
              :item="element"
              @toggle-hidden="element.hidden = element.hidden ? 0 : 1"
              @edit="editRow(element)"
            />
          </li>
        </template>
      </Draggable>
      <div class="flex shrink-0">
        <Button
          :label="__('Add DocType')"
          icon-left="lucide-plus"
          @click="editRow(null)"
        />
      </div>
      <ErrorMessage :message="error" />
    </div>

    <SidebarItemDialog
      v-model:open="showDialog"
      :item="editingRow"
      :used-doctypes="usedDoctypes"
      @save="saveItem"
      @delete="removeRow(editingRow)"
    />
  </div>
</template>

<script setup>
import SidebarItemDialog from '@/components/Settings/Sidebar/SidebarItemDialog.vue'
import SidebarItemRow from '@/components/Settings/Sidebar/SidebarItemRow.vue'
import { getSettings } from '@/stores/settings'
import { getRandom } from '@/utils'
import { setSidebarItems } from '@/utils/navigation'
import Draggable from 'vuedraggable'
import { Badge, ErrorMessage } from 'frappe-ui'
import { computed, ref, watch } from 'vue'

const { _settings: settings, settings: liveSettings } = getSettings()

const rows = ref([])
// The rows as last loaded or saved. Not the live doc: `setValue` writes the doc before the
// server answers and reverts it on failure, which would drop the edits with the error.
const baseline = ref([])
const error = ref('')
const showDialog = ref(false)
const editingRow = ref(null)

watch(
  () => Boolean(settings.doc),
  (isLoaded) => isLoaded && load(),
  { immediate: true },
)

const isDirty = computed(
  () => fingerprint(rows.value) !== fingerprint(baseline.value),
)

const usedDoctypes = computed(() =>
  rows.value.filter((row) => row.dt).map((row) => row.dt),
)

function fingerprint(items) {
  return JSON.stringify(
    items.map((row) => [
      row.name,
      row.label,
      row.icon || '',
      row.dt,
      Boolean(row.hidden),
    ]),
  )
}

function load() {
  baseline.value = settings.doc.sidebar_items || []
  discard()
}

function discard() {
  rows.value = JSON.parse(JSON.stringify(baseline.value))
  error.value = ''
}

function editRow(row) {
  editingRow.value = row
  showDialog.value = true
}

function saveItem(values) {
  if (editingRow.value) {
    Object.assign(editingRow.value, values)
    return
  }
  rows.value.push({
    name: getRandom(10),
    __islocal: true,
    doctype: 'CRM Sidebar Item',
    parenttype: 'FCRM Settings',
    parentfield: 'sidebar_items',
    type: 'DocType',
    is_standard: 0,
    hidden: 0,
    ...values,
  })
}

function removeRow(row) {
  rows.value.splice(rows.value.indexOf(row), 1)
}

function save() {
  error.value = ''
  settings.setValue.submit(
    {
      sidebar_items: rows.value.map((row, index) => ({
        ...row,
        idx: index + 1,
      })),
    },
    {
      onSuccess: () => {
        load()
        liveSettings.value = settings.doc
        setSidebarItems(baseline.value.filter((row) => !row.hidden))
      },
      onError: (err) => (error.value = err.messages?.join('\n') || err.message),
    },
  )
}
</script>
