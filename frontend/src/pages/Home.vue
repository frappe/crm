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
        <template v-if="!editing">
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
        <template v-else>
          <Dropdown :options="catalogOptions">
            <Button
              :label="__('Widget')"
              iconLeft="lucide-plus"
              :disabled="!availableWidgets.length"
            />
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
      </template>
    </LayoutHeader>

    <div class="flex flex-1 flex-col overflow-y-auto">
      <HomeHeader v-if="target === 'mine'" />
      <DashboardGrid
        v-if="visibleItems.length"
        v-model="visibleItems"
        class="px-2"
        :editing="editing"
        dragHandle=".home-drag-handle"
      >
        <template #item="{ item, remove }">
          <div class="relative h-full w-full">
            <component
              :is="getWidget(item.name).component"
              class="h-full w-full"
              :class="{ 'pointer-events-none select-none': editing }"
              :config="item.config"
              @update:config="(config) => updateConfig(item, config)"
            />
            <template v-if="editing">
              <div
                class="pointer-events-none absolute inset-0 rounded-4 border border-dashed border-outline-gray-4"
              />
              <div class="absolute right-2 top-1.5 flex items-center gap-0.5">
                <Tooltip :text="__('Drag to move')">
                  <span
                    class="home-drag-handle flex size-7 cursor-grab items-center justify-center rounded text-ink-gray-6 hover:bg-surface-gray-2 active:cursor-grabbing"
                    :aria-label="__('Drag to move')"
                  >
                    <span
                      class="lucide-grip-vertical size-4"
                      aria-hidden="true"
                    />
                  </span>
                </Tooltip>
                <Button
                  variant="ghost"
                  icon="lucide-x"
                  :tooltip="__('Remove')"
                  @click="remove"
                />
              </div>
            </template>
          </div>
        </template>
      </DashboardGrid>
      <div
        v-else-if="!loading"
        class="flex flex-1 flex-col items-center justify-center gap-1 p-5 text-center"
      >
        <span class="text-base-medium text-ink-gray-8">
          {{ __('Nothing on Home yet') }}
        </span>
        <span class="text-p-base text-ink-gray-6">
          {{
            availableWidgets.length
              ? __('Add widgets to see what needs you next.')
              : __('Widgets will appear here once they are available.')
          }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import DashboardGrid from '@/components/Dashboard/DashboardGrid.vue'
import HomeHeader from '@/components/Home/HomeHeader.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import { getWidget } from '@/components/Home/widgets'
import { useHomeLayout } from '@/composables/homeLayout'
import { getSettings } from '@/stores/settings'
import { usersStore } from '@/stores/users'
import { Badge, Dropdown, Tooltip, usePageMeta } from 'frappe-ui'
import { computed } from 'vue'

const { brand } = getSettings()
const { isAdmin } = usersStore()

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

const catalogOptions = computed(() =>
  availableWidgets.value.map((widget) => ({
    label: __(widget.label),
    onClick: () => addWidget(widget),
  })),
)

const resetLabel = computed(() =>
  target.value === 'mine' ? __('Reset to default') : __('Reset to built-in'),
)

usePageMeta(() => ({ title: __('Home'), icon: brand.favicon }))
</script>
