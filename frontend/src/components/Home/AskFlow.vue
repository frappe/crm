<template>
  <div
    v-if="resource.data?.available && hasChat"
    class="rounded-4 border border-outline-gray-2 bg-surface-elevation-2"
  >
    <FlowChatCard surface="home" @new-chat="focusBox" />
  </div>
  <form
    v-else-if="resource.data?.available"
    :aria-label="__('Ask Flow')"
    class="flex flex-col gap-2.5 rounded-4 border border-outline-gray-2 bg-surface-elevation-2 p-3"
    @submit.prevent="send(message)"
  >
    <label for="ask-flow" class="sr-only">{{ __('Ask Flow') }}</label>
    <textarea
      id="ask-flow"
      ref="boxRef"
      v-model="message"
      rows="3"
      class="w-full resize-none border-0 bg-transparent p-1 text-p-base text-ink-gray-8 placeholder:text-ink-gray-4 focus:ring-0"
      :placeholder="placeholder"
      @keydown.enter="sendOnEnter"
    />
    <div class="flex items-end gap-2.5">
      <div class="flex min-w-0 flex-1 flex-wrap gap-2">
        <Button
          v-for="chip in chips"
          :key="chip"
          :label="chip"
          iconLeft="lucide-sparkles"
          @click="sendChip(chip)"
        />
      </div>
      <ChatHistory />
      <Button
        type="submit"
        variant="solid"
        icon="lucide-arrow-up"
        :aria-label="__('Send to Flow')"
        :disabled="!message.trim()"
      />
    </div>
  </form>
</template>
<script setup>
import { askFlowChips } from '@/utils/brief'
import { Button } from 'frappe-ui'
import { computed, nextTick, ref } from 'vue'
import ChatHistory from '@/components/FlowChat/ChatHistory.vue'
import FlowChatCard from '@/components/FlowChat/FlowChatCard.vue'
import { ask, askFlow } from '@/components/FlowChat/askFlow'

const props = defineProps({
  resource: { type: Object, required: true },
  team: { type: Boolean, default: false },
})

const message = ref('')
const boxRef = ref(null)

// The chat open here is the one the command palette shows too.
const hasChat = computed(() => Boolean(askFlow.session || askFlow.question))

const placeholder = computed(() =>
  props.team
    ? __(
        'What do you want to get done? For example: who on my team needs help this week',
      )
    : __(
        'What do you want to get done? For example: draft replies for everyone waiting on me',
      ),
)

const chips = computed(() =>
  askFlowChips({
    team: props.team,
    repliesWaiting: props.resource.data?.replies_waiting,
  }),
)

function sendChip(chip) {
  send(chip)
}

function sendOnEnter(event) {
  if (event.shiftKey || event.isComposing) return
  event.preventDefault()
  send(message.value)
}

// The box turns into the answer; ask reports its own failure in the answer card.
function send(text) {
  if (!text.trim()) return
  ask(text)
  message.value = ''
}

function focusBox() {
  nextTick(() => boxRef.value?.focus())
}
</script>
