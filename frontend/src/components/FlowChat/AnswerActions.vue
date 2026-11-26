<template>
  <div class="flex flex-col items-start gap-3 pt-3">
    <div class="-ms-1.5 flex items-center gap-0.5">
      <Button
        variant="ghost"
        size="xs"
        :icon="copied ? 'lucide-check' : 'lucide-copy'"
        :tooltip="__('Copy')"
        @click="copyAnswer"
      />
      <Button
        variant="ghost"
        size="xs"
        icon="lucide-thumbs-up"
        :class="{
          'bg-surface-gray-3 text-ink-gray-9': askFlow.rating === 'Up',
        }"
        :tooltip="
          askFlow.rating === 'Up' ? __('Undo rating') : __('Good response')
        "
        :disabled="busy"
        @click="submit(askFlow.rating === 'Up' ? 'None' : 'Up')"
      />
      <Button
        variant="ghost"
        size="xs"
        icon="lucide-thumbs-down"
        :class="{
          'bg-surface-gray-3 text-ink-gray-9': askFlow.rating === 'Down',
        }"
        :tooltip="
          askFlow.rating === 'Down' ? __('Undo rating') : __('Bad response')
        "
        :disabled="busy"
        @click="askFlow.rating === 'Down' ? submit('None') : askWhy()"
      />
    </div>

    <div
      v-if="askFlow.replies.length"
      class="flex max-w-full flex-wrap items-center gap-1.5"
      :aria-label="
        askFlow.multiSelect ? __('Pick answers') : __('Suggested replies')
      "
    >
      <Button
        v-for="reply in askFlow.replies"
        :key="reply"
        variant="outline"
        class="min-w-0 max-w-full"
        :label="reply"
        :title="reply"
        :icon-left="pickIcon(reply)"
        @click="tap(reply)"
      />
      <Button
        v-if="askFlow.multiSelect && picked.length"
        variant="solid"
        icon-right="lucide-arrow-up"
        :label="__('Send')"
        @click="sendPicked"
      />
    </div>
  </div>
</template>

<script setup>
import { Button, dialog, toast } from 'frappe-ui'
import { ref } from 'vue'
import { askFlow, rate } from './askFlow'

const emit = defineEmits(['send'])

const copied = ref(false)
const busy = ref(false)
const picked = ref([])

async function copyAnswer() {
  await navigator.clipboard.writeText(askFlow.answer)
  copied.value = true
  setTimeout(() => (copied.value = false), 1500)
}

// A thumbs-down comment becomes agent memory, so it is asked for, as Flow does.
function askWhy() {
  dialog.prompt({
    title: __('What went wrong?'),
    fields: [
      {
        name: 'comment',
        type: 'textarea',
        label: __('Feedback'),
        placeholder: __('What went wrong? How should it respond instead?'),
      },
    ],
    confirmLabel: __('Submit'),
    onConfirm: ({ values }) => submit('Down', (values.comment || '').trim()),
  })
}

async function submit(rating, comment = '') {
  if (busy.value) return
  busy.value = true
  try {
    const result = await rate(rating, comment)
    if (result?.memory)
      toast.success(__('Saved to memory: Flow uses it in your chats.'))
  } catch (error) {
    toast.error(error?.messages?.[0] || __('Could not save feedback'))
  } finally {
    busy.value = false
  }
}

function pickIcon(reply) {
  if (!askFlow.multiSelect) return undefined
  return picked.value.includes(reply) ? 'lucide-square-check' : 'lucide-square'
}

function tap(reply) {
  if (!askFlow.multiSelect) return emit('send', reply)
  picked.value = picked.value.includes(reply)
    ? picked.value.filter((item) => item !== reply)
    : [...picked.value, reply]
}

function sendPicked() {
  const replies = askFlow.replies.filter((reply) =>
    picked.value.includes(reply),
  )
  picked.value = []
  emit('send', replies.join(', '))
}
</script>
