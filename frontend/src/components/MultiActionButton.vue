<template>
  <div class="flex items-center">
    <Button
      :variant="$attrs.variant"
      class="border-0"
      :label="activeButton.label"
      :size="$attrs.size"
      :class="[
        $attrs.class,
        showDropdown ? 'rounded-br-none rounded-tr-none' : '',
      ]"
      :iconLeft="activeButton.icon"
      @click="() => activeButton.onClick()"
    />
    <Dropdown
      v-if="showDropdown"
      :options="parsedOptions"
      size="sm"
      placement="right"
      :button="{
        icon: 'chevron-down',
        variant: $attrs.variant,
        size: $attrs.size,
        class:
          '!w-6 justify-start rounded-bl-none rounded-tl-none border-0 pr-0 text-xs',
      }"
    />
  </div>
</template>
<script setup>
import { DropdownOption } from '@/utils'
import { Button, Dropdown } from 'frappe-ui'
import { computed, ref } from 'vue'

const props = defineProps({
  options: {
    type: Array,
    default: () => [],
  },
})

const showDropdown = ref(props.options?.length > 1)
const activeButton = ref(props.options?.[0] || {})

const parsedOptions = computed(() => {
  return (
    props.options?.map((option) => {
      return {
        label: option.label,
        component: (props) =>
          DropdownOption({
            option: option.label,
            active: props.active,
            selected: option.label === activeButton.value.label,
            onClick: () => (activeButton.value = option),
          }),
      }
    }) || []
  )
})
</script>
