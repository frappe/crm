<template>
  <div class="flex h-full flex-col overflow-hidden">
    <LayoutHeader>
      <template #left-header>
        <ViewBreadcrumbs routeName="Home" />
        <Badge
          v-if="target !== 'mine'"
          :label="defaultLabels[target]"
          theme="orange"
          variant="subtle"
        />
      </template>
      <template #right-header>
        <template v-if="editing">
          <Dropdown
            v-if="widgetOptions.length"
            align="end"
            :options="widgetOptions"
          >
            <Button :label="__('Widget')" iconLeft="lucide-plus" />
          </Dropdown>
          <Button
            :label="resetLabel"
            iconLeft="lucide-undo-2"
            @click="reset()"
          />
          <Button :label="__('Cancel')" @click="cancel()" />
          <Button
            variant="solid"
            :label="__('Save')"
            :disabled="!dirty"
            @click="save()"
          />
        </template>
        <template v-else>
          <Button
            :label="__('Edit')"
            iconLeft="lucide-pen-line"
            @click="edit()"
          />
          <Dropdown v-if="isAdmin()" :options="defaultOptions">
            <Button
              icon="lucide-more-horizontal"
              :tooltip="__('Role defaults')"
            />
          </Dropdown>
        </template>
      </template>
    </LayoutHeader>

    <div class="flex flex-1 flex-col overflow-y-auto">
      <div
        class="mx-auto flex w-full max-w-[1120px] flex-1 flex-col gap-8 px-6 pb-12 pt-9"
      >
        <template v-if="target === 'mine'">
          <HomeHeader
            :count="brief.data?.total"
            :team="brief.data?.tab === 'team'"
            :flow="askFlow.data?.available"
          />
          <AskFlow :resource="askFlow" :team="isManager()" />
          <Brief v-model:tab="briefTab" :resource="brief" />
        </template>
        <DashboardGrid
          v-if="visibleItems.length"
          v-model="visibleItems"
          class="-mx-2 !flex-none !overflow-visible !p-0"
          :editing="editing"
          @layout-updated="showAddedWidget"
        >
          <template #item="{ item }">
            <div class="h-full w-full rounded-4" :data-home-widget="item.name">
              <component
                :is="getWidget(item.name).component"
                class="h-full w-full"
                :config="item.config"
                @update:config="(config) => updateConfig(item, config)"
              />
            </div>
          </template>
        </DashboardGrid>
        <HomeEmptyState
          v-else-if="!loading"
          class="flex-1 p-5"
          icon="lucide-layout-dashboard"
          :title="__('Nothing on Home yet')"
          :text="
            availableWidgets.length
              ? __('Add widgets to see what needs you next.')
              : __('Widgets will appear here once they are available.')
          "
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import DashboardGrid from '@/components/Dashboard/DashboardGrid.vue'
import AskFlow from '@/components/Home/AskFlow.vue'
import Brief from '@/components/Home/Brief.vue'
import HomeEmptyState from '@/components/Home/HomeEmptyState.vue'
import HomeHeader from '@/components/Home/HomeHeader.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import { getWidget } from '@/components/Home/widgets'
import { useBrief } from '@/composables/homeWidget'
import { useHomeLayout } from '@/composables/homeLayout'
import { getSettings } from '@/stores/settings'
import { usersStore } from '@/stores/users'
import { Badge, Dropdown, createResource, usePageMeta } from 'frappe-ui'
import { computed, nextTick, provide, ref } from 'vue'

const { brand } = getSettings()
const { isAdmin, isManager } = usersStore()

const {
  target,
  loading,
  editing,
  dirty,
  visibleItems,
  availableWidgets,
  load,
  edit,
  cancel,
  save,
  reset,
  addWidget,
  updateConfig,
} = useHomeLayout()

load()

provide('homeEditing', editing)

const { tab: briefTab, resource: brief } = useBrief()

const askFlow = createResource({ url: 'crm.api.home.get_ask_flow', auto: true })

const defaultLabels = {
  agent: __('Agent default'),
  manager: __('Manager default'),
}

const defaultOptions = [
  {
    label: __('Edit agent default'),
    icon: 'lucide-user',
    onClick: () => edit('agent'),
  },
  {
    label: __('Edit manager default'),
    icon: 'lucide-users',
    onClick: () => edit('manager'),
  },
]

const resetLabel = computed(() =>
  target.value === 'mine' ? __('Reset to default') : __('Reset to built-in'),
)

const widgetOptions = computed(() =>
  availableWidgets.value.map((widget) => ({
    label: __(widget.label),
    icon: widget.icon,
    onClick: () => addAndShow(widget),
  })),
)

// The grid places a new widget a moment after it is added; scrolling earlier lands at the top.
const addedWidget = ref(null)

function addAndShow(widget) {
  addedWidget.value = widget.key
  addWidget(widget)
}

async function showAddedWidget() {
  if (!addedWidget.value) return
  const key = addedWidget.value
  addedWidget.value = null
  await nextTick()
  document
    .querySelector(`[data-home-widget="${key}"]`)
    ?.scrollIntoView({ behavior: 'smooth', block: 'center' })
}

usePageMeta(() => ({ title: __('Home'), icon: brand.favicon }))
</script>
