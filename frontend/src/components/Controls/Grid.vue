<template>
  <div class="flex flex-col text-base">
    <div v-if="label" class="mb-1.5 text-sm text-gray-600">{{ label }}</div>

    <div class="rounded border border-gray-100">
      <!-- Header -->
      <div
        class="grid items-center rounded-t-sm bg-gray-100 text-gray-600"
        :style="{ gridTemplateColumns: gridTemplateColumns }"
      >
        <div class="inline-flex items-center justify-center border-r p-2">
          <Checkbox
            class="cursor-pointer duration-300"
            :modelValue="allRowsSelected"
            @click.stop="toggleSelectAllRows($event.target.checked)"
          />
        </div>
        <div class="inline-flex items-center justify-center border-r py-2 px-1">
          No.
        </div>
        <div
          class="inline-flex items-center border-r p-2"
          v-for="field in gridFields"
          :key="field.fieldname"
        >
          {{ field.label }}
        </div>
        <div class="p-2" />
      </div>
      <!-- Rows -->
      <template v-if="rows.length">
        <Draggable class="w-full" v-model="rows" group="rows" item-key="name">
          <template #item="{ element: row, index }">
            <div
              class="grid-row grid cursor-pointer items-center border-b border-gray-100 bg-white last:rounded-b last:border-b-0"
              :style="{ gridTemplateColumns: gridTemplateColumns }"
            >
              <div
                class="inline-flex h-full items-center justify-center border-r p-2"
              >
                <Checkbox
                  class="cursor-pointer duration-300"
                  :modelValue="selectedRows.has(row.name)"
                  @click.stop="toggleSelectRow(row)"
                />
              </div>
              <div
                class="flex h-full items-center justify-center border-r p-2 text-sm text-gray-800"
              >
                {{ index + 1 }}
              </div>
              <div
                class="border-r border-gray-100 h-full"
                v-for="field in gridFields"
                :key="field.fieldname"
              >
                <Link
                  v-if="field.fieldtype === 'Link'"
                  class="text-sm text-gray-800"
                  :value="row[field.fieldname]"
                  :doctype="field.options"
                  :placeholder="row.placeholder"
                  @change="
                    (data: String) =>
                      field.onChange && field.onChange(data, index)
                  "
                />
                <div
                  v-else-if="field.fieldtype === 'Check'"
                  class="flex h-full justify-center items-center"
                >
                  <Checkbox
                    class="cursor-pointer duration-300"
                    v-model="row[field.fieldname]"
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
                <FormControl
                  v-else
                  class="text-sm text-gray-800"
                  v-model="row[field.fieldname]"
                  :type="field.fieldtype.toLowerCase()"
                  :options="field.options"
                  variant="outline"
                  size="md"
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
              <div class="edit-row">
                <Button
                  class="flex w-full items-center justify-center rounded"
                  @click="showRowList[index] = true"
                >
                  <FeatherIcon
                    name="edit-2"
                    class="h-3.5 w-3.5 text-gray-700"
                  />
                </Button>
              </div>
              <Dialog
                v-model="showRowList[index]"
                :options="{ title: `Editing Row ${index + 1}` }"
              >
                <template #body-content>
                  <div v-for="field in fields" :key="field.fieldname">
                    {{ field.label }}: {{ row[field.fieldname] }}
                  </div>
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
        No Data
      </div>
    </div>

    <div class="mt-2 flex flex-row gap-2">
      <Button
        v-if="showDeleteBtn"
        label="Delete"
        variant="solid"
        theme="red"
        @click="deleteRows"
      />
      <Button label="Add Row" @click="addRow" />
    </div>
  </div>
</template>

<script setup lang="ts">
import Link from '@/components/Controls/Link.vue'
import { GridColumn, GridRow } from '@/types/controls'
import { getRandom } from '@/utils'
import { Dialog, FormControl, Checkbox } from 'frappe-ui'
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
  // for the checkbox & sr no. columns
  let columns = '0.5fr 0.5fr'
  columns +=
    ' ' +
    props.gridFields.map((col) => `minmax(0, ${col.width || 2}fr)`).join(' ')
  // for the edit button column
  columns += ' 0.5fr'

  return columns
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
  props.gridFields.forEach((field) => {
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
