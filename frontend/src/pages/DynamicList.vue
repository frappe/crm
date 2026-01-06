<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs :routeName="routeName" />
    </template>
    <template #right-header>
      <Button
        variant="solid"
        :label="__('Create')"
        iconLeft="plus"
        @click="showQuickEntryModal = true"
      />
    </template>
  </LayoutHeader>
  <Controls />
  <List />
</template>
<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import Controls from '@/components/Views/List/Controls.vue'
import List from '@/components/Views/List/List.vue'
import { useViews } from '@/stores/view'
import { ref, provide } from 'vue'

const props = defineProps({
  routeName: {
    type: String,
    required: true,
  },
  doctype: {
    type: String,
    required: true,
  },
})

const { currentView } = useViews(props.doctype)

provide('doctype', props.doctype)
provide('currentView', currentView)

const showQuickEntryModal = ref(false)
</script>
