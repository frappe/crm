<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :routeName="routeName" :title="doctype" />
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
import Breadcrumbs from '@/components/Views/Breadcrumbs.vue'
import Controls from '@/components/Views/List/Controls.vue'
import List from '@/components/Views/List/List.vue'
import { useView } from '@/stores/view'
import { ref, provide } from 'vue'

const props = defineProps({
  doctype: {
    type: String,
    required: true,
  },
  routeName: {
    type: String,
    required: true,
  },
  viewName: {
    type: String,
    default: null,
  },
})

const { currentView } = useView(props.doctype, props.viewName)

provide('doctype', props.doctype)
provide('viewName', props.viewName)
provide('currentView', currentView)

const showQuickEntryModal = ref(false)
</script>
