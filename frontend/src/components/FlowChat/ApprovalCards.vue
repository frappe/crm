<template>
  <div class="flex flex-col gap-3 pt-4">
    <div
      v-if="calls.length > 1 && !hasCode && undecided.length"
      class="flex items-center justify-between text-sm text-ink-gray-6"
    >
      {{ __('Flow wants to make {0} changes', [calls.length]) }}
      <Button
        variant="solid"
        :label="__('Approve all')"
        :disabled="busy"
        @click="act(approveAll)"
      />
    </div>

    <div
      v-for="item in calls"
      :key="item.call.id"
      class="overflow-hidden rounded-4 border border-outline-gray-2"
    >
      <div
        class="flex items-center justify-between gap-3 px-3 py-2.5 text-base"
      >
        <span class="min-w-0 truncate font-medium text-ink-gray-9">
          {{ item.summary.title }}
        </span>
        <span class="shrink-0 text-sm" :class="stateOf(item.call).class">
          {{ stateOf(item.call).label }}
        </span>
      </div>

      <p
        v-if="item.summary.code"
        class="border-t border-outline-gray-1 px-3 py-2 text-sm text-ink-gray-7"
      >
        {{ item.summary.description || __('Flow wants to run code.') }}
      </p>
      <table v-else class="w-full border-collapse text-sm">
        <tr
          v-for="(row, index) in item.summary.rows"
          :key="index"
          class="border-t border-outline-gray-1"
        >
          <td class="w-1/3 px-3 py-1.5 align-top text-ink-gray-5">
            {{ row.label }}
          </td>
          <td
            class="whitespace-pre-wrap break-words px-3 py-1.5 align-top text-ink-gray-8"
          >
            <span class="line-clamp-4">{{ row.value }}</span>
          </td>
        </tr>
      </table>

      <div
        v-if="!hasCode && !(item.call.id in approval.answers)"
        class="flex items-center gap-1.5 border-t border-outline-gray-1 px-3 py-2"
      >
        <Button
          variant="solid"
          :label="__('Approve')"
          :disabled="busy"
          @click="act(() => answerApproval(item.call.id, 'Approve'))"
        />
        <Button
          :label="__('Deny')"
          :disabled="busy"
          @click="act(() => answerApproval(item.call.id, 'Deny'))"
        />
        <Button
          variant="ghost"
          :label="__('Ask for changes')"
          :disabled="busy"
          @click="emit('ask-changes', item.call.id)"
        />
      </div>
    </div>

    <div
      v-if="hasCode"
      class="flex items-center gap-3 rounded-4 bg-surface-amber-2 px-3 py-2.5 text-base text-ink-amber-6"
    >
      <span class="flex-1">{{ __('Review code in Flow before it runs') }}</span>
      <Button
        variant="solid"
        :label="__('Review in Flow')"
        @click="emit('review')"
      />
    </div>
  </div>
</template>

<script setup>
import { Button, toast } from 'frappe-ui'
import { computed, ref } from 'vue'
import { answerApproval, approveAll, askFlow } from './askFlow'
import { summarizeCall } from './approvalSummary'

const emit = defineEmits(['ask-changes', 'review'])

const busy = ref(false)

const approval = computed(() => askFlow.approval)
const calls = computed(() =>
  approval.value.calls.map((call) => ({ call, summary: summarizeCall(call) })),
)
// Code is reviewed in Flow, so a batch holding any is answered there whole.
const hasCode = computed(() => calls.value.some((item) => item.summary.code))
const undecided = computed(() =>
  approval.value.calls.filter((call) => !(call.id in approval.value.answers)),
)

const ANSWERED = {
  Approve: { label: 'Approved', class: 'text-ink-green-6' },
  Deny: { label: 'Denied', class: 'text-ink-red-6' },
}

function stateOf(call) {
  const answer = approval.value.answers[call.id]
  if (answer === undefined)
    return { label: __('Needs your approval'), class: 'text-ink-amber-6' }
  const known = ANSWERED[answer]
  return known
    ? { label: __(known.label), class: known.class }
    : { label: __('Changes asked'), class: 'text-ink-gray-6' }
}

async function act(action) {
  if (busy.value) return
  busy.value = true
  try {
    await action()
  } catch (error) {
    toast.error(
      error?.messages?.[0] || __('Could not send your answer to Flow'),
    )
  } finally {
    busy.value = false
  }
}
</script>
