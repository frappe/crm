<template>
  <div class="flex h-full flex-col gap-6 p-8 text-ink-gray-8">
    <!-- Header -->
    <div class="flex justify-between">
      <div class="flex gap-1 w-9/12">
        <div
          class="flex text-ink-gray-7 gap-2 cursor-pointer"
          :tabindex="0"
          @keydown.enter="() => emit('updateStep', 'template-list')"
          @click="() => emit('updateStep', 'template-list')"
        >
          <FeatherIcon name="chevron-left" class="size-5" />
          <span class="text-xl font-semibold">
            {{
              templateData?.name ? __('Duplicate template') : __('New template')
            }}
          </span>
        </div>
      </div>
      <div class="flex item-center space-x-2 w-3/12 justify-end">
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
      <div
        class="flex justify-between items-center cursor-pointer border-b py-3"
        @click="() => (template.enabled = !template.enabled)"
      >
        <div class="text-base text-ink-gray-7">{{ __('Enabled') }}</div>
        <Switch v-model="template.enabled" @click.stop />
      </div>
      <div class="flex sm:flex-row flex-col gap-4">
        <div class="flex-1">
          <FormControl
            size="md"
            v-model="template.name"
            :placeholder="__('Payment Reminder')"
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
          :placeholder="__('Payment Reminder from Frappé - (#{{ name }})')"
          :required="true"
        />
      </div>
      <div class="border-t pt-4">
        <FormControl
          type="select"
          size="md"
          v-model="template.content_type"
          :label="__('Content Type')"
          default="Rich Text"
          :options="['Rich Text', 'HTML']"
          :placeholder="__('Rich Text')"
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
            editor-class="!prose-sm overflow-auto min-h-[180px] max-h-80 py-1.5 px-2 rounded border border-[--surface-gray-2] bg-surface-gray-2 placeholder-ink-gray-4 hover:border-outline-gray-modals hover:bg-surface-gray-3 hover:shadow-sm focus:bg-surface-white focus:border-outline-gray-4 focus:shadow-sm focus:ring-0 focus-visible:ring-2 focus-visible:ring-outline-gray-3 text-ink-gray-8 transition-colors"
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
  if (props.templateData) {
    Object.assign(template.value, props.templateData)
    template.value.name = template.value.name + ' - Copy'
    template.value.enabled = false // Default to disabled for new templates
  }
})
</script>
