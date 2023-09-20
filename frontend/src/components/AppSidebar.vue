<template>
  <div
    class="flex flex-col h-full justify-between transition-all duration-300 ease-in-out"
    :class="isSidebarCollapsed ? 'w-12' : 'w-56'"
  >
    <div>
      <div class="flex p-2">
        <UserDropdown :isCollapsed="isSidebarCollapsed" />
      </div>
      <div v-for="link in links">
        <SidebarLink
          :icon="link.icon"
          :label="link.label"
          :to="link.to"
          :isCollapsed="isSidebarCollapsed"
          class="my-0.5 mx-2"
        />
      </div>
    </div>
    <SidebarLink
      :label="isSidebarCollapsed ? 'Expand' : 'Collapse'"
      :isCollapsed="isSidebarCollapsed"
      @click="isSidebarCollapsed = !isSidebarCollapsed"
      class="m-2"
    >
      <template #icon>
        <span class="grid h-5 w-6 place-items-center flex-shrink-0">
          <component
            :is="CollapseSidebar"
            class="h-4.5 w-4.5 text-gray-700 duration-300 ease-in-out"
            :class="{ '[transform:rotateY(180deg)]': isSidebarCollapsed }"
          />
        </span>
      </template>
    </SidebarLink>
  </div>
</template>

<script setup>
import UserDropdown from '@/components/UserDropdown.vue'
import LeadsIcon from '@/components/Icons/LeadsIcon.vue'
import DealsIcon from '@/components/Icons/DealsIcon.vue'
import ContactsIcon from '@/components/Icons/ContactsIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import DashboardIcon from '@/components/Icons/DashboardIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import CollapseSidebar from '@/components/Icons/CollapseSidebar.vue'
import SidebarLink from '@/components/SidebarLink.vue'
import { ref } from 'vue'

const links = [
  {
    label: 'Leads',
    icon: LeadsIcon,
    to: 'Leads',
  },
  {
    label: 'Deals',
    icon: DealsIcon,
    to: 'Deals',
  },
  {
    label: 'Contacts',
    icon: ContactsIcon,
    to: 'Contacts',
  },
  {
    label: 'Notes',
    icon: NoteIcon,
    to: 'Notes',
  },
  {
    label: 'Call Logs',
    icon: PhoneIcon,
    to: 'Call Logs',
  },
  // {
  //   label: 'Dashboard',
  //   icon: DashboardIcon,
  //   to: 'Dashboard',
  // },
]

const navigations = [
  {
    name: 'Leads',
    icon: LeadsIcon,
    route: { name: 'Leads' },
  },
  {
    name: 'Deals',
    icon: DealsIcon,
    route: { name: 'Deals' },
  },
  {
    name: 'Contacts',
    icon: ContactsIcon,
    route: { name: 'Contacts' },
  },
  {
    name: 'Notes',
    icon: NoteIcon,
    route: { name: 'Notes' },
  },
  {
    name: 'Call Logs',
    icon: PhoneIcon,
    route: { name: 'Call Logs' },
  },
  // {
  //   name: 'Dashboard',
  //   icon: DashboardIcon,
  //   route: { name: 'Dashboard' },
  // },
]

const isSidebarCollapsed = ref(false)
</script>
