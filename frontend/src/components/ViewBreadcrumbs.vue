<template>
  <div class="flex items-center">
    <router-link
      :to="{ name: routeName }"
      class="px-0.5 py-1 text-lg-medium focus:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
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
      <template #default="{ open }">
        <Button
          variant="ghost"
          class="text-lg-medium text-nowrap"
          :label="__(viewControls.currentView?.label)"
          :iconRight="open ? 'chevron-up' : 'chevron-down'"
        >
          <template #prefix>
            <Icon :icon="viewControls.currentView?.icon" class="h-4" />
          </template>
        </Button>
      </template>
      <template #item-suffix="{ item, close, selected }">
        <div v-if="item.name" class="flex flex-row-reverse gap-2 items-center">
          <Dropdown
            side="right"
            :offset="15"
            :options="viewControls.viewActions(item, close)"
          >
            <template #default>
              <Button
                variant="ghost"
                class="!size-5 opacity-0 group-hover:opacity-100"
                icon="lucide-more-horizontal"
                @click.stop
              />
            </template>
          </Dropdown>
          <span
            v-if="selected"
            class="lucide-check size-4 text-ink-gray-7"
            aria-hidden="true"
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
</script>
