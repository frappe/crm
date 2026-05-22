<template>
  <div
    v-if="!isSidebarCollapsed && showBanner"
    class="flex flex-col gap-3 shadow-sm rounded-lg py-2.5 px-3 bg-surface-modal text-base"
  >
    <div class="flex items-start justify-between gap-2">
      <div class="inline-flex text-ink-gray-9 gap-2 items-center font-medium">
        <FeatherIcon class="h-4" name="info" />
        {{ __('Permissions update') }}
      </div>
      <button
        class="text-ink-gray-7 hover:text-ink-gray-8"
        :aria-label="__('Dismiss')"
        @click="dismiss"
      >
        <FeatherIcon class="h-3.5" name="x" />
      </button>
    </div>
    <div class="text-ink-gray-7 text-p-sm">
      {{ __('We are changing how permissions work in Frappe CRM') }}
    </div>
    <Button :label="__('Learn more')" @click="openBlog">
      <template #suffix>
        <FeatherIcon class="h-3.5" name="external-link" />
      </template>
    </Button>
  </div>
  <Button v-else-if="isSidebarCollapsed && showBanner" @click="openBlog">
    <FeatherIcon class="h-4 my-0.5 shrink-0" name="info" />
  </Button>
</template>

<script setup>
import { Button, FeatherIcon } from 'frappe-ui'
import { useStorage } from '@vueuse/core'
import { computed } from 'vue'
import { usersStore } from '@/stores/users'

defineProps({
  isSidebarCollapsed: {
    type: Boolean,
    default: false,
  },
})

const BLOG_URL =
  'https://frappe.io/blog/frappe-crm/understanding-permissions-in-frappe-crm'

const { isManager } = usersStore()
const dismissed = useStorage('salesHierarchyBannerDismissed', false)

const showBanner = computed(() => !dismissed.value && isManager())

function dismiss() {
  dismissed.value = true
}

function openBlog() {
  if (!BLOG_URL) return
  window.open(BLOG_URL, '_blank', 'noopener')
}
</script>
