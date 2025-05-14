<template>
  <Dialog v-model="show">
    <template #body-title>
      <h3
        class="flex items-center gap-2 text-2xl font-semibold leading-6 text-ink-gray-9"
      >
        <div>{{ __('Edit Grid Fields Layout') }}</div>
        <Badge
          v-if="dirty"
          :label="__('Not Saved')"
          variant="subtle"
          theme="orange"
        />
      </h3>
    </template>
    <template #body-content>
      <div class="mt-4">
        <div class="text-base text-ink-gray-8 mb-2">
          {{ __('Fields Order') }}
        </div>
        <Draggable
          v-if="oldFields?.length"
          :list="fields"
          group="fields"
          item-key="fieldname"
          class="flex flex-col gap-1"
        >
          <template #item="{ element: field }">
            <div
              class="px-1 py-0.5 bg-surface-gray-2 border border-outline-gray-modals rounded text-base text-ink-gray-8 flex items-center justify-between gap-2"
            >
              <div class="flex items-center gap-2">
                <DragVerticalIcon class="h-3.5 cursor-grab" />
                <div>{{ field.label }}</div>
              </div>
              <div class="flex items-center gap-2">
                <TextInput
                  variant="outline"
                  type="number"
                  v-model="field.columns"
                  class="w-20"
                />
                <Button variant="ghost" icon="x" @click="removeField(field)" />
              </div>
            </div>
          </template>
        </Draggable>
        <Autocomplete
          v-if="dropdownFields?.length"
          value=""
          :options="dropdownFields"
          @change="(e) => addField(e)"
        >
          <template #target="{ togglePopover }">
            <Button
              class="w-full mt-2"
              @click="togglePopover()"
              :label="__('Add Field')"
            >
              <template #prefix>
                <FeatherIcon name="plus" class="h-4" />
              </template>
            </Button>
          </template>
          <template #item-label="{ option }">
            <div class="flex flex-col gap-1 text-ink-gray-9">
              <div>{{ option.label }}</div>
              <div class="text-ink-gray-4 text-sm">
                {{ `${option.fieldname} - ${option.fieldtype}` }}
              </div>
            </div>
          </template>
        </Autocomplete>
        <ErrorMessage class="mt-3" v-if="error" :message="error" />
      </div>
    </template>
    <template #actions>
      <div class="flex flex-col gap-2">
        <Button
          v-if="dirty"
          class="w-full"
          :label="__('Reset')"
          @click="reset"
        />
        <Button
          class="w-full"
          :label="__('Save')"
          variant="solid"
          @click="update"
          :loading="loading"
          :disabled="!dirty"
        />
      </div>
    </template>
  </Dialog>
</template>
<script setup>
import DragVerticalIcon from '@/components/Icons/DragVerticalIcon.vue'
import Autocomplete from '@/components/frappe-ui/Autocomplete.vue'
import { getMeta } from '@/stores/meta'
import Draggable from 'vuedraggable'
import { Dialog, ErrorMessage } from 'frappe-ui'
import { ref, computed } from 'vue'

const props = defineProps({
  doctype: String,
  parentDoctype: String,
})

const { getFields, getGridViewSettings, saveUserSettings } = getMeta(
  props.doctype,
)

const show = defineModel()

const loading = ref(false)
const error = ref(null)

const dirty = computed(() => {
  return JSON.stringify(fields.value) !== JSON.stringify(oldFields.value)
})

const oldFields = computed(() => {
  let _fields = getFields()
  let gridViewSettings = getGridViewSettings(props.parentDoctype)

  if (gridViewSettings.length) {
    return gridViewSettings.map((field) => {
      let f = _fields.find((f) => f.fieldname === field.fieldname)
      if (f) {
        f.columns = field.columns
        return fieldObj(f)
      }
    })
  }
  return _fields?.filter((field) => field.in_list_view).map((f) => fieldObj(f))
})

const fields = ref(JSON.parse(JSON.stringify(oldFields.value || [])))

const dropdownFields = computed(() => {
  return getFields()?.filter((field) => {
    return (
      !fields.value.find((f) => f.fieldname === field.fieldname) &&
      !['Tab Break', 'Section Break', 'Column Break', 'Table'].includes(
        field.fieldtype,
      )
    )
  })
})

function reset() {
  fields.value = JSON.parse(JSON.stringify(oldFields.value || []))
}

function addField(field) {
  fields.value.push(fieldObj(field))
}

function removeField(field) {
  const index = fields.value.findIndex((f) => f.fieldname === field.fieldname)
  fields.value.splice(index, 1)
}

function update() {
  loading.value = true

  let updateFields = fields.value.map((field) => {
    return {
      fieldname: field.fieldname,
      columns: field.columns,
    }
  })

  if (updateFields.length === 0) {
    error.value = __('At least one field is required')
    return
  }

  saveUserSettings(props.parentDoctype, 'GridView', updateFields, () => {
    loading.value = false
    show.value = false
  })
}

function fieldObj(field) {
  return {
    label: field.label,
    fieldname: field.fieldname,
    fieldtype: field.fieldtype,
    options: field.options,
    in_list_view: field.in_list_view,
    columns: field.columns || 2,
  }
}
</script>
