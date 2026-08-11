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
          :label="__('Create New Template')"
          variant="solid"
          @click="newWhatsAppTemplate"
        >
          <template #prefix>
            <span class="lucide-plus h-4 w-4" aria-hidden="true" />
          </template>
        </Button>
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
          @click="send(template.name)"
        >
          <div
            class="truncate border-b border-outline-gray-2 pb-2 text-base-semibold"
            :title="template.name"
          >
            {{ template.name }}
          </div>
          <!-- the bubble's own surface and ink, one size down for a grid card -->
          <TemplateContent
            class="min-h-0 flex-1 text-p-sm text-ink-gray-9"
            :header="template.header_text"
            :body="template.message"
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
    </template>
  </Dialog>
</template>

<script setup>
import { TemplateContent, useTemplates } from '@whatsapp/ui'
import { toast } from 'frappe-ui'
import { ref, computed, nextTick, watch } from 'vue'

const props = defineProps({
  doctype: { type: String, default: '' },
  docname: { type: String, default: '' },
  to: { type: String, default: '' },
})

const show = defineModel({ type: Boolean })
const searchInput = ref('')

const emit = defineEmits(['sent'])

const search = ref('')

const templates = useTemplates({
  referenceDoctype: () => props.doctype,
  referenceDocname: () => props.docname,
  to: () => props.to,
})

watch(
  () => templates.error,
  (error) => {
    if (error) toast.error(error.messages?.[0] || error.message || __('Error'))
  },
)

const filteredTemplates = computed(() =>
  templates.templates.filter((template) =>
    template.name.toLowerCase().includes(search.value.toLowerCase()),
  ),
)

async function send(templateName) {
  show.value = false
  if (await templates.sendTemplate(templateName)) emit('sent')
}

function newWhatsAppTemplate() {
  show.value = false
  window.open('/app/whatsapp-template/new')
}

watch(show, (value) => value && nextTick(() => searchInput.value?.el?.focus()))
</script>
