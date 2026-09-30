<template>
  <div class="flex-1 overflow-y-auto p-3">
    <GridLayout
      v-if="items.length > 0"
      class="h-fit w-full"
      :class="[editing ? 'mb-[20rem] !select-none' : '']"
      :col-num="20"
      :cols="{ lg: 20, md: 20, sm: 20, xs: 1, xxs: 1 }"
      :row-height="42"
      :margin="[0, 0]"
      :is-draggable="editing"
      :is-resizable="editing"
      responsive
      :layout="items.map((item) => item.layout)"
      @update:layout="
        (newLayout) => {
          items.forEach((item, idx) => {
            item.layout = newLayout[idx]
          })
        }
      "
      @layout-ready="layoutReady = true"
    >
      <GridItem
        v-for="({ layout: l }, index) in items"
        :key="l.i"
        :i="l.i"
        :x="l.x"
        :y="l.y"
        :w="l.w"
        :h="l.h"
        :min-w="l.minW"
        :min-h="l.minH"
        :max-w="l.maxW"
        :max-h="l.maxH"
      >
        <div
          v-if="layoutReady"
          class="group relative flex h-full w-full p-2 text-ink-gray-8"
        >
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
            class="flex absolute right-0 top-0 bg-surface-gray-9 rounded cursor-pointer opacity-0 group-hover:opacity-100"
          >
            <div
              class="rounded p-1 hover:bg-surface-gray-8"
              @click="items.splice(index, 1)"
            >
              <span
                class="lucide-trash-2 size-3 text-ink-base"
                aria-hidden="true"
              />
            </div>
          </div>
        </div>
      </GridItem>
    </GridLayout>
  </div>
</template>
<script setup>
import { GridLayout, GridItem } from 'grid-layout-plus'
import { ref } from 'vue'

defineProps({
  editing: { type: Boolean, default: false },
})

const items = defineModel({ type: Array, default: () => [] })

const layoutReady = ref(false)
</script>

<style scoped>
.vgl-layout {
  --vgl-placeholder-bg: #b1b1b1;
  --vgl-placeholder-opacity: 15%;
  --vgl-placeholder-z-index: 2;

  --vgl-item-resizing-z-index: 3;
  --vgl-item-resizing-opacity: 100%;
  --vgl-item-dragging-z-index: 3;
  --vgl-item-dragging-opacity: 100%;

  --vgl-resizer-size: 10px;
  --vgl-resizer-border-color: #444;
  --vgl-resizer-border-width: 2px;
}

:deep(.vgl-item--placeholder) {
  z-index: var(--vgl-placeholder-z-index, 2);
  user-select: none;
  background-color: var(--vgl-placeholder-bg);
  opacity: var(--vgl-placeholder-opacity);
  transition-duration: 100ms;
  border-radius: 0.5rem;
}

:deep(.vgl-item__resizer) {
  position: absolute;
  right: 12px;
  bottom: 12px;
  box-sizing: border-box;
  width: var(--vgl-resizer-size);
  height: var(--vgl-resizer-size);
  cursor: se-resize;
}

:deep(.vgl-item__resizer:before) {
  position: absolute;
  inset: 0 3px 3px 0;
  content: '';
  border: 0 solid var(--vgl-resizer-border-color);
  border-right-width: var(--vgl-resizer-border-width);
  border-bottom-width: var(--vgl-resizer-border-width);
}
</style>
