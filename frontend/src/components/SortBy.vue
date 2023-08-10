<template>
  <NestedPopover v-if="options">
    <template #target>
      <Button label="Sort" ref="sortButtonRef">
        <template #prefix><SortIcon class="h-4" /></template>
        <template v-if="sortValues.length" #suffix>
          <div
            class="flex justify-center items-center w-5 h-5 text-2xs font-medium pt-[1px] bg-gray-900 text-white rounded"
          >
            {{ sortValues.length }}
          </div>
        </template>
      </Button>
    </template>
    <template #body="{ close }">
      <div class="rounded-lg border border-gray-100 bg-white shadow-xl my-2">
        <div class="p-2 min-w-[352px]">
          <div
            v-if="sortValues.length"
            id="sort-list"
            class="flex flex-col gap-2 mb-3"
          >
            <div
              v-for="(sort, i) in sortValues"
              :key="sort.fieldname"
              class="flex items-center gap-2"
            >
              <div class="flex items-center justify-center h-7 w-7 handle">
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
                v-model="sort.direction"
                :options="[
                  { label: 'Ascending', value: 'asc' },
                  { label: 'Descending', value: 'desc' },
                ]"
                placeholder="Sort by"
              />
              <Button variant="ghost" icon="x" @click="removeSort(i)" />
            </div>
          </div>
          <div
            v-else
            class="text-gray-600 flex items-center text-sm px-3 h-7 mb-3"
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
                  label="Add sort"
                >
                  <template #prefix>
                    <FeatherIcon name="plus" class="h-4" />
                  </template>
                </Button>
              </template>
            </Autocomplete>
            <Button
              v-if="sortValues.length"
              class="!text-gray-600"
              variant="ghost"
              label="Clear sort"
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
import { useOrderBy } from '@/composables/orderby'
import {
  FeatherIcon,
  Button,
  Autocomplete,
  FormControl,
  createResource,
} from 'frappe-ui'
import { computed, ref, watch } from 'vue'

const props = defineProps({
  doctype: {
    type: String,
    required: true,
  },
})

const { get: getOrderBy, set: setOrderBy } = useOrderBy()

const sortButtonRef = ref(null)
const sortValues = ref(initialOrderBy())

const sortOptions = createResource({
  url: 'crm.extends.doc.sort_options',
  auto: true,
  params: {
    doctype: props.doctype,
  },
})

const options = computed(() => {
  if (!sortOptions.data) return []
  const selectedOptions = sortValues.value.map((sort) => sort.fieldname)
  return sortOptions.data.filter((option) => {
    return !selectedOptions.includes(option.value)
  })
})

function initialOrderBy() {
  const orderBy = getOrderBy()
  if (!orderBy) return []
  const sortOptions = orderBy.split(', ')
  return sortOptions.map((sortOption) => {
    const [fieldname, direction] = sortOption.split(' ')
    return { fieldname, direction }
  })
}

const sortSortable = useSortable('#sort-list', sortValues, {
  handle: '.handle',
  animation: 200,
})

watch(
  () => sortValues.value,
  (value) => {
    const updatedSort = value
      .map((sort) => {
        const option = sortOptions.data.find((o) => o.value === sort.fieldname)
        return `${option.value} ${sort.direction}`
      })
      .join(', ')
    setOrderBy(updatedSort)
  },
  {
    deep: true,
  }
)

watch(
  () => getOrderBy(),
  (value) => {
    if (!value) {
      sortValues.value = []
    }
  }
)

function setSort(data) {
  sortValues.value = [
    ...sortValues.value,
    { fieldname: data.value, direction: 'asc' },
  ]
  sortSortable.start()
}

function updateSort(data, index) {
  sortValues.value[index] = {
    fieldname: data.value,
    direction: sortValues.value[index].direction,
  }
}

function removeSort(index) {
  sortValues.value.splice(index, 1)
}

function clearSort(close) {
  sortValues.value = []
  close()
}
</script>
