<template>
  <div class="flex flex-col h-full justify-between">
    <div>
      <div class="flex p-2">
        <UserDropdown />
      </div>
      <div class="flex-1">
        <nav class="space-y-0.5 px-2">
          <NavLinks
            :links="navigations"
            class="flex items-center rounded px-2 py-1 text-gray-800 transition-all duration-300 ease-in-out"
            active="bg-white shadow-sm"
            inactive="hover:bg-gray-100"
          >
            <template v-slot="{ link }">
              <div class="flex w-full items-center space-x-2">
                <span class="grid h-5 w-6 place-items-center">
                  <component
                    :is="link.icon"
                    class="h-4.5 w-4.5 text-gray-700"
                  />
                </span>
                <span class="text-base">{{ link.name }}</span>
              </div>
            </template>
          </NavLinks>
        </nav>
      </div>
    </div>
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
import NavLinks from '@/components/NavLinks.vue'

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
  {
    name: 'Dashboard',
    icon: DashboardIcon,
    route: { name: 'Dashboard' },
  },
]
</script>
