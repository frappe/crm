<template>
  <Popover placement="bottom-end">
    <template #target="{ togglePopover }">
      <Button :label="__('Columns')" @click="togglePopover">
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
        class="my-2 p-1.5 min-w-40 rounded-lg bg-surface-modal shadow-2xl ring-1 ring-black ring-opacity-5 focus:outline-none"
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
                class="flex cursor-grab items-center justify-between gap-6 rounded px-2 py-1.5 text-base text-ink-gray-8 hover:bg-surface-gray-2"
              >
                <div class="flex items-center gap-2">
                  <DragIcon class="h-3.5" />
                  <div>{{ __(element.label) }}</div>
                </div>
                <div class="flex cursor-pointer items-center gap-0.5">
                  <Button
                    variant="ghost"
                    class="!h-5 w-5 !p-1"
                    @click="editColumn(element)"
                  >
                    <template #icon>
                      <EditIcon class="h-3.5" />
                    </template>
                  </Button>
                  <Button
                    variant="ghost"
                    class="!h-5 w-5 !p-1"
                    @click="removeColumn(element)"
                  >
                    <template #icon>
                      <FeatherIcon name="x" class="h-3.5" />
                    </template>
                  </Button>
                </div>
              </div>
            </template>
          </Draggable>
          <div
            class="mt-1.5 flex flex-col gap-1 border-t border-outline-gray-modals pt-1.5"
          >
            <Autocomplete
              value=""
              :options="fields"
              @change="(e) => addColumn(e)"
            >
              <template #target="{ togglePopover }">
                <Button
                  class="w-full !justify-start !text-ink-gray-5"
                  variant="ghost"
                  :label="__('Add Column')"
                  iconLeft="plus"
                  @click="togglePopover"
                />
              </template>
              <template #item-label="{ option }">
                <Tooltip :text="option.fieldname">
                  <div class="flex-1 truncate text-ink-gray-7">
                    {{ option.label }}
                  </div>
                </Tooltip>
              </template>
            </Autocomplete>
            <Button
              v-if="columnsUpdated"
              class="w-full !justify-start !text-ink-gray-5"
              variant="ghost"
              :label="__('Reset Changes')"
              :iconLeft="ReloadIcon"
              @click="reset(close)"
            />
          </div>
        </div>
        <div v-else>
          <div
            class="flex flex-col items-center justify-between gap-2 rounded px-2 py-1.5 text-base text-ink-gray-8"
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
                    'Width can be in number, pixel or rem (eg. 3, 30px, 10rem)',
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
  </Popover>
</template>

<script setup>
import ColumnsIcon from '@/components/Icons/ColumnsIcon.vue'
import EditIcon from '@/components/Icons/EditIcon.vue'
import DragIcon from '@/components/Icons/DragIcon.vue'
import ReloadIcon from '@/components/Icons/ReloadIcon.vue'
import Autocomplete from '@/components/frappe-ui/Autocomplete.vue'
import { getMeta } from '@/stores/meta'
import Draggable from 'vuedraggable'
import { useViews } from '@/stores/view'
import { isTouchScreenDevice } from '@/utils'
import { watchOnce } from '@vueuse/core'
import { Popover, Tooltip } from 'frappe-ui'
import { computed, ref } from 'vue'

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

const { getValueFields } = getMeta(props.doctype)
const { currentView } = useViews(props.doctype)

const emit = defineEmits(['update'])
const columnsUpdated = ref(false)

const oldValues = ref({
  columns: [],
  rows: [],
  isDefault: false,
})

const edit = ref(false)
const column = ref({
  old: {},
  label: '',
  key: '',
  width: '10rem',
})

const isDefault = computed({
  get: () => currentView?.value?.is_default,
  set: (val) => {
    currentView.value.is_default = val
  },
})

const columns = computed({
  get: () => currentView?.value?.columns,
  set: (val) => {
    currentView.value.columns = val
  },
})

const rows = computed({
  get: () => currentView?.value?.rows,
  set: (val) => {
    currentView.value.rows = val
  },
})

const fields = computed(() => {
  let allFields = getValueFields()
  if (!allFields) return []

  return allFields.filter((field) => {
    return !columns.value?.find((column) => column.key === field.fieldname)
  })
})

function addColumn(c) {
  if (!c) return
  let align = ['Float', 'Int', 'Percent', 'Currency'].includes(c.type)
    ? 'right'
    : 'left'
  let _column = {
    label: c.label,
    type: c.fieldtype,
    key: c.fieldname,
    width: '10rem',
    align,
  }
  columns.value.push(_column)
  rows.value.push(c.value)
  apply()
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
  apply(true)
  close()
}

function apply(reset = false) {
  if (reset) {
    columns.value = JSON.parse(JSON.stringify(oldValues.value.columns))
    rows.value = JSON.parse(JSON.stringify(oldValues.value.rows))
    isDefault.value = oldValues.value.isDefault
    columnsUpdated.value = false
  } else {
    columnsUpdated.value = true
  }

  emit('update')
}

watchOnce(
  () => currentView.value,
  (val) => {
    if (!val) return
    oldValues.value.columns = JSON.parse(JSON.stringify(val.columns))
    oldValues.value.rows = JSON.parse(JSON.stringify(val.rows))
    oldValues.value.isDefault = val.is_default
  },
)
</script>
