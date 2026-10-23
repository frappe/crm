<template>
  <div class="flex h-full flex-col overflow-hidden">
    <LayoutHeader>
      <template #left-header>
        <ViewBreadcrumbs routeName="Home" />
      </template>
      <template #right-header>
        <template v-if="!editing">
          <Button
            :label="__('Edit')"
            iconLeft="lucide-pen-line"
            @click="edit()"
          />
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
            :label="__('Reset to default')"
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
      <HomeHeader />
      <DashboardGrid
        v-if="visibleItems.length"
        v-model="visibleItems"
        class="px-2"
        :editing="editing"
      >
        <template #item="{ item }">
          <component
            :is="getWidget(item.name).component"
            class="h-full w-full"
            :config="item.config"
            @update:config="(config) => updateConfig(item, config)"
          />
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
import { Dropdown, usePageMeta } from 'frappe-ui'
import { computed } from 'vue'

const { brand } = getSettings()

const {
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

const catalogOptions = computed(() =>
  availableWidgets.value.map((widget) => ({
    label: __(widget.label),
    onClick: () => addWidget(widget),
  })),
)

usePageMeta(() => ({ title: __('Home'), icon: brand.favicon }))
</script>
