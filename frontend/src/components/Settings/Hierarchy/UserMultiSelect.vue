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
    <div
      v-if="loading"
      class="my-2 flex items-center justify-center min-h-32"
    >
      <LoadingIndicator class="size-4 text-ink-gray-5" />
    </div>
    <ul
      v-else-if="filtered.length"
      class="my-2 max-h-64 overflow-y-auto px-1.5"
    >
      <li
        v-for="user in filtered"
        :key="user.value"
        class="flex items-center gap-2 rounded p-1.5 cursor-pointer hover:bg-surface-gray-1"
        :class="{ 'bg-surface-gray-2': isSelected(user) }"
        @click="toggle(user)"
      >
        <Checkbox :model-value="isSelected(user)" @click.stop="toggle(user)" />
        <Avatar :image="user.user_image" :label="user.full_name" size="sm" />
        <div class="flex items-center gap-2 min-w-0 flex-1">
          <span class="text-ink-gray-8 truncate text-p-sm">
            {{ user.full_name }}
          </span>
          <span
            v-if="user.role_label"
            class="text-ink-gray-5 truncate text-p-sm shrink-0"
          >
            {{ user.role_label }}
          </span>
        </div>
      </li>
    </ul>
    <div
      v-else
      class="my-2 flex items-center justify-center min-h-32 text-p-sm text-ink-gray-5"
    >
      {{ __('No users found') }}
    </div>
  </div>
</template>

<script setup>
import {
  Avatar,
  Checkbox,
  FeatherIcon,
  LoadingIndicator,
  TextInput,
} from 'frappe-ui'
import { computed, ref } from 'vue'

const props = defineProps({
  candidates: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
})

const selected = defineModel({ type: Array, default: () => [] })
const query = ref('')

const filtered = computed(() => {
  const qry = query.value.trim().toLowerCase()
  if (!qry) return props.candidates
  return props.candidates.filter(
    (user) =>
      user.full_name?.toLowerCase().includes(qry) ||
      user.email?.toLowerCase().includes(qry)
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
