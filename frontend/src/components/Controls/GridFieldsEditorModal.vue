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
          v-if="oldFields.length"
          :list="fields"
          @end="reorder"
          group="fields"
          item-key="name"
          class="flex flex-col gap-1"
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
                <Button variant="ghost" icon="x" @click="removeField(field)" />
              </div>
            </div>
          </template>
        </Draggable>
        <Autocomplete
          v-if="fields"
          value=""
          :options="fields"
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
            <div class="flex flex-col gap-1">
              <div>{{ option.label }}</div>
              <div class="text-ink-gray-4 text-sm">
                {{ `${option.fieldname} - ${option.fieldtype}` }}
              </div>
            </div>
          </template>
        </Autocomplete>
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
import Autocomplete from '@/components/frappe-ui/Autocomplete.vue'
import { getMeta } from '@/stores/meta'
import Draggable from 'vuedraggable'
import { Dialog } from 'frappe-ui'
import { ref, computed } from 'vue'

const props = defineProps({
  doctype: String,
  parentDoctype: String,
})

const { userSettings, getFields, getGridSettings, saveUserSettings } = getMeta(
  props.doctype,
)

const show = defineModel()

const loading = ref(false)

const dirty = computed(() => {
  return JSON.stringify(fields.value) !== JSON.stringify(oldFields.value)
})

const oldFields = computed(() => {
  let _fields = getFields()
  let gridSettings = getGridSettings()

  if (gridSettings.length) {
    return gridSettings.map((field) => {
      return _fields.find((f) => f.fieldname === field.fieldname)
    })
  }
  return _fields?.filter((field) => field.in_list_view)
})

const fields = ref(JSON.parse(JSON.stringify(oldFields.value)) || [])

function reset() {
  fields.value = JSON.parse(JSON.stringify(oldFields.value))
}

function addField(field) {
  fields.value.push(field)
}

function removeField(field) {
  const index = fields.value.findIndex((f) => f.name === field.name)
  fields.value.splice(index, 1)
}

const update = () => {
  loading.value = true

  let updateFields = fields.value.map((field, idx) => {
    return {
      fieldname: field.fieldname,
      columns: 2,
    }
  })

  saveUserSettings(props.parentDoctype, 'GridView', updateFields, () => {
    loading.value = false
    show.value = false
    userSettings.value['GridView'][props.doctype] = updateFields
  })
}
</script>
