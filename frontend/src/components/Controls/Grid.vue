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
          {{ __('No.') }}
        </div>
        <div
          class="grid w-full truncate"
          :style="{ gridTemplateColumns: gridTemplateColumns }"
        >
          <div
            v-for="field in fields"
            :key="field.fieldname"
            class="border-r border-outline-gray-2 p-2 truncate"
            :class="
              ['Int', 'Float', 'Currency', 'Percent'].includes(field.fieldtype)
                ? 'text-right'
                : ''
            "
            :title="field.label"
          >
            {{ __(field.label) }}
            <span
              v-if="
                field.reqd ||
                (field.mandatory_depends_on && field.mandatory_via_depends_on)
              "
              class="text-ink-red-2"
              >*</span
            >
          </div>
        </div>
        <div class="flex items-center justify-center w-12">
          <Button
            :tooltip="__('Edit Grid Fields')"
            class="rounded !bg-surface-gray-2 border-0 !text-ink-gray-5"
            variant="outline"
            icon="settings"
            @click="showGridFieldsEditorModal = true"
          />
        </div>
      </div>
      <!-- Rows -->
      <template v-if="rows?.length">
        <Draggable
          v-model="rows"
          class="w-full"
          :delay="isTouchScreenDevice() ? 200 : 0"
          group="rows"
          item-key="name"
          @end="reorder"
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
                <template
                  v-for="baseField in fields"
                  :key="baseField.fieldname"
                >
                  <!-- Resolve per-row field overrides -->
                  <div
                    v-if="!getRowFieldObj(baseField, row).hidden"
                    class="border-r border-outline-gray-modals h-9.5"
                  >
                    <template
                      v-for="field in [getRowFieldObj(baseField, row)]"
                      :key="field.fieldname + '-inner'"
                    >
                      <FormControl
                        v-if="
                          field.read_only &&
                          ![
                            'Int',
                            'Float',
                            'Currency',
                            'Percent',
                            'Check',
                            'Duration',
                            'Rating',
                            'Button',
                            'Attach',
                            'Attach Image',
                            'HTML',
                            'Geolocation',
                          ].includes(field.fieldtype)
                        "
                        v-model="row[field.fieldname]"
                        type="text"
                        :placeholder="field.placeholder"
                        :disabled="true"
                      />
                      <Link
                        v-else-if="
                          ['Link', 'Dynamic Link'].includes(field.fieldtype)
                        "
                        class="text-sm text-ink-gray-8"
                        :value="row[field.fieldname]"
                        :doctype="
                          field.fieldtype == 'Link'
                            ? field.options
                            : row[field.options]
                        "
                        :filters="field.filters"
                        :onCreate="
                          (value, close) => field.create(v, field, row, close)
                        "
                        @change="(v) => fieldChange(v, field, row)"
                      />
                      <Link
                        v-else-if="field.fieldtype === 'User'"
                        class="form-control"
                        :value="getUser(row[field.fieldname]).full_name"
                        :doctype="field.options"
                        :filters="field.filters"
                        :placeholder="field.placeholder"
                        :hideMe="true"
                        @change="(v) => fieldChange(v, field, row)"
                      >
                        <template #prefix>
                          <UserAvatar
                            class="mr-2"
                            :user="row[field.fieldname]"
                            size="sm"
                          />
                        </template>
                        <template #item-prefix="{ option }">
                          <UserAvatar
                            class="mr-2"
                            :user="option.value"
                            size="sm"
                          />
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
                          v-model="row[field.fieldname]"
                          class="cursor-pointer duration-300"
                          :disabled="!gridSettings.editable_grid"
                          @change="
                            (e) => fieldChange(e.target.checked, field, row)
                          "
                        />
                      </div>
                      <TimePicker
                        v-else-if="field.fieldtype === 'Time'"
                        :value="row[field.fieldname]"
                        variant="outline"
                        :format="getFormat('', '', false, true, false)"
                        input-class="border-none text-sm text-ink-gray-8"
                        @change="(v) => fieldChange(v, field, row)"
                      />
                      <DatePicker
                        v-else-if="field.fieldtype === 'Date'"
                        :value="row[field.fieldname]"
                        variant="outline"
                        :format="getFormat('', '', true, false, false)"
                        input-class="border-none text-sm text-ink-gray-8"
                        @change="(v) => fieldChange(v, field, row)"
                      />
                      <DateTimePicker
                        v-else-if="field.fieldtype === 'Datetime'"
                        :value="row[field.fieldname]"
                        variant="outline"
                        :format="getFormat('', '', true, true, false)"
                        input-class="border-none text-sm text-ink-gray-8"
                        @change="(v) => fieldChange(v, field, row)"
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
                        :value="row[field.fieldname]"
                        @change="fieldChange($event.target.value, field, row)"
                      />
                      <FormControl
                        v-else-if="field.fieldtype === 'Select'"
                        v-model="row[field.fieldname]"
                        class="text-sm text-ink-gray-8"
                        type="select"
                        variant="outline"
                        :options="field.options"
                        @update:modelValue="(e) => fieldChange(e, field, row)"
                      />
                      <Password
                        v-else-if="field.fieldtype === 'Password'"
                        variant="outline"
                        :value="row[field.fieldname]"
                        :disabled="Boolean(field.read_only)"
                        @change="fieldChange($event.target.value, field, row)"
                      />
                      <FormattedInput
                        v-else-if="field.fieldtype === 'Int'"
                        class="[&_input]:text-right"
                        type="text"
                        variant="outline"
                        :value="row[field.fieldname] || '0'"
                        :disabled="Boolean(field.read_only)"
                        @change="fieldChange($event.target.value, field, row)"
                      />
                      <FormattedInput
                        v-else-if="field.fieldtype === 'Percent'"
                        class="[&_input]:text-right"
                        type="text"
                        variant="outline"
                        :value="getFloatWithPrecision(field.fieldname, row)"
                        :formattedValue="(row[field.fieldname] || '0') + '%'"
                        :disabled="Boolean(field.read_only)"
                        @change="
                          fieldChange(flt($event.target.value), field, row)
                        "
                      />
                      <FormattedInput
                        v-else-if="field.fieldtype === 'Float'"
                        class="[&_input]:text-right"
                        type="text"
                        variant="outline"
                        :value="getFloatWithPrecision(field.fieldname, row)"
                        :formattedValue="row[field.fieldname]"
                        :disabled="Boolean(field.read_only)"
                        @change="
                          fieldChange(flt($event.target.value), field, row)
                        "
                      />
                      <FormattedInput
                        v-else-if="field.fieldtype === 'Currency'"
                        class="[&_input]:text-right"
                        type="text"
                        variant="outline"
                        :value="getCurrencyWithPrecision(field.fieldname, row)"
                        :formattedValue="
                          getFormattedCurrency(field.fieldname, row, parentDoc)
                        "
                        :disabled="Boolean(field.read_only)"
                        @change="
                          fieldChange(flt($event.target.value), field, row)
                        "
                      />
                      <DurationInput
                        v-else-if="field.fieldtype === 'Duration'"
                        :value="row[field.fieldname]"
                        variant="outline"
                        :disabled="Boolean(field.read_only)"
                        @change="(v) => fieldChange(v, field, row)"
                      />
                      <div
                        v-else-if="field.fieldtype === 'Rating'"
                        class="flex h-full w-full items-center overflow-hidden [&_::-webkit-scrollbar]:h-0"
                      >
                        <RatingInput
                          class="flex-nowrap overflow-x-auto px-2"
                          :value="row[field.fieldname]"
                          :disabled="Boolean(field.read_only)"
                          :max="field.options || 5"
                          @change="(v) => fieldChange(v, field, row)"
                        />
                      </div>
                      <div
                        v-else-if="field.fieldtype === 'Button'"
                        class="flex items-center px-1 h-full"
                      >
                        <ButtonControl
                          class="button-control"
                          :label="field.label"
                          :icon="field.icon"
                          :theme="getButtonTheme(field.button_color)"
                          :variant="getButtonVariant(field.button_color)"
                          :disabled="Boolean(field.read_only)"
                          @click="handleButtonClick(field, row)"
                        />
                      </div>
                      <div
                        v-else-if="
                          ['Attach', 'Attach Image'].includes(field.fieldtype)
                        "
                        class="flex h-full w-full items-center"
                      >
                        <AttachControl
                          variant="ghost"
                          class="w-full"
                          :value="row[field.fieldname]"
                          :doctype="doctype"
                          :docname="row.name"
                          :fieldname="field.fieldname"
                          :imageOnly="field.fieldtype === 'Attach Image'"
                          :disabled="Boolean(field.read_only)"
                          @change="(v) => fieldChange(v, field, row)"
                        />
                      </div>
                      <div
                        v-else-if="field.fieldtype === 'HTML'"
                        class="px-2 py-1 overflow-hidden"
                      >
                        <HtmlControl
                          :html="interpolateTemplate(field.options || '', row)"
                        />
                      </div>
                      <div
                        v-else-if="field.fieldtype === 'Geolocation'"
                        class="flex h-full w-full items-center"
                      >
                        <GeolocationControl
                          variant="ghost"
                          class="w-full"
                          :value="row[field.fieldname]"
                          :disabled="Boolean(field.read_only)"
                          @change="(v) => fieldChange(v, field, row)"
                        />
                      </div>
                      <Combobox
                        v-else-if="field.fieldtype === 'Autocomplete'"
                        v-model="row[field.fieldname]"
                        class="combobox"
                        variant="outline"
                        :options="getOptions(field.options)"
                        :placeholder="field.placeholder"
                        :disabled="Boolean(field.read_only)"
                        @update:modelValue="(v) => fieldChange(v, field, row)"
                      />
                      <FormControl
                        v-else
                        v-model="row[field.fieldname]"
                        class="text-sm text-ink-gray-8"
                        type="text"
                        variant="outline"
                        :options="field.options"
                        @change="fieldChange($event.target.value, field, row)"
                      />
                    </template>
                  </div>
                </template>
              </div>
              <div class="edit-row flex items-center justify-center w-12">
                <Button
                  :tooltip="__('Edit Row')"
                  class="rounded border-0 !text-ink-gray-7"
                  variant="outline"
                  :icon="EditIcon"
                  @click="showRowList[index] = true"
                />
              </div>
              <GridRowModal
                v-if="showRowList[index]"
                v-model="showRowList[index]"
                v-model:showGridRowFieldsModal="showGridRowFieldsModal"
                :index="index"
                :data="row"
                :doctype="doctype"
                :parentDoctype="parentDoctype"
                :parentFieldname="parentFieldname"
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
import Password from '@/components/Controls/Password.vue'
import DurationInput from '@/components/Controls/DurationInput.vue'
import RatingInput from '@/components/Controls/RatingInput.vue'
import AttachControl from '@/components/Controls/AttachControl.vue'
import HtmlControl from '@/components/Controls/HtmlControl.vue'
import GeolocationControl from '@/components/Controls/GeolocationControl.vue'
import ButtonControl, {
  getButtonTheme,
  getButtonVariant,
} from '@/components/Controls/ButtonControl.vue'
import FormattedInput from '@/components/Controls/FormattedInput.vue'
import GridFieldsEditorModal from '@/components/Controls/GridFieldsEditorModal.vue'
import GridRowFieldsModal from '@/components/Controls/GridRowFieldsModal.vue'
import GridRowModal from '@/components/Controls/GridRowModal.vue'
import EditIcon from '@/components/Icons/EditIcon.vue'
import Link from '@/components/Controls/Link.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import {
  getRandom,
  getFormat,
  isTouchScreenDevice,
  interpolateTemplate,
} from '@/utils'
import { flt } from '@/utils/numberFormat.js'
import { usersStore } from '@/stores/users'
import { getMeta } from '@/stores/meta'
import { parseLinkFilters } from '@/utils/fieldTransforms'
import { createDocument } from '@/composables/document'
import {
  FormControl,
  Checkbox,
  TimePicker,
  DateTimePicker,
  DatePicker,
  Tooltip,
  dayjs,
  Combobox,
} from 'frappe-ui'
import Draggable from 'vuedraggable'
import { ref, reactive, computed, inject, provide } from 'vue'

