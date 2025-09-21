<template>
  <Popover
    placement="right-start"
    trigger="hover"
    :hoverDelay="0.1"
    :leaveDelay="0.1"
  >
    <template #target="{ togglePopover }">
      <button
        :class="[
          active ? 'bg-surface-gray-3' : 'text-ink-gray-6',
          'group w-full flex h-7 items-center justify-between rounded px-2 text-base hover:bg-surface-gray-2',
        ]"
        @click.prevent="togglePopover()"
      >
        <div class="flex gap-2">
          <AppsIcon class="size-4" />
          <span class="whitespace-nowrap">
            {{ __('Apps') }}
          </span>
        </div>
        <FeatherIcon name="chevron-right" class="size-4 text-ink-gray-5" />
      </button>
    </template>
    <template #body>
      <div
        class="flex w-fit mx-2 min-w-32 max-w-48 flex-col rounded-lg border border-outline-gray-2 bg-surface-white p-1.5 text-sm text-ink-gray-8 shadow-xl auto-fill-[100px]"
      >
        <a
          :href="app.route"
          v-for="app in apps.data"
          key="name"
          class="flex items-center gap-2 rounded p-1.5 hover:bg-surface-gray-2"
        >
          <img class="size-6" :src="app.logo" />
          <span class="max-w-18 w-full truncate">
            {{ app.title }}
          </span>
        </a>
      </div>
    </template>
  </Popover>
</template>
<script setup>
import AppsIcon from '@/components/Icons/AppsIcon.vue'
import { Popover, createResource } from 'frappe-ui'
import { onUnmounted } from 'vue'
import { stopRecording } from '@/telemetry'

const props = defineProps({
  active: Boolean,
})

const apps = createResource({
  url: 'frappe.apps.get_apps',
  cache: 'apps',
  auto: true,
  transform: (data) => {
    let _apps = [
      {
        name: 'frappe',
        logo: '/assets/frappe/images/framework.png',
        title: __('Desk'),
        route: '/app',
      },
    ]
    data.map((app) => {
      if (app.name === 'crm') return
      _apps.push({
        name: app.name,
        logo: app.logo,
        title: __(app.title),
        route: app.route,
      })
    })

    return _apps
  },
})

onUnmounted(() => {
  stopRecording()
})
</script>
