<template>
  <NestedPopover>
    <template #target>
      <Button :label="__('Columns')">
        <template v-if="hideLabel">
          <ColumnsIcon class="h-4" />
        </template>
        <template v-if="!hideLabel" #prefix>
          <ColumnsIcon class="h-4" />
        </template>
      </Button>
    </template>
    <template #body="{ close }">
      <div
        class="my-2 rounded-lg border border-gray-100 bg-white p-1.5 shadow-xl"
      >
        <div v-if="!edit">
          <Draggable
            :list="columns"
            @end="apply"
            :delay="isTouchScreenDevice() ? 200 : 0"
            item-key="key"
            class="list-group"
          >
            <template #item="{ element }">
              <div
                class="flex cursor-grab items-center justify-between gap-6 rounded px-2 py-1.5 text-base text-gray-800 hover:bg-gray-100"
              >
                <div class="flex items-center gap-2">
                  <DragIcon class="h-3.5" />
                  <div>{{ __(element.label) }}</div>
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
          <div class="mt-1.5 flex flex-col gap-1 border-t pt-1.5">
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
                  :label="__('Add Column')"
                >
                  <template #prefix>
                    <FeatherIcon name="plus" class="h-4" />
                  </template>
                </Button>
              </template>
            </Autocomplete>
            <Button
              v-if="columnsUpdated"
              class="w-full !justify-start !text-gray-600"
              variant="ghost"
              @click="reset(close)"
              :label="__('Reset Changes')"
            >
              <template #prefix>
                <ReloadIcon class="h-4" />
              </template>
            </Button>
            <Button
              v-if="!is_default"
              class="w-full !justify-start !text-gray-600"
              variant="ghost"
              @click="resetToDefault(close)"
              :label="__('Reset to Default')"
            >
              <template #prefix>
                <ReloadIcon class="h-4" />
              </template>
            </Button>
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
                :label="__('Label')"
                v-model="column.label"
                class="sm:w-full w-52"
                :placeholder="__('First Name')"
              />
              <FormControl
                type="text"
                size="md"
                :label="__('Width')"
                class="sm:w-full w-52"
                v-model="column.width"
                placeholder="10rem"
                :description="
                  __(
                    'Width can be in number, pixel or rem (eg. 3, 30px, 10rem)'
                  )
                "
                :debounce="500"
              />
            </div>
            <div class="flex w-full gap-2 border-t pt-2">
              <Button
                variant="subtle"
                :label="__('Cancel')"
                class="w-full flex-1"
                @click="cancelUpdate"
              />
              <Button
                variant="solid"
                :label="__('Update')"
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
import ColumnsIcon from '@/components/Icons/ColumnsIcon.vue'
import EditIcon from '@/components/Icons/EditIcon.vue'
import DragIcon from '@/components/Icons/DragIcon.vue'
import ReloadIcon from '@/components/Icons/ReloadIcon.vue'
import NestedPopover from '@/components/NestedPopover.vue'
import Autocomplete from '@/components/frappe-ui/Autocomplete.vue'
import { isTouchScreenDevice } from '@/utils'
import Draggable from 'vuedraggable'
import { computed, ref } from 'vue'
import { watchOnce } from '@vueuse/core'

const props = defineProps({
  doctype: {
    type: String,
    required: true,
  },
  hideLabel: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update'])
const columnsUpdated = ref(false)

const oldValues = ref({
  columns: [],
  rows: [],
  isDefault: false,
})

const list = defineModel()
const edit = ref(false)
const column = ref({
  old: {},
  label: '',
  key: '',
  width: '10rem',
})

const is_default = computed({
  get: () => list.value?.data?.is_default,
  set: (val) => {
    list.value.data.is_default = val
  },
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

function addColumn(c) {
  let _column = {
    label: c.label,
    type: c.type,
    key: c.value,
    width: '10rem',
  }
  columns.value.push(_column)
  rows.value.push(c.value)
  apply(true)
}

function removeColumn(c) {
  columns.value = columns.value.filter((column) => column.key !== c.key)
  if (c.key !== 'name') {
    rows.value = rows.value.filter((row) => row !== c.key)
  }
  apply()
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

  if (columns.value[index].old) {
    delete columns.value[index].old
  }
  apply()
}

function cancelUpdate() {
  edit.value = false
  column.value.label = column.value.old.label
  column.value.width = column.value.old.width
  delete column.value.old
}

function reset(close) {
  apply(true, false, true)
  close()
}

function resetToDefault(close) {
  apply(true, true)
  close()
}

function apply(reload = false, isDefault = false, reset = false) {
  is_default.value = isDefault
  columnsUpdated.value = true
  let obj = {
    columns: reset ? oldValues.value.columns : columns.value,
    rows: reset ? oldValues.value.rows : rows.value,
    isDefault: reset ? oldValues.value.isDefault : isDefault,
    reload,
    reset,
  }
  emit('update', obj)

  if (reload) {
    // will have think of a better way to do this
    setTimeout(() => {
      is_default.value = reset ? oldValues.value.isDefault : isDefault
      columnsUpdated.value = !reset
    }, 100)
  }
}

watchOnce(
  () => list.value.data,
  (val) => {
    if (!val) return
    oldValues.value.columns = JSON.parse(JSON.stringify(val.columns))
    oldValues.value.rows = JSON.parse(JSON.stringify(val.rows))
    oldValues.value.isDefault = val.is_default
  }
)
</script>
