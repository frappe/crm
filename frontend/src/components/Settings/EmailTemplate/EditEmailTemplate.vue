<template>
  <div class="flex h-full flex-col gap-6 p-8 text-ink-gray-8">
    <!-- Header -->
    <div class="flex justify-between">
      <div class="flex gap-1 -ml-4 w-9/12">
        <Button
          variant="ghost"
          icon-left="chevron-left"
          :label="__(template.name)"
          size="md"
          @click="() => emit('updateStep', 'template-list')"
          class="text-xl !h-7 font-semibold hover:bg-transparent focus:bg-transparent focus:outline-none focus:ring-0 focus:ring-offset-0 focus-visible:none active:bg-transparent active:outline-none active:ring-0 active:ring-offset-0 active:text-ink-gray-5"
        />
      </div>
      <div class="flex item-center space-x-2 w-3/12 justify-end">
        <Button
          :label="__('Update')"
          icon-left="plus"
          variant="solid"
          :disabled="!dirty"
          :loading="renameDoc.loading || templates.setValue.loading"
          @click="updateTemplate"
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
import {
  TextEditor,
  FormControl,
  Switch,
  toast,
  call,
  createResource,
} from 'frappe-ui'
import { computed, inject, onMounted, ref } from 'vue'

const props = defineProps({
  templateData: {
    type: Object,
    required: true,
  },
})

const emit = defineEmits(['updateStep'])
const errorMessage = ref('')

const templates = inject('templates')
const template = ref({})

const updateTemplate = async () => {
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

  template.value.use_html = template.value.content_type === 'HTML'

  const old = {
    ...props.templateData,
    use_html: Boolean(props.templateData.use_html),
  }
  const newEmailTemplate = {
    ...template.value,
    use_html: Boolean(template.value.use_html),
  }

  delete newEmailTemplate.content_type

  const nameChanged = old.name !== newEmailTemplate.name
  delete old.name
  delete newEmailTemplate.name

  const otherFieldChanged =
    JSON.stringify(old) !== JSON.stringify(newEmailTemplate)
  const values = newEmailTemplate

  if (!nameChanged && !otherFieldChanged) return

  let name = props.templateData.name

  if (nameChanged) {
    name = await renameDoc.fetch()
    if (!otherFieldChanged) {
      emit('updateStep', 'template-list')
    }
  }
  if (otherFieldChanged) {
    templates.setValue.submit(
      { ...values, name },
      {
        onSuccess: () => {
          emit('updateStep', 'template-list')
          toast.success(__('Template updated successfully'))
        },
        onError: (error) => {
          errorMessage.value =
            error.messages[0] || __('Failed to update template')
        },
      },
    )
  }
}

const dirty = computed(() => {
  return (
    template.value.name !== props.templateData.name ||
    template.value.reference_doctype !== props.templateData.reference_doctype ||
    template.value.subject !== props.templateData.subject ||
    template.value.response_html !== props.templateData.response_html ||
    template.value.response !== props.templateData.response ||
    template.value.use_html !== props.templateData.use_html ||
    Boolean(template.value.enabled) !== Boolean(props.templateData.enabled)
  )
})

const renameDoc = createResource({
  url: 'frappe.client.rename_doc',
  method: 'POST',
  makeParams() {
    return {
      doctype: 'Email Template',
      old_name: props.templateData.name,
      new_name: template.value.name,
    }
  },
  onSuccess: () => {
    templates.reload()
    toast.success(__('Template renamed successfully'))
  },
  onError: (error) => {
    errorMessage.value = error.messages[0] || __('Failed to rename template')
  },
})

onMounted(() => {
  template.value = { ...props.templateData }
  template.value.content_type = template.value.use_html ? 'HTML' : 'Rich Text'
})
</script>
