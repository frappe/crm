<template>
  <Select
    class="w-48"
    :model-value="page"
    :options="options"
    @update:model-value="save"
  >
    <template #item-prefix="{ item }">
      <Icon v-if="item.icon" :icon="item.icon" class="size-4 text-ink-gray-7" />
    </template>
  </Select>
</template>

<script setup>
import Icon from '@/components/Icon.vue'
import { viewsStore } from '@/stores/views'
import { sessionStore } from '@/stores/session'
import { getNavigationItems } from '@/utils/navigation'
import {
  getLandingPage,
  landingViews,
  setLandingPageLocally,
} from '@/utils/landingPage'
import { Select, call, toast } from 'frappe-ui'
import { computed, ref } from 'vue'

const { views } = viewsStore()
const { user } = sessionStore()

const page = ref(getLandingPage())

const pages = getNavigationItems()

const options = computed(() => [
  ...pages.map((item) => ({
    label: __(item.label),
    value: item.route,
    icon: item.icon,
  })),
  ...landingViews(views.data, user).map((view) => ({
    label: __(view.label),
    value: view.name,
    icon: view.icon || pages.find((p) => p.route === view.route_name)?.icon,
    description: __(view.route_name),
  })),
])

async function save(value) {
  const previous = page.value
  page.value = value
  try {
    await call('crm.api.home.set_landing_page', { page: value })
    setLandingPageLocally(value)
  } catch (error) {
    page.value = previous
    toast.error(error.messages?.[0] || __('Could not update landing page'))
  }
}
</script>
