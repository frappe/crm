<template>
  <div class="flex items-center">
    <router-link
      :to="{ name: routeName }"
      class="px-0.5 py-1 text-lg font-medium focus:outline-none focus-visible:ring-2 focus-visible:ring-gray-400 text-gray-600 hover:text-gray-700"
    >
      {{ __(routeName) }}
    </router-link>
    <span class="mx-0.5 text-base text-gray-500" aria-hidden="true"> / </span>
    <Dropdown v-if="viewControls" :options="viewControls.viewsDropdownOptions">
      <template #default="{ open }">
        <Button
          variant="ghost"
          class="text-lg font-medium"
          :label="__(viewControls.currentView.label)"
        >
          <template #prefix>
            <Icon :icon="viewControls.currentView.icon" class="h-4" />
          </template>
          <template #suffix>
            <FeatherIcon
              :name="open ? 'chevron-up' : 'chevron-down'"
              class="h-4 text-gray-800"
            />
          </template>
        </Button>
      </template>
    </Dropdown>
    <Dropdown :options="viewControls.viewActions">
      <template #default>
        <Button variant="ghost" icon="more-horizontal" />
      </template>
    </Dropdown>
  </div>
</template>
<script setup>
import Icon from '@/components/Icon.vue'
import { Dropdown } from 'frappe-ui'

const props = defineProps({
  routeName: {
    type: String,
    required: true,
  },
})

const viewControls = defineModel()
</script>
