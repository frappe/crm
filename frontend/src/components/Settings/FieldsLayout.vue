<template>
  <div ref="parentRef" class="flex h-full">
    <div class="flex-1 p-8">
      <FormControl
        type="select"
        v-model="doctype"
        :label="__('DocType')"
        :options="['CRM Lead', 'CRM Deal']"
      />
    </div>
    <Resizer
      class="flex flex-col justify-between border-l"
      :parent="parentRef"
      side="right"
    >
      <div
        v-if="sections.data"
        class="flex flex-1 flex-col justify-between overflow-hidden"
      >
        <div class="flex flex-col overflow-y-auto">
          <div
            v-for="(section, i) in sections.data"
            :key="section.label"
            class="flex flex-col p-3"
            :class="{ 'border-b': i !== sections.data - 1 }"
          >
            <Section :is-opened="section.opened" :label="section.label">
              <div v-for="field in section.fields" class="p-3">
                {{ field.label }}
              </div>
            </Section>
          </div>
        </div>
      </div>
    </Resizer>
  </div>
</template>
<script setup>
import Resizer from '@/components/Resizer.vue'
import Section from '@/components/Section.vue'
import { createResource } from 'frappe-ui'
import { ref, watch } from 'vue'

const parentRef = ref(null)
const doctype = ref('CRM Lead')

const sections = createResource({
  url: 'crm.api.doc.get_fields_layout',
  cache: ['sidebar-sections', doctype],
  params: { doctype: doctype.value, type: 'Side Panel' },
  auto: true,
})

watch(doctype, (val) => sections.fetch({ doctype: val, type: 'Side Panel' }), {
  immediate: true,
})
</script>
