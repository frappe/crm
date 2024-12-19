<template>
  <Menu as="div" class="relative inline-block text-left" v-slot="{ open }">
    <Popover
      :transition="dropdownTransition"
      :show="open"
      :placement="popoverPlacement"
    >
      <template #target="{ togglePopover }">
        <MenuButton as="template">
          <slot v-if="$slots.default" v-bind="{ open, togglePopover }" />
          <Button v-else :active="open" v-bind="button">
            {{ button ? button?.label || null : 'Options' }}
          </Button>
        </MenuButton>
      </template>

      <template #body>
        <div
          class="mt-2 min-w-40 divide-y divide-outline-gray-modals rounded-lg bg-surface-modal shadow-2xl ring-1 ring-black ring-opacity-5 focus:outline-none"
          :class="{
            'mt-2': ['bottom', 'left', 'right'].includes(placement),
            'ml-2': placement == 'right-start',
          }"
        >
          <MenuItems
            class="min-w-40 divide-y divide-outline-gray-modals"
            :class="{
              'left-0 origin-top-left': placement == 'left',
              'right-0 origin-top-right': placement == 'right',
              'inset-x-0 origin-top': placement == 'center',
              'mt-0 origin-top-right': placement == 'right-start',
            }"
          >
            <div v-for="group in groups" :key="group.key" class="p-1.5">
              <div
                v-if="group.group && !group.hideLabel"
                class="flex h-7 items-center px-2 text-sm font-medium text-ink-gray-4"
              >
                {{ group.group }}
              </div>
              <MenuItem
                v-for="item in group.items"
                :key="item.label"
                v-slot="{ active }"
              >
                <slot name="item" v-bind="{ item, active }">
                  <component
                    v-if="item.component"
                    :is="item.component"
                    :active="active"
                  />
                  <button
                    v-else
                    :class="[
                      active ? 'bg-surface-gray-3' : 'text-ink-gray-6',
                      'group flex h-7 w-full items-center rounded px-2 text-base',
                    ]"
                    @click="item.onClick"
                  >
                    <FeatherIcon
                      v-if="item.icon && typeof item.icon === 'string'"
                      :name="item.icon"
                      class="mr-2 h-4 w-4 flex-shrink-0 text-ink-gray-7"
                      aria-hidden="true"
                    />
                    <component
                      class="mr-2 h-4 w-4 flex-shrink-0 text-ink-gray-7"
                      v-else-if="item.icon"
                      :is="item.icon"
                    />
                    <span class="whitespace-nowrap text-ink-gray-7">
                      {{ item.label }}
                    </span>
                  </button>
                </slot>
              </MenuItem>
            </div>
          </MenuItems>
          <div v-if="slots.footer" class="border-t p-1.5">
            <slot name="footer"></slot>
          </div>
        </div>
      </template>
    </Popover>
  </Menu>
</template>

<script setup>
import { Menu, MenuButton, MenuItems, MenuItem } from '@headlessui/vue'
import { Popover, Button, FeatherIcon } from 'frappe-ui'
import { computed, useSlots } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  button: {
    type: Object,
    default: null,
  },
  options: {
    type: Array,
    default: () => [],
  },
  placement: {
    type: String,
    default: 'left',
  },
})

const router = useRouter()
const slots = useSlots()

const dropdownTransition = {
  enterActiveClass: 'transition duration-100 ease-out',
  enterFromClass: 'transform scale-95 opacity-0',
  enterToClass: 'transform scale-100 opacity-100',
  leaveActiveClass: 'transition duration-75 ease-in',
  leaveFromClass: 'transform scale-100 opacity-100',
  leaveToClass: 'transform scale-95 opacity-0',
}

const groups = computed(() => {
  let groups = props.options[0]?.group
    ? props.options
    : [{ group: '', items: props.options }]

  return groups.map((group, i) => {
    return {
      key: i,
      group: group.group,
      hideLabel: group.hideLabel || false,
      items: filterOptions(group.items),
    }
  })
})

const popoverPlacement = computed(() => {
  if (props.placement === 'left') return 'bottom-start'
  if (props.placement === 'right') return 'bottom-end'
  if (props.placement === 'center') return 'bottom-center'
  if (props.placement === 'right-start') return 'right-start'
  return 'bottom'
})

function normalizeDropdownItem(option) {
  let onClick = option.onClick || null
  if (!onClick && option.route && router) {
    onClick = () => router.push(option.route)
  }

  return {
    name: option.name,
    label: option.label,
    icon: option.icon,
    group: option.group,
    component: option.component,
    onClick,
  }
}

function filterOptions(options) {
  return (options || [])
    .filter(Boolean)
    .filter((option) => (option.condition ? option.condition() : true))
    .map((option) => normalizeDropdownItem(option))
}
</script>
