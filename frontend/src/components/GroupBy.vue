<template>
  <Dropdown :options="options">
    <template #default="{ open }">
      <Button :label="hideLabel ? __('Status') : __('Group By: Status')">
        <template #prefix>
          <DetailsIcon />
        </template>
        <template #suffix>
          <FeatherIcon
            :name="open ? 'chevron-up' : 'chevron-down'"
            class="h-4"
          />
        </template>
      </Button>
    </template>
  </Dropdown>
</template>
<script setup>
import DetailsIcon from '@/components/icons/DetailsIcon.vue'
import { Dropdown } from 'frappe-ui'
import { ref } from 'vue'

const props = defineProps({
  doctype: {
    type: String,
    required: true,
  },
  hideLabel: {
    type: Boolean,
    default: false,
  },
})

const list = defineModel()

const selected = ref('Status')

const options = ref([
  { label: 'Status', value: 'status' },
  { label: 'Source', value: 'source' },
  { label: 'Owner', value: 'owner' },
  { label: 'Created At', value: 'created_at' },
])
</script>
