<template>
  <div id="content" class="flex flex-col w-full overflow-x-auto flex-1">
    <div class="flex flex-col overflow-y-hidden w-max min-w-full">
      <div
        id="list-header"
        class="flex space-x-4 items-center mx-5 mb-2 p-2 rounded bg-gray-100"
      >
        <Checkbox
          class="duration-300 cursor-pointer"
          :modelValue="allRowsSelected"
          @click.stop="toggleAllRows"
        />
        <div
          v-for="column in columns"
          :key="column"
          class="text-base text-gray-600"
          :class="[column.size, column.align]"
        >
          {{ column.label }}
        </div>
      </div>
      <div id="list-rows" class="h-full overflow-y-auto">
        <router-link
          v-for="(row, i) in rows"
          :key="row[rowKey]"
          :to="$router.currentRoute.value.path + '/' + row[rowKey]"
          class="flex flex-col mx-5 cursor-pointer transition-all duration-300 ease-in-out"
        >
          <div
            class="flex space-x-4 items-center px-2 py-2.5 rounded"
            :class="
              selections.has(row[rowKey])
                ? 'bg-gray-100 hover:bg-gray-200'
                : 'hover:bg-gray-50'
            "
          >
            <Checkbox
              :modelValue="selections.has(row[rowKey])"
              @click.stop="toggleRow(row[rowKey])"
              class="duration-300 cursor-pointer"
            />
            <div
              v-for="column in columns"
              :key="column.key"
              :class="[column.size, column.align]"
            >
              <ListRowItem
                :value="getValue(row[column.key]).label"
                :type="column.type"
                :align="column.align"
              >
                <template #prefix>
                  <div v-if="column.type === 'indicator'">
                    <IndicatorIcon :class="getValue(row[column.key]).color" />
                  </div>
                  <div v-else-if="column.type === 'avatar'">
                    <Avatar
                      v-if="getValue(row[column.key]).label"
                      class="flex items-center"
                      :image="getValue(row[column.key]).image"
                      :label="getValue(row[column.key]).image_label"
                      size="sm"
                    />
                  </div>
                  <div v-else-if="column.type === 'logo'">
                    <Avatar
                      v-if="getValue(row[column.key]).label"
                      class="flex items-center"
                      :image="getValue(row[column.key]).logo"
                      :label="getValue(row[column.key]).image_label"
                      size="sm"
                    />
                  </div>
                  <div v-else-if="column.type === 'icon'">
                    <FeatherIcon
                      :name="getValue(row[column.key]).icon"
                      class="h-3 w-3"
                    />
                  </div>
                  <div v-else-if="column.type === 'phone'">
                    <PhoneIcon class="h-4 w-4" />
                  </div>
                </template>
                <div v-if="column.type === 'badge'">
                  <Badge
                    :variant="'subtle'"
                    :theme="row[column.key].color"
                    size="md"
                    :label="row[column.key].label"
                  />
                </div>
              </ListRowItem>
            </div>
          </div>
          <div
            v-if="i < rows.length - 1"
            class="mx-2 h-px border-t border-gray-200"
          />
        </router-link>
      </div>
      <transition
        enter-active-class="duration-300 ease-out"
        enter-from-class="transform opacity-0"
        enter-to-class="opacity-100"
        leave-active-class="duration-300 ease-in"
        leave-from-class="opacity-100"
        leave-to-class="transform opacity-0"
      >
        <div
          v-if="selections.size"
          class="fixed inset-x-0 bottom-6 mx-auto w-max text-base"
        >
          <div
            class="w-[596px] flex items-center space-x-3 rounded-lg bg-white px-4 py-2 shadow-2xl"
          >
            <div
              class="flex flex-1 items-center space-x-3 border-r border-gray-300 text-gray-900"
            >
              <Checkbox
                :modelValue="true"
                :disabled="true"
                class="text-gray-900"
              />
              <div>{{ selectedText }}</div>
            </div>
            <div class="flex items-center space-x-1">
              <Button
                class="text-gray-700"
                :disabled="allRowsSelected"
                :class="allRowsSelected ? 'cursor-not-allowed' : ''"
                variant="ghost"
                @click="toggleAllRows(true)"
              >
                Select all
              </Button>
              <Button icon="x" variant="ghost" @click="toggleAllRows(false)" />
            </div>
          </div>
        </div>
      </transition>
    </div>
  </div>
</template>
<script setup>
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import ListRowItem from '@/components/ListRowItem.vue'
import { Checkbox, Avatar, Badge, FeatherIcon } from 'frappe-ui'
import { reactive, computed } from 'vue'

const props = defineProps({
  list: {
    type: Object,
    required: true,
  },
  columns: {
    type: Array,
    default: [],
  },
  rows: {
    type: Array,
    default: [],
  },
  rowKey: {
    type: String,
    required: true,
  },
})

function getValue(value) {
  if (value && typeof value === 'object') {
    value.label = value.full_name || value.label
    value.image = value.image || value.user_image || value.logo
    value.image_label = value.image_label || value.label
    return value
  }
  return { label: value }
}

let selections = reactive(new Set())
let selectedText = computed(() => {
  let title =
    selections.size === 1 ? props.list.singular_label : props.list.plural_label
  return `${selections.size} ${title} selected`
})

const allRowsSelected = computed(() => {
  if (!props.rows.length) return false
  return selections.size === props.rows.length
})

function toggleRow(row) {
  if (!selections.delete(row)) {
    selections.add(row)
  }
}

function toggleAllRows(select) {
  if (!select || allRowsSelected.value) {
    selections.clear()
    return
  }
  props.rows.forEach((row) => selections.add(row[props.rowKey]))
}
</script>
