<template>
  <NestedPopover v-if="options">
    <template #target>
      <Button label="Sort" ref="sortButtonRef">
        <template #prefix><SortIcon class="h-4" /></template>
        <template v-if="sortValues?.size" #suffix>
          <div
            class="flex h-5 w-5 items-center justify-center rounded bg-gray-900 pt-[1px] text-2xs font-medium text-white"
          >
            {{ sortValues.size }}
          </div>
        </template>
      </Button>
    </template>
    <template #body="{ close }">
      <div class="my-2 rounded-lg border border-gray-100 bg-white shadow-xl">
        <div class="min-w-[352px] p-2">
          <div
            v-if="sortValues?.size"
            id="sort-list"
            class="mb-3 flex flex-col gap-2"
          >
            <div
              v-for="(sort, i) in sortValues"
              :key="sort.fieldname"
              class="flex items-center gap-2"
            >
              <div class="handle flex h-7 w-7 items-center justify-center">
                <DragIcon class="h-4 w-4 cursor-grab text-gray-600" />
              </div>
              <Autocomplete
                class="!w-32"
                :value="sort.fieldname"
                :options="sortOptions.data"
                @change="(e) => updateSort(e, i)"
                placeholder="Sort by"
              />
              <FormControl
                class="!w-32"
                type="select"
                :value="sort.direction"
                :options="[
                  { label: 'Ascending', value: 'asc' },
                  { label: 'Descending', value: 'desc' },
                ]"
                @change="
                  (e) => {
                    sort.direction = e.target.value
                    apply()
                  }
                "
                placeholder="Sort by"
              />
              <Button variant="ghost" icon="x" @click="removeSort(i)" />
            </div>
          </div>
          <div
            v-else
            class="mb-3 flex h-7 items-center px-3 text-sm text-gray-600"
          >
            Empty - Choose a field to sort by
          </div>
          <div class="flex items-center justify-between gap-2">
            <Autocomplete
              :options="options"
              value=""
              placeholder="Sort by"
              @change="(e) => setSort(e)"
            >
              <template #target="{ togglePopover }">
                <Button
                  class="!text-gray-600"
                  variant="ghost"
                  @click="togglePopover()"
                  label="Add Sort"
                >
                  <template #prefix>
                    <FeatherIcon name="plus" class="h-4" />
                  </template>
                </Button>
              </template>
            </Autocomplete>
            <Button
              v-if="sortValues?.size"
              class="!text-gray-600"
              variant="ghost"
              label="Clear Sort"
              @click="clearSort(close)"
            />
          </div>
        </div>
      </div>
    </template>
  </NestedPopover>
</template>

<script setup>
import NestedPopover from '@/components/NestedPopover.vue'
import SortIcon from '@/components/Icons/SortIcon.vue'
import DragIcon from '@/components/Icons/DragIcon.vue'
import { useSortable } from '@vueuse/integrations/useSortable'
import { Autocomplete, createResource } from 'frappe-ui'
import { computed, ref, nextTick } from 'vue'

const props = defineProps({
  doctype: {
    type: String,
    required: true,
  },
})

const emit = defineEmits(['update'])
const list = defineModel()

const sortButtonRef = ref(null)

const sortOptions = createResource({
  url: 'crm.api.doc.sort_options',
  auto: true,
  params: {
    doctype: props.doctype,
  },
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
    return !selectedOptions.includes(option.value)
  })
})

const sortSortable = useSortable('#sort-list', sortValues, {
  handle: '.handle',
  animation: 200,
  onEnd: () => apply(),
})

function setSort(data) {
  sortValues.value.add({ fieldname: data.value, direction: 'asc' })
  restartSort()
  apply()
}

function updateSort(data, index) {
  let oldSort = Array.from(sortValues.value)[index]
  sortValues.value.delete(oldSort)
  sortValues.value.add({
    fieldname: data.value,
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
