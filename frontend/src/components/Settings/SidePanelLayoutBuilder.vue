<template>
  <div>
    <Draggable :list="sections" item-key="label" class="flex flex-col gap-5.5">
      <template #item="{ element: section }">
        <div class="flex flex-col gap-3">
          <div
            class="flex items-center justify-between rounded px-2.5 py-2 bg-gray-50"
          >
            <div
              class="flex max-w-fit cursor-pointer items-center gap-2 text-base leading-4"
              @click="section.opened = !section.opened"
            >
              <FeatherIcon
                name="chevron-right"
                class="h-4 text-gray-900 transition-all duration-300 ease-in-out"
                :class="{ 'rotate-90': section.opened }"
              />
              <div v-if="!section.editingLabel">
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
                  class="!size-4 rounded-sm"
                  variant="ghost"
                  @click.stop="section.editingLabel = false"
                />
              </div>
            </div>
            <div class="flex gap-1 items-center">
              <Button
                v-if="!section.editingLabel"
                class="!size-4 rounded-sm"
                variant="ghost"
                @click="section.editingLabel = true"
              >
                <EditIcon class="h-3.5" />
              </Button>
              <Button
                v-if="section.editable !== false"
                class="!size-4 rounded-sm"
                icon="x"
                variant="ghost"
                @click="sections.splice(sections.indexOf(section), 1)"
              />
            </div>
          </div>
          <div v-show="section.opened">
            <Draggable
              :list="section.fields"
              group="fields"
              item-key="label"
              class="flex flex-col gap-1.5"
              handle=".cursor-grab"
            >
              <template #item="{ element: field }">
                <div
                  class="px-2.5 py-2 border rounded text-base leading-4 text-gray-800 flex items-center justify-between gap-2"
                >
                  <div class="flex items-center gap-2">
                    <DragVerticalIcon class="h-3.5 cursor-grab" />
                    <div>{{ field.label }}</div>
                  </div>
                  <Button
                    variant="ghost"
                    icon="x"
                    class="!size-4 rounded-sm"
                    @click="
                      section.fields.splice(section.fields.indexOf(field), 1)
                    "
                  />
                </div>
              </template>
            </Draggable>
            <Autocomplete
              v-if="fields.data && section.editable !== false"
              value=""
              :options="fields.data"
              @change="(e) => addField(section, e)"
            >
              <template #target="{ togglePopover }">
                <Button
                  class="w-full h-8 mt-1.5 !border-gray-200 hover:!border-gray-300"
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
            <div
              v-else
              class="flex justify-center items-center border rounded border-dashed p-3"
            >
              <div class="text-sm text-gray-500">
                {{ __('This section is not editable') }}
              </div>
            </div>
          </div>
        </div>
      </template>
    </Draggable>
    <div class="mt-5.5">
      <Button
        class="w-full h-8"
        variant="subtle"
        :label="__('Add Section')"
        @click="
          sections.push({ label: __('New Section'), opened: true, fields: [] })
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
import EditIcon from '@/components/Icons/EditIcon.vue'
import Autocomplete from '@/components/frappe-ui/Autocomplete.vue'
import DragVerticalIcon from '@/components/Icons/DragVerticalIcon.vue'
import Draggable from 'vuedraggable'
import { Input, createResource } from 'frappe-ui'
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

watch(
  () => props.doctype,
  () => fields.fetch(params.value),
  { immediate: true },
)
</script>
