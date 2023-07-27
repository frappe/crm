<template>
  <div id="tabs-header" class="flex items-center gap-6 border-b pl-5">
    <div
      class="cursor-pointer flex items-center gap-2 py-2 border-b hover:text-gray-900 hover:border-gray-400 -mb-[1px]"
      :class="
        activeTab == tab.label
          ? 'border-blue-500 text-gray-900 hover:border-blue-500'
          : 'border-transparent text-gray-700'
      "
      v-for="tab in tabs"
      :key="tab.label"
      @click="activeTab = tab.label"
    >
      <component v-if="tab.icon" :is="tab.icon" class="h-5" />
      {{ tab.label }}
    </div>
  </div>
  <div id="tabs-contents" class="h-full">
    <div class="bg-gray-50 h-full">
      <div v-for="tab in tabs" :key="tab.label">
        <div v-if="activeTab == tab.label" class="p-6">
          <slot name="tab-content" v-bind="{ tab }" />
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref } from 'vue'

const props = defineProps({
  tabs: {
    type: Array,
    required: true,
  },
})
let activeTab = ref(props.tabs[0].label)
</script>