const props = defineProps({
  label: { type: String, default: '' },
  doctype: { type: String, required: true },
  parentDoctype: { type: String, required: true },
  parentFieldname: { type: String, required: true },
  overrides: { type: Object, default: () => ({}) },
})

const restrictedFieldTypes = [
  'Section Break',
  'Column Break',
  'Tab Break',
  'Table',
  'Table MultiSelect',
  'Image',
]

const triggerOnChange = inject('triggerOnChange', () => {})
const triggerButton = inject('triggerButton', () => {})
const triggerOnRowAdd = inject('triggerOnRowAdd', () => {})
const triggerOnRowRemove = inject('triggerOnRowRemove', () => {})
const parentFieldPropertyOverrides = inject(
  'fieldPropertyOverrides',
  computed(() => ({})),
)

const {
  getGridViewSettings,
  getFields,
  getFloatWithPrecision,
  getCurrencyWithPrecision,
  getFormattedCurrency,
  getGridSettings,
} = getMeta(props.doctype)
getMeta(props.parentDoctype)
const { users, getUser } = usersStore()

const rows = defineModel({ type: Array, default: () => [] })
const parentDoc = defineModel('parent', { type: Object, default: () => ({}) })

provide('parentDoc', parentDoc)
provide('fieldPropertyOverrides', parentFieldPropertyOverrides)
provide('parentFieldname', props.parentFieldname)

