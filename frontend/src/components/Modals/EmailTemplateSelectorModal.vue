<template>
  <Dialog
    v-model="show"
    :options="{ title: __('Email Templates'), size: '4xl' }"
  >
    <template #body-content>
      <div class="flex items-center gap-2">
        <TextInput
          class="w-full"
          ref="searchInput"
          v-model="search"
          type="text"
          :placeholder="__('Payment Reminder')"
        >
          <template #prefix>
            <FeatherIcon name="search" class="h-4 w-4 text-ink-gray-4" />
          </template>
        </TextInput>
        <Button
          :label="__('Create')"
          icon-left="plus"
          @click="
            () => {
              show = false
              showSettings = true
              activeSettingsPage = 'Email Templates'
            }
          "
        />
      </div>
      <div
        v-if="filteredTemplates.length"
        class="mt-4 grid max-h-[560px] sm:grid-cols-3 gris-cols-1 gap-2 overflow-y-auto"
      >
        <div
          v-for="template in filteredTemplates"
          :key="template.name"
          class="flex h-56 cursor-pointer flex-col gap-2 rounded-lg border p-3 hover:bg-surface-gray-2"
          @click="emit('apply', template)"
        >
          <div class="border-b pb-2 text-base font-semibold">
            {{ template.name }}
          </div>
          <div v-if="template.subject" class="text-sm text-ink-gray-5">
            {{ __('Subject: {0}', [template.subject]) }}
          </div>
          <TextEditor
            v-if="template.use_html && template.response_html"
            :content="template.response_html"
            :editable="false"
            editor-class="!prose-sm max-w-none !text-sm text-ink-gray-5 focus:outline-none"
            class="flex-1 overflow-hidden"
          />
          <TextEditor
            v-else-if="template.response"
            :content="template.response"
            :editable="false"
            editor-class="!prose-sm max-w-none !text-sm text-ink-gray-5 focus:outline-none"
            class="flex-1 overflow-hidden"
          />
        </div>
      </div>
      <div v-else class="mt-2">
        <div class="flex h-56 flex-col items-center justify-center">
          <div class="text-lg text-ink-gray-4">
            {{ __('No templates found') }}
          </div>
          <Button
            :label="__('Create New')"
            class="mt-4"
            @click="
              () => {
                show = false
                showSettings = true
                activeSettingsPage = 'Email Templates'
              }
            "
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { showSettings, activeSettingsPage } from '@/composables/settings'
import { TextEditor, createListResource } from 'frappe-ui'
import { ref, computed, nextTick, watch, onMounted } from 'vue'

const props = defineProps({
  doctype: {
    type: String,
    default: '',
  },
})

const show = defineModel()
const searchInput = ref('')

const emit = defineEmits(['apply'])

const search = ref('')

const templates = createListResource({
  type: 'list',
  doctype: 'Email Template',
  cache: ['emailTemplates', props.doctype],
  fields: [
    'name',
    'enabled',
    'use_html',
    'reference_doctype',
    'subject',
    'response',
    'response_html',
    'modified',
    'owner',
  ],
  filters: { enabled: 1, reference_doctype: props.doctype },
  orderBy: 'modified desc',
  pageLength: 99999,
})

onMounted(() => {
  if (templates.data == null) {
    templates.fetch()
  }
})

const filteredTemplates = computed(() => {
  return (
    templates.data?.filter((template) => {
      return (
        template.name.toLowerCase().includes(search.value.toLowerCase()) ||
        template.subject.toLowerCase().includes(search.value.toLowerCase())
      )
    }) ?? []
  )
})

watch(show, (value) => value && nextTick(() => searchInput.value?.el?.focus()))
</script>
