<!-- The App menu as people will see it, drawn from the unsaved rows. -->
<template>
  <aside :aria-label="__('Preview')" class="flex w-64 shrink-0 flex-col gap-3">
    <div class="text-sm text-ink-gray-6">{{ __('Preview') }}</div>
    <div class="flex flex-col gap-1.5 rounded-6 bg-surface-gray-1 p-3">
      <div
        class="flex h-10 items-center gap-2 rounded-4 bg-surface-elevation-1 px-2 shadow-sm"
      >
        <BrandLogo v-model="brand" class="h-6 max-w-12 shrink-0" />
        <span class="truncate text-base-medium text-ink-gray-9">
          {{ __(brand.name || 'CRM') }}
        </span>
      </div>
      <div
        class="flex flex-col rounded-6 bg-surface-elevation-2 p-1 shadow-lg ring-1 ring-black/5"
      >
        <template v-for="(group, index) in visibleGroups" :key="index">
          <div v-if="index" class="my-1 border-t border-outline-gray-2" />
          <div
            v-for="option in group.options"
            :key="option.label"
            class="flex h-7 items-center gap-2 px-2 text-base text-ink-gray-8"
          >
            <component :is="option.icon" class="size-4 text-ink-gray-6" />
            <span class="flex-1 truncate">{{ option.label }}</span>
            <span
              v-if="option.submenu"
              class="lucide-chevron-right size-4 text-ink-gray-5"
              aria-hidden="true"
            />
          </div>
        </template>
        <div
          v-if="!visibleGroups.length"
          class="px-2 py-1.5 text-sm text-ink-gray-5"
        >
          {{ __('Every item is hidden.') }}
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup>
import BrandLogo from '@/components/BrandLogo.vue'
import { useAppMenu } from '@/composables/appMenu'
import { getSettings } from '@/stores/settings'
import { computed } from 'vue'

const props = defineProps({ items: { type: Array, required: true } })

const { brand } = getSettings()
const { groups } = useAppMenu(() => props.items)

// Items that only show on Frappe Cloud sites or on desktop are left out, as they are for the viewer.
const visibleGroups = computed(() =>
  groups.value
    .map((group) => ({
      options: group.options.filter(
        (option) => option && (!option.condition || option.condition()),
      ),
    }))
    .filter((group) => group.options.length),
)
</script>
