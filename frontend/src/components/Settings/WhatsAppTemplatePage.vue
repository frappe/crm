<template>
  <div class="flex h-full flex-col gap-6 p-6">
    <div class="flex justify-between">
      <div class="flex w-9/12 items-center gap-1">
        <Button
          variant="ghost"
          icon-left="lucide-chevron-left"
          :label="title"
          size="md"
          class="cursor-pointer -ml-4 hover:bg-transparent focus:bg-transparent focus:outline-none focus:ring-0 focus:ring-offset-0 focus-visible:none active:bg-transparent active:outline-none active:ring-0 active:ring-offset-0 active:text-ink-gray-5 text-2xl-semibold hover:opacity-70 !pr-0 !max-w-96 !justify-start"
          @click="emit('back')"
        />
        <Badge
          v-if="template.indicator"
          :label="__(template.indicator.label)"
          :theme="template.indicator.theme"
          variant="subtle"
        />
      </div>
      <div class="flex w-3/12 justify-end gap-2">
        <Button
          :label="preview ? __('Edit') : __('Preview')"
          :icon-left="preview ? 'lucide-edit-2' : 'lucide-eye'"
          @click="preview = !preview"
        />
        <Button
          v-if="template.editable && (template.isDirty || template.isNew)"
          :loading="template.saving"
          :label="template.isNew ? __('Create') : __('Save')"
          variant="solid"
          @click="save"
        />
      </div>
    </div>
    <div
      v-if="template.loading"
      class="flex flex-1 items-center justify-center"
    >
      <LoadingIndicator class="size-8" />
    </div>
    <!-- p-1/-m-1 leaves the scroll box a little slack beyond the content, so a
         focused control's ring isn't clipped by the edge it sits flush against. -->
    <div v-else class="-m-1 flex-1 overflow-y-auto p-1">
      <TemplateForm v-if="!preview" :controller="template" />
      <TemplatePreview v-else :controller="template" />
    </div>
  </div>
</template>

<script setup>
import {
  serverErrorMessage,
  TemplateForm,
  TemplatePreview,
  useTemplate,
} from '@whatsapp/ui'
import { LoadingIndicator, toast } from 'frappe-ui'
import { computed, ref } from 'vue'

const props = defineProps({
  // Empty renders a blank template that the first save creates.
  name: { type: String, default: '' },
  // Prefilled on a new template, for a picker that opens this screen from a document.
  referenceDoctype: { type: String, default: '' },
})

const emit = defineEmits(['back', 'created'])

const template = useTemplate({ name: () => props.name })
const preview = ref(false)

if (template.isNew && props.referenceDoctype) {
  template.doc.reference_doctype = props.referenceDoctype
}

const title = computed(() => {
  if (template.isNew) return __('New Template')
  return template.doc.template_label || template.doc.template_name || ''
})

// Saving pushes the template to Meta. The form shows a refusal under itself,
// but that is below a long form, so the toast repeats it where it is seen.
async function save() {
  const wasNew = template.isNew
  const saved = await template.save()
  if (!saved) {
    toast.error(
      serverErrorMessage(template.error) || __('Failed to save template'),
    )
    return
  }
  if (wasNew) {
    toast.success(__('Template created and sent to Meta for review'))
    emit('created', saved)
  } else {
    toast.success(__('Template updated'))
  }
}
</script>
