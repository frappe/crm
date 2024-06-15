<template>
  <div ref="parentRef" class="flex h-full">
    <div class="flex-1 flex flex-col justify-between gap-2 p-8">
      <div class="flex flex-col gap-2">
        <h2 class="flex gap-2 text-xl font-semibold leading-none h-5 mb-4">
          <div>{{ __('Sidebar Fields Layout') }}</div>
          <Badge
            v-if="dirty"
            :label="__('Not Saved')"
            variant="subtle"
            theme="orange"
          />
        </h2>
        <FormControl
          type="select"
          v-model="doctype"
          :label="__('DocType')"
          :options="['CRM Lead', 'CRM Deal']"
        />
      </div>
      <div class="flex flex-row-reverse gap-2">
        <Button
          :loading="loading"
          :label="__('Save')"
          variant="solid"
          @click="saveChanges"
        />
        <Button :label="__('Reset')" @click="sections.reload" />
      </div>
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
          <SidebarLayoutBuilder :sections="sections.data" />
        </div>
      </div>
    </Resizer>
  </div>
</template>
<script setup>
import Resizer from '@/components/Resizer.vue'
import SidebarLayoutBuilder from '@/components/Settings/SidebarLayoutBuilder.vue'
import { Badge, call, createResource } from 'frappe-ui'
import { ref, computed, watch } from 'vue'

const parentRef = ref(null)
const doctype = ref('CRM Lead')

const oldSections = ref([])

const sections = createResource({
  url: 'crm.api.doc.get_fields_layout',
  cache: ['sidebar-sections', doctype.value],
  params: { doctype: doctype.value, type: 'Side Panel' },
  auto: true,
  onSuccess(data) {
    oldSections.value = JSON.parse(JSON.stringify(data))
  },
})
const loading = ref(false)

const dirty = computed(() => {
  if (!sections.data) return false
  return JSON.stringify(sections.data) !== JSON.stringify(oldSections.value)
})

function saveChanges() {
  let _sections = JSON.parse(JSON.stringify(sections.data))
  _sections.forEach((section) => {
    if (!section.fields) return
    section.fields = section.fields.map((field) => field.name)
  })
  loading.value = true
  call('crm.api.doc.save_fields_layout', {
    doctype: doctype.value,
    type: 'Side Panel',
    layout: JSON.stringify(_sections),
  }).then(() => {
    loading.value = false
    sections.reload()
  })
}

watch(doctype, (val) => sections.fetch({ doctype: val, type: 'Side Panel' }), {
  immediate: true,
})
</script>
