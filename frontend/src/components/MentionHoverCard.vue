<template>
  <HoverCard v-model:open="open" side="top" :offset="6" arrow>
    <template #trigger>
      <span
        aria-hidden="true"
        class="pointer-events-none fixed"
        :style="{
          left: `${rect.left}px`,
          top: `${rect.top}px`,
          width: `${rect.width}px`,
          height: `${rect.height}px`,
        }"
      />
    </template>
    <div
      v-if="user"
      class="flex w-64 items-start gap-3 p-3"
      @mouseenter="cancelClose"
      @mouseleave="scheduleClose"
    >
      <UserAvatar :user="user.name" size="xl" />
      <div class="flex min-w-0 flex-col gap-1">
        <div class="truncate text-base-medium text-ink-gray-9">
          {{ user.full_name }}
        </div>
        <div v-if="user.role" class="text-p-sm text-ink-gray-6">
          {{ __(user.role) }}
        </div>
        <div class="truncate text-p-sm text-ink-gray-5">
          {{ user.email || user.name }}
        </div>
      </div>
    </div>
  </HoverCard>
</template>

<script setup>
import UserAvatar from '@/components/UserAvatar.vue'
import { usersStore } from '@/stores/users'
import { HoverCard } from 'frappe-ui'
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'

// one card for every @mention on the page, including mentions inside saved notes and comments
const { getUser } = usersStore()

const open = ref(false)
const userId = ref(null)
const rect = reactive({ left: 0, top: 0, width: 0, height: 0 })
const user = computed(() => (userId.value ? getUser(userId.value) : null))

let openTimer = null
let closeTimer = null

function cancelClose() {
  clearTimeout(closeTimer)
}

function scheduleClose() {
  clearTimeout(openTimer)
  closeTimer = setTimeout(() => (open.value = false), 300)
}

function onMouseOver(e) {
  const mention = e.target.closest?.('.mention[data-id]')
  if (!mention) return
  cancelClose()
  Object.assign(rect, mention.getBoundingClientRect().toJSON())
  userId.value = mention.dataset.id
  clearTimeout(openTimer)
  openTimer = setTimeout(() => (open.value = true), 300)
}

function onMouseOut(e) {
  if (e.target.closest?.('.mention[data-id]')) scheduleClose()
}

onMounted(() => {
  document.addEventListener('mouseover', onMouseOver)
  document.addEventListener('mouseout', onMouseOut)
})

onBeforeUnmount(() => {
  document.removeEventListener('mouseover', onMouseOver)
  document.removeEventListener('mouseout', onMouseOut)
  clearTimeout(openTimer)
  clearTimeout(closeTimer)
})
</script>
