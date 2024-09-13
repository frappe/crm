<template>
  <div>
    <Draggable :list="sections" item-key="label" class="flex flex-col gap-5.5">
      <template #item="{ element: section }">
        <div class="flex flex-col gap-1.5 p-2.5 bg-gray-50 rounded">
          <div class="flex items-center justify-between">
            <div
              class="flex h-7 max-w-fit cursor-pointer items-center gap-2 text-base font-medium leading-4"
            >
              <div
                v-if="!section.editingLabel"
                :class="section.hideLabel ? 'text-gray-400' : ''"
              >
                {{ __(section.label) || __('Untitled') }}
              </div>
              <div v-else class="flex gap-2 items-center">
                <Input
                  v-model="section.label"
                  @keydown.enter="section.editingLabel = false"
                  @blur="section.editingLabel = false"
                  @click.stop
                />
                <Button
                  v-if="section.editingLabel"
                  icon="check"
                  variant="ghost"
                  @click="section.editingLabel = false"
                />
              </div>
            </div>
            <Dropdown :options="getOptions(section)">
              <template #default>
                <Button variant="ghost">
                  <FeatherIcon name="more-horizontal" class="h-4" />
                </Button>
              </template>
            </Dropdown>
          </div>
          <Draggable
            :list="section.fields"
            group="fields"
            item-key="label"
            class="grid gap-1.5"
            :class="
              section.columns ? 'grid-cols-' + section.columns : 'grid-cols-3'
            "
            handle=".cursor-grab"
          >
            <template #item="{ element: field }">
              <div
                class="px-2.5 py-2 border rounded text-base bg-white text-gray-800 flex items-center leading-4 justify-between gap-2"
              >
                <div class="flex items-center gap-2">
                  <DragVerticalIcon class="h-3.5 cursor-grab" />
                  <div>{{ field.label }}</div>
                </div>
                <Button
                  variant="ghost"
                  class="!size-4 rounded-sm"
                  icon="x"
                  @click="
                    section.fields.splice(section.fields.indexOf(field), 1)
                  "
                />
              </div>
            </template>
          </Draggable>
          <Autocomplete
            v-if="fields.data"
            value=""
            :options="fields.data"
            @change="(e) => addField(section, e)"
          >
            <template #target="{ togglePopover }">
              <div class="gap-2 w-full">
                <Button
                  class="w-full !h-8 !border-gray-200 hover:!border-gray-300"
                  variant="outline"
                  @click="togglePopover()"
                  :label="__('Add Field')"
                >
                  <template #prefix>
                    <FeatherIcon name="plus" class="h-4" />
                  </template>
                </Button>
              </div>
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
    </Draggable>
    <div class="mt-5.5">
      <Button
        class="w-full h-8"
        variant="subtle"
        :label="__('Add Section')"
        @click="
          sections.push({
            label: __('New Section'),
            opened: true,
            fields: [],
          })
        "
      >
        <template #prefix>
          <FeatherIcon name="plus" class="h-4" />
        </template>
      </Button>
    </div>
  </div>
</template>
<script setup>
import Autocomplete from '@/components/frappe-ui/Autocomplete.vue'
import DragVerticalIcon from '@/components/Icons/DragVerticalIcon.vue'
import Draggable from 'vuedraggable'
import { Dropdown, createResource } from 'frappe-ui'
import { computed, watch } from 'vue'

const props = defineProps({
  sections: Object,
  doctype: String,
})

const restrictedFieldTypes = [
  'Table',
  'Geolocation',
  'Attach',
  'Attach Image',
  'HTML',
  'Signature',
]

const params = computed(() => {
  return {
    doctype: props.doctype,
    restricted_fieldtypes: restrictedFieldTypes,
    as_array: true,
  }
})

const fields = createResource({
  url: 'crm.api.doc.get_fields_meta',
  params: params.value,
  cache: ['fieldsMeta', props.doctype],
  auto: true,
})

function addField(section, field) {
  if (!field) return
  section.fields.push(field)
}

function getOptions(section) {
  return [
    {
      label: 'Edit',
      icon: 'edit',
      onClick: () => (section.editingLabel = true),
      condition: () => section.editable !== false,
    },
    {
      label: section.hideLabel ? 'Show Label' : 'Hide Label',
      icon: section.hideLabel ? 'eye' : 'eye-off',
      onClick: () => (section.hideLabel = !section.hideLabel),
    },
    {
      label: section.hideBorder ? 'Show Border' : 'Hide Border',
      icon: 'minus',
      onClick: () => (section.hideBorder = !section.hideBorder),
    },
    {
      label: 'Add Column',
      icon: 'columns',
      onClick: () =>
        (section.columns = section.columns ? section.columns + 1 : 4),
      condition: () => !section.columns || section.columns < 4,
    },
    {
      label: 'Remove Column',
      icon: 'columns',
      onClick: () =>
        (section.columns = section.columns ? section.columns - 1 : 2),
      condition: () => !section.columns || section.columns > 1,
    },
    {
      label: 'Remove Section',
      icon: 'trash-2',
      onClick: () => props.sections.splice(props.sections.indexOf(section), 1),
      condition: () => section.editable !== false,
    },
  ]
}

watch(
  () => props.doctype,
  () => fields.fetch(params.value),
  { immediate: true },
)
</script>
