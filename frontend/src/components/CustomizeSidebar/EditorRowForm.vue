<!-- Adds a DocType or a section to the layer being edited. -->
<template>
  <form
    class="flex min-h-0 flex-1 flex-col overflow-y-auto px-6 pt-5"
    novalidate
    @submit.prevent="submit"
  >
    <EditorPaneHeading
      icon="plus"
      :title="type === 'DocType' ? __('Add a DocType') : __('Add a section')"
      :origin="
        editor.scope === 'site'
          ? __('A new row for everyone')
          : __('A new row for you')
      "
    />
    <div class="flex flex-col gap-3">
      <template v-if="type === 'DocType'">
        <DoctypePicker
          v-model="doctype"
          :label="__('DocType')"
          :error="gap"
          @update:model-value="clearErrors"
        />
        <p class="text-p-sm text-ink-gray-5">
          {{
            __(
              "The row takes the DocType's name as its label. Change it after you add it.",
            )
          }}
        </p>
      </template>
      <template v-else>
        <FormControl
          v-model="label"
          type="text"
          :label="__('Label')"
          :placeholder="__('Partners')"
          :error="gap || undefined"
          @update:model-value="clearErrors"
        />
        <Checkbox v-model="collapsible" :label="__('Can collapse')" />
        <Checkbox
          v-model="keepClosed"
          :disabled="!collapsible"
          :label="__('Starts closed')"
        />
      </template>
      <p v-if="editor.refusal" class="text-p-sm text-ink-red-5" role="alert">
        {{ editor.refusal }}
      </p>
    </div>
    <div
      class="mt-auto flex h-[49px] shrink-0 items-center justify-end border-t border-outline-gray-1"
    >
      <Button variant="subtle" type="submit" :label="__('Add row')" />
    </div>
  </form>
</template>

<script setup>
import DoctypePicker from './DoctypePicker.vue'
import EditorPaneHeading from './EditorPaneHeading.vue'
import { addDoctype, addSection, editor } from './editor'
import { Checkbox, FormControl } from 'frappe-ui'
import { ref } from 'vue'

const props = defineProps({
  type: { type: String, required: true },
})

const doctype = ref(null)
const label = ref('')
const collapsible = ref(true)
const keepClosed = ref(false)
const gap = ref(null)

function clearErrors() {
  gap.value = null
  editor.refusal = null
}

function submit() {
  editor.refusal = null
  if (props.type === 'DocType') {
    if (!doctype.value) return (gap.value = __('Pick a DocType.'))
    return addDoctype(doctype.value)
  }
  if (!label.value.trim()) {
    return (gap.value = __('Give the section a label.'))
  }
  addSection(label.value, collapsible.value, keepClosed.value)
}
</script>
