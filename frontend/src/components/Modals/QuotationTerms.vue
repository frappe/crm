<template>
  <div class="space-y-6">
    <Section title="Terms & Conditions">
      <div class="space-y-4">
        <Field label="Title" :value="doc.term_title" />
        <Field label="Validity" :value="doc.validity" />
        <Field label="Payment Term" :value="doc.payterm" />
        <div>
          <label class="text-xs font-medium uppercase tracking-wide text-ink-gray-5">Detail</label>
          <div
            class="mt-2 rounded-lg border border-outline-gray-2 bg-surface-gray-1 p-4 text-sm text-ink-gray-9"
            v-html="doc.term_detail || '<em class=\'text-ink-gray-5\'>No detail</em>'"
          ></div>
        </div>
      </div>
    </Section>

    <Section title="Rate Notes">
      <div class="space-y-4">
        <Field label="Rate Include" :value="doc.rate_include" multiline />
        <Field label="Rate Exclude" :value="doc.rate_exclude" multiline />
        <Field label="Remark" :value="doc.remark" multiline />
      </div>
    </Section>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import Section from './shared/Section.vue'
import Field from './shared/Field.vue'

const props = defineProps(['quotation'])
const doc = computed(() => props.quotation.doc)
</script>