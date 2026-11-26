<template>
  <div class="relative flex h-full w-full justify-center">
    <div
      class="absolute left-1/2 flex -translate-x-1/2 flex-col items-center gap-3"
      :class="widthClass"
      :style="{ top: top }"
    >
      <Icon :icon="icon" class="size-7.5 text-ink-gray-5" />
      <div class="flex flex-col items-center gap-1">
        <span class="text-lg-medium text-ink-gray-8">
          {{ computedTitle }}
        </span>
        <span class="text-center text-p-base text-ink-gray-6">
          {{ computedDescription }}
        </span>
      </div>
      <div
        v-if="onCreate || importDoctype || docsLink"
        class="mt-2 flex flex-wrap items-center justify-center gap-2"
      >
        <Button
          v-if="onCreate"
          variant="solid"
          :label="__('Create')"
          iconLeft="lucide-plus"
          @click="onCreate"
        />
        <Button
          v-if="importDoctype"
          :label="__('Import')"
          iconLeft="lucide-upload"
          :route="{ name: 'NewDataImport', params: { doctype: importDoctype } }"
        />
        <Button
          v-if="docsLink"
          variant="outline"
          :label="__('Documentation')"
          iconLeft="lucide-external-link"
          :href="docsLink"
        />
      </div>
    </div>
  </div>
</template>
<script setup>
import Icon from '@/components/Icon.vue'
import { computed } from 'vue'

const props = defineProps({
  name: { type: String, required: true },
  title: { type: String, default: '' },
  description: { type: String, default: '' },
  icon: {
    type: [String, Object],
    default: 'file-text',
  },
  top: { type: String, default: '35%' },
  width: { type: String, default: 'md' },
  // true when the list is empty only because of the applied filters
  filtered: { type: Boolean, default: false },
  docsLink: { type: String, default: '' },
  importDoctype: { type: String, default: '' },
  // declared as a prop so the Create button only shows when a page listens to @create
  onCreate: { type: Function, default: null },
})

const computedTitle = computed(() => {
  if (props.filtered) return __('No {0} Found', [__(props.name)])
  return props.title ? props.title : __('No {0} Found', [__(props.name)])
})

const computedDescription = computed(() => {
  if (props.filtered) return __('Clear the filters to see all records.')
  return props.description
    ? props.description
    : __(
        'It appears that there are currently no {0} available. You can create more {0} by using the Create button.',
        [__(props.name)],
      )
})

const widthClass = computed(() => {
  switch (props.width) {
    case 'sm':
      return 'w-2/12'
    case 'lg':
      return 'w-8/12'
    default:
      return 'w-4/12'
  }
})
</script>
