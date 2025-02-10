<template>
  <div>
    <div
      v-for="avito in messages"
      :key="avito.name"
      class="activity group flex gap-2"
      :class="[
        avito.type == 'Outgoing' ? 'flex-row-reverse' : '',
        avito.reaction ? 'mb-7' : 'mb-3',
      ]"
    >
      <div
        :id="avito.name"
        class="group/message relative max-w-[90%] rounded-md bg-surface-gray-1 text-ink-gray-9 p-1.5 pl-2 text-base shadow-sm"
      >
        <div
          v-if="avito.is_reply"
          @click="() => scrollToMessage(avito.reply_to)"
          class="mb-1 cursor-pointer rounded border-0 border-l-4 bg-surface-gray-3 p-2 text-ink-gray-5"
          :class="
            avito.reply_to_type == 'Incoming'
              ? 'border-green-500'
              : 'border-blue-400'
          "
        >
          <div
            class="mb-1 text-sm font-bold"
            :class="
              avito.reply_to_type == 'Incoming'
                ? 'text-ink-green-2'
                : 'text-ink-blue-link'
            "
          >
            {{ avito.reply_to_from || __('You') }}
          </div>
          <div class="flex flex-col gap-2 max-h-12 overflow-hidden">
            <div v-if="avito.header" class="text-base font-semibold">
              {{ avito.header }}
            </div>
            <div v-html="formatAvitoMessage(avito.reply_message)" />
            <div v-if="avito.footer" class="text-xs text-ink-gray-5">
              {{ avito.footer }}
            </div>
          </div>
        </div>
        <div class="flex gap-2 justify-between">
          <div
            class="absolute -right-0.5 -top-0.5 flex cursor-pointer gap-1 rounded-full bg-surface-white pb-2 pl-2 pr-1.5 pt-1.5 opacity-0 group-hover/message:opacity-100"
            :style="{
              background:
                'radial-gradient(circle at 50% 50%, rgba(255, 255, 255, 1) 0%, rgba(255, 255, 255, 1) 35%, rgba(238, 130, 238, 0) 100%)',
            }"
          >
            <Dropdown :options="messageOptions(avito)">
              <FeatherIcon name="chevron-down" class="size-4 text-ink-gray-5" />
            </Dropdown>
          </div>
          <div
            class="absolute -bottom-5 flex gap-1 rounded-full border bg-surface-white p-1 pb-[3px] shadow-sm"
            v-if="avito.reaction"
          >
            <div class="flex size-4 items-center justify-center">
              {{ avito.reaction }}
            </div>
          </div>
          <div
            class="flex flex-col gap-2"
            v-if="avito.message_type == 'Template'"
          >
            <div v-if="avito.header" class="text-base font-semibold">
              {{ avito.header }}
            </div>
            <div v-html="formatAvitoMessage(avito.template)" />
            <div v-if="avito.footer" class="text-xs text-ink-gray-5">
              {{ avito.footer }}
            </div>
          </div>
          <div
            v-else-if="avito.content_type == 'text'"
            v-html="formatAvitoMessage(avito.message)"
          />
          <div
            v-else-if="avito.content_type == 'button'"
            v-html="formatAvitoMessage(avito.message)"
          />
          <div v-else-if="avito.content_type == 'image'">
            <img
              :src="avito.attach"
              class="h-40 cursor-pointer rounded-md"
              @click="() => openFileInAnotherTab(avito.attach)"
            />
            <div
              v-if="!avito.message.startsWith('/files/')"
              class="mt-1.5"
              v-html="formatAvitoMessage(avito.message)"
            />
          </div>
          <div
            v-else-if="avito.content_type == 'document'"
            class="flex items-center gap-2"
          >
            <DocumentIcon
              class="size-10 cursor-pointer rounded-md text-ink-gray-4"
              @click="() => openFileInAnotherTab(avito.attach)"
            />
            <div class="text-ink-gray-5">Document</div>
          </div>
          <div
            v-else-if="avito.content_type == 'audio'"
            class="flex items-center gap-2"
          >
            <audio :src="avito.attach" controls class="cursor-pointer" />
          </div>
          <div
            v-else-if="avito.content_type == 'video'"
            class="flex-col items-center gap-2"
          >
            <video
              :src="avito.attach"
              controls
              class="h-40 cursor-pointer rounded-md"
            />
            <div
              v-if="!avito.message.startsWith('/files/')"
              class="mt-1.5"
              v-html="formatAvitoMessage(avito.message)"
            />
          </div>
          <div class="-mb-1 flex shrink-0 items-end gap-1 text-ink-gray-5">
            <Tooltip :text="formatAvitoDate(avito.creation, 'ddd, MMM D, YYYY')">
              <div class="text-ink-gray-6">
                {{ formatAvitoDate(avito.creation, 'hh:mm a') }}
              </div>
            </Tooltip>
            <div v-if="avito.type == 'Outgoing'">
              <CheckIcon
                v-if="['sent', 'Success'].includes(avito.status)"
                class="size-4"
              />
              <DoubleCheckIcon
                v-else-if="['read', 'delivered'].includes(avito.status)"
                class="size-4"
                :class="{ 'text-ink-blue-2': avito.status == 'read' }"
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
          @update:modelValue="() => reactOnMessage(avito.name, emoji)"
        >
          <Button
            @click="() => (reaction = true) && togglePopover()"
            class="rounded-full !size-6 mt-0.5"
          >
            <ReactIcon class="text-ink-gray-3" />
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
import { formatDate } from '@/utils'
import { capture } from '@/telemetry'
import { Tooltip, Dropdown, createResource } from 'frappe-ui'
import { ref } from 'vue'
import dayjs from '@/utils/dayjs'
import { usersStore } from '@/stores/users'
import { globalStore } from '@/stores/global'

const props = defineProps({
  messages: Array,
})

const list = defineModel()

function openFileInAnotherTab(url) {
  window.open(url, '_blank')
}

function formatAvitoMessage(message) {
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
    url: 'crm.api.avito.react_on_avito_message',
    params: {
      emoji,
      reply_to_name: name,
    },
    auto: true,
    onSuccess() {
      capture('avito_react_on_message')
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
          message: formatAvitoMessage(message.message)
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

function formatAvitoDate(date, format) {
  if (!date) return ''
  return dayjs(date).format(format)
}
</script>
