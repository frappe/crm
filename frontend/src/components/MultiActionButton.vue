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
      @click="() => activeButton.onClick()"
    >
      <template #prefix>
        <FeatherIcon
          v-if="activeButton.icon && typeof activeButton.icon === 'string'"
          :name="activeButton.icon"
          class="h-4 w-4"
        />
        <component
          v-else-if="activeButton.icon"
          :is="activeButton.icon"
          class="h-4 w-4"
        />
      </template>
    </Button>
    <Dropdown
      v-show="showDropdown"
      :options="parsedOptions"
      size="sm"
      class="flex-1 [&>div>div>div]:w-full"
      placement="right"
    >
      <template v-slot="{ togglePopover }">
        <Button
          :variant="$attrs.variant"
          @click="togglePopover"
          icon="chevron-down"
          class="!w-6 justify-start rounded-bl-none rounded-tl-none border-0 pr-0 text-xs"
        />
      </template>
    </Dropdown>
  </div>
</template>
<script setup>
import { Dropdown } from 'frappe-ui'
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
        onClick: () => {
          activeButton.value = option
        },
      }
    }) || []
  )
})
</script>
