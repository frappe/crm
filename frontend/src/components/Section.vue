<template>
  <div>
    <slot name="header" v-bind="{ opened, hide, open, close, toggle }">
      <div
        v-if="!hide"
        class="section-header flex items-center justify-between"
        :class="headerClass"
      >
        <div
          class="flex text-ink-gray-9 max-w-fit cursor-pointer items-center gap-2 text-base"
          :class="labelClass"
          @click="collapsible && toggle()"
        >
          <FeatherIcon
            v-if="collapsible && collapseIconPosition === 'left'"
            name="chevron-right"
            class="h-4 transition-all duration-300 ease-in-out"
            :class="{ 'rotate-90': opened }"
          />
          <span>
            {{ __(label) || __('Untitled') }}
          </span>
          <FeatherIcon
            v-if="collapsible && collapseIconPosition === 'right'"
            name="chevron-right"
            class="h-4 transition-all duration-300 ease-in-out"
            :class="{ 'rotate-90': opened }"
          />
        </div>
        <slot name="actions"></slot>
      </div>
    </slot>
    <transition
      enter-active-class="duration-300 ease-in"
      leave-active-class="duration-300 ease-[cubic-bezier(0, 1, 0.5, 1)]"
      enter-to-class="max-h-[200px] overflow-hidden"
      leave-from-class="max-h-[200px] overflow-hidden"
      enter-from-class="max-h-0 overflow-hidden"
      leave-to-class="max-h-0 overflow-hidden"
    >
      <div class="columns" v-bind="$attrs" v-show="opened">
        <slot v-bind="{ opened, open, close, toggle }" />
      </div>
    </transition>
  </div>
</template>
<script setup>
import { ref } from 'vue'

const props = defineProps({
  label: {
    type: String,
    default: '',
  },
  hideLabel: {
    type: Boolean,
    default: false,
  },
  opened: {
    type: Boolean,
    default: true,
  },
  collapsible: {
    type: Boolean,
    default: true,
  },
  collapseIconPosition: {
    type: String,
    default: 'left',
  },
  labelClass: {
    type: [String, Object, Array],
    default: '',
  },
  headerClass: {
    type: [String, Object, Array],
    default: '',
  },
})

const hide = ref(props.hideLabel)
const opened = ref(props.opened)

function toggle() {
  opened.value = !opened.value
}

function open() {
  opened.value = true
}

function close() {
  opened.value = false
}
</script>
<script>
export default {
  inheritAttrs: false,
}
</script>
