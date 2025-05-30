<template>
  <div class="flex flex-col flex-1 text-base">
    <div v-if="label" class="mb-1.5 text-sm text-ink-gray-5">
      {{ __(label) }}
    </div>

    <div
      v-if="fields?.length"
      class="rounded border border-outline-gray-modals"
    >
      <!-- Header -->
      <div
        class="grid-header flex items-center rounded-t-[7px] bg-surface-gray-2 text-ink-gray-5 truncate"
      >
        <div
          class="inline-flex items-center justify-center border-r border-outline-gray-2 h-8 p-2 w-12"
        >
          <Checkbox
            class="cursor-pointer duration-300"
            :modelValue="allRowsSelected"
            @click.stop="toggleSelectAllRows($event.target.checked)"
          />
        </div>
        <div
          class="inline-flex items-center justify-center border-r border-outline-gray-2 py-2 px-1 w-12"
        >
          {{ __('No') }}
        </div>
        <div
          class="grid w-full truncate"
          :style="{ gridTemplateColumns: gridTemplateColumns }"
        >
          <div
            v-for="field in fields"
            class="border-r border-outline-gray-2 p-2 truncate"
            :key="field.fieldname"
            :title="field.label"
          >
            {{ __(field.label) }}
          </div>
        </div>
        <div class="w-12">
          <Button
            class="flex w-full items-center justify-center rounded !bg-surface-gray-2 border-0"
            variant="outline"
            @click="showGridFieldsEditorModal = true"
          >
            <FeatherIcon name="settings" class="h-4 w-4 text-ink-gray-7" />
          </Button>
        </div>
      </div>
      <!-- Rows -->
      <template v-if="rows?.length">
        <Draggable
          class="w-full"
          v-model="rows"
          :delay="isTouchScreenDevice() ? 200 : 0"
          group="rows"
          item-key="name"
        >
          <template #item="{ element: row, index }">
            <div
              class="grid-row flex cursor-pointer items-center border-b border-outline-gray-modals bg-surface-modals last:rounded-b last:border-b-0"
              @click.stop="
                () => {
                  if (!gridSettings.editable_grid) {
                    showRowList[index] = true
                  }
                }
              "
            >
              <div
                class="grid-row-checkbox inline-flex h-9.5 items-center bg-surface-white justify-center border-r border-outline-gray-modals p-2 w-12"
              >
                <Checkbox
                  class="cursor-pointer duration-300"
                  :modelValue="selectedRows.has(row.name)"
                  @click.stop="toggleSelectRow(row)"
                />
              </div>
              <div
                class="flex h-9.5 items-center justify-center bg-surface-white border-r border-outline-gray-modals py-2 px-1 text-sm text-ink-gray-8 w-12"
              >
                {{ index + 1 }}
              </div>
              <div
                class="grid w-full h-9.5"
                :style="{ gridTemplateColumns: gridTemplateColumns }"
              >
                <div
                  class="border-r border-outline-gray-modals h-full"
                  v-for="field in fields"
                  :key="field.fieldname"
                >
                  <FormControl
                    v-if="field.read_only && field.fieldtype !== 'Check'"
                    type="text"
                    :placeholder="field.placeholder"
                    v-model="row[field.fieldname]"
                    :disabled="true"
                  />
                  <Link
                    v-else-if="
                      ['Link', 'Dynamic Link'].includes(field.fieldtype)
                    "
                    class="text-sm text-ink-gray-8"
                    v-model="row[field.fieldname]"
                    :doctype="
                      field.fieldtype == 'Link'
                        ? field.options
                        : row[field.options]
                    "
                    :filters="field.filters"
                  />
                  <Link
                    v-else-if="field.fieldtype === 'User'"
                    class="form-control"
                    :value="getUser(row[field.fieldname]).full_name"
                    :doctype="field.options"
                    :filters="field.filters"
                    @change="(v) => (row[field.fieldname] = v)"
                    :placeholder="field.placeholder"
                    :hideMe="true"
                  >
                    <template #prefix>
                      <UserAvatar
                        class="mr-2"
                        :user="row[field.fieldname]"
                        size="sm"
                      />
                    </template>
                    <template #item-prefix="{ option }">
                      <UserAvatar class="mr-2" :user="option.value" size="sm" />
                    </template>
                    <template #item-label="{ option }">
                      <Tooltip :text="option.value">
                        <div class="cursor-pointer">
                          {{ getUser(option.value).full_name }}
                        </div>
                      </Tooltip>
                    </template>
                  </Link>
                  <div
                    v-else-if="field.fieldtype === 'Check'"
                    class="flex h-full bg-surface-white justify-center items-center"
                  >
                    <Checkbox
                      class="cursor-pointer duration-300"
                      v-model="row[field.fieldname]"
                      :disabled="!gridSettings.editable_grid"
                    />
                  </div>
                  <DatePicker
                    v-else-if="field.fieldtype === 'Date'"
                    v-model="row[field.fieldname]"
                    icon-left=""
                    variant="outline"
                    :formatter="(date) => getFormat(date, '', true)"
                    input-class="border-none text-sm text-ink-gray-8"
                  />
                  <DateTimePicker
                    v-else-if="field.fieldtype === 'Datetime'"
                    v-model="row[field.fieldname]"
                    icon-left=""
                    variant="outline"
                    :formatter="(date) => getFormat(date, '', true, true)"
                    input-class="border-none text-sm text-ink-gray-8"
                  />
                  <FormControl
                    v-else-if="
                      ['Small Text', 'Text', 'Long Text', 'Code'].includes(
                        field.fieldtype,
                      )
                    "
                    rows="1"
                    type="textarea"
                    variant="outline"
                    v-model="row[field.fieldname]"
                  />
                  <FormControl
                    v-else-if="['Int'].includes(field.fieldtype)"
                    type="number"
                    variant="outline"
                    v-model="row[field.fieldname]"
                  />
                  <FormControl
                    v-else-if="field.fieldtype === 'Select'"
                    class="text-sm text-ink-gray-8"
                    type="select"
                    variant="outline"
                    v-model="row[field.fieldname]"
                    :options="field.options"
                  />
                  <FormControl
                    v-else
                    class="text-sm text-ink-gray-8"
                    type="text"
                    variant="outline"
                    v-model="row[field.fieldname]"
                    :options="field.options"
                  />
                </div>
              </div>
              <div class="edit-row w-12">
                <Button
                  class="flex w-full items-center justify-center rounded border-0"
                  variant="outline"
                  @click="showRowList[index] = true"
                >
                  <EditIcon class="h-4 w-4 text-ink-gray-7" />
                </Button>
              </div>
              <GridRowModal
                v-if="showRowList[index]"
                v-model="showRowList[index]"
                v-model:showGridRowFieldsModal="showGridRowFieldsModal"
                :index="index"
                :data="row"
                :doctype="doctype"
                :parentDoctype="parentDoctype"
              />
            </div>
          </template>
        </Draggable>
      </template>

      <div
        v-else
        class="flex flex-col items-center rounded p-5 text-sm text-ink-gray-5"
      >
        {{ __('No Data') }}
      </div>
    </div>

    <div v-if="fields?.length" class="mt-2 flex flex-row gap-2">
      <Button
        v-if="showDeleteBtn"
        :label="__('Delete')"
        variant="solid"
        theme="red"
        @click="deleteRows"
      />
      <Button :label="__('Add Row')" @click="addRow" />
    </div>
    <GridRowFieldsModal
      v-if="showGridRowFieldsModal"
      v-model="showGridRowFieldsModal"
      :doctype="doctype"
      :parentDoctype="parentDoctype"
    />
    <GridFieldsEditorModal
      v-if="showGridFieldsEditorModal"
      v-model="showGridFieldsEditorModal"
      :doctype="doctype"
      :parentDoctype="parentDoctype"
    />
  </div>
