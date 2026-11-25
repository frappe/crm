<template>
  <Dialog
    v-model:open="showChangelogDialog"
    :title="__('What\'s new')"
    size="2xl"
  >
    <ChangelogReleases />
  </Dialog>
</template>

<script setup>
import { Dialog } from 'frappe-ui'
import { defineAsyncComponent, onMounted } from 'vue'
import { sessionStore } from '@/stores/session'
import { showChangelogDialog, openChangelogIfReleased } from '@/data/changelog'

const ChangelogReleases = defineAsyncComponent(
  () => import('./ChangelogReleases.vue'),
)

const { user } = sessionStore()

onMounted(() => openChangelogIfReleased(user))
</script>
