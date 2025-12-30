<template>
  <div>
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
  </div>
</template>
<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import { ref } from 'vue'

const props = defineProps({
  routeName: {
    type: String,
    required: true,
  },
})

const viewControls = ref(null)
const showQuickEntryModal = ref(false)
</script>
