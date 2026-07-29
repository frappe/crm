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
        <div class="relative z-10 h-full w-fit">
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

// Covers navigation the sidebar does not originate, such as browser back or a
// redirect. Rows close the drawer themselves on click, since re-selecting the
// current route leaves fullPath unchanged and would not trigger this.
watch(
  () => route.fullPath,
  () => (sidebarOpened.value = false),
)
</script>
