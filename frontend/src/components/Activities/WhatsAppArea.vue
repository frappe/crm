<template>
  <div>
    <div
      v-for="whatsapp in messages"
      :key="whatsapp.name"
      class="activity group flex gap-2"
      :class="[
        whatsapp.type == 'Outgoing' ? 'flex-row-reverse' : '',
        whatsapp.reaction ? 'mb-7' : 'mb-3',
      ]"
    >
      <div
        :id="whatsapp.name"
        class="group/message relative max-w-[90%] rounded-md bg-gray-50 p-1.5 pl-2 text-base shadow-sm"
      >
        <div
          v-if="whatsapp.is_reply"
          @click="() => scrollToMessage(whatsapp.reply_to)"
          class="mb-1 cursor-pointer rounded border-0 border-l-4 bg-gray-200 p-2 text-gray-600"
          :class="
            whatsapp.reply_to_type == 'Incoming'
              ? 'border-green-500'
              : 'border-blue-400'
          "
        >
          <div
            class="mb-1 text-sm font-bold"
            :class="
              whatsapp.reply_to_type == 'Incoming'
                ? 'text-green-500'
                : 'text-blue-400'
            "
          >
            {{ whatsapp.reply_to_from || __('You') }}
          </div>
          <div class="flex flex-col gap-2 max-h-12 overflow-hidden">
            <div v-if="whatsapp.header" class="text-base font-semibold">
              {{ whatsapp.header }}
            </div>
            <div v-html="formatWhatsAppMessage(whatsapp.reply_message)" />
            <div v-if="whatsapp.footer" class="text-xs text-gray-600">
              {{ whatsapp.footer }}
            </div>
          </div>
        </div>
        <div class="flex gap-2 justify-between">
          <div
            class="absolute -right-0.5 -top-0.5 flex cursor-pointer gap-1 rounded-full bg-white pb-2 pl-2 pr-1.5 pt-1.5 opacity-0 group-hover/message:opacity-100"
            :style="{
              background:
                'radial-gradient(circle at 50% 50%, rgba(255, 255, 255, 1) 0%, rgba(255, 255, 255, 1) 35%, rgba(238, 130, 238, 0) 100%)',
            }"
          >
            <Dropdown :options="messageOptions(whatsapp)">
              <FeatherIcon name="chevron-down" class="size-4 text-gray-600" />
            </Dropdown>
          </div>
          <div
            class="absolute -bottom-5 flex gap-1 rounded-full border bg-white p-1 pb-[3px] shadow-sm"
            v-if="whatsapp.reaction"
          >
            <div class="flex size-4 items-center justify-center">
              {{ whatsapp.reaction }}
            </div>
          </div>
          <div
            class="flex flex-col gap-2"
            v-if="whatsapp.message_type == 'Template'"
          >
            <div v-if="whatsapp.header" class="text-base font-semibold">
              {{ whatsapp.header }}
            </div>
            <div v-html="formatWhatsAppMessage(whatsapp.template)" />
            <div v-if="whatsapp.footer" class="text-xs text-gray-600">
              {{ whatsapp.footer }}
            </div>
          </div>
          <div
            v-else-if="whatsapp.content_type == 'text'"
            v-html="formatWhatsAppMessage(whatsapp.message)"
          />
          <div
            v-else-if="whatsapp.content_type == 'button'"
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
      <div
        class="flex items-center justify-center opacity-0 transition-all ease-in group-hover:opacity-100"
      >
        <IconPicker
          v-model="emoji"
          v-model:reaction="reaction"
          v-slot="{ togglePopover }"
          @update:modelValue="() => reactOnMessage(whatsapp.name, emoji)"
        >
          <Button
            @click="() => (reaction = true) && togglePopover()"
            class="rounded-full !size-6 mt-0.5"
          >
            <ReactIcon class="text-gray-400" />
          </Button>
        </IconPicker>
      </div>
    </div>
  </div>
</template>

<script setup>
import IconPicker from '@/components/IconPicker.vue'
import CheckIcon from '@/components/Icons/CheckIcon.vue'
import DoubleCheckIcon from '@/components/Icons/DoubleCheckIcon.vue'
import DocumentIcon from '@/components/Icons/DocumentIcon.vue'
import ReactIcon from '@/components/Icons/ReactIcon.vue'
import { dateFormat } from '@/utils'
import { capture } from '@/telemetry'
import { Tooltip, Dropdown, createResource } from 'frappe-ui'
import { ref } from 'vue'

const props = defineProps({
  messages: Array,
})

const list = defineModel()

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

const emoji = ref('')
const reaction = ref(true)

function reactOnMessage(name, emoji) {
  createResource({
    url: 'crm.api.whatsapp.react_on_whatsapp_message',
    params: {
      emoji,
      reply_to_name: name,
    },
    auto: true,
    onSuccess() {
      capture('whatsapp_react_on_message')
      list.value.reload()
    },
  })
}

const reply = defineModel('reply')
const replyMode = ref(false)

function messageOptions(message) {
  return [
    {
      label: 'Reply',
      onClick: () => {
        replyMode.value = true
        reply.value = {
          ...message,
          message: formatWhatsAppMessage(message.message)
        }
      },
    },
    // {
    //   label: 'Forward',
    //   onClick: () => console.log('Forward'),
    // },
    // {
    //   label: 'Delete',
    //   onClick: () => console.log('Delete'),
    // },
  ]
}

function scrollToMessage(name) {
  const element = document.getElementById(name)
  element.scrollIntoView({ behavior: 'smooth' })

  // Highlight the message
  element.classList.add('bg-yellow-100')
  setTimeout(() => {
    element.classList.remove('bg-yellow-100')
  }, 1000)
}
</script>
