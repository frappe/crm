<template>
  <form
    v-if="resource.data?.available"
    :aria-label="__('Ask Flow')"
    class="flex flex-col gap-2.5 rounded-4 border border-outline-gray-2 bg-surface-elevation-2 p-3"
    @submit.prevent="send(message)"
  >
    <label for="ask-flow" class="sr-only">{{ __('Ask Flow') }}</label>
    <textarea
      id="ask-flow"
      v-model="message"
      rows="3"
      class="w-full resize-none border-0 bg-transparent p-1 text-p-base text-ink-gray-8 placeholder:text-ink-gray-4 focus:ring-0"
      :placeholder="placeholder"
      @keydown.enter.exact.prevent="send(message)"
    />
    <div class="flex items-end gap-2.5">
      <div class="flex min-w-0 flex-1 flex-wrap gap-2">
        <Button
          v-for="chip in chips"
          :key="chip"
          :label="chip"
          iconLeft="lucide-sparkles"
          :disabled="sending"
          @click="send(chip)"
        />
      </div>
      <span
        class="flex h-7 shrink-0 items-center gap-1 text-sm text-ink-gray-5"
      >
        <span aria-hidden="true" class="lucide-lock size-3.5" />
        {{ __('Private') }}
      </span>
      <Button
        type="submit"
        variant="solid"
        icon="lucide-arrow-up"
        :aria-label="__('Send to Flow')"
        :loading="sending"
        :disabled="!message.trim()"
      />
    </div>
  </form>
</template>
<script setup>
import { askFlowChips, flowSessionUrl } from '@/utils/brief'
import { call, toast } from 'frappe-ui'
import { computed, ref } from 'vue'

const props = defineProps({
  resource: { type: Object, required: true },
  team: { type: Boolean, default: false },
})

const message = ref('')
const sending = ref(false)

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

async function send(text) {
  if (!text.trim() || sending.value) return
  sending.value = true
  try {
    const { session } = await call('crm.api.home.ask_flow', { message: text })
    window.location.assign(flowSessionUrl(session))
  } catch (error) {
    toast.error(error.messages?.[0] || __('Could not start Flow'))
    sending.value = false
  }
}
</script>
