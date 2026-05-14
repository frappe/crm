<template>
  <Button
    :label="__('Kanban settings')"
    v-bind="$attrs"
    :iconLeft="KanbanIcon"
    @click="showDialog = true"
  />
  <Dialog v-model="showDialog" :options="{ title: __('Kanban Settings') }">
    <template #body-content>
      <div>
        <div class="text-base text-ink-gray-8 mb-2">
          {{ __('Column Field') }}
        </div>
        <Combobox
          v-if="columnFields"
          v-model="columnField"
          class="w-full"
          :options="columnFields"
          :openOnClick="true"
        />
        <div class="text-base text-ink-gray-8 mb-2 mt-4">
          {{ __('Title Field') }}
        </div>
        <Combobox
          v-model="titleField"
          class="w-full"
          :options="fields"
          :openOnClick="true"
        />
      </div>
      <div class="mt-4">
        <div class="text-base text-ink-gray-8 mb-2">
          {{ __('Fields Order') }}
        </div>
        <Draggable
          :list="allFields"
          group="fields"
          item-key="name"
          class="flex flex-col gap-1"
          @end="reorder"
        >
          <template #item="{ element: field }">
            <div
              class="px-1 py-0.5 border border-outline-gray-modals rounded text-base text-ink-gray-8 flex items-center justify-between gap-2"
            >
              <div class="flex items-center gap-2">
                <DragVerticalIcon class="h-3.5 cursor-grab" />
                <div>{{ field.label }}</div>
              </div>
              <div>
                <Button
                  variant="ghost"
                  icon="lucide-x"
                  @click="removeField(field)"
                />
              </div>
            </div>
          </template>
        </Draggable>
        <Combobox :options="fields" @update:selectedOption="(e) => addField(e)">
          <template #trigger>
            <Button
              class="w-full mt-2"
              :label="__('Add Field')"
              iconLeft="lucide-plus"
            />
          </template>
          <template #item-label="{ item }">
            <div class="flex flex-col gap-1 text-ink-gray-9">
              <div>{{ item.label }}</div>
              <div class="text-ink-gray-4 text-sm">
                {{ `${item.fieldname} - ${item.fieldtype}` }}
              </div>
            </div>
          </template>
        </Combobox>
      </div>
    </template>
    <template #actions>
      <Button
        class="w-full"
        variant="solid"
        :label="__('Apply')"
        @click="apply"
      />
    </template>
  </Dialog>
</template>
<script setup>
import DragVerticalIcon from '@/components/Icons/DragVerticalIcon.vue'
import KanbanIcon from '@/components/Icons/KanbanIcon.vue'
import { getMeta } from '@/stores/meta'
import { Combobox, Dialog } from 'frappe-ui'
import Draggable from 'vuedraggable'
import { ref, computed, nextTick } from 'vue'

const props = defineProps({
  doctype: {
    type: String,
    required: true,
  },
})

const emit = defineEmits(['update'])

const list = defineModel({ type: Object })
const showDialog = ref(false)

const columnField = computed({
  get: () => list.value?.data?.column_field || '',
  set: (val) => {
    list.value.data.column_field = val
  },
})

const titleField = computed({
  get: () => list.value?.data?.title_field || '',
  set: (val) => {
    list.value.data.title_field = val
  },
})

const columnFields = computed(() => {
  return (
    fields.value?.filter((field) =>
      ['Link', 'Select'].includes(field.fieldtype),
    ) || []
  )
})

const { getFields } = getMeta(props.doctype)

const fields = computed(() => {
  const _fields = getFields({ withStandardFields: true }) || []
  if (!_fields.length) return []

  let existingFields = []

  allFields.value?.forEach((fieldname) => {
    let field = _fields.find((f) => f.fieldname === fieldname)
    if (field) existingFields.push(field)
  })

  return _fields
    .filter(
      (field) => !existingFields?.find((f) => f.fieldname === field.fieldname),
    )
    .map((field) => {
      return {
        label: field.label,
        value: field.fieldname,
        fieldname: field.fieldname,
        fieldtype: field.fieldtype,
      }
    })
})

const allFields = computed({
  get: () => {
    let rows = list.value?.data?.kanban_fields
    if (!rows) return []

    if (typeof rows === 'string') {
      rows = JSON.parse(rows)
    }

    if (rows && fields.value) {
      rows = rows.map((row) => {
        return fields.value.find((field) => field.fieldname === row) || {}
      })
    }
    return rows.filter((row) => row.label)
  },
  set: (val) => {
    list.value.data.kanban_fields = val
  },
})

function reorder() {
  allFields.value = allFields.value.map((row) => row.fieldname)
}

function addField(field) {
  if (!field) return
  let rows = allFields.value || []
  rows.push(field)
  allFields.value = rows.map((row) => row.fieldname)
}

function removeField(field) {
  let rows = allFields.value
  rows = rows.filter((row) => row.fieldname !== field.fieldname)
  allFields.value = rows.map((row) => row.fieldname)
}

function apply() {
  nextTick(() => {
    showDialog.value = false
    emit('update', {
      column_field: columnField.value,
      title_field: titleField.value,
      kanban_fields: allFields.value.map((row) => row.fieldname),
    })
  })
}
</script>
