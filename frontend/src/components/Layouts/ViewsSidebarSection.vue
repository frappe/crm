<template>
  <div>
    <div v-for="view in allViews" :key="view.label">
      <div
        v-if="!view.hideLabel && isSidebarCollapsed && view.views?.length"
        class="mx-2 my-2 h-1 border-b"
      />
      <CollapsibleSection
        :label="view.name"
        :hideLabel="view.hideLabel"
        :opened="view.opened"
      >
        <template #header="{ opened, hide, toggle }">
          <div
            v-if="!hide"
            class="flex cursor-pointer gap-1.5 px-1 text-base font-medium text-ink-gray-5 transition-all duration-300 ease-in-out"
            :class="
              isSidebarCollapsed
                ? 'ml-0 h-0 overflow-hidden opacity-0'
                : 'ml-2 mt-4 h-7 w-auto opacity-100'
            "
            @click="toggle()"
          >
            <FeatherIcon
              name="chevron-right"
              class="h-4 text-ink-gray-9 transition-all duration-300 ease-in-out"
              :class="{ 'rotate-90': opened }"
            />
            <span>{{ __(view.name) }}</span>
          </div>
        </template>
        <nav class="flex flex-col">
          <SidebarLink
            v-for="link in view.views"
            :key="link.label"
            :icon="link.icon"
            :label="__(link.label)"
            :to="link.to"
            :isCollapsed="isSidebarCollapsed"
            class="mx-2 my-0.5"
          />
        </nav>
      </CollapsibleSection>
    </div>
  </div>
</template>

<script setup>
import CollapsibleSection from '@/components/CollapsibleSection.vue'
import SidebarLink from '@/components/SidebarLink.vue'
import { FeatherIcon } from 'frappe-ui'
import { allViews } from './view.js'

defineProps({
  isSidebarCollapsed: {
    type: Boolean,
    required: true,
  },
})
</script>
