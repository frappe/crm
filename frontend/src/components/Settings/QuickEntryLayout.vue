<template>
  <div class="flex flex-col overflow-hidden">
    <div class="flex flex-col gap-2 p-8 pb-5">
      <h2 class="flex gap-2 text-xl font-semibold leading-none h-5 mb-4">
        <div>{{ __('Quick Entry Layout') }}</div>
        <Badge
          v-if="dirty"
          :label="__('Not Saved')"
          variant="subtle"
          theme="orange"
        />
      </h2>
      <div class="flex gap-6 items-end">
        <FormControl
          class="flex-1"
          type="select"
          v-model="doctype"
          :label="__('DocType')"
          :options="['CRM Lead', 'CRM Deal', 'Contact', 'CRM Organization']"
          @change="reload"
        />
        <div class="flex flex-row-reverse gap-2">
          <Button
            :loading="loading"
            :label="__('Save')"
            variant="solid"
            @click="saveChanges"
          />
          <Button :label="__('Reset')" @click="reload" />
        </div>
      </div>
    </div>
    <div v-if="sections?.data" class="overflow-y-auto p-8 pt-3">
      <QuickEntryLayoutBuilder :sections="sections.data" :doctype="doctype" />
    </div>
  </div>
</template>
<script setup>
import QuickEntryLayoutBuilder from '@/components/Settings/QuickEntryLayoutBuilder.vue'
import { useDebounceFn } from '@vueuse/core'
import { Badge, call, createResource } from 'frappe-ui'
import { ref, watch, onMounted } from 'vue'

const doctype = ref('CRM Lead')
const loading = ref(false)
const dirty = ref(false)

function getParams() {
  return { doctype: doctype.value, type: 'Quick Entry' }
}

const sections = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_fields_layout',
  cache: ['quick-entry-sections', doctype.value],
  params: getParams(),
  onSuccess(data) {
    sections.originalData = JSON.parse(JSON.stringify(data))
  },
})

watch(
  () => sections?.data,
  () => {
    dirty.value =
      JSON.stringify(sections?.data) !== JSON.stringify(sections?.originalData)
  },
  { deep: true },
)

onMounted(() => useDebounceFn(reload, 100)())

function reload() {
  sections.params = getParams()
  sections.reload()
}

function saveChanges() {
  let _sections = JSON.parse(JSON.stringify(sections.data))
  _sections.forEach((section) => {
    if (!section.fields) return
    section.fields = section.fields.map(
      (field) => field.fieldname || field.name,
    )
  })
  loading.value = true
  call(
    'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.save_fields_layout',
    {
      doctype: doctype.value,
      type: 'Quick Entry',
      layout: JSON.stringify(_sections),
    },
  ).then(() => {
    loading.value = false
    reload()
  })
}
</script>
