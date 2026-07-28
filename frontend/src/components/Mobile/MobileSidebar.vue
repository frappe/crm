<template>
  <TransitionRoot :show="sidebarOpened">
    <Dialog as="div" class="fixed inset-0" @close="sidebarOpened = false">
      <!-- The panel wrapper below needs w-fit so it stays at the sidebar's
           width. Without it the block div spans the viewport and swallows the
           clicks meant for DialogOverlay, so tapping outside would not close
           the drawer. It also has to be the lone child of TransitionChild,
           which renders as a template and forwards its ref to a single node. -->
      <TransitionChild
        as="template"
        enter="transition ease-in-out duration-200 transform"
        enter-from="-translate-x-full"
        enter-to="translate-x-0"
        leave="transition ease-in-out duration-200 transform"
        leave-from="translate-x-0"
        leave-to="-translate-x-full"
      >
<<<<<<< HEAD
<<<<<<< HEAD
        <div
          class="relative z-10 flex h-full w-[260px] flex-col justify-between border-r bg-surface-gray-1 transition-all duration-300 ease-in-out"
        >
          <div>
            <UserDropdown class="p-2" :isCollapsed="!sidebarOpened" />
          </div>
          <div class="flex-1 overflow-y-auto">
            <div class="mb-3 flex flex-col">
              <SidebarLink
                id="notifications-btn"
                :label="__('Notifications')"
                :icon="NotificationsIcon"
                :to="{ name: 'Notifications' }"
                class="relative mx-2 my-0.5"
              >
                <template #right>
                  <Badge
                    v-if="unreadNotificationsCount"
                    :label="unreadNotificationsCount"
                    variant="subtle"
                  />
                </template>
              </SidebarLink>
            </div>
            <div v-for="view in allViews" :key="view.label">
              <Section
                :label="view.name"
                :hideLabel="view.hideLabel"
                :opened="view.opened"
              >
                <template #header="{ opened, hide, toggle }">
                  <div
                    v-if="!hide"
                    class="ml-2 mt-4 flex h-7 w-auto cursor-pointer gap-1.5 px-1 text-base-medium text-ink-gray-5 opacity-100 transition-all duration-300 ease-in-out"
                    @click="toggle()"
                  >
                    <span
                      class="lucide-chevron-right h-4 text-ink-gray-9 transition-all duration-300 ease-in-out"
                      :class="{ 'rotate-90': opened }"
                      aria-hidden="true"
                    />
                    <span>{{ __(view.name) }}</span>
                  </div>
                </template>
                <nav class="flex flex-col">
                  <SidebarLink
                    v-for="link in view.views"
                    :key="link.label"
                    :icon="link.icon"
                    :label="__(link.label)"
                    :to="link.to"
                    class="mx-2 my-0.5"
                  />
                </nav>
              </Section>
            </div>
          </div>
=======
        <div class="relative z-10 h-full">
=======
        <div class="relative z-10 h-full w-fit">
>>>>>>> 9e1d6ef4 (fix: mobile sidebar not closing due to z index mismatch)
          <AppSidebar mobile />
>>>>>>> 02838e56 (feat: migrate to frappe-ui sidebar)
        </div>
      </TransitionChild>
      <TransitionChild
        as="template"
        enter="transition-opacity ease-linear duration-200"
        enter-from="opacity-0"
        enter-to="opacity-100"
        leave="transition-opacity ease-linear duration-200"
        leave-from="opacity-100"
        leave-to="opacity-0"
      >
        <DialogOverlay class="fixed inset-0 bg-surface-gray-8 bg-opacity-50" />
      </TransitionChild>
    </Dialog>
  </TransitionRoot>
</template>
<script setup>
import {
  TransitionRoot,
  TransitionChild,
  Dialog,
  DialogOverlay,
} from '@headlessui/vue'
<<<<<<< HEAD
import Section from '@/components/CollapsibleSection.vue'
import PinIcon from '@/components/Icons/PinIcon.vue'
import UserDropdown from '@/components/UserDropdown.vue'
import LeadsIcon from '@/components/Icons/LeadsIcon.vue'
import DealsIcon from '@/components/Icons/DealsIcon.vue'
import ContactsIcon from '@/components/Icons/ContactsIcon.vue'
import OrganizationsIcon from '@/components/Icons/OrganizationsIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import NotificationsIcon from '@/components/Icons/NotificationsIcon.vue'
import SidebarLink from '@/components/SidebarLink.vue'
import { viewsStore } from '@/stores/views'
import { unreadNotificationsCount } from '@/stores/notifications'
import { computed, h } from 'vue'
=======
import AppSidebar from '@/components/Layouts/AppSidebar.vue'
>>>>>>> 02838e56 (feat: migrate to frappe-ui sidebar)
import { mobileSidebarOpened as sidebarOpened } from '@/composables/settings'
import { watch } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

// Close on any navigation, which also covers browser back — the sidebar rows
// no longer close the drawer themselves.
watch(
  () => route.fullPath,
  () => (sidebarOpened.value = false),
)
</script>