</template>

<script setup>
import GridFieldsEditorModal from '@/components/Controls/GridFieldsEditorModal.vue'
import GridRowFieldsModal from '@/components/Controls/GridRowFieldsModal.vue'
import GridRowModal from '@/components/Controls/GridRowModal.vue'
import EditIcon from '@/components/Icons/EditIcon.vue'
import Link from '@/components/Controls/Link.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import { getRandom, getFormat, isTouchScreenDevice } from '@/utils'
import { usersStore } from '@/stores/users'
import { getMeta } from '@/stores/meta'
import {
  FeatherIcon,
  FormControl,
  Checkbox,
  DateTimePicker,
  DatePicker,
  Tooltip,
} from 'frappe-ui'
import Draggable from 'vuedraggable'
import { ref, reactive, computed } from 'vue'

const props = defineProps({
  label: {
    type: String,
    default: '',
  },
  doctype: {
    type: String,
    required: true,
  },
  parentDoctype: {
    type: String,
    required: true,
  },
})

const { getGridViewSettings, getFields, getGridSettings } = getMeta(
  props.doctype,
)
getMeta(props.parentDoctype)
const { getUser } = usersStore()

const rows = defineModel()
const showRowList = ref(new Array(rows.value?.length || []).fill(false))
const selectedRows = reactive(new Set())

