<!-- Smart filter field component -->
<template>
  <div class="relative w-96">
    <FormControl
      type="text"
      v-model="searchText"
      :placeholder="getPlaceholder"
      @input="handleInput"
      class="w-full"
    >
      <template #prefix>
        <FeatherIcon name="search" class="h-4 w-4 text-gray-500" />
      </template>
      <template #suffix v-if="searchText">
        <div class="flex items-center h-full">
          <Button
            variant="ghost"
            class="!p-1"
            @click="clearSearch"
          >
            <FeatherIcon name="x" class="h-4 w-4" />
          </Button>
        </div>
      </template>
    </FormControl>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { FormControl, Button, FeatherIcon } from 'frappe-ui'
import { useDebounceFn } from '@vueuse/core'
import { parseSmartFilter, formatSmartFilterParams } from '@/utils/smartFilter'

const props = defineProps({
  doctype: {
    type: String,
    default: 'CRM Lead'
  }
})

const searchText = ref('')
const emit = defineEmits(['update:filters'])

const getPlaceholder = computed(() => {
  switch (props.doctype) {
    case 'CRM Organization':
      return __('Search by website or industry...')
    case 'Contact':
      return __('Search by phone, email or company...')
    case 'CRM Deal':
      return __('Search by phone, email or company...')
    default:
      return __('Search by phone, name or email...')
  }
})

const debouncedSearch = useDebounceFn((value) => {
  if (!value) {
    emit('update:filters', {})
    return
  }
  const smartFilterParams = parseSmartFilter(value, props.doctype)
  if (smartFilterParams) {
    emit('update:filters', smartFilterParams)
  }
}, 300)

function handleInput(event) {
  debouncedSearch(event.target.value)
}

function clearSearch() {
  searchText.value = ''
  emit('update:filters', {})
}

defineExpose({
  clearSearch
})
</script> 