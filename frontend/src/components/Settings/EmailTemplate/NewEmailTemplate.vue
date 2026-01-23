<template>
  <div class="flex h-full flex-col gap-6 p-8 text-ink-gray-8">
    <!-- Header -->
    <div class="flex justify-between">
      <div class="flex gap-1 -ml-4 w-9/12">
        <Button
          variant="ghost"
          icon-left="chevron-left"
          :label="
            templateData?.name ? __('Duplicate template') : __('New template')
          "
          size="md"
          @click="() => emit('updateStep', 'template-list')"
          class="cursor-pointer hover:bg-transparent focus:bg-transparent focus:outline-none focus:ring-0 focus:ring-offset-0 focus-visible:none active:bg-transparent active:outline-none active:ring-0 active:ring-offset-0 active:text-ink-gray-5 font-semibold text-xl hover:opacity-70 !pr-0 !max-w-96 !justify-start"
        />
      </div>
      <div class="flex item-center space-x-4 w-3/12 justify-end">
        <div class="flex items-center space-x-2">
          <Switch size="sm" v-model="template.enabled" />
          <span class="text-sm text-ink-gray-7">{{ __('Enabled') }}</span>
        </div>
        <Button
          :label="templateData?.name ? __('Duplicate') : __('Create')"
          icon-left="plus"
          variant="solid"
          @click="createTemplate"
        />
      </div>
    </div>

    <!-- Fields -->
    <div class="flex flex-1 flex-col gap-4 overflow-y-auto">
      <div class="flex sm:flex-row flex-col gap-4">
        <div class="flex-1">
          <FormControl
            size="md"
            v-model="template.name"
            :placeholder="__('Payment reminder')"
            :label="__('Name')"
            :required="true"
          />
        </div>
        <div class="flex-1">
          <FormControl
            type="select"
            size="md"
            v-model="template.reference_doctype"
            :label="__('For')"
            :options="[
              {
                label: __('Deal'),
                value: 'CRM Deal',
              },
              {
                label: __('Lead'),
                value: 'CRM Lead',
              },
            ]"
            :placeholder="__('Deal')"
          />
        </div>
      </div>
      <div>
        <FormControl
          ref="subjectRef"
          size="md"
          v-model="template.subject"
          :label="__('Subject')"
          :placeholder="__('Payment reminder from Frappé - (#{{ name }})')"
          :required="true"
        />
      </div>
      <div class="border-t pt-4">
        <FormControl
          type="select"
          size="md"
          v-model="template.content_type"
          :label="__('Content type')"
          default="Rich Text"
          :options="['Rich Text', 'HTML']"
          :placeholder="__('Rich text')"
        />
      </div>
      <div>
        <FormControl
          v-if="template.content_type === 'HTML'"
          size="md"
          type="textarea"
          :label="__('Content')"
          :required="true"
          ref="content"
          :rows="10"
          v-model="template.response_html"
          :placeholder="
            __(
              '<p>Dear {{ lead_name }},</p>\n\n<p>This is a reminder for the payment of {{ grand_total }}.</p>\n\n<p>Thanks,</p>\n<p>Frappé</p>',
            )
          "
        />
        <div v-else>
          <div class="mb-1.5 text-base text-ink-gray-5">
            {{ __('Content') }}
            <span class="text-ink-red-3">*</span>
          </div>
          <TextEditor
            ref="content"
            editor-class="!prose-sm max-w-full overflow-auto min-h-[180px] max-h-80 py-1.5 px-2 rounded border border-[--surface-gray-2] bg-surface-gray-2 placeholder-ink-gray-4 hover:border-outline-gray-modals hover:bg-surface-gray-3 hover:shadow-sm focus:bg-surface-white focus:border-outline-gray-4 focus:shadow-sm focus:ring-0 focus-visible:ring-2 focus-visible:ring-outline-gray-3 text-ink-gray-8 transition-colors"
            :bubbleMenu="true"
            :content="template.response"
            @change="(val) => (template.response = val)"
            :placeholder="
              __(
                'Dear {{ lead_name }}, \n\nThis is a reminder for the payment of {{ grand_total }}. \n\nThanks, \nFrappé',
              )
            "
          />
        </div>
      </div>
    </div>
    <div v-if="errorMessage">
      <ErrorMessage :message="__(errorMessage)" />
    </div>
  </div>
</template>
<script setup>
import { TextEditor, FormControl, Switch, toast } from 'frappe-ui'
import { inject, onMounted, ref } from 'vue'

const props = defineProps({
  templateData: {
    type: Object,
    default: () => ({}),
  },
})

const emit = defineEmits(['updateStep'])
const errorMessage = ref('')

const template = ref({
  name: '',
  reference_doctype: 'CRM Deal',
  subject: '',
  content_type: 'Rich Text',
  response_html: '',
  response: '',
  enabled: false,
})

const templates = inject('templates')

const createTemplate = () => {
  errorMessage.value = ''
  if (!template.value.name) {
    errorMessage.value = __('Name is required')
    return
  }
  if (!template.value.subject) {
    errorMessage.value = __('Subject is required')
    return
  }
  if (template.value.content_type === 'Rich Text' && !template.value.response) {
    errorMessage.value = __('Content is required')
    return
  }
  if (template.value.content_type === 'HTML' && !template.value.response_html) {
    errorMessage.value = __('Content is required')
    return
  }

  templates.insert.submit(
    { ...template.value },
    {
      onSuccess: () => {
        emit('updateStep', 'template-list')
        toast.success(__('Template created successfully'))
      },
      onError: (error) => {
        errorMessage.value =
          error.messages[0] || __('Failed to create template')
      },
    },
  )
}

onMounted(() => {
  if (props.templateData?.name) {
    Object.assign(template.value, props.templateData)
    template.value.name = template.value.name + ' - Copy'
    template.value.enabled = false // Default to disabled for new templates
  }
})
</script>
