<template>
  <Autocomplete
    v-if="!sortValues?.size"
    :options="options"
    value=""
    :placeholder="__('First name')"
    @change="(e) => setSort(e)"
  >
    <template #target="{ togglePopover }">
      <Button :label="__('Sort')" @click="togglePopover()">
        <template v-if="hideLabel">
          <SortIcon class="h-4" />
        </template>
        <template v-if="!hideLabel && !sortValues?.size" #prefix>
          <SortIcon class="h-4" />
        </template>
      </Button>
    </template>
  </Autocomplete>
  <Popover placement="bottom-end" v-else>
    <template #target="{ isOpen, togglePopover }">
      <Button
        v-if="sortValues.size > 1"
        :label="__('Sort')"
        :icon="hideLabel && SortIcon"
        :iconLeft="!hideLabel && SortIcon"
        @click="togglePopover"
      >
        <template v-if="sortValues?.size" #suffix>
          <div
            class="flex h-5 w-5 items-center justify-center rounded-[5px] bg-surface-white pt-px text-xs font-medium text-ink-gray-8 shadow-sm"
          >
            {{ sortValues.size }}
          </div>
        </template>
      </Button>
      <div v-else class="flex items-center justify-center">
        <Button
          v-if="sortValues.size"
          class="rounded-r-none border-r"
          :icon="
            Array.from(sortValues)[0].direction == 'asc'
              ? AscendingIcon
              : DesendingIcon
          "
          @click.stop="
            () => {
              Array.from(sortValues)[0].direction =
                Array.from(sortValues)[0].direction == 'asc' ? 'desc' : 'asc'
              apply()
            }
          "
        />
        <Button
          :label="getSortLabel()"
          class="shrink-0 [&_svg]:text-ink-gray-5"
          :iconLeft="!hideLabel && !sortValues?.size && SortIcon"
          :iconRight="
            sortValues?.size && (isOpen ? 'chevron-up' : 'chevron-down')
          "
          :class="sortValues.size ? 'rounded-l-none' : ''"
          @click.stop="togglePopover"
        />
      </div>
    </template>
    <template #body="{ close }">
      <div
        class="my-2 min-w-40 rounded-lg bg-surface-modal shadow-2xl ring-1 ring-black ring-opacity-5 focus:outline-none"
      >
        <div class="min-w-60 p-2">
          <div
            v-if="sortValues?.size"
            id="sort-list"
            class="mb-3 flex flex-col gap-2"
          >
            <div
              v-for="(sort, i) in sortValues"
              :key="sort.fieldname"
              class="flex items-center gap-1"
            >
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
                  @click="
                    () => {
                      sort.direction = sort.direction == 'asc' ? 'desc' : 'asc'
                      apply()
                    }
                  "
                />
                <Autocomplete
                  class="[&>_div]:w-full"
                  :value="sort.fieldname"
                  :options="sortOptions.data"
                  @change="(e) => updateSort(e, i)"
                  :placeholder="__('First name')"
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
                </Autocomplete>
              </div>
              <Button variant="ghost" icon="x" @click="removeSort(i)" />
            </div>
          </div>
          <div
            v-else
            class="mb-3 flex h-7 items-center px-3 text-sm text-ink-gray-5"
          >
            {{ __('Empty - Choose a field to sort by') }}
          </div>
          <div class="flex items-center justify-between gap-2">
            <Autocomplete
              :options="options"
              value=""
              :placeholder="__('First name')"
              @change="(e) => setSort(e)"
            >
              <template #target="{ togglePopover }">
                <Button
                  class="!text-ink-gray-5"
                  :label="__('Add sort')"
                  variant="ghost"
                  iconLeft="plus"
                  @click="togglePopover()"
                />
              </template>
            </Autocomplete>
            <Button
              v-if="sortValues?.size"
              class="!text-ink-gray-5"
              variant="ghost"
              :label="__('Clear sort')"
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
import Autocomplete from '@/components/frappe-ui/Autocomplete.vue'
import { useSortable } from '@vueuse/integrations/useSortable'
import { createResource, Popover } from 'frappe-ui'
import { computed, nextTick, onMounted } from 'vue'

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
const list = defineModel()

const sortOptions = createResource({
  url: 'crm.api.doc.sort_options',
  cache: ['sortOptions', props.doctype],
  params: { doctype: props.doctype },
})

onMounted(() => {
  if (sortOptions.data?.length) return
  sortOptions.fetch()
})

const sortValues = computed({
  get: () => {
    if (!list.value?.data) return new Set()
    let allSortValues = list.value?.params?.order_by
    if (!allSortValues || !sortOptions.data) return new Set()
    if (allSortValues.trim() === 'modified desc') return new Set()
    allSortValues = allSortValues.split(', ').map((sortValue) => {
      const [fieldname, direction] = sortValue.split(' ')
      return { fieldname, direction }
    })
    return new Set(allSortValues)
  },
  set: (value) => {
    list.value.params.order_by = convertToString(value)
  },
})

const options = computed(() => {
  if (!sortOptions.data) return []
  if (!sortValues.value.size) return sortOptions.data
  const selectedOptions = [...sortValues.value].map((sort) => sort.fieldname)
  restartSort()
  return sortOptions.data.filter((option) => {
    return !selectedOptions.includes(option.fieldname)
  })
})

const sortSortable = useSortable('#sort-list', sortValues, {
  handle: '.handle',
  animation: 200,
  onEnd: () => apply(),
})

function getSortLabel() {
  if (!sortValues.value.size) return __('Sort')
  let values = Array.from(sortValues.value)
  let label = sortOptions.data?.find(
    (option) => option.fieldname === values[0].fieldname,
  )?.label
  return label || values[0].fieldname
}

function setSort(data) {
  sortValues.value.add({ fieldname: data.fieldname, direction: 'asc' })
  restartSort()
  apply()
}

function updateSort(data, index) {
  let oldSort = Array.from(sortValues.value)[index]
  sortValues.value.delete(oldSort)
  sortValues.value.add({
    fieldname: data.fieldname,
    direction: oldSort.direction,
  })
  apply()
}

function removeSort(index) {
  sortValues.value.delete(Array.from(sortValues.value)[index])
  apply()
}

function clearSort(close) {
  sortValues.value.clear()
  apply()
  close()
}

function apply() {
  nextTick(() => {
    emit('update', convertToString(sortValues.value))
  })
}

function convertToString(values) {
  let _sortValues = ''
  values.forEach((f) => {
    _sortValues += `${f.fieldname} ${f.direction}, `
  })
  _sortValues = _sortValues.slice(0, -2)
  return _sortValues
}

function restartSort() {
  sortSortable.stop()
  sortSortable.start()
}
</script>
