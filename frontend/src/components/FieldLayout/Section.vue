<template>
  <div
    v-if="!section.hidden"
    class="section"
    :class="[
      section.hideBorder
        ? 'pt-4'
        : 'border-t border-outline-gray-modals mt-5 pt-5',
    ]"
  >
    <Section
      class="flex sm:flex-row flex-col gap-4 text-lg font-medium"
      :class="{ 'px-3 sm:px-5': hasTabs }"
      :labelClass="['text-lg font-medium', { 'px-3 sm:px-5': hasTabs }]"
      :label="section.label"
      :hideLabel="section.hideLabel || !section.label"
      :opened="section.opened"
      :collapsible="section.collapsible"
      collapseIconPosition="right"
    >
      <template v-for="column in section.columns" :key="column.name">
        <Column
          :class="{ 'mt-6': section.label && !section.hideLabel }"
          :column="column"
          :data-name="column.name"
        />
      </template>
    </Section>
  </div>
</template>
<script setup>
import Section from '@/components/Section.vue'
import Column from '@/components/FieldLayout/Column.vue'
import { inject } from 'vue'

const props = defineProps({
  section: Object,
})

const hasTabs = inject('hasTabs')
</script>
