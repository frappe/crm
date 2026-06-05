<template>
  <Section title="Cargo & Logistics">
    <div class="space-y-6">
      <Field label="Cargo" :value="doc.cargo1" />
      <Field label="Loading" :value="doc.loading" multiline />
      <Field label="Unloading" :value="doc.unloading" multiline />
    </div>
  </Section>
</template>

<script setup>
import { computed } from 'vue'
import Section from './shared/Section.vue'
import Field from './shared/Field.vue'

const props = defineProps(['quotation'])
const doc = computed(() => props.quotation.doc)
</script>