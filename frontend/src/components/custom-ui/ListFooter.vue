<template>
  <ListFooter
    :model-value="modelValue"
    :show-more="showMore"
    :loading="loading"
    :options="options"
    @update:model-value="$emit('update:modelValue', $event)"
    @load-more="$emit('load-more')"
  >
    <template #right>
      <div class="flex items-center">
        <Button
          v-if="showLoadMore"
              :label="__('Load More')"
          @click="$emit('load-more')"
        />
        <div v-if="showLoadMore" class="mx-3 h-[80%] border-l" />
        <div class="flex items-center gap-1 text-base text-ink-gray-5">
          <div>{{ options.rowCount || '0' }}</div>
          <div>из</div>
          <div>{{ options.totalCount || '0' }}</div>
        </div>
      </div>
    </template>
  </ListFooter>
</template> 

<script setup>
import { ListFooter } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: Number,
    default: 20,
  },
  showMore: {
    type: Boolean,
    default: false,
  },
  loading: {
    type: Boolean,
    default: false,
  },
  options: {
    type: Object,
    default: () => ({
      rowCount: 0,
      totalCount: 0,
    }),
  },
})

defineEmits(['load-more', 'update:modelValue'])

const showLoadMore = computed(() => {
  return (
    props.options.rowCount &&
    props.options.totalCount &&
    props.options.rowCount < props.options.totalCount
  )
})
</script>