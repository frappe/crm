<template>
  <div class="flex flex-col">
    <div class="px-2 pt-1.5">
      <TextInput
        v-model="query"
        :placeholder="__('Search users')"
        :debounce="200"
      >
        <template #prefix>
          <FeatherIcon name="search" class="size-4 text-ink-gray-5" />
        </template>
      </TextInput>
    </div>
    <ul class="my-2 max-h-64 overflow-y-auto px-1.5">
      <li
        v-for="user in filtered"
        :key="user.value"
        class="flex items-center gap-2 rounded p-1.5 cursor-pointer hover:bg-surface-gray-1"
        :class="{ 'bg-surface-gray-2': isSelected(user) }"
        @click="toggle(user)"
      >
        <Checkbox :model-value="isSelected(user)" @click.stop="toggle(user)" />
        <Avatar :image="user.user_image" :label="user.full_name" size="sm" />
        <div class="flex flex-col min-w-0 flex-1">
          <div class="text-ink-gray-8 truncate text-p-sm">
            {{ user.full_name }}
          </div>
        </div>
      </li>
      <li
        v-if="!filtered.length"
        class="p-2 text-p-sm text-ink-gray-5 text-center"
      >
        {{ __('No users found') }}
      </li>
    </ul>
  </div>
</template>

<script setup>
import { Avatar, Checkbox, FeatherIcon, TextInput } from 'frappe-ui'
import { computed, ref } from 'vue'

const props = defineProps({
  candidates: { type: Array, default: () => [] },
})

const selected = defineModel({ type: Array, default: () => [] })
const query = ref('')

const filtered = computed(() => {
  const qry = query.value.trim().toLowerCase()
  if (!qry) return props.candidates
  return props.candidates.filter(
    (user) =>
      user.full_name?.toLowerCase().includes(qry) ||
      user.email?.toLowerCase().includes(qry),
  )
})

function isSelected(val) {
  return selected.value.includes(val.value)
}

function toggle(val) {
  if (isSelected(val)) {
    selected.value = selected.value.filter((id) => id !== val.value)
  } else {
    selected.value = [...selected.value, val.value]
  }
}
</script>
