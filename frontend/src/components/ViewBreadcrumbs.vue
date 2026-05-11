<template>
  <div class="flex items-center">
    <router-link
      :to="{ name: routeName }"
      class="px-0.5 py-1 text-lg font-medium focus:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
      :class="[
        viewControls && viewControls.viewsDropdownOptions
          ? 'text-ink-gray-5 hover:text-ink-gray-7'
          : 'text-ink-gray-7',
      ]"
    >
      {{ __(routeName) }}
    </router-link>
    <span
      v-if="viewControls && viewControls.viewsDropdownOptions"
      class="mx-0.5 text-base text-ink-gray-4"
      aria-hidden="true"
    >
      /
    </span>
    <Dropdown
      v-if="viewControls && viewControls.viewsDropdownOptions"
      :options="viewControls.viewsDropdownOptions"
    >
      <template #trigger="{ open }">
        <Button
          variant="ghost"
          class="text-lg font-medium text-nowrap"
          :label="__(viewControls.currentView?.label)"
          :iconRight="open ? 'chevron-up' : 'chevron-down'"
        >
          <template #prefix>
            <Icon :icon="viewControls.currentView?.icon" class="h-4" />
          </template>
        </Button>
      </template>
      <template #item-suffix="{ item }">
        <div
          v-if="item.name"
          class="flex flex-row-reverse gap-2 items-center min-w-11"
        >
          <Dropdown
            side="right"
            :offset="15"
            :options="viewControls.viewActions(item, close)"
          >
            <template #trigger>
              <Button
                variant="ghost"
                class="[[role=menuitem]:hover_&]:!w-auto !h-4 !w-0 opacity-0 [[role=menuitem]:hover_&]:opacity-100 pointer-events-none [[role=menuitem]:hover_&]:pointer-events-auto"
                icon="more-horizontal"
                @click.stop
              />
            </template>
          </Dropdown>
          <FeatherIcon
            v-if="isCurrentView(item)"
            name="check"
            class="size-4 text-ink-gray-7"
          />
        </div>
      </template>
    </Dropdown>
  </div>
</template>
<script setup>
import Icon from '@/components/Icon.vue'
import { Dropdown } from 'frappe-ui'

defineProps({
  routeName: { type: String, required: true },
})

const viewControls = defineModel({ type: Object, default: () => ({}) })

const isCurrentView = (item) => {
  if (viewControls.value.currentView.is_standard) {
    return item.label === viewControls.value.currentView.label
  }
  return item.name === viewControls.value.currentView.name
}
</script>
