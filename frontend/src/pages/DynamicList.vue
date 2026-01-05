<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs v-model="controls" :routeName="routeName" />
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
  <Controls ref="controls" />
</template>
<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import Controls from '@/components/Views/List/Controls.vue'
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

provide('doctype', props.doctype)

const controls = ref(null)
const showQuickEntryModal = ref(false)
</script>
