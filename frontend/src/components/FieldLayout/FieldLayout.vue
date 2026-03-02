<template>
  <div
    class="flex flex-col"
    :class="{
      'border border-outline-gray-1 rounded-lg': hasTabs,
      'border-outline-gray-modals': hasTabs,
    }"
  >
    <Tabs
      v-model="tabIndex"
      as="div"
      :tabs="tabs"
      :class="[
        !hasTabs ? `[&_[role='tablist']]:hidden` : '',
        `[&_[role='tabpanel']]:overflow-visible !overflow-visible`,
      ]"
    >
      <template #tab-panel="{ tab }">
        <div class="sections" :class="{ 'my-4 sm:my-5': hasTabs }">
          <template v-for="section in tab.sections" :key="section.name">
            <Section :section="section" :data-name="section.name" />
          </template>
        </div>
      </template>
    </Tabs>
  </div>
</template>

<script setup>
import Section from '@/components/FieldLayout/Section.vue'
import { Tabs } from 'frappe-ui'
import { ref, computed, provide } from 'vue'

const props = defineProps({
  tabs: { type: Array, default: () => [] },
  data: { type: Object, default: () => ({}) },
  doctype: { type: String, default: 'CRM Lead' },
  isGridRow: { type: Boolean, default: false },
  preview: { type: Boolean, default: false },
})

const tabIndex = ref(0)

const hasTabs = computed(() => {
  return (
    props.tabs.length > 1 || (props.tabs.length == 1 && props.tabs[0].label)
  )
})

provide(
  'data',
  computed(() => props.data),
)
provide('hasTabs', hasTabs)
provide('doctype', props.doctype)
provide('preview', props.preview)
provide('isGridRow', props.isGridRow)
</script>
<style scoped>
.section:not(:has(.field)) {
  display: none;
}

.section:has(.field):nth-child(1 of .section:has(.field)) {
  border-top: none;
  margin-top: 0;
  padding-top: 0;
}
</style>
