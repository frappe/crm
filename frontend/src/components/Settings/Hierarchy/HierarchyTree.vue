<!-- Local recursive tree for the Sales Hierarchy. Reproduces frappe-ui's
     pre-beta.12 Tree so this view keeps owning its rows, drag-drop and
     connectors. -->
<template>
  <slot
    name="node"
    v-bind="{ node, hasChildren, isCollapsed, toggleCollapsed }"
  >
    <div
      class="flex items-center cursor-pointer gap-1"
      :style="{ height: options.rowHeight }"
      @click="toggleCollapsed"
    >
      <div ref="iconRef">
        <slot name="icon" v-bind="{ hasChildren, isCollapsed }">
          <span
            v-if="hasChildren && !isCollapsed"
            class="lucide-chevron-down size-3.5"
            aria-hidden="true"
          />
          <span
            v-else-if="hasChildren"
            class="lucide-chevron-right size-3.5"
            aria-hidden="true"
          />
        </slot>
      </div>

      <slot name="label" v-bind="{ node, hasChildren, isCollapsed }">
        <div class="text-base truncate" :class="hasChildren ? '' : 'pl-3.5'">
          {{ node.label }}
        </div>
      </slot>
    </div>
  </slot>

  <div v-if="hasChildren && !isCollapsed" class="flex">
    <div
      v-if="options.showIndentationGuides"
      :style="{ paddingLeft: linePadding }"
      class="border-r"
    ></div>
    <ul class="w-full" :style="{ paddingLeft: options.indentWidth }">
      <li v-for="child in node.children" :key="child[nodeKey]">
        <HierarchyTree :node="child" :node-key="nodeKey" :options="options">
          <template #node="slotProps">
            <slot name="node" v-bind="slotProps" />
          </template>
          <template #icon="slotProps">
            <slot name="icon" v-bind="slotProps" />
          </template>
          <template #label="slotProps">
            <slot name="label" v-bind="slotProps" />
          </template>
        </HierarchyTree>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const props = defineProps({
  node: { type: Object, required: true },
  nodeKey: { type: String, required: true },
  options: {
    type: Object,
    default: () => ({
      rowHeight: '25px',
      indentWidth: '20px',
      showIndentationGuides: true,
      defaultCollapsed: true,
    }),
  },
})

const isCollapsed = ref(props.options.defaultCollapsed ?? true)
const linePadding = ref('')
const iconRef = ref(null)

const hasChildren = computed(() => props.node.children?.length > 0)

function toggleCollapsed(event) {
  event.stopPropagation()
  if (hasChildren.value) isCollapsed.value = !isCollapsed.value
}

onMounted(() => {
  if (iconRef.value?.clientWidth)
    linePadding.value = iconRef.value.clientWidth / 2 + 'px'
})
</script>
