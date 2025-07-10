<template>
  <div class="flex h-full flex-col gap-6 p-8 text-ink-gray-8">
    <div class="flex flex-col gap-1">
      <h2 class="flex gap-2 text-xl font-semibold leading-none h-5">
        {{ __('General') }}
      </h2>
      <p class="text-p-base text-ink-gray-6">
        {{ __('Configure general settings for your CRM') }}
      </p>
    </div>

    <div class="flex-1 flex flex-col overflow-y-auto">
      <template v-for="(setting, i) in settings" :key="setting.name">
        <li
          class="flex items-center justify-between p-3 cursor-pointer hover:bg-surface-menu-bar rounded"
          @click="() => emit('updateStep', setting.name)"
        >
          <div class="flex flex-col">
            <div class="text-base font-medium text-ink-gray-7 truncate">
              {{ __(setting.label) }}
            </div>
            <div class="text-p-base text-ink-gray-5 truncate">
              {{ __(setting.description) }}
            </div>
          </div>
          <div>
            <FeatherIcon name="chevron-right" class="text-ink-gray-7 size-4" />
          </div>
        </li>
        <div
          v-if="settings !== i + 1"
          class="h-px border-t mx-2 border-outline-gray-modals"
        />
      </template>
    </div>
  </div>
</template>

<script setup>
const emit = defineEmits(['updateStep'])

const settings = [
  {
    name: 'brand-settings',
    label: 'Brand settings',
    description: 'Configure your brand name, logo and favicon',
  },
  {
    name: 'home-actions',
    label: 'Home actions',
    description: 'Configure actions that appear on the home dropdown',
  },
]
</script>
