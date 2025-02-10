<template>
  <transition
    enter-active-class="duration-300 ease-out"
    enter-from-class="transform opacity-0"
    enter-to-class="opacity-100"
    leave-active-class="duration-300 ease-in"
    leave-from-class="opacity-100"
    leave-to-class="transform opacity-0"
  >
    <div
      v-if="list.selections.size"
      class="absolute inset-x-0 bottom-6 mx-auto w-max text-base"
    >
      <div
        class="flex min-w-[596px] items-center space-x-3 rounded-lg bg-surface-white px-4 py-2 shadow-2xl"
        :class="$attrs.class"
      >
        <slot
          v-bind="{
            selections: list.selections,
            allRowsSelected: list.allRowsSelected,
            selectAll: () => list.toggleAllRows(true),
            unselectAll: () => list.toggleAllRows(false),
          }"
        >
          <div
            class="flex flex-1 justify-between border-r border-outline-gray-2 text-ink-gray-9"
          >
            <div class="flex items-center space-x-3">
              <FormControl
                type="checkbox"
                :modelValue="true"
                :disabled="true"
                class="text-ink-gray-9"
              />
              <div>{{ selectedText }}</div>
            </div>
            <div class="mr-3">
              <slot
                name="actions"
                v-bind="{
                  selections: list.selections,
                  allRowsSelected: list.allRowsSelected,
                  selectAll: () => list.toggleAllRows(true),
                  unselectAll: () => list.toggleAllRows(false),
                }"
              />
            </div>
          </div>
          <div class="flex items-center space-x-1">
            <Button
              class="w- text-ink-gray-7"
              :disabled="list.allRowsSelected"
              :class="list.allRowsSelected ? 'cursor-not-allowed' : ''"
              variant="ghost"
              @click="list.toggleAllRows(true)"
            >
              {{ __('Select All') }}
            </Button>
            <Button
              icon="x"
              variant="ghost"
              @click="list.toggleAllRows(false)"
            />
          </div>
        </slot>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { Button, FormControl } from 'frappe-ui'
import { computed, inject } from 'vue'

defineOptions({
  inheritAttrs: false,
})

const list = inject('list')
const Selected = __('Selected')
let selectedText = computed(() => {
  return `${Selected}: ${list.value.selections.size}`
})
</script> 
