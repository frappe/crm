<template>
  <Dialog v-model="show" :options="{ size: '3xl' }">
    <template #body-title>
      <h3
        class="flex items-center gap-2 text-2xl font-semibold leading-6 text-ink-gray-9"
      >
        <div>{{ __('Edit field layout') }}</div>
        <Badge
          v-if="dirty"
          :label="__('Not saved')"
          variant="subtle"
          theme="orange"
        />
      </h3>
    </template>
    <template #body-content>
      <div class="flex flex-col gap-5.5">
        <div class="flex justify-between gap-2">
          <Button
            :label="preview ? __('Hide preview') : __('Show preview')"
            @click="preview = !preview"
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
        <div v-if="tabs.data?.[0]?.sections" class="flex gap-4">
          <SidePanelLayoutEditor
            class="flex flex-1 flex-col pr-2"
            :sections="tabs.data[0].sections"
            :doctype="_doctype"
          />
          <div v-if="preview" class="flex flex-1 flex-col border rounded">
            <SidePanelLayout
              :sections="tabs.data[0].sections"
              :doctype="_doctype"
              docname=""
              :preview="true"
              v-slot="{ section }"
            >
              <div
                v-if="section.name == 'contacts_section'"
                class="flex h-16 items-center justify-center text-base text-ink-gray-5"
              >
                {{ __('No contacts added') }}
              </div>
            </SidePanelLayout>
          </div>
          <div
            v-else
            class="flex flex-1 justify-center items-center text-ink-gray-5 bg-surface-gray-2 rounded"
          >
            {{ __('Toggle on for preview') }}
          </div>
        </div>
      </div>
    </template>
  </Dialog>
</template>
<script setup>
import SidePanelLayout from '@/components/SidePanelLayout.vue'
import SidePanelLayoutEditor from '@/components/SidePanelLayoutEditor.vue'
import { useDebounceFn } from '@vueuse/core'
import { capture } from '@/telemetry'
import { Dialog, Badge, call, createResource } from 'frappe-ui'
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

const tabs = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_fields_layout',
  cache: ['SidePanel', _doctype.value],
  params: getParams(),
  onSuccess(data) {
    tabs.originalData = JSON.parse(JSON.stringify(data))
  },
})

watch(
  () => tabs?.data,
  () => {
    dirty.value =
      JSON.stringify(tabs?.data) !== JSON.stringify(tabs?.originalData)
  },
  { deep: true },
)

onMounted(() => useDebounceFn(reload, 100)())

function reload() {
  nextTick(() => {
    tabs.params = getParams()
    tabs.reload()
  })
}

function saveChanges() {
  let _tabs = JSON.parse(JSON.stringify(tabs.data))
  _tabs.forEach((tab) => {
    tab.sections.forEach((section) => {
      if (!section.columns) return
      section.columns.forEach((column) => {
        if (!column.fields) return
        column.fields = column.fields
          .map((field) => field.fieldname)
          .filter(Boolean)
      })
    })
  })
  loading.value = true
  call(
    'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.save_fields_layout',
    {
      doctype: _doctype.value,
      type: 'Side Panel',
      layout: JSON.stringify(_tabs[0].sections),
    },
  ).then(() => {
    loading.value = false
    show.value = false
    capture('side_panel_layout_builder', { doctype: _doctype.value })
    emit('reload')
  })
}
</script>
