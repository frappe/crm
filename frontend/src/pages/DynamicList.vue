<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs v-model="viewControls" :routeName="routeName" />
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
  <Controls v-model="list" :doctype="doctype" />
</template>
<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import Controls from '@/components/Views/List/Controls.vue'
import { ref } from 'vue'

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

const list = ref({})
const viewControls = ref(null)
const showQuickEntryModal = ref(false)
</script>
