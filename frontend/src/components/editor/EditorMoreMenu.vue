<template>
  <span ref="anchor" class="inline-flex">
    <Dropdown :options="options">
      <slot :isActive="false" :onClick="() => {}" />
    </Dropdown>
  </span>
</template>

<script setup>
import { Dropdown } from 'frappe-ui'
import { computed, ref } from 'vue'
import { moreToolbarItems } from '@/components/editor/config'

const props = defineProps({
  editor: { type: Object, required: true },
})

const anchor = ref(null)

const options = computed(() =>
  moreToolbarItems
    .filter((item) => !item.isAvailable || item.isAvailable(props.editor))
    .map((item) => ({
      label: __(item.label),
      icon: item.icon,
      // pickers like font colour open next to the More button
      onClick: () => item.action(props.editor, { trigger: anchor.value }),
    })),
)
</script>
