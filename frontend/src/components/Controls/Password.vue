<template>
  <FormControl
    :type="show ? 'text' : 'password'"
    :value="modelValue || value"
    v-bind="$attrs"
    @keydown.meta.i.prevent="show = !show"
    @keydown.ctrl.i.prevent="show = !show"
  >
    <template #prefix v-if="$slots.prefix">
      <slot name="prefix" />
    </template>
    <template #suffix>
      <Tooltip>
        <template #body>
          <div
            class="rounded bg-surface-gray-7 py-1.5 px-2 text-xs text-ink-white shadow-xl"
          >
            <span class="flex items-center gap-1">
              {{ show ? __('Hide Password') : __('Show Password') }}
              <KeyboardShortcut
                bg
                ctrl
                class="!bg-surface-gray-5 !text-ink-gray-2 px-1"
              >
                <span class="font-mono leading-none tracking-widest">+I</span>
              </KeyboardShortcut>
            </span>
          </div>
        </template>
        <div>
          <FeatherIcon
            v-show="showEye"
            :name="show ? 'eye-off' : 'eye'"
            class="h-3 cursor-pointer mr-1"
            @click="show = !show"
          />
        </div>
      </Tooltip>
    </template>
  </FormControl>
</template>
<script setup>
import KeyboardShortcut from '@/components/KeyboardShortcut.vue'
import { FormControl, Tooltip } from 'frappe-ui'
import { ref, computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: [String, Number],
    default: '',
  },
  value: {
    type: [String, Number],
    default: '',
  },
})
const show = ref(false)
const showEye = computed(() => {
  let v = props.modelValue || props.value
  return !v?.includes('*')
})
</script>
