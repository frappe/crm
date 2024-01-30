<template>
  <button
    class="flex h-7 cursor-pointer items-center rounded text-gray-800 duration-300 ease-in-out focus:outline-none focus:transition-none focus-visible:rounded focus-visible:ring-2 focus-visible:ring-gray-400"
    :class="isActive ? 'bg-white shadow-sm' : 'hover:bg-gray-100'"
    @click="handleClick"
  >
    <div
      class="flex w-full justify-between items-center duration-300 ease-in-out"
      :class="isCollapsed ? 'p-1' : 'px-2 py-1'"
    >
      <div class="flex items-center">
        <Tooltip :text="label" placement="right">
          <slot name="icon">
            <span class="grid h-5 w-6 flex-shrink-0 place-items-center">
              <component :is="icon" class="h-4 w-4 text-gray-700" />
            </span>
          </slot>
        </Tooltip>
        <span
          class="flex-1 flex-shrink-0 text-sm duration-300 ease-in-out"
          :class="
            isCollapsed
              ? 'ml-0 w-0 overflow-hidden opacity-0'
              : 'ml-2 w-auto opacity-100'
          "
        >
          {{ label }}
        </span>
      </div>
      <slot name="right" />
    </div>
  </button>
</template>

<script setup>
import { Tooltip } from 'frappe-ui'
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()

const props = defineProps({
  icon: {
    type: Object,
  },
  label: {
    type: String,
    default: '',
  },
  to: {
    type: [Object, String],
    default: '',
  },
  isCollapsed: {
    type: Boolean,
    default: false,
  },
})

function handleClick() {
  if (typeof props.to === 'object') {
    router.push(props.to)
  } else {
    router.push({ name: props.to })
  }
}

let isActive = computed(() => {
  if (route.query.view) {
    return route.query.view == props.to?.query?.view
  }
  return route.name === props.to
})
</script>
