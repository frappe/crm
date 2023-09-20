<template>
  <div
    class="flex h-7 items-center rounded text-gray-800 cursor-pointer transition-all duration-300 ease-in-out"
    :class="isActive ? 'bg-white shadow-sm' : 'hover:bg-gray-100'"
    @click="handleClick"
  >
    <div class="flex items-center p-1">
      <Tooltip :text="label" placement="right">
        <slot name="icon">
          <span class="grid h-5 w-6 place-items-center flex-shrink-0">
            <component :is="icon" class="h-4.5 w-4.5 text-gray-700" />
          </span>
        </slot>
      </Tooltip>
      <span
        class="flex-shrink-0 text-base duration-300 ease-in-out"
        :class="
          isCollapsed ? 'opacity-0 ml-0 w-0 overflow-hidden' : 'opacity-100 ml-2 w-auto'
        "
      >
        {{ label }}
      </span>
    </div>
  </div>
</template>

<script setup>
import { Tooltip } from 'frappe-ui'
import { computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const props = defineProps({
  icon: {
    type: Object,
  },
  label: {
    type: String,
    default: '',
  },
  to: {
    type: String,
    default: '',
  },
  isCollapsed: {
    type: Boolean,
    default: false,
  },
})

function handleClick() {
  router.push({ name: props.to })
}

let isActive = computed(() => {
  return router.currentRoute.value.name === props.to
})
</script>
