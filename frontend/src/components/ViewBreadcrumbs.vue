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
          class="text-lg font-medium text-nowrap"
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
      <template #item="{ item, active }">
        <button
          :class="[
            active ? 'bg-gray-100' : 'text-gray-800',
            'group flex gap-4 h-7 w-full justify-between items-center rounded px-2 text-base',
          ]"
          @click="item.onClick"
        >
          <div class="flex items-center">
            <FeatherIcon
              v-if="item.icon && typeof item.icon === 'string'"
              :name="item.icon"
              class="mr-2 h-4 w-4 flex-shrink-0 text-gray-700"
              aria-hidden="true"
            />
            <component
              class="mr-2 h-4 w-4 flex-shrink-0 text-gray-700"
              v-else-if="item.icon"
              :is="item.icon"
            />
            <span class="whitespace-nowrap">
              {{ item.label }}
            </span>
          </div>
          <div
            v-if="item.name"
            class="flex flex-row-reverse gap-2 items-center min-w-11"
          >
            <Dropdown
              :class="active ? 'block' : 'hidden'"
              placement="right-start"
              :options="viewControls.viewActions(item)"
            >
              <template #default="{ togglePopover }">
                <Button
                  variant="ghost"
                  class="!size-5"
                  icon="more-horizontal"
                  @click.stop="togglePopover()"
                />
              </template>
            </Dropdown>
            <FeatherIcon
              v-if="isCurrentView(item)"
              name="check"
              class="size-4 text-gray-700"
            />
          </div>
        </button>
      </template>
    </Dropdown>
  </div>
</template>
<script setup>
import Icon from '@/components/Icon.vue'
import Dropdown from '@/components/frappe-ui/Dropdown.vue'

const props = defineProps({
  routeName: {
    type: String,
    required: true,
  },
})

const viewControls = defineModel()

const isCurrentView = (item) => {
  return item.name === viewControls.value.currentView.name
}
</script>
