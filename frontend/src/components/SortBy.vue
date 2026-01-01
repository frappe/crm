<template>
  <Autocomplete
    v-if="!sortValues?.length"
    :options="options"
    value=""
    :placeholder="__('First Name')"
    @change="(e) => setSort(e)"
  >
    <template #target="{ togglePopover }">
      <Button :label="__('Sort')" @click="togglePopover()">
        <template v-if="hideLabel">
          <SortIcon class="h-4" />
        </template>
        <template v-if="!hideLabel && !sortValues?.length" #prefix>
          <SortIcon class="h-4" />
        </template>
      </Button>
    </template>
    <template #item-label="{ option }">
      <Tooltip :text="option.fieldname">
        <div class="flex-1 truncate text-ink-gray-7">
          {{ option.label }}
        </div>
      </Tooltip>
    </template>
  </Autocomplete>
  <Popover placement="bottom-end" v-else>
    <template #target="{ isOpen, togglePopover }">
      <Button
        v-if="sortValues.length > 1"
        :label="__('Sort')"
        :icon="hideLabel && SortIcon"
        :iconLeft="!hideLabel && SortIcon"
        @click="togglePopover"
      >
        <template v-if="sortValues?.length" #suffix>
          <div
            class="flex h-5 w-5 items-center justify-center rounded-[5px] bg-surface-white pt-px text-xs font-medium text-ink-gray-8 shadow-sm"
          >
            {{ sortValues.length }}
          </div>
        </template>
      </Button>
      <div v-else class="flex items-center justify-center">
        <Button
          v-if="sortValues.length"
          class="rounded-r-none border-r"
          :icon="
            sortValues[0].direction == 'asc' ? AscendingIcon : DesendingIcon
          "
          @click.stop="toggleDirection(0)"
        />
        <Button
          :label="getSortLabel()"
          class="shrink-0 [&_svg]:text-ink-gray-5"
          :iconLeft="!hideLabel && !sortValues?.length && SortIcon"
          :iconRight="
            sortValues?.length && (isOpen ? 'chevron-up' : 'chevron-down')
          "
          :class="sortValues.length ? 'rounded-l-none' : ''"
          @click.stop="togglePopover"
        />
      </div>
    </template>
    <template #body="{ close }">
      <div
        class="my-2 min-w-40 rounded-lg bg-surface-modal shadow-2xl ring-1 ring-black ring-opacity-5 focus:outline-none"
      >
        <div class="min-w-60 p-2">
          <Draggable
            v-if="sortValues?.length"
            v-model="sortValues"
            class="sort-items mb-3 flex flex-col gap-2"
            item-key="fieldname"
            handle=".handle"
            @end="apply"
          >
            <template #item="{ element: sort, index: i }">
              <div class="sort-item flex items-center gap-1">
                <div class="handle flex h-7 w-7 items-center justify-center">
                  <DragIcon class="h-4 w-4 cursor-grab text-ink-gray-5" />
                </div>
                <div class="flex flex-1">
                  <Button
                    size="md"
                    class="rounded-r-none border-r"
                    :icon="
                      sort.direction == 'asc' ? AscendingIcon : DesendingIcon
                    "
                    @click="toggleDirection(i)"
                  />
                  <Autocomplete
                    class="[&>_div]:w-full"
                    :value="sort.fieldname"
                    :options="sortOptions"
                    @change="(e) => updateSort(e, i)"
                    :placeholder="__('First Name')"
                  >
                    <template
                      #target="{
                        open,
                        togglePopover,
                        selectedValue,
                        displayValue,
                      }"
                    >
                      <Button
                        class="flex w-full items-center justify-between rounded-l-none !text-ink-gray-5"
                        size="md"
                        :label="displayValue(selectedValue)"
                        :iconRight="open ? 'chevron-down' : 'chevron-up'"
                        @click="togglePopover()"
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
                </div>
                <Button variant="ghost" icon="x" @click="removeSort(i)" />
              </div>
            </template>
          </Draggable>
          <div class="flex items-center justify-between gap-2">
            <Autocomplete
              :options="options"
              value=""
              :placeholder="__('First Name')"
              @change="(e) => setSort(e)"
            >
              <template #target="{ togglePopover }">
                <Button
                  class="!text-ink-gray-5"
                  :label="__('Add Sort')"
                  variant="ghost"
                  iconLeft="plus"
                  @click="togglePopover()"
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
              v-if="sortValues?.length"
              class="!text-ink-gray-5"
              variant="ghost"
              :label="__('Clear Sort')"
              @click="clearSort(close)"
            />
          </div>
        </div>
      </div>
    </template>
  </Popover>
</template>

<script setup>
import AscendingIcon from '@/components/Icons/AscendingIcon.vue'
import DesendingIcon from '@/components/Icons/DesendingIcon.vue'
import SortIcon from '@/components/Icons/SortIcon.vue'
import DragIcon from '@/components/Icons/DragIcon.vue'
import Draggable from 'vuedraggable'
import Autocomplete from '@/components/frappe-ui/Autocomplete.vue'
import { getMeta } from '@/stores/meta'
import { useViews } from '@/stores/view'
import { Popover, Tooltip } from 'frappe-ui'
import { computed } from 'vue'

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

const sortOptions = computed(() => {
  let _options = getValueFields() || []
  _options = _options.map((f) => ({
    fieldname: f.fieldname,
    label: f.label,
    value: f.fieldname,
  }))
  return _options
})

const sortValues = computed({
  get: () => {
    if (!currentView.value) return []
    let allSortValues = currentView.value.order_by
    if (!allSortValues || !sortOptions.value) return []
    if (allSortValues.trim() === 'modified desc') return []
    allSortValues = allSortValues.split(', ').map((sortValue) => {
      const [fieldname, direction] = sortValue.split(' ')
      return { fieldname, direction }
    })
    return allSortValues
  },
  set: (value) => {
    currentView.value.order_by = convertToString(value)
  },
})

const options = computed(() => {
  if (!sortOptions.value) return []
  if (!sortValues.value.length) return sortOptions.value
  const selectedOptions = sortValues.value.map((sort) => sort.fieldname)
  return sortOptions.value.filter((option) => {
    return !selectedOptions.includes(option.value)
  })
})

function toggleDirection(index) {
  const newValues = [...sortValues.value]
  const sort = newValues[index]
  sort.direction = sort.direction === 'asc' ? 'desc' : 'asc'
  sortValues.value = newValues
  apply()
}

function getSortLabel() {
  if (!sortValues.value.length) return __('Sort')
  let label = sortOptions.value?.find(
    (option) => option.value === sortValues.value[0].fieldname,
  )?.label
  return label || sortValues.value[0].fieldname
}

function setSort(data) {
  sortValues.value = [
    ...sortValues.value,
    { fieldname: data.value, direction: 'asc' },
  ]
  apply()
}

function updateSort(data, index) {
  const newValues = [...sortValues.value]
  const oldSort = newValues[index]
  newValues[index] = {
    fieldname: data.value,
    direction: oldSort.direction,
  }
  sortValues.value = newValues
  apply()
}

function removeSort(index) {
  const newValues = [...sortValues.value]
  newValues.splice(index, 1)
  sortValues.value = newValues
  apply()
}

function clearSort(close) {
  sortValues.value = []
  apply()
  close()
}

function apply() {
  emit('update')
}

function convertToString(values) {
  let _sortValues = ''
  values.forEach((f) => {
    _sortValues += `${f.fieldname} ${f.direction}, `
  })
  _sortValues = _sortValues.slice(0, -2)
  return _sortValues
}
</script>
