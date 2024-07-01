<template>
  <Button
    :label="__('Kanban Settings')"
    @click="showDialog = true"
    v-bind="$attrs"
  >
    <template #prefix>
      <KanbanIcon class="h-4" />
    </template>
  </Button>
  <Dialog v-model="showDialog" :options="{ title: __('Kanban Settings') }">
    <template #body-content>
      <div>
        <div class="text-base text-gray-800 mb-2">{{ __('Column Field') }}</div>
        <Autocomplete
          v-if="columnFields"
          value=""
          :options="columnFields"
          @change="(f) => (columnField = f)"
        >
          <template #target="{ togglePopover }">
            <Button
              class="w-full !justify-start"
              variant="subtle"
              @click="togglePopover()"
              :label="columnField.label"
            />
          </template>
        </Autocomplete>
        <div class="text-base text-gray-800 mb-2 mt-4">
          {{ __('Title Field') }}
        </div>
        <Autocomplete
          v-if="fields.data"
          value=""
          :options="fields.data"
          @change="(f) => (titleField = f)"
        >
          <template #target="{ togglePopover }">
            <Button
              class="w-full !justify-start"
              variant="subtle"
              @click="togglePopover()"
              :label="titleField.label"
            />
          </template>
        </Autocomplete>
      </div>
      <div class="mt-4">
        <div class="text-base text-gray-800 mb-2">{{ __('Fields Order') }}</div>
        <Draggable
          :list="allFields"
          @end="reorder"
          group="fields"
          item-key="name"
          class="flex flex-col gap-1"
        >
          <template #item="{ element: field }">
            <div
              class="px-1 py-0.5 border rounded text-base text-gray-800 flex items-center justify-between gap-2"
            >
              <div class="flex items-center gap-2">
                <DragVerticalIcon class="h-3.5 cursor-grab" />
                <div>{{ field.label }}</div>
              </div>
              <div>
                <Button variant="ghost" icon="x" @click="removeField(field)" />
              </div>
            </div>
          </template>
        </Draggable>
        <Autocomplete
          v-if="fields.data"
          value=""
          :options="fields.data"
          @change="(e) => addField(e)"
        >
          <template #target="{ togglePopover }">
            <Button
              class="w-full mt-2"
              variant="outline"
              @click="togglePopover()"
              :label="__('Add Field')"
            >
              <template #prefix>
                <FeatherIcon name="plus" class="h-4" />
              </template>
            </Button>
          </template>
          <template #item-label="{ option }">
            <div class="flex flex-col gap-1">
              <div>{{ option.label }}</div>
              <div class="text-gray-500 text-sm">
                {{ `${option.fieldname} - ${option.fieldtype}` }}
              </div>
            </div>
          </template>
        </Autocomplete>
      </div>
    </template>
    <template #actions>
      <Button
        class="w-full"
        variant="solid"
        @click="apply"
        :label="__('Apply')"
      />
    </template>
  </Dialog>
</template>
<script setup>
import DragVerticalIcon from '@/components/Icons/DragVerticalIcon.vue'
import KanbanIcon from '@/components/Icons/KanbanIcon.vue'
import Autocomplete from '@/components/frappe-ui/Autocomplete.vue'
import { Dialog, createResource } from 'frappe-ui'
import Draggable from 'vuedraggable'
import { ref, computed, nextTick } from 'vue'

const props = defineProps({
  doctype: {
    type: String,
    required: true,
  },
})

const emit = defineEmits(['update'])

const list = defineModel()
const showDialog = ref(false)

const columnField = computed({
  get: () => {
    let fieldname = list.value?.data?.column_field
    if (!fieldname) return ''

    return columnFields.value?.find((field) => field.fieldname === fieldname)
  },
  set: (val) => {
    list.value.data.column_field = val.fieldname
  },
})

const titleField = computed({
  get: () => {
    let fieldname = list.value?.data?.title_field
    if (!fieldname) return ''

    return fields.data?.find((field) => field.fieldname === fieldname)
  },
  set: (val) => {
    list.value.data.title_field = val.fieldname
  },
})

const columnFields = computed(() => {
  return (
    fields.data?.filter((field) =>
      ['Link', 'Select'].includes(field.fieldtype),
    ) || []
  )
})

const fields = createResource({
  url: 'crm.api.doc.get_fields_meta',
  params: { doctype: props.doctype, as_array: true },
  cache: ['kanban_fields', props.doctype],
  auto: true,
  onSuccess: (data) => {
    data
  },
})

const allFields = computed({
  get: () => {
    let rows = list.value?.data?.kanban_fields
    if (!rows) return []

    if (typeof rows === 'string') {
      rows = JSON.parse(rows)
    }

    if (rows && fields.data) {
      rows = rows.map((row) => {
        return fields.data.find((field) => field.fieldname === row) || {}
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
      column_field: columnField.value.fieldname,
      title_field: titleField.value.fieldname,
      kanban_fields: allFields.value.map((row) => row.fieldname),
    })
  })
}
</script>