/**
 * Resolve field overrides for a specific row.
 * Priority: row-specific (products.qty:row_name) > column-level (products.qty) > base meta
 */
function getRowFieldObj(field, row) {
  const ov = parentFieldPropertyOverrides.value || {}
  const colKey = `${props.parentFieldname}.${field.fieldname}`
  const rowKey = row?.name ? `${colKey}:${row.name}` : null
  const colOverrides = ov[colKey]
  const rowOverrides = rowKey ? ov[rowKey] : null

  if (!colOverrides && !rowOverrides) return field

  let merged = { ...field }
  if (colOverrides) Object.assign(merged, colOverrides)
  if (rowOverrides) Object.assign(merged, rowOverrides)
  return merged
}

const showRowList = ref(new Array(rows.value?.length || []).fill(false))
const selectedRows = reactive(new Set())

const showGridFieldsEditorModal = ref(false)
const showGridRowFieldsModal = ref(false)

const gridSettings = computed(() => getGridSettings())

const fields = computed(() => {
  let gridViewSettings = getGridViewSettings(props.parentDoctype)
  let gridFields = getFields({
    restrictNoValueFields: false,
    restrictedFieldTypes,
  })

  if (!gridFields?.length) return []

  let processed
  if (gridViewSettings.length) {
    processed = gridViewSettings.map((gs) =>
      getFieldObj(gridFields.find((f) => f.fieldname === gs.fieldname)),
    )
  } else {
    processed =
      gridFields?.filter((f) => f.in_list_view).map((f) => getFieldObj(f)) || []
  }

  // Filter out hidden columns (from script overrides)
  return processed.filter((f) => !f.hidden)
})

