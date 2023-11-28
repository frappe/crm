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
        <div v-if="!edit">
          <Draggable
            :list="columns"
            @end="updateColumnDetails"
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
                  <Button
                    variant="ghost"
                    class="!h-5 w-5 !p-1"
                    @click="editColumn(element)"
                  >
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
        <div v-else>
          <div
            class="flex flex-col items-center justify-between gap-2 rounded px-2 py-1.5 text-base text-gray-800"
          >
            <div class="flex flex-col items-center gap-3">
              <FormControl
                type="text"
                size="md"
                label="Label"
                v-model="column.label"
                class="w-full"
                placeholder="Column Label"
              />
              <FormControl
                type="text"
                size="md"
                label="Width"
                class="w-full"
                v-model="column.width"
                placeholder="Column Width"
                description="Width can be in number, pixel or rem (eg. 3, 30px, 10rem)"
              />
            </div>
            <div class="flex w-full gap-2 border-t pt-2">
              <Button
                variant="subtle"
                label="Cancel"
                class="w-full flex-1"
                @click="cancelUpdate"
              />
              <Button
                variant="solid"
                label="Update"
                class="w-full flex-1"
                @click="updateColumn(column)"
              />
            </div>
          </div>
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
import { computed, defineModel, ref } from 'vue'
import { FeatherIcon, FormControl, call } from 'frappe-ui'

const props = defineProps({
  doctype: {
    type: String,
    required: true,
  },
})

const list = defineModel()
const edit = ref(false)
const column = ref({
  old: {},
  label: '',
  key: '',
  width: '10rem',
})

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
  let _column = {
    label: c.label,
    key: c.value,
    width: '10rem',
  }
  columns.value.push(_column)
  rows.value.push(c.value)
  await updateColumnDetails()
  list.value.reload()
}

function removeColumn(c) {
  columns.value = columns.value.filter((column) => column.key !== c.key)
  if (c.key !== 'name') {
    rows.value = rows.value.filter((row) => row !== c.key)
  }
  updateColumnDetails()
}

function editColumn(c) {
  edit.value = true
  column.value = c
  column.value.old = { ...c }
}

function updateColumn(c) {
  edit.value = false
  let index = columns.value.findIndex((column) => column.key === c.key)
  columns.value[index].label = c.label
  columns.value[index].width = c.width
  updateColumnDetails()
}

function cancelUpdate() {
  edit.value = false
  column.value = {
    ...column.value.old,
    old: {},
  }
}

async function updateColumnDetails() {
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
