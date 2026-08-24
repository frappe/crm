<template>
  <MultiSelect
    :model-value="modelValue"
    :label="label"
    :options="options"
    :loading="loading"
    :placeholder="__('Select users')"
    :empty-text="__('No users found')"
    @update:model-value="$emit('update:modelValue', $event)"
    @update:query="query = $event"
  >
    <template #item-prefix="{ item }">
      <UserAvatar :user="item.value" size="sm" />
    </template>
    <template #item-label="{ item }">
      <div class="truncate text-ink-gray-9">{{ item.label }}</div>
    </template>
  </MultiSelect>
</template>

<script setup>
import UserAvatar from '@/components/UserAvatar.vue'
import { MultiSelect, call } from 'frappe-ui'
import { watchDebounced } from '@vueuse/core'
import { computed, ref } from 'vue'

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  actionType: { type: String, required: true },
  fieldname: { type: String, required: true },
  doctype: { type: String, default: '' },
  params: { type: String, default: '{}' },
  label: { type: String, default: '' },
})

defineEmits(['update:modelValue'])

const query = ref('')
const loading = ref(false)
const fetchedOptions = ref([])
let requestId = 0

const options = computed(() => {
  const values = new Map(props.modelValue.map(fallbackOption))
  fetchedOptions.value.forEach((option) => values.set(option.value, option))
  return [...values.values()]
})

watchDebounced(query, loadUsers, { debounce: 250, immediate: true })

async function loadUsers(searchText) {
  const currentRequest = ++requestId
  loading.value = true
  try {
    const users = await call('frappe.automation_engine.api.get_param_options', {
      action_type: props.actionType,
      fieldname: props.fieldname,
      doctype: props.doctype,
      params: props.params,
      search_text: searchText,
    })
    if (currentRequest === requestId)
      fetchedOptions.value = users.map(userOption)
  } catch (error) {
    console.error('Unable to load automation assignees', error)
    if (currentRequest === requestId) fetchedOptions.value = []
  } finally {
    if (currentRequest === requestId) loading.value = false
  }
}

function fallbackOption(value) {
  return [value, { label: value, value }]
}

function userOption(user) {
  return {
    label: user.full_name || user.name,
    value: user.name,
  }
}
</script>
