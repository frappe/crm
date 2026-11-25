<!-- Settings › App menu: order, hide and add the items of the menu under the app logo. -->
<template>
  <div class="flex h-full flex-col gap-6 p-8 text-ink-gray-8">
    <div class="flex items-start justify-between gap-6">
      <div class="flex flex-col gap-1">
        <div class="flex h-5 items-center gap-2">
          <h2 class="text-2xl-semibold leading-none">{{ __('App menu') }}</h2>
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
              'Choose what shows in the menu under the CRM logo. Drag rows to reorder.',
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

    <div class="flex min-h-0 flex-1 gap-10 overflow-y-auto p-1 -m-1">
      <div class="flex min-w-0 flex-1 flex-col gap-3">
        <Draggable
          v-model="rows"
          tag="ul"
          item-key="name"
          handle=".drag-handle"
          :aria-label="__('Menu items')"
          class="overflow-hidden rounded-6 border border-outline-gray-2"
          @end="renumber"
        >
          <template #item="{ element }">
            <AppMenuRow
              :item="element"
              @toggle-hidden="element.hidden = element.hidden ? 0 : 1"
              @edit="editLink(element)"
              @remove="removeRow(element)"
            />
          </template>
        </Draggable>
        <div class="flex gap-2">
          <Button
            :label="__('Add link')"
            icon-left="lucide-plus"
            @click="editLink(null)"
          />
          <Button
            variant="ghost"
            :label="__('Add divider')"
            @click="addDivider"
          />
        </div>
        <ErrorMessage :message="error" />
      </div>
      <AppMenuPreview :items="rows" />
    </div>

    <AppMenuLinkDialog
      v-model:open="showLinkDialog"
      :link="editingLink"
      @save="saveLink"
      @delete="removeRow(editingLink)"
    />
  </div>
</template>

<script setup>
import AppMenuRow from '@/components/Settings/AppMenu/AppMenuRow.vue'
import AppMenuPreview from '@/components/Settings/AppMenu/AppMenuPreview.vue'
import AppMenuLinkDialog from '@/components/Settings/AppMenu/AppMenuLinkDialog.vue'
import { getSettings } from '@/stores/settings'
import { getRandom } from '@/utils'
import Draggable from 'vuedraggable'
import { Badge, ErrorMessage } from 'frappe-ui'
import { computed, ref, watch } from 'vue'

const { _settings: settings, settings: liveSettings } = getSettings()

// A copy of the saved rows, so the live menu changes only on Save.
const rows = ref([])
const error = ref('')
const showLinkDialog = ref(false)
const editingLink = ref(null)

const savedRows = computed(() => settings.doc?.dropdown_items || [])

watch(savedRows, discard, { immediate: true })

const isDirty = computed(
  () => fingerprint(rows.value) !== fingerprint(savedRows.value),
)

function fingerprint(items) {
  return JSON.stringify(
    items.map((row) => [
      row.name,
      row.type,
      row.label,
      row.icon,
      row.route,
      Boolean(row.hidden),
      Boolean(row.open_in_new_window),
    ]),
  )
}

function discard() {
  rows.value = JSON.parse(JSON.stringify(savedRows.value))
  error.value = ''
}

function renumber() {
  rows.value.forEach((row, index) => (row.idx = index + 1))
}

function newRow(values) {
  return {
    name: getRandom(10),
    __islocal: true,
    doctype: 'CRM Dropdown Item',
    parenttype: 'FCRM Settings',
    parentfield: 'dropdown_items',
    is_standard: 0,
    hidden: 0,
    ...values,
  }
}

function addDivider() {
  rows.value.push(newRow({ type: 'Separator', label: '' }))
  renumber()
}

function editLink(row) {
  editingLink.value = row
  showLinkDialog.value = true
}

function saveLink(values) {
  if (editingLink.value) Object.assign(editingLink.value, values)
  else rows.value.push(newRow({ type: 'Route', ...values }))
  renumber()
}

function removeRow(row) {
  rows.value = rows.value.filter((item) => item !== row)
  renumber()
}

function save() {
  error.value = ''
  settings.setValue.submit(
    { dropdown_items: rows.value },
    {
      onSuccess: () => (liveSettings.value = settings.doc),
      onError: (err) => (error.value = err.messages?.join('\n') || err.message),
    },
  )
}
</script>
