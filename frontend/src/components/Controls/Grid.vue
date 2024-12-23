<template>
  <div class="flex flex-col text-base">
    <div v-if="label" class="mb-1.5 text-sm text-gray-600">
      {{ __(label) }}
    </div>

    <div class="rounded border border-gray-100">
      <!-- Header -->
      <div
        class="grid-header flex items-center rounded-t-sm bg-gray-100 text-gray-600 truncate"
      >
        <div class="inline-flex items-center justify-center border-r p-2 w-12">
          <Checkbox
            class="cursor-pointer duration-300"
            :modelValue="allRowsSelected"
            @click.stop="toggleSelectAllRows($event.target.checked)"
          />
        </div>
        <div
          class="inline-flex items-center justify-center border-r py-2 px-1 w-12"
        >
          {{ __('No') }}
        </div>
        <div
          class="grid w-full truncate"
          :style="{ gridTemplateColumns: gridTemplateColumns }"
        >
          <div
            v-if="gridFields?.length"
            class="border-r p-2 truncate"
            v-for="field in gridFields"
            :key="field.name"
            :title="field.label"
          >
            {{ __(field.label) }}
          </div>
        </div>
        <div class="w-12" />
      </div>
      <!-- Rows -->
      <template v-if="rows.length">
        <Draggable class="w-full" v-model="rows" group="rows" item-key="name">
          <template #item="{ element: row, index }">
            <div
              class="grid-row flex cursor-pointer items-center border-b border-gray-100 bg-white last:rounded-b last:border-b-0"
            >
              <div
                class="inline-flex h-9.5 items-center justify-center border-r p-2 w-12"
              >
                <Checkbox
                  class="cursor-pointer duration-300"
                  :modelValue="selectedRows.has(row.name)"
                  @click.stop="toggleSelectRow(row)"
                />
              </div>
              <div
                class="flex h-9.5 items-center justify-center border-r py-2 px-1 text-sm text-gray-800 w-12"
              >
                {{ index + 1 }}
              </div>
              <div
                class="grid w-full h-9.5"
                :style="{ gridTemplateColumns: gridTemplateColumns }"
              >
                <div
                  v-if="gridFields?.length"
                  class="border-r border-gray-100 h-full"
                  v-for="field in gridFields"
                  :key="field.name"
                >
                  <Link
                    v-if="field.type === 'Link'"
                    class="text-sm text-gray-800"
                    :value="row[field.name]"
                    :doctype="field.options"
                    :filters="field.filters"
                    @change="
                      (data: String) =>
                        field.onChange && field.onChange(data, index)
                    "
                  />
                  <Grid
                    v-else-if="field.type === 'Table'"
                    v-model="data[field.name]"
                    :fields="field.fields || []"
                    :gridFields="field.gridFields || []"
                  />
                  <div
                    v-else-if="field.type === 'Check'"
                    class="flex h-full justify-center items-center"
                  >
                    <Checkbox
                      class="cursor-pointer duration-300"
                      v-model="row[field.name]"
                      @change="
                        (e: Event) =>
                          field.onChange &&
                          field.onChange(
                            (e.target as HTMLInputElement).checked,
                            index,
                          )
                      "
                    />
                  </div>
                  <DatePicker
                    v-else-if="field.type === 'Date'"
                    :value="row[field.name]"
                    icon-left=""
                    variant="outline"
                    :formatter="(date) => getFormat(date, '', true)"
                    input-class="border-none text-sm text-gray-800"
                    @change="
                      (data: String) =>
                        field.onChange && field.onChange(data, index)
                    "
                  />
                  <DateTimePicker
                    v-else-if="field.type === 'Datetime'"
                    :value="row[field.name]"
                    icon-left=""
                    variant="outline"
                    :formatter="(date) => getFormat(date, '', true, true)"
                    input-class="border-none text-sm text-gray-800"
                    @change="
                      (data: String) =>
                        field.onChange && field.onChange(data, index)
                    "
                  />
                  <FormControl
                    v-else-if="
                      ['Small Text', 'Text', 'Long Text', 'Code'].includes(
                        field.type,
                      )
                    "
                    type="textarea"
                    v-model="row[field.name]"
                    variant="outline"
                    @change="
                      (e: Event) =>
                        field.onChange &&
                        field.onChange(
                          (e.target as HTMLInputElement).value,
                          index,
                        )
                    "
                  />
                  <FormControl
                    v-else-if="['Int'].includes(field.type)"
                    type="number"
                    v-model="row[field.name]"
                    variant="outline"
                    @change="
                      (e: Event) =>
                        field.onChange &&
                        field.onChange(
                          (e.target as HTMLInputElement).value,
                          index,
                        )
                    "
                  />
                  <FormControl
                    v-else-if="field.type === 'Select'"
                    class="text-sm text-gray-800"
                    v-model="row[field.name]"
                    type="select"
                    :options="field.options"
                    variant="outline"
                    @change="
                      (e: Event) =>
                        field.onChange &&
                        field.onChange(
                          (e.target as HTMLInputElement).value,
                          index,
                        )
                    "
                  />
                  <FormControl
                    v-else
                    class="text-sm text-gray-800"
                    v-model="row[field.name]"
                    type="text"
                    :options="field.options"
                    variant="outline"
                    @change="
                      (e: Event) =>
                        field.onChange &&
                        field.onChange(
                          (e.target as HTMLInputElement).value,
                          index,
                        )
                    "
                  />
                </div>
              </div>
              <div class="edit-row w-12">
                <Button
                  class="flex w-full items-center justify-center rounded"
                  @click="showRowList[index] = true"
                >
                  <EditIcon class="h-4 w-4 text-gray-700" />
                </Button>
              </div>
              <Dialog
                v-model="showRowList[index]"
                :options="{
                  title: __('Editing Row {0}', [index + 1]),
                  size: '4xl',
                }"
              >
                <template #body-content>
                  <FieldLayout
                    v-if="fields?.length"
                    :tabs="fields"
                    :data="row"
                  />
                </template>
              </Dialog>
            </div>
          </template>
        </Draggable>
      </template>

      <div
        v-else
        class="flex flex-col items-center rounded p-5 text-sm text-gray-600"
      >
        {{ __('No Data') }}
      </div>
    </div>

    <div v-if="gridFields?.length" class="mt-2 flex flex-row gap-2">
      <Button
        v-if="showDeleteBtn"
        :label="__('Delete')"
        variant="solid"
        theme="red"
        @click="deleteRows"
      />
      <Button :label="__('Add Row')" @click="addRow" />
    </div>
  </div>
