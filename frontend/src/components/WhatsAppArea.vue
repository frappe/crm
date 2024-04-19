<template>
  <div>
    <div
      v-for="whatsapp in messages"
      :key="whatsapp.name"
      class="activity flex"
      :class="{ 'justify-end': whatsapp.type == 'Outgoing' }"
    >
      <div
        :id="whatsapp.name"
        class="mb-3 inline-flex max-w-[90%] gap-2 rounded-md bg-gray-50 p-1.5 pl-2 text-base shadow-sm"
      >
        <div
          v-if="whatsapp.content_type == 'text'"
          v-html="formatWhatsAppMessage(whatsapp.message)"
        />
        <div v-else-if="whatsapp.content_type == 'image'">
          <img
            :src="whatsapp.attach"
            class="h-40 cursor-pointer rounded-md"
            @click="() => openFileInAnotherTab(whatsapp.attach)"
          />
          <div
            v-if="!whatsapp.message.startsWith('/files/')"
            class="mt-1.5"
            v-html="formatWhatsAppMessage(whatsapp.message)"
          />
        </div>
        <div
          v-else-if="whatsapp.content_type == 'document'"
          class="flex items-center gap-2"
        >
          <DocumentIcon
            class="size-10 cursor-pointer rounded-md text-gray-500"
            @click="() => openFileInAnotherTab(whatsapp.attach)"
          />
          <div class="text-gray-600">Document</div>
        </div>
        <div
          v-else-if="whatsapp.content_type == 'audio'"
          class="flex items-center gap-2"
        >
          <audio :src="whatsapp.attach" controls class="cursor-pointer" />
        </div>
        <div
          v-else-if="whatsapp.content_type == 'video'"
          class="flex-col items-center gap-2"
        >
          <video
            :src="whatsapp.attach"
            controls
            class="h-40 cursor-pointer rounded-md"
          />
          <div
            v-if="!whatsapp.message.startsWith('/files/')"
            class="mt-1.5"
            v-html="formatWhatsAppMessage(whatsapp.message)"
          />
        </div>
        <div class="-mb-1 flex shrink-0 items-end gap-1 text-gray-600">
          <Tooltip :text="dateFormat(whatsapp.creation, 'ddd, MMM D, YYYY')">
            <div class="text-2xs">
              {{ dateFormat(whatsapp.creation, 'hh:mm a') }}
            </div>
          </Tooltip>
          <div v-if="whatsapp.type == 'Outgoing'">
            <CheckIcon
              v-if="['sent', 'Success'].includes(whatsapp.status)"
              class="size-4"
            />
            <DoubleCheckIcon
              v-else-if="['read', 'delivered'].includes(whatsapp.status)"
              class="size-4"
              :class="{ 'text-blue-500': whatsapp.status == 'read' }"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import CheckIcon from '@/components/Icons/CheckIcon.vue'
import DoubleCheckIcon from '@/components/Icons/DoubleCheckIcon.vue'
import DocumentIcon from '@/components/Icons/DocumentIcon.vue'
import { Tooltip } from 'frappe-ui'
import { dateFormat } from '@/utils'

const props = defineProps({
  messages: Array,
})

function openFileInAnotherTab(url) {
  window.open(url, '_blank')
}

function formatWhatsAppMessage(message) {
  // if message contains _text_, make it italic
  message = message.replace(/_(.*?)_/g, '<i>$1</i>')
  // if message contains *text*, make it bold
  message = message.replace(/\*(.*?)\*/g, '<b>$1</b>')
  // if message contains ~text~, make it strikethrough
  message = message.replace(/~(.*?)~/g, '<s>$1</s>')
  // if message contains ```text```, make it monospace
  message = message.replace(/```(.*?)```/g, '<code>$1</code>')
  // if message contains `text`, make it inline code
  message = message.replace(/`(.*?)`/g, '<code>$1</code>')
  // if message contains > text, make it a blockquote
  message = message.replace(/^> (.*)$/gm, '<blockquote>$1</blockquote>')
  // if contain /n, make it a new line
  message = message.replace(/\n/g, '<br>')
  // if contains *<space>text, make it a bullet point
  message = message.replace(/\* (.*?)(?=\s*\*|$)/g, '<li>$1</li>')
  message = message.replace(/- (.*?)(?=\s*-|$)/g, '<li>$1</li>')
  message = message.replace(/(\d+)\. (.*?)(?=\s*(\d+)\.|$)/g, '<li>$2</li>')

  return message
}
</script>
