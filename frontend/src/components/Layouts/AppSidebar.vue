<template>
  <div
    class="flex h-full flex-col justify-between transition-all duration-300 ease-in-out"
    :class="isSidebarCollapsed ? 'w-12' : 'w-56'"
  >
    <div class="flex flex-1 flex-col overflow-hidden">
      <UserDropdown class="p-2" :isCollapsed="isSidebarCollapsed" />
      <div class="flex flex-col overflow-y-auto">
        <SidebarLink
          v-for="link in links"
          :icon="link.icon"
          :label="link.label"
          :to="link.to"
          :isCollapsed="isSidebarCollapsed"
          class="mx-2 my-0.5"
        />
      </div>
      <div
        v-if="isSidebarCollapsed && getPublicViews().length"
        class="mx-2 my-2 h-1 border-b"
      />
      <div
        v-if="getPublicViews().length"
        class="px-3 text-base text-gray-600 transition-all duration-300 ease-in-out"
        :class="
          isSidebarCollapsed
            ? 'ml-0 h-0 overflow-hidden opacity-0'
            : 'ml-2 h-7 w-auto opacity-100 mt-4'
        "
      >
        Public Views
      </div>
      <div v-if="getPublicViews().length" class="flex flex-col overflow-y-auto">
        <SidebarLink
          v-for="publicView in getPublicViews()"
          :icon="
            h(getIcon(publicView.route_name), {
              class: 'h-4.5 w-4.5 text-gray-700',
            })
          "
          :label="publicView.label"
          :to="{
            name: publicView.route_name,
            query: { view: publicView.name },
          }"
          :isCollapsed="isSidebarCollapsed"
          class="mx-2 my-0.5"
        />
      </div>
      <div
        v-if="isSidebarCollapsed && getPinnedViews().length"
        class="mx-2 my-2 h-1 border-b"
      />
      <div
        v-if="getPinnedViews().length"
        class="px-3 text-base text-gray-600 transition-all duration-300 ease-in-out"
        :class="
          isSidebarCollapsed
            ? 'ml-0 h-0 overflow-hidden opacity-0'
            : 'ml-2 h-7 w-auto opacity-100 mt-4'
        "
      >
        Pinned Views
      </div>
      <div v-if="getPinnedViews().length" class="flex flex-col overflow-y-auto">
        <SidebarLink
          v-for="pinnedView in getPinnedViews()"
          :icon="
            h(getIcon(pinnedView.route_name), {
              class: 'h-4.5 w-4.5 text-gray-700',
            })
          "
          :label="pinnedView.label"
          :to="{
            name: pinnedView.route_name,
            query: { view: pinnedView.name },
          }"
          :isCollapsed="isSidebarCollapsed"
          class="mx-2 my-0.5"
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
        <span class="grid h-5 w-6 flex-shrink-0 place-items-center">
          <CollapseSidebar
            class="h-4.5 w-4.5 text-gray-700 duration-300 ease-in-out"
            :class="{ '[transform:rotateY(180deg)]': isSidebarCollapsed }"
          />
        </span>
      </template>
    </SidebarLink>
  </div>
</template>

<script setup>
import EmailIcon from '@/components/Icons/EmailIcon.vue'
import PinIcon from '@/components/Icons/PinIcon.vue'
import UserDropdown from '@/components/UserDropdown.vue'
import LeadsIcon from '@/components/Icons/LeadsIcon.vue'
import DealsIcon from '@/components/Icons/DealsIcon.vue'
import ContactsIcon from '@/components/Icons/ContactsIcon.vue'
import OrganizationsIcon from '@/components/Icons/OrganizationsIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import CollapseSidebar from '@/components/Icons/CollapseSidebar.vue'
import SidebarLink from '@/components/SidebarLink.vue'
import { viewsStore } from '@/stores/views'
import { useStorage } from '@vueuse/core'
import { h } from 'vue'

const { getPinnedViews, getPublicViews } = viewsStore()

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
    label: 'Organizations',
    icon: OrganizationsIcon,
    to: 'Organizations',
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
  {
    label: 'Email Templates',
    icon: EmailIcon,
    to: 'Email Templates',
  },
]

function getIcon(routeName) {
  switch (routeName) {
    case 'Leads':
      return LeadsIcon
    case 'Deals':
      return DealsIcon
    case 'Contacts':
      return ContactsIcon
    case 'Organizations':
      return OrganizationsIcon
    case 'Notes':
      return NoteIcon
    case 'Call Logs':
      return PhoneIcon
    default:
      return PinIcon
  }
}

const isSidebarCollapsed = useStorage('sidebar_is_collapsed', false)
</script>
