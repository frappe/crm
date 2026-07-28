<template>
  <TransitionRoot :show="sidebarOpened">
    <Dialog as="div" class="fixed inset-0" @close="sidebarOpened = false">
      <TransitionChild
        as="template"
        enter="transition ease-in-out duration-200 transform"
        enter-from="-translate-x-full"
        enter-to="translate-x-0"
        leave="transition ease-in-out duration-200 transform"
        leave-from="translate-x-0"
        leave-to="-translate-x-full"
      >
        <div class="relative z-10 h-full">
          <AppSidebar mobile />
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
import AppSidebar from '@/components/Layouts/AppSidebar.vue'
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
