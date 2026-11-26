<template>
  <Dropdown :options="dropdownItems" v-bind="$attrs">
    <template #default="{ open }">
      <button
        class="flex h-9 items-center rounded-4 px-1 duration-300 ease-in-out"
        :class="
          isCollapsed
            ? 'w-auto'
            : open
              ? 'w-full bg-surface-elevation-3 shadow-sm'
              : 'w-full hover:bg-surface-gray-2'
        "
      >
        <BrandLogo v-model="brand" class="h-6 max-w-12 flex-shrink-0" />
        <div
          class="flex flex-1 flex-col text-left duration-300 ease-in-out truncate"
          :class="
            isCollapsed
              ? 'ml-0 w-0 overflow-hidden opacity-0'
              : 'ml-2 w-auto opacity-100'
          "
        >
          <div class="text-base-medium leading-none text-ink-gray-9 truncate">
            {{ __(brand.name || 'CRM') }}
          </div>
        </div>
        <div
          class="duration-300 ease-in-out"
          :class="
            isCollapsed
              ? 'ml-0 w-0 overflow-hidden opacity-0'
              : 'ml-2 mr-1 w-auto opacity-100'
          "
        >
          <span
            class="lucide-chevron-down size-4 text-ink-gray-5"
            aria-hidden="true"
          />
        </div>
      </button>
    </template>
  </Dropdown>
</template>

<script setup>
import BrandLogo from '@/components/BrandLogo.vue'
import { getSettings } from '@/stores/settings'
import { useAppMenu } from '@/composables/appMenu'
import { Dropdown } from 'frappe-ui'

defineProps({
  isCollapsed: { type: Boolean, default: false },
})

const { settings, brand } = getSettings()
const { groups: dropdownItems } = useAppMenu(
  () => settings.value?.dropdown_items,
)
</script>
