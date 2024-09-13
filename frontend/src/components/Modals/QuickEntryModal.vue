<template>
  <Dialog v-model="show" :options="{ size: '3xl' }">
    <template #body-title>
      <h3
        class="flex items-center gap-2 text-2xl font-semibold leading-6 text-gray-900"
      >
        <div>{{ __('Edit Quick Entry Layout') }}</div>
        <Badge
          v-if="dirty"
          :label="__('Not Saved')"
          variant="subtle"
          theme="orange"
        />
      </h3>
    </template>
    <template #body-content>
      <div class="flex flex-col gap-3">
        <div class="flex justify-between gap-2">
          <FormControl
            type="select"
            class="w-1/4"
            v-model="_doctype"
            :options="[
              'CRM Lead',
              'CRM Deal',
              'Contact',
              'CRM Organization',
              'Address',
            ]"
            @change="reload"
          />
          <Switch
            v-model="preview"
            :label="preview ? __('Hide preview') : __('Show preview')"
            size="sm"
          />
        </div>
        <div v-if="sections?.data">
          <QuickEntryLayoutBuilder
            v-if="!preview"
            :sections="sections.data"
            :doctype="_doctype"
          />
          <Fields v-else :sections="sections.data" :data="{}" />
        </div>
      </div>
    </template>
    <template #actions>
      <div class="flex flex-row-reverse gap-2">
        <Button
          :loading="loading"
          :label="__('Save')"
          variant="solid"
          @click="saveChanges"
        />
        <Button :label="__('Reset')" @click="reload" />
      </div>
    </template>
  </Dialog>
</template>
<script setup>
import Fields from '@/components/Fields.vue'
import QuickEntryLayoutBuilder from '@/components/QuickEntryLayoutBuilder.vue'
import { useDebounceFn } from '@vueuse/core'
import { capture } from '@/telemetry'
import { Dialog, Badge, Switch, call, createResource } from 'frappe-ui'
import { ref, watch, onMounted, nextTick } from 'vue'

const props = defineProps({
  doctype: {
    type: String,
    default: 'CRM Lead',
  },
})

const show = defineModel()
const _doctype = ref(props.doctype)
const loading = ref(false)
const dirty = ref(false)
const preview = ref(false)

function getParams() {
  return { doctype: _doctype.value, type: 'Quick Entry' }
}

const sections = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_fields_layout',
  cache: ['quick-entry-sections', _doctype.value],
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
  nextTick(() => {
    sections.params = getParams()
    sections.reload()
  })
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
      doctype: _doctype.value,
      type: 'Quick Entry',
      layout: JSON.stringify(_sections),
    },
  ).then(() => {
    loading.value = false
    show.value = false
    capture('quick_entry_layout_builder', { doctype: _doctype.value })
  })
}
</script>
