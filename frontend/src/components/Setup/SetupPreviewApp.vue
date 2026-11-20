<template>
  <div class="flex h-full bg-surface-base">
    <Sidebar width="14rem" class="shrink-0 border-r border-outline-gray-1">
      <div class="flex h-full flex-col p-2">
        <div class="flex h-12 items-center gap-2 px-2">
          <BrandLogo :model-value="brand" class="size-8 shrink-0" />
          <div class="flex min-w-0 flex-1 flex-col">
            <span class="truncate text-base font-medium text-ink-gray-9">
              {{ brand.name || __('CRM') }}
            </span>
            <span class="mt-1 truncate text-sm text-ink-gray-7">
              {{ user.full_name }}
            </span>
          </div>
          <span class="lucide-chevron-down size-4 text-ink-gray-5" />
        </div>
        <nav class="mt-2 flex flex-col gap-1">
          <SidebarItem :label="__('Search')">
            <template #prefix>
              <span class="lucide-search size-4 text-ink-gray-7" />
            </template>
          </SidebarItem>
          <SidebarItem :label="__('Notifications')">
            <template #prefix>
              <span class="lucide-bell size-4 text-ink-gray-7" />
            </template>
          </SidebarItem>
          <SidebarItem
            v-for="(item, i) in NAV"
            :key="item.label"
            :label="__(item.label)"
            :active="item.label === 'Leads'"
            :class="i === 0 && 'mt-4'"
          >
            <template #prefix>
              <component :is="item.icon" class="size-4 text-ink-gray-7" />
            </template>
          </SidebarItem>
        </nav>
      </div>
    </Sidebar>

    <div class="relative flex min-w-0 flex-1 flex-col overflow-hidden">
      <Transition v-bind="slide">
        <SetupPreviewLeads v-if="page === 'leads'" key="leads" :state />
        <SetupPreviewLead v-else key="lead" :state />
      </Transition>
    </div>
  </div>
</template>

<script setup>
import BrandLogo from '@/components/BrandLogo.vue'
import SetupPreviewLead from '@/components/Setup/SetupPreviewLead.vue'
import SetupPreviewLeads from '@/components/Setup/SetupPreviewLeads.vue'
import { getSettings } from '@/stores/settings'
import { usersStore } from '@/stores/users'
import { navigationItems } from '@/utils/navigation'
import { Sidebar, SidebarItem } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  page: { type: String, required: true },
  state: { type: Object, required: true },
})

const { brand } = getSettings()
const { getUser } = usersStore()
const user = computed(() => getUser() || {})

const NAV = navigationItems.filter((item) => item.label !== 'Call Logs')

const slide = computed(() => ({
  enterActiveClass:
    'transition duration-500 delay-100 ease-[cubic-bezier(.22,1,.36,1)] motion-reduce:transition-none',
  enterFromClass:
    props.page === 'leads'
      ? 'opacity-0 -translate-x-6'
      : 'opacity-0 translate-x-6',
  leaveActiveClass:
    'absolute inset-0 transition duration-150 ease-in motion-reduce:transition-none',
  leaveToClass: 'opacity-0',
}))
</script>
