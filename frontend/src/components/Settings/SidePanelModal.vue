<template>
  <Dialog v-model="show" :options="{ size: '3xl' }">
    <template #body>
      <div ref="parentRef" class="flex h-[calc(100vh_-_8rem)]">
        <div class="flex-1 flex flex-col justify-between gap-2 p-8">
          <div class="flex flex-col gap-2">
            <h2 class="flex gap-2 text-xl font-semibold leading-none h-5 mb-4">
              <div>{{ __('Edit Fields Layout') }}</div>
              <Badge
                v-if="dirty"
                :label="__('Not Saved')"
                variant="subtle"
                theme="orange"
              />
            </h2>
            <FormControl
              type="select"
              v-model="_doctype"
              :label="__('DocType')"
              :options="['CRM Lead', 'CRM Deal']"
              @change="reload"
            />
          </div>
          <div class="flex flex-row-reverse gap-2">
            <Button
              :loading="loading"
              :label="__('Save')"
              variant="solid"
              @click="saveChanges"
            />
            <Button :label="__('Reset')" @click="reload" />
            <Button
              :label="preview ? __('Hide Preview') : __('Show Preview')"
              @click="preview = !preview"
            />
          </div>
        </div>
        <Resizer
          v-if="sections.data"
          class="flex flex-col justify-between border-l"
          :parent="parentRef"
          side="right"
        >
          <div class="flex flex-1 flex-col justify-between overflow-hidden">
            <div class="flex flex-col overflow-y-auto">
              <SidePanelLayoutBuilder
                v-if="!preview"
                :sections="sections.data"
                :doctype="_doctype"
              />
              <div
                v-else
                v-for="(section, i) in sections.data"
                :key="section.label"
                class="flex flex-col p-3"
                :class="{ 'border-b': i !== sections.data.length - 1 }"
              >
                <Section :is-opened="section.opened" :label="section.label">
                  <SectionFields :fields="section.fields" v-model="data" />
                </Section>
              </div>
            </div>
          </div>
        </Resizer>
      </div>
    </template>
  </Dialog>
</template>
<script setup>
import Section from '@/components/Section.vue'
import SectionFields from '@/components/SectionFields.vue'
import Resizer from '@/components/Resizer.vue'
import SidePanelLayoutBuilder from '@/components/Settings/SidePanelLayoutBuilder.vue'
import { useDebounceFn } from '@vueuse/core'
import { Dialog, Badge, call, createResource } from 'frappe-ui'
import { ref, watch, onMounted, nextTick } from 'vue'

const props = defineProps({
  doctype: {
    type: String,
    default: 'CRM Lead',
  },
})

const show = defineModel()
const _doctype = ref(props.doctype)
const parentRef = ref(null)
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
    section.fields = section.fields.map(
      (field) => field.fieldname || field.name,
    )
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
    reload()
  })
}
</script>