</template>

<script setup lang="ts">
import EditIcon from '@/components/Icons/EditIcon.vue'
import FieldLayout from '@/components/FieldLayout.vue'
import Link from '@/components/Controls/Link.vue'
import Grid from '@/components/Controls/Grid.vue'
import { GridColumn, GridRow } from '@/types/controls'
import { getRandom, getFormat } from '@/utils'
import {
  Dialog,
  FormControl,
  Checkbox,
  DateTimePicker,
  DatePicker,
} from 'frappe-ui'
import Draggable from 'vuedraggable'
import { ref, reactive, computed, PropType } from 'vue'

const props = defineProps<{
  label?: string
  gridFields: GridColumn[]
  fields: GridColumn[]
}>()

const rows = defineModel({
  type: Array as PropType<GridRow[]>,
  default: () => [],
})
const showRowList = ref(new Array(rows.value.length).fill(false))
const selectedRows = reactive(new Set<string>())

const gridTemplateColumns = computed(() => {
  if (!props.gridFields?.length) return '1fr'
  // for the checkbox & sr no. columns
  return props.gridFields
    .map((col) => `minmax(0, ${col.width || 2}fr)`)
    .join(' ')
})

const allRowsSelected = computed(() => {
  if (!rows.value.length) return false
  return rows.value.length === selectedRows.size
})

const showDeleteBtn = computed(() => selectedRows.size > 0)

const toggleSelectAllRows = (iSelected: boolean) => {
  if (iSelected) {
    rows.value.forEach((row: GridRow) => selectedRows.add(row.name))
  } else {
    selectedRows.clear()
  }
}

const toggleSelectRow = (row: GridRow) => {
  if (selectedRows.has(row.name)) {
    selectedRows.delete(row.name)
  } else {
    selectedRows.add(row.name)
  }
}

const addRow = () => {
  const newRow = {} as GridRow
  props.gridFields?.forEach((field) => {
    if (field.type === 'Check') newRow[field.name] = false
    else newRow[field.name] = ''
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
:deep(.grid-row input:not([type='checkbox'])) {
  border: none;
  border-radius: 0;
  height: 38px;
}

:deep(.grid-row input:focus, .grid-row input:hover) {
  box-shadow: none;
}

:deep(.grid-row input:focus-within) {
  border: 1px solid #d1d8dd;
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
  background-color: white;
  height: 38px;
}

:deep(.grid-row .edit-row button) {
  border-bottom-right-radius: 7px;
}

:deep(.grid-row button:focus, .grid-row button:hover) {
  box-shadow: none;
  background-color: white;
}

:deep(.grid-row button:focus-within) {
  border: 1px solid #d1d8dd;
}
</style>
