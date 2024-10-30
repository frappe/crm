<template>
  <Dialog v-model="show" :options="{ size: '3xl' }">
    <template #body-title>
      <h3
        class="flex items-center gap-2 text-2xl font-semibold leading-6 text-gray-900"
      >
        <div>{{ __('Edit Field Layout') }}</div>
        <Badge
          v-if="dirty"
          :label="__('Not Saved')"
          variant="subtle"
          theme="orange"
        />
      </h3>
    </template>
    <template #body-content>
      <div class="flex flex-col gap-5.5">
        <div class="flex justify-between gap-2">
          <FormControl
            type="select"
            class="w-1/4"
            v-model="_doctype"
            :options="['CRM Lead', 'CRM Deal', 'Contact', 'CRM Organization']"
            @change="reload"
          />
          <Switch
            v-model="preview"
            :label="preview ? __('Hide preview') : __('Show preview')"
            size="sm"
          />
        </div>
        <div v-if="sections.data" class="flex gap-4">
          <SidePanelLayoutBuilder
            class="flex flex-1 flex-col pr-2"
            :sections="sections.data"
            :doctype="_doctype"
          />
          <div v-if="preview" class="flex flex-1 flex-col border rounded">
            <div
              v-for="(section, i) in sections.data"
              :key="section.label"
              class="flex flex-col py-1.5 px-1"
              :class="{ 'border-b': i !== sections.data?.length - 1 }"
            >
              <Section :is-opened="section.opened" :label="section.label">
                <SectionFields
                  :fields="section.fields"
                  :isLastSection="i == section.data?.length - 1"
                  v-model="data"
                />
              </Section>
            </div>
          </div>
          <div
            v-else
            class="flex flex-1 justify-center items-center text-gray-600 bg-gray-50 rounded border border-gray-50"
          >
            {{ __('Toggle on for preview') }}
          </div>
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
import Section from '@/components/Section.vue'
import SectionFields from '@/components/SectionFields.vue'
import SidePanelLayoutBuilder from '@/components/Settings/SidePanelLayoutBuilder.vue'
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

const emit = defineEmits(['reload'])

const show = defineModel()
const _doctype = ref(props.doctype)
const loading = ref(false)
const dirty = ref(false)
const preview = ref(false)
const data = ref({})

function getParams() {
  return { doctype: _doctype.value, type: 'Side Panel' }
}

const sections = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_fields_layout',
  cache: ['sidebar-sections', _doctype.value],
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
    section.fields = section.fields
      .map((field) => field.fieldname || field.name)
      .filter(Boolean)
  })
  loading.value = true
  call(
    'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.save_fields_layout',
    {
      doctype: _doctype.value,
      type: 'Side Panel',
      layout: JSON.stringify(_sections),
    },
  ).then(() => {
    loading.value = false
    show.value = false
    capture('side_panel_layout_builder', { doctype: _doctype.value })
    emit('reload')
  })
}
</script>
