<template>
  <div
    class="preview-window absolute flex overflow-hidden rounded-5 border border-outline-gray-2 bg-surface-base shadow-2xl"
    :style="frame"
  >
    <div v-if="sidebar" class="flex h-full bg-surface-gray-1">
      <Sidebar
        :collapsible="false"
        width="184px"
        class="border-r border-outline-gray-1"
      >
        <div class="flex h-full flex-col p-2">
          <SidebarHeader
            :title="__('Your workspace')"
            subtitle="Frappe CRM"
            :logo="CRMLogo"
          />
          <div class="mt-2 flex flex-col gap-1">
            <SidebarItem
              v-for="item in NAV"
              :key="item.label"
              :label="item.label"
              :icon="item.icon"
              :active="item.label === active"
            />
          </div>
        </div>
      </Sidebar>
    </div>
    <div class="flex min-w-0 flex-1 flex-col">
      <slot />
    </div>
  </div>
</template>

<script setup>
import CRMLogo from '@/components/Icons/CRMLogo.vue'
import LeadsIcon from '@/components/Icons/LeadsIcon.vue'
import DealsIcon from '@/components/Icons/DealsIcon.vue'
import ContactsIcon from '@/components/Icons/ContactsIcon.vue'
import OrganizationsIcon from '@/components/Icons/OrganizationsIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import { Sidebar, SidebarHeader, SidebarItem } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  sidebar: { type: Boolean, default: true },
  active: { type: String, default: '' },
  top: { type: Number, default: 72 },
})

const SCALE = 0.86
const INSET = 32

const NAV = [
  { label: __('Leads'), icon: LeadsIcon },
  { label: __('Deals'), icon: DealsIcon },
  { label: __('Contacts'), icon: ContactsIcon },
  { label: __('Organizations'), icon: OrganizationsIcon },
  { label: __('Notes'), icon: NoteIcon },
  { label: __('Tasks'), icon: TaskIcon },
  { label: __('Call Logs'), icon: PhoneIcon },
]

const frame = computed(() => ({
  left: `${INSET}px`,
  top: `${props.top}px`,
  width: `calc((100% - ${INSET * 2}px) / ${SCALE})`,
  height: `calc((100% - ${props.top + INSET}px) / ${SCALE})`,
}))
</script>

<style scoped>
.preview-window {
  transform: scale(0.86);
  transform-origin: top left;
}
</style>
