<template>
  <span ref="anchor" class="inline-flex">
    <Dropdown :options="options">
      <slot :isActive="false" :onClick="() => {}" />
    </Dropdown>
  </span>
</template>

<script setup lang="ts">
import { Dropdown } from 'frappe-ui'
import type { Editor } from '@tiptap/core'
import { computed, ref } from 'vue'
import { moreToolbarItems } from '@/components/editor/config'

const props = defineProps<{ editor: Editor }>()

const anchor = ref<HTMLElement | null>(null)

const options = computed(() =>
  moreToolbarItems
    .filter((item) => !item.isAvailable || item.isAvailable(props.editor))
    .map((item) => ({
      label: __(item.label),
      icon: item.icon,
      // pickers like font colour open next to the More button
      onClick: () =>
        item.action(props.editor, { trigger: anchor.value ?? undefined }),
    })),
)
</script>
