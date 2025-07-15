<template>
  <div class="flex-1 overflow-y-auto p-3">
    <GridLayout
      v-if="items.length > 0"
      class="h-fit w-full"
      :class="[editing ? 'mb-[20rem] !select-none' : '']"
      :cols="20"
      :rowHeight="42"
      :disabled="!editing"
      :modelValue="items.map((item) => item.layout)"
      @update:modelValue="
        (newLayout) => {
          items.forEach((item, idx) => {
            item.layout = newLayout[idx]
          })
        }
      "
    >
      <template #item="{ index }">
        <div class="group relative flex h-full w-full p-2 text-ink-gray-8">
          <div
            class="flex h-full w-full items-center justify-center"
            :class="
              editing
                ? 'pointer-events-none  [&>div:first-child]:rounded [&>div:first-child]:group-hover:ring-2 [&>div:first-child]:group-hover:ring-outline-gray-2'
                : ''
            "
          >
            <DashboardItem
              :index="index"
              :item="items[index]"
              :editing="editing"
            />
          </div>
          <div
            v-if="editing"
            class="flex absolute right-0 top-0 bg-surface-gray-6 rounded cursor-pointer opacity-0 group-hover:opacity-100"
          >
            <div
              class="rounded p-1 hover:bg-surface-gray-5"
              @click="items.splice(index, 1)"
            >
              <FeatherIcon name="trash-2" class="size-3 text-ink-white" />
            </div>
          </div>
        </div>
      </template>
    </GridLayout>
  </div>
</template>
<script setup>
import { GridLayout } from 'frappe-ui'

const props = defineProps({
  editing: {
    type: Boolean,
    default: false,
  },
})

const items = defineModel()
</script>
