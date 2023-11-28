<template>
  <NestedPopover>
    <template #target>
      <Button label="View Settings">
        <template #prefix>
          <SettingsIcon class="h-4" />
        </template>
      </Button>
    </template>
    <template #body>
      <div
        class="my-2 rounded-lg border border-gray-100 bg-white p-1.5 shadow-xl"
      >
        <Draggable
          :list="columns"
          @end="onEnd"
          item-key="key"
          class="list-group"
        >
          <template #item="{ element }">
            <div
              class="flex cursor-grab items-center justify-between gap-6 rounded px-2 py-1.5 text-base text-gray-800 hover:bg-gray-100"
            >
              <div class="flex items-center gap-2">
                <DragIcon class="h-3.5" />
                <div>{{ element.label }}</div>
              </div>
              <div class="flex cursor-pointer items-center gap-1">
                <Button variant="ghost" class="!h-5 w-5 !p-1">
                  <EditIcon class="h-3.5" />
                </Button>
                <Button
                  variant="ghost"
                  class="!h-5 w-5 !p-1"
                  @click="removeColumn(element)"
                >
                  <FeatherIcon name="x" class="h-3.5" />
                </Button>
              </div>
            </div>
          </template>
        </Draggable>
        <div class="mt-1.5 border-t pt-1.5">
          <Autocomplete
            value=""
            :options="fields"
            @change="(e) => addColumn(e)"
          >
            <template #target="{ togglePopover }">
              <Button
                class="w-full !justify-start !text-gray-600"
                variant="ghost"
                @click="togglePopover()"
                label="Add Column"
              >
                <template #prefix>
                  <FeatherIcon name="plus" class="h-4" />
                </template>
              </Button>
            </template>
          </Autocomplete>
        </div>
      </div>
    </template>
  </NestedPopover>
</template>

<script setup>
import SettingsIcon from '@/components/Icons/SettingsIcon.vue'
import EditIcon from '@/components/Icons/EditIcon.vue'
import DragIcon from '@/components/Icons/DragIcon.vue'
import NestedPopover from '@/components/NestedPopover.vue'
import Autocomplete from '@/components/frappe-ui/Autocomplete.vue'
import Draggable from 'vuedraggable'
import { computed, defineModel } from 'vue'
import { FeatherIcon, call } from 'frappe-ui'

const props = defineProps({
  doctype: {
    type: String,
    required: true,
  },
})

const list = defineModel()

const columns = computed({
  get: () => list.value?.data?.columns,
  set: (val) => {
    list.value.data.columns = val
  },
})

const rows = computed({
  get: () => list.value?.data?.rows,
  set: (val) => {
    list.value.data.rows = val
  },
})

const fields = computed(() => {
  let allFields = list.value?.data?.fields
  if (!allFields) return []

  return allFields.filter((field) => {
    return !columns.value.find((column) => column.key === field.value)
  })
})

async function addColumn(c) {
  let column = {
    label: c.label,
    key: c.value,
    width: '10rem',
  }
  columns.value.push(column)
  rows.value.push(c.value)
  await onEnd()
  list.value.reload()
}

function removeColumn(c) {
  columns.value = columns.value.filter((column) => column.key !== c.key)
  rows.value = rows.value.filter((row) => row !== c.key)
  onEnd()
}

async function onEnd() {
  await call(
    'crm.fcrm.doctype.crm_list_view_settings.crm_list_view_settings.update',
    {
      doctype: props.doctype,
      columns: columns.value,
      rows: rows.value,
    }
  )
}
</script>