const allFields = computed(() => {
  return getFields()?.map((f) => getFieldObj(f)) || []
})

function getFieldObj(field) {
  // Clone to avoid mutating cached meta
  field = { ...field }

  // Merge script property overrides (dot notation: parentFieldname.childFieldname)
  const overrideKey = `${props.parentFieldname}.${field.fieldname}`
  const scriptOverrides = parentFieldPropertyOverrides.value?.[overrideKey]
  if (scriptOverrides) {
    Object.assign(field, scriptOverrides)
  }

  if (field.fieldtype === 'Link' && field.options !== 'User') {
    if (!field.create) {
      field.create = (value, field, row, close) => {
        const callback = (d) => {
          if (d) fieldChange(d.name, field, row)
        }
        createDocument(field.options, value, close, callback)
      }
    }
  }

  if (field.fieldtype === 'Link' && field.options === 'User') {
    field.fieldtype = 'User'
    field.link_filters = JSON.stringify({
      name: ['in', users.data.crmUsers?.map((user) => user.name)],
      ignore_user_type: 1,
      ...(parseLinkFilters(field.link_filters) || {}),
    })
  }

  const fieldObjWithFilters = {
    ...field,
    filters: parseLinkFilters(field.link_filters),
    placeholder: field.placeholder || field.label,
  }

  return {
    ...fieldObjWithFilters,
    ...props.overrides.fields?.find((f) => f.fieldname === field.fieldname),
  }
}

