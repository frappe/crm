<template>
  <Popover side="bottom" align="end" @open="load">
    <template #trigger>
      <Button
        variant="ghost"
        icon="lucide-history"
        :tooltip="__('Chats')"
        :aria-label="__('Chats')"
      />
    </template>
    <template #default="{ close }">
      <div class="flex w-80 flex-col gap-1 p-1.5">
        <TextInput
          v-model="query"
          :placeholder="__('Search chats')"
          autocomplete="off"
          @update:model-value="search"
        />
        <div class="max-h-72 overflow-y-auto">
          <button
            v-for="chat in chats"
            :key="chat.name"
            type="button"
            class="flex w-full items-baseline justify-between gap-3 rounded-4 px-2 py-1.5 text-start text-sm hover:bg-surface-gray-2"
            :class="
              chat.name === askFlow.session
                ? 'bg-surface-gray-2 text-ink-gray-9'
                : 'text-ink-gray-8'
            "
            @click="pick(chat, close)"
          >
            <span class="min-w-0 truncate">
              {{ chat.title || __('Untitled chat') }}
            </span>
            <span class="shrink-0 text-xs text-ink-gray-5">
              {{ prettyDate(chat.modified, true) }}
            </span>
          </button>
          <div
            v-if="!loading && !chats.length"
            class="px-2 py-3 text-sm text-ink-gray-5"
          >
            {{ query ? __('No chats match') : __('No chats yet') }}
          </div>
        </div>
      </div>
    </template>
  </Popover>
</template>

<script setup>
import { Button, Popover, TextInput } from 'frappe-ui'
import { ref } from 'vue'
import { prettyDate } from '@/utils'
import { askFlow, listChats, openChat } from './askFlow'

const emit = defineEmits(['open'])

const query = ref('')
const chats = ref([])
const loading = ref(false)
let timer = null

async function load() {
  loading.value = true
  chats.value = await listChats(query.value).catch(() => [])
  loading.value = false
}

function search() {
  clearTimeout(timer)
  timer = setTimeout(load, 200)
}

function pick(chat, close) {
  close()
  openChat(chat.name)
  emit('open')
}
</script>
