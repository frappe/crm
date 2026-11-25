<template>
  <!-- Built from Home's own parts and data, so the preview is the page setup opens. -->
  <div class="flex h-full flex-col">
    <header
      class="flex h-[42px] shrink-0 items-center justify-between border-b border-outline-gray-1 px-5"
    >
      <span class="text-lg text-ink-gray-9">{{ __('Home') }}</span>
      <div class="flex items-center gap-2">
        <Button :label="__('Edit')" icon-left="lucide-pen-line" tabindex="-1" />
        <Button v-if="isAdmin()" icon="lucide-more-horizontal" tabindex="-1" />
      </div>
    </header>

    <div class="flex flex-1 flex-col overflow-hidden">
      <div
        class="mx-auto flex w-full max-w-[1120px] flex-1 flex-col gap-10 px-6 pb-12 pt-9"
      >
        <HomeHeader
          :count="brief?.total"
          :team="brief?.tab === 'team'"
          :flow="askFlow.data?.available"
        />
        <AskFlow :resource="askFlow" :team="isManager()" />
        <Brief
          :tab="briefTab"
          :brief="brief"
          :counts="briefCounts"
          @update:tab="setBriefTab"
          @update:doctype="setBriefDoctype"
        />
        <DashboardGrid
          v-if="visibleItems.length"
          v-model="visibleItems"
          class="-mx-2 !flex-none !overflow-visible !p-0"
          :editing="false"
        >
          <template #item="{ item }">
            <div class="h-full w-full rounded-4">
              <component
                :is="getWidget(item.name).component"
                class="h-full w-full"
                :config="item.config"
              />
            </div>
          </template>
        </DashboardGrid>
      </div>
    </div>
  </div>
</template>

<script setup>
import DashboardGrid from '@/components/Dashboard/DashboardGrid.vue'
import AskFlow from '@/components/Home/AskFlow.vue'
import Brief from '@/components/Home/Brief.vue'
import HomeHeader from '@/components/Home/HomeHeader.vue'
import { getWidget } from '@/components/Home/widgets'
import { useAskFlow, useBrief } from '@/composables/homeWidget'
import { useHomeLayout } from '@/composables/homeLayout'
import { usersStore } from '@/stores/users'
import { Button } from 'frappe-ui'

const { isAdmin, isManager } = usersStore()

const { visibleItems, load } = useHomeLayout()
load()

const {
  tab: briefTab,
  brief,
  counts: briefCounts,
  setTab: setBriefTab,
  setDoctype: setBriefDoctype,
} = useBrief()

const askFlow = useAskFlow()
</script>