const gridTemplateColumns = computed(() => {
  if (!fields.value?.length) return '1fr'
  let gridViewSettings = getGridViewSettings(props.parentDoctype)
  return fields.value
    .map((f) => {
      const gs = gridViewSettings.length
        ? gridViewSettings.find((g) => g.fieldname === f.fieldname)
        : f
      return `minmax(0, ${gs?.columns || 2}fr)`
    })
    .join(' ')
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
  allFields.value?.forEach((field) => {
    if (field.fieldtype === 'Check') {
      newRow[field.fieldname] = false
    } else {
      newRow[field.fieldname] = ''
    }

    if (field.default) {
      newRow[field.fieldname] = getDefaultValue(field.default, field.fieldtype)
    }
  })
  newRow.name = getRandom(10)
  showRowList.value.push(false)
  newRow['__islocal'] = true
  newRow['idx'] = rows.value.length + 1
  newRow['doctype'] = props.doctype
  newRow['parentfield'] = props.parentFieldname
  newRow['parenttype'] = props.parentDoctype
  rows.value.push(newRow)
  triggerOnRowAdd(newRow)
}

const deleteRows = () => {
  rows.value = rows.value.filter((row) => !selectedRows.has(row.name))
  triggerOnRowRemove(selectedRows, rows.value)

  showRowList.value.pop()
  selectedRows.clear()
}

const reorder = () => {
  rows.value.forEach((row, index) => {
    row.idx = index + 1
  })
}

async function handleButtonClick(field, row) {
  if (typeof field.click === 'function') {
    await field.click(row)
  } else {
    await triggerButton(field.fieldname, row)
  }
}

function fieldChange(value, field, row) {
  value = Array.isArray(value)
    ? value
    : typeof value === 'object' && value !== null && 'value' in value
      ? value.value
      : value

  triggerOnChange(field.fieldname, value, row)
}

function getDefaultValue(defaultValue, fieldtype) {
  if (['Float', 'Currency', 'Percent'].includes(fieldtype)) {
    return flt(defaultValue)
  } else if (fieldtype === 'Check') {
    if (['1', 'true', 'True'].includes(defaultValue)) {
      return true
    } else if (['0', 'false', 'False'].includes(defaultValue)) {
      return false
    }
  } else if (fieldtype === 'Int') {
    return parseInt(defaultValue)
  } else if (defaultValue === 'Today' && fieldtype === 'Date') {
    return dayjs().format('YYYY-MM-DD')
  } else if (
    ['Now', 'now'].includes(defaultValue) &&
    fieldtype === 'Datetime'
  ) {
    return dayjs().format('YYYY-MM-DD HH:mm:ss')
  } else if (['Now', 'now'].includes(defaultValue) && fieldtype === 'Time') {
    return dayjs().format('HH:mm:ss')
  } else if (fieldtype === 'Date') {
    return dayjs(defaultValue).format('YYYY-MM-DD')
  } else if (fieldtype === 'Datetime') {
    return dayjs(defaultValue).format('YYYY-MM-DD HH:mm:ss')
  } else if (fieldtype === 'Time') {
    return dayjs(defaultValue).format('HH:mm:ss')
  }

  return defaultValue
}

const getOptions = (options) => {
  if (Array.isArray(options)) {
    return options
  } else if (typeof options === 'string') {
    return options.split('\n').map((option) => {
      return { label: option, value: option }
    })
  } else {
    return []
  }
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

/* For Autocomplete, Link */
:deep(.grid-row button:not(.button-control):not(.rating-star)),
:deep(.grid-row .combobox > div > div) {
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

:deep(.grid-row button:focus-within:not(.rating-star):not(.button-control)) {
  border: 1px solid var(--outline-gray-2);
}
</style>
