<template>
  <div class="inline-flex h-full flex-col border-r w-[220px]">
    <div class="flex p-2">
      <h1 class="text-xl px-3 py-2">Frappe CRM</h1>
    </div>
    <div class="flex-1">
      <nav class="space-y-0.5 px-2">
        <div v-for="link in navigations" :key="link.name">
          <router-link
            custom
            :to="link.route"
            v-slot="{ href, isActive, navigate }"
          >
            <a
              :href="href"
              @click="navigate"
              class="flex items-center rounded px-2 py-1 text-gray-800 transition-all duration-300 ease-in-out"
              :class="[isActive ? 'bg-gray-100 hover:bg-gray-200' : 'hover:bg-gray-50']"
            >
              <div class="flex w-full items-center space-x-2">
                <span class="grid h-5 w-6 place-items-center">
                  <component
                    :is="link.icon"
                    class="h-4.5 w-4.5 text-gray-700"
                  />
                </span>
                <span class="text-base">{{ link.name }}</span>
              </div>
            </a>
          </router-link>
        </div>
      </nav>
    </div>
  </div>
</template>

<script setup>
import LeadsIcon from './Icons/LeadsIcon.vue'
import DealsIcon from './Icons/DealsIcon.vue'
import InboxIcon from './Icons/InboxIcon.vue'
import DashboardIcon from './Icons/DashboardIcon.vue'

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
    name: 'Dashboard',
    icon: DashboardIcon,
    route: { name: 'Dashboard' },
  },
]
</script>
