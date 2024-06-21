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
      <div class="text-base text-gray-800 mb-2">Column Field</div>
      <Autocomplete
        v-if="fields.data"
        value=""
        :options="fields.data"
        @change="(f) => (column_field = f)"
      >
        <template #target="{ togglePopover }">
          <Button
            class="w-full !justify-start"
            variant="subtle"
            @click="togglePopover()"
            :label="column_field.label"
          />
        </template>
      </Autocomplete>
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
import KanbanIcon from '@/components/Icons/KanbanIcon.vue'
import Autocomplete from '@/components/frappe-ui/Autocomplete.vue'
import { Dialog, createResource } from 'frappe-ui'
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

const column_field = computed({
  get: () => {
    let fieldname = list.value?.params?.column_field
    if (!fieldname) return ''
    return fields.data.find((field) => field.name === fieldname)
  },
  set: (val) => {
    list.value.params.column_field = val.name
  },
})

const fields = createResource({
  url: 'crm.api.doc.get_kanban_fields',
  params: { doctype: props.doctype },
  cache: ['kanban_fields', props.doctype],
  auto: true,
  onSuccess: (data) => {
    // data
  },
})

function apply() {
  nextTick(() => {
    showDialog.value = false
    emit('update', {
      column_field: column_field.value.name,
    })
  })
}
</script>
