<template>
  <Dialog v-model:open="show" :title="__('WhatsApp Templates')" :size="'4xl'">
    <template #default>
      <div class="w-full flex items-center gap-2">
        <TextInput
          ref="searchInput"
          v-model="search"
          class="w-full"
          type="text"
          :placeholder="__('Welcome Message')"
        >
          <template #prefix>
            <span
              class="lucide-search h-4 w-4 text-ink-gray-4"
              aria-hidden="true"
            />
          </template>
        </TextInput>
        <Button
          v-if="isManager()"
          :label="__('Create')"
          icon-left="lucide-plus"
          @click="newWhatsAppTemplate"
        />
      </div>
      <div
        v-if="filteredTemplates.length"
        class="mt-4 grid max-h-[560px] grid-cols-1 gap-4 overflow-y-auto p-0.5 sm:grid-cols-3"
      >
        <!-- filled with the incoming-message surface, so a card previews the thing it sends -->
        <div
          v-for="template in filteredTemplates"
          :key="template.name"
          class="flex h-56 cursor-pointer flex-col gap-2.5 rounded-lg border border-outline-gray-2 bg-surface-gray-1 p-3 transition-colors hover:bg-surface-gray-2"
          :class="{
            'ring-2 ring-outline-gray-4': selected?.name === template.name,
          }"
          @click="selected = template"
        >
          <div
            class="flex items-center gap-2 border-b border-outline-gray-2 pb-2"
            :title="template.template_label || template.template_name"
          >
            <span class="truncate text-base-semibold">
              {{ template.template_label || template.template_name }}
            </span>
            <Badge v-if="template.language" theme="gray" variant="subtle">
              {{ template.language }}
            </Badge>
          </div>
          <!-- the bubble's own surface and ink, one size down for a grid card -->
          <TemplateContent
            class="min-h-0 flex-1 text-p-sm text-ink-gray-9"
            :header="fill(template, template.header_text)"
            :body="fill(template, template.message)"
            :footer="template.footer"
            :buttons="template.buttons"
            body-class="min-h-0 flex-1 overflow-y-auto"
          />
        </div>
      </div>
      <div v-else class="mt-4">
        <div class="flex h-56 flex-col items-center justify-center">
          <div class="text-lg text-ink-gray-6">
            {{ __('No Templates Found') }}
          </div>
          <Button
            :label="__('Create New')"
            class="mt-4"
            @click="newWhatsAppTemplate"
          />
        </div>
      </div>
      <!-- in the body rather than `#actions`, whose padding leaves a band of space under the grid -->
      <div class="mt-4 flex items-center justify-between gap-4">
        <ErrorMessage :message="sendError || missingRecipientError" />
        <Button
          class="ml-auto"
          :label="__('Send')"
          variant="solid"
          icon-left="lucide-send"
          :disabled="!selected || !to"
          :loading="sending"
          @click="send"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { showSettings, activeSettingsPage } from '@/composables/settings'
import { useBroadcast } from '@/composables/useBroadcast'
import { usersStore } from '@/stores/users'
import { TemplateContent, useTemplates } from '@whatsapp/ui'
import { Badge, ErrorMessage, toast } from 'frappe-ui'
import { ref, computed, nextTick, watch } from 'vue'

const props = defineProps({
  doctype: { type: String, default: '' },
  docname: { type: String, default: '' },
  doc: { type: Object, default: () => ({}) },
  to: { type: String, default: '' },
})

const show = defineModel({ type: Boolean })
const { isManager } = usersStore()
const { send: broadcast } = useBroadcast()
const searchInput = ref('')

const emit = defineEmits(['sent'])

const search = ref('')
const selected = ref(null)
const sending = ref(false)
const sendError = ref('')

const templates = useTemplates({
  referenceDoctype: () => props.doctype,
  referenceDocname: () => props.docname,
  to: () => props.to,
})

const missingRecipientError = computed(() =>
  props.to ? '' : __('Add a mobile number to send a template.'),
)

const errorMessage = computed(() => {
  const error = templates.error
  if (!error) return ''
  return error.messages?.[0] || error.message || __('Error')
})

watch(errorMessage, (message) => {
  if (message && !sending.value) toast.error(message)
})

const filteredTemplates = computed(() => {
  const query = search.value.toLowerCase()
  return templates.templates.filter((template) =>
    [template.template_label, template.template_name, template.language].some(
      (field) => field?.toLowerCase().includes(query),
    ),
  )
})

// Mirrors the server's substitution: `{{name}}` becomes the mapped field's value, and an
// unmapped variable is left as written so the preview never hides a gap.
function fill(template, text) {
  const fields = Object.fromEntries(
    (template.template_variables ?? [])
      .filter((variable) => variable.variable_field)
      .map((variable) => [variable.variable_name, variable.variable_field]),
  )
  return text?.replace(/\{\{\s*(\w+)\s*\}\}/g, (match, name) =>
    name in fields ? String(props.doc[fields[name]] ?? '') : match,
  )
}

async function send() {
  sending.value = true
  sendError.value = ''
  const sent = await templates.sendTemplate(selected.value.name)
  sending.value = false
  if (!sent) {
    sendError.value = errorMessage.value
    return
  }
  show.value = false
  emit('sent')
}

// Only managers see the WhatsApp settings page, which is why the button is gated.
function newWhatsAppTemplate() {
  show.value = false
  showSettings.value = true
  activeSettingsPage.value = 'WhatsApp'
  broadcast('whatsapp_template_page', {
    page: 'new-template',
    reference_doctype: props.doctype,
  })
}

watch(selected, () => (sendError.value = ''))

watch(show, (value) => {
  if (value) {
    nextTick(() => searchInput.value?.el?.focus())
    return
  }
  selected.value = null
  search.value = ''
})
</script>
