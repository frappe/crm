<template>
  <div class="flex-1 flex flex-col overflow-hidden">
    <div class="border-b px-5 flex items-center">
      <div class="flex gap-4 h-12 overflow-x-hidden">
        <button
          v-for="(tab, index) in tabs"
          :key="index"
          class="flex items-center gap-2 px-4 py-2 text-sm font-medium whitespace-nowrap"
          :class="{
            'text-gray-900 border-b-2 border-gray-900': modelValue === index,
            'text-gray-600 hover:text-gray-900': modelValue !== index
          }"
          @click="emit('update:modelValue', index)"
        >
          <component :is="tab.icon" class="h-4 w-4" />
          {{ __(tab.label) }}
          <span
            v-if="tab.count > 0"
            class="ml-2 rounded-full bg-gray-100 px-2 py-0.5 text-xs"
          >
            {{ tab.count }}
          </span>
        </button>
      </div>
    </div>
    <div class="flex-1 overflow-y-auto overflow-x-hidden">

      <div v-if="modelValue === 0" class="p-5">
        <TimelineView
          v-if="contact?.name"
          :items="timeline || []"
          :doctype="'Contact'"
          :docname="contact?.name"
          @comment-added="$emit('comment-added')"
        />
      </div>
      <div v-else-if="modelValue === 1" class="p-5">
        <div v-if="deals?.length" class="space-y-4">
          <ListView
            :rows="rows"
            :columns="columns"
            :options="{
              getRowRoute: (row) => ({
                name: 'Deal',
                params: { dealId: row?.name },
              }),
            }"
          >
            <ListHeader>
              <ListHeaderItem
                v-for="column in columns"
                :key="column.key"
                :item="column"
              />
            </ListHeader>
            <ListRows :rows="rows" v-slot="{ column, item }">
              <ListRowItem :item="item" :align="column?.align">
                <template #prefix>
                  <div v-if="column?.key === 'organization'">
                    <Avatar
                      v-if="item"
                      class="flex items-center"
                      :image="item?.logo"
                      :label="item?.label"
                      size="sm"
                    />
                  </div>
                </template>
                <template #default="{ label }">
                  <div
                    v-if="column?.key === 'modified'"
                    class="truncate text-base"
                  >
                    <Tooltip :text="item?.label">
                      <div>{{ item?.timeAgo }}</div>
                    </Tooltip>
                  </div>
                  <div v-else-if="column?.key === 'status'" class="flex items-center gap-2">
                    <div
                      class="h-2 w-2 rounded-full"
                      :style="{ backgroundColor: item?.color }"
                    />
                    <span>{{ item?.label }}</span>
                  </div>
                  <div v-else-if="column?.key === 'deal_owner'" class="flex items-center gap-2">
                    <Avatar
                      v-if="item"
                      :image="item?.image"
                      :label="item?.label"
                      size="sm"
                    />
                    <span>{{ item?.label }}</span>
                  </div>
                  <div v-else class="truncate text-base">
                    {{ item?.label }}
                  </div>
                </template>
              </ListRowItem>
            </ListRows>
          </ListView>
        </div>
        <div v-else class="text-center text-gray-600 py-8">
          {{ __('No deals found') }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import {
  ListView,
  ListHeader,
  ListHeaderItem,
  ListRows,
  ListRowItem,
  Avatar,
  Tooltip,
} from 'frappe-ui'
import TimelineView from '@/components/Timeline/TimelineView.vue'
import CalendarIcon from '@/components/Icons/CalendarIcon.vue'
import DealsIcon from '@/components/Icons/DealsIcon.vue'

const props = defineProps({
  modelValue: {
    type: Number,
    required: true,
  },
  timeline: {
    type: Array,
    default: () => [],
  },
  deals: {
    type: Array,
    default: () => [],
  },
  contact: {
    type: Object,
    default: () => ({}),
  },
  rows: {
    type: Array,
    default: () => [],
  },
  columns: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['update:modelValue', 'comment-added'])

const tabs = computed(() => [
  {
    label: 'Timeline',
    icon: CalendarIcon,
    count: props.timeline?.length || 0,
  },
  {
    label: 'Deals',
    icon: DealsIcon,
    count: props.deals?.length || 0,
  },
])
</script>

<style scoped>
.tab-content {
  height: calc(100vh - 12rem);
}
</style> 