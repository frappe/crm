<template>
  <div class="flex p-2">
    <UserDropdown />
  </div>
  <div class="flex-1">
    <nav class="space-y-0.5 px-2">
      <NavLinks
        :links="navigations"
        class="flex items-center rounded px-2 py-1 text-gray-800 transition-all duration-300 ease-in-out"
        active="bg-gray-100 hover:bg-gray-200"
        inactive="hover:bg-gray-50"
      >
        <template v-slot="{ link }">
          <div class="flex w-full items-center space-x-2">
            <span class="grid h-5 w-6 place-items-center">
              <component :is="link.icon" class="h-4.5 w-4.5 text-gray-700" />
            </span>
            <span class="text-base">{{ link.name }}</span>
          </div>
        </template>
      </NavLinks>
    </nav>
  </div>
</template>

<script setup>
import UserDropdown from './UserDropdown.vue'
import LeadsIcon from './Icons/LeadsIcon.vue'
import DealsIcon from './Icons/DealsIcon.vue'
import ContactsIcon from './Icons/ContactsIcon.vue'
import InboxIcon from './Icons/InboxIcon.vue'
import DashboardIcon from './Icons/DashboardIcon.vue'
import NavLinks from './NavLinks.vue'

const navigations = [
  {
    name: 'Inbox',
    icon: InboxIcon,
    route: { name: 'Inbox' },
  },
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
    name: 'Dashboard',
    icon: DashboardIcon,
    route: { name: 'Dashboard' },
  },
]
</script>
