<template>
  <RouterLink
    :to="route"
    class="flex cursor-pointer items-center gap-3 px-4 py-2.5 hover:bg-surface-gray-2"
  >
    <NotificationIcon :notification="n" />
    <div class="min-w-0 flex-1">
      <div class="flex items-center gap-2">
        <span
          class="truncate"
          :class="
            group.unread ? 'font-medium text-ink-gray-9' : 'text-ink-gray-7'
          "
        >
          {{ n.title || n.from_user.full_name }}
        </span>
        <span v-if="group.count > 1" class="shrink-0 text-sm text-ink-gray-5">
          {{ group.count }}
        </span>
        <span class="ml-auto shrink-0 text-sm text-ink-gray-5">
          {{ prettyDate(n.creation, true) }}
        </span>
      </div>
      <div class="mt-0.5 flex items-center gap-2">
        <div class="truncate text-sm text-ink-gray-5">
          <span v-if="n.sender" class="text-ink-gray-7">{{ n.sender }}:</span>
          {{ n.preview }}
        </div>
        <div
          class="ml-auto size-1.5 shrink-0 rounded-full"
          :class="group.unread ? 'bg-surface-blue-6' : 'bg-transparent'"
        />
      </div>
    </div>
  </RouterLink>
</template>
<script setup lang="ts">
import NotificationIcon from '@/components/NotificationIcon.vue'
import { prettyDate } from '@/utils'
import type { NotificationGroup } from '@/utils/notifications'
import { computed } from 'vue'

const props = defineProps<{ group: NotificationGroup }>()

const n = computed(() => props.group.latest)

const route = computed(() => ({
  name: n.value.route_name,
  params:
    n.value.route_name === 'Deal'
      ? { dealId: n.value.reference_name }
      : { leadId: n.value.reference_name },
  hash: n.value.hash,
}))
</script>