const showGridFieldsEditorModal = ref(false)
const showGridRowFieldsModal = ref(false)

const gridSettings = computed(() => getGridSettings())

const fields = computed(() => {
  let gridViewSettings = getGridViewSettings(props.parentDoctype)
  let gridFields = getFields()
  if (gridViewSettings.length) {
    let d = gridViewSettings.map((gs) =>
      getFieldObj(gridFields.find((f) => f.fieldname === gs.fieldname)),
    )
    return d
  }
  return (
    gridFields?.filter((f) => f.in_list_view).map((f) => getFieldObj(f)) || []
  )
})

function getFieldObj(field) {
  return {
    ...field,
    filters: field.link_filters && JSON.parse(field.link_filters),
    placeholder: field.placeholder || field.label,
  }
}

const gridTemplateColumns = computed(() => {
  if (!fields.value?.length) return '1fr'
  // for the checkbox & sr no. columns
  let gridViewSettings = getGridViewSettings(props.parentDoctype)
  if (gridViewSettings.length) {
    return gridViewSettings
      .map((gs) => `minmax(0, ${gs.columns || 2}fr)`)
      .join(' ')
  }
  return fields.value.map(() => `minmax(0, 2fr)`).join(' ')
})

const allRowsSelected = computed(() => {
  if (!rows.value?.length) return false
  return rows.value.length === selectedRows.size
})

const showDeleteBtn = computed(() => selectedRows.size > 0)

const toggleSelectAllRows = (iSelected) => {
  if (iSelected) {
    rows.value?.forEach((row) => selectedRows.add(row.name))
  } else {
    selectedRows.clear()
  }
}

const toggleSelectRow = (row) => {
  if (selectedRows.has(row.name)) {
    selectedRows.delete(row.name)
  } else {
    selectedRows.add(row.name)
  }
}

const addRow = () => {
  const newRow = {}
  fields.value?.forEach((field) => {
    if (field.fieldtype === 'Check') newRow[field.fieldname] = false
    else newRow[field.fieldname] = ''
  })
  newRow.name = getRandom(10)
  showRowList.value.push(false)
  newRow['__islocal'] = true
  rows.value.push(newRow)
}

const deleteRows = () => {
  rows.value = rows.value.filter((row) => !selectedRows.has(row.name))
  showRowList.value.pop()
  selectedRows.clear()
}
</script>

<style scoped>
/* For Input fields */
:deep(.grid-row input:not([type='checkbox'])),
:deep(.grid-row textarea) {
  border: none;
  border-radius: 0;
  height: 38px;
}

:deep(.grid-row input:focus),
:deep(.grid-row input:hover),
:deep(.grid-row textarea:focus),
:deep(.grid-row textarea:hover) {
  box-shadow: none;
}

:deep(.grid-row input:focus-within) :deep(.grid-row textarea:focus-within) {
  border: 1px solid var(--outline-gray-2);
}

/* For select field */
:deep(.grid-row select) {
  border: none;
  border-radius: 0;
  height: 38px;
}

/* For Autocomplete */
:deep(.grid-row button) {
  border: none;
  border-radius: 0;
  background-color: var(--surface-white);
  height: 38px;
}

:deep(.grid-row:last-child .grid-row-checkbox) {
  border-bottom-left-radius: 7px;
}

:deep(.grid-row .edit-row button) {
  border-bottom-right-radius: 7px;
}

:deep(.grid-row button:focus) :deep(.grid-row button:hover) {
  box-shadow: none;
  background-color: var(--surface-white);
}

:deep(.grid-row button:focus-within) {
  border: 1px solid var(--outline-gray-2);
}
</style>
