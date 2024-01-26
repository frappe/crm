<template>
  <Dialog v-model="show" :options="{ title: 'Email Templates', size: '4xl' }">
    <template #body-content>
      <FormControl
        v-model="search"
        type="text"
        class="mb-2 w-full"
        placeholder="Search"
      />
      <div class="grid grid-cols-3 gap-2">
        <div
          v-for="template in filteredTemplates"
          :key="template.name"
          class="cursor-pointer rounded-lg border p-2 hover:bg-gray-100"
          @click="emit('apply', template)"
        >
          <div class="border-b pb-2 text-base font-semibold">
            {{ template.name }}
          </div>
          <div v-if="template.subject" class="my-1.5 text-sm text-gray-600">
            Subject: {{ template.subject }}
          </div>
          <TextEditor
            v-if="template.response"
            :content="template.response"
            :editable="false"
            editor-class="!prose-sm max-w-none !text-sm text-gray-600 focus:outline-none"
            class="mt-1.5 flex-1 overflow-hidden"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { TextEditor, createListResource } from 'frappe-ui'
import { defineModel, ref, computed } from 'vue'

const props = defineProps({
  doctype: {
    type: String,
    default: '',
  },
})

const show = defineModel()

const emit = defineEmits(['apply'])

const search = ref('')

const templates = createListResource({
  type: 'list',
  doctype: 'Email Template',
  cache: ['Email Templates', props.doctype],
  fields: [
    'name',
    'enabled',
    'reference_doctype',
    'subject',
    'response',
    'modified',
    'owner',
  ],
  filters: { enabled: 1, reference_doctype: props.doctype },
  orderBy: 'modified desc',
  pageLength: 99999,
  auto: true,
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
</script>
