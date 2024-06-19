<template>
  <div ref="parentRef" class="flex flex-col p-8 overflow-hidden">
    <h2 class="flex gap-2 text-xl font-semibold leading-none h-5 mb-4">
      <div>{{ __('Quick Entry Layout') }}</div>
      <Badge
        v-if="dirty"
        :label="__('Not Saved')"
        variant="subtle"
        theme="orange"
      />
    </h2>
    <div class="flex-1 flex flex-col justify-between -m-3 p-3 gap-6 overflow-y-auto">
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
      <div v-if="sections?.data" class="">
        <QuickEntryLayoutBuilder :sections="sections.data" :doctype="doctype" />
      </div>
    </div>
  </div>
</template>
<script setup>
import QuickEntryLayoutBuilder from '@/components/Settings/QuickEntryLayoutBuilder.vue'
import { useDebounceFn } from '@vueuse/core'
import { Badge, createResource } from 'frappe-ui'
import { ref, onMounted } from 'vue'

const parentRef = ref(null)
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

onMounted(() => useDebounceFn(reload, 100)())

function reload() {
  sections.params = getParams()
  sections.reload()
}

function saveChanges() {
  // TODO: Save changes
}
</script>
