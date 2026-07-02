<template>
  <div class="relative mx-auto w-full max-w-2xl">
    <div class="flex min-h-[22rem] flex-col">
      <div class="flex items-center justify-between">
        <span class="text-xs font-medium uppercase tracking-wide text-ink-gray-5">
          {{ labels.progress(current + 1, total) }}
        </span>
        <span class="text-xs font-medium uppercase tracking-wide text-ink-gray-5">
          {{ labels.complete(percent) }}
        </span>
      </div>
      <div class="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-surface-gray-3">
        <div
          class="h-full rounded-full bg-surface-gray-10 transition-all duration-500 ease-out"
          :style="{ width: `${percent}%` }"
        />
      </div>

      <Transition name="q-fade" mode="out-in" @after-enter="focusQuestion">
        <fieldset
          :key="question.key"
          tabindex="-1"
          class="mt-6 mx-0 min-w-0 border-0 p-0 focus:outline-none"
        >
          <legend class="p-0 text-xl font-semibold text-ink-gray-9">
            {{ question.title }}
          </legend>
          <p v-if="question.multiple" class="mt-1 text-sm text-ink-gray-5">
            {{ labels.selectMultiple }}
          </p>
          <div class="mt-5 flex flex-wrap gap-2.5">
            <label
              v-for="option in question.options"
              :key="String(option.value)"
              class="inline-flex cursor-pointer items-center rounded-full border px-4 py-2 text-sm transition-colors focus-within:ring-2 focus-within:ring-outline-gray-3 focus-within:ring-offset-1"
              :class="
                isSelected(option)
                  ? 'border-transparent bg-surface-gray-10 text-ink-white'
                  : 'border-outline-gray-2 bg-surface-white text-ink-gray-8 hover:border-outline-gray-3 hover:bg-surface-gray-2'
              "
            >
              <input
                :type="question.multiple ? 'checkbox' : 'radio'"
                class="sr-only"
                :name="question.key"
                :value="option.value"
                :checked="isSelected(option)"
                @change="select(option)"
              />
              {{ option.label }}
            </label>
          </div>
        </fieldset>
      </Transition>
    </div>

    <button
      v-if="current > 0"
      type="button"
      class="absolute right-full top-1/3 mr-4 -translate-y-1/2 inline-flex items-center gap-1 rounded-lg border border-outline-gray-2 bg-surface-white p-1.5 text-sm font-medium text-ink-gray-7 transition-colors hover:border-outline-gray-3 hover:bg-surface-gray-2 focus:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3 focus-visible:ring-offset-1"
      :aria-label="labels.back"
      @click="back"
    >
      <LucideChevronLeft class="size-4" />
    </button>

    <button
      v-if="canProceed && current < total - 1"
      type="button"
      class="absolute left-full top-1/3 ml-4 -translate-y-1/2 inline-flex items-center gap-1 rounded-lg border border-outline-gray-2 bg-surface-white p-1.5 text-sm font-medium text-ink-gray-7 transition-colors hover:border-outline-gray-3 hover:bg-surface-gray-2 focus:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3 focus-visible:ring-offset-1"
      :aria-label="labels.next"
      @click="next"
    >
      <LucideChevronRight class="size-4" />
    </button>

    <div class="mt-8 flex justify-center">
      <Button
        v-if="current === total - 1"
        variant="solid"
        :label="labels.finish"
        :disabled="!canProceed"
        @click="finish"
      />
    </div>

    <button
      v-if="showSkip"
      type="button"
      class="mx-auto mt-6 block text-sm text-ink-gray-5 transition-colors hover:text-ink-gray-7"
      @click="emit('skip')"
    >
      {{ labels.skip }}
    </button>
  </div>
</template>

<script setup>
import { Button } from 'frappe-ui'
import { computed, reactive, ref } from 'vue'

const props = defineProps({
  questions: {
    type: Array,
    required: true,
  },
  showSkip: {
    type: Boolean,
    default: true,
  },
  labels: {
    type: Object,
    default: () => ({}),
  },
})

const emit = defineEmits(['submit', 'skip'])

const labels = computed(() => ({
  progress: (n, total) => __('Question {0} of {1}', [n, total]),
  complete: (pct) => __('{0}% complete', [pct]),
  selectMultiple: __('Select all that apply'),
  back: __('Back to previous question'),
  next: __('Next question'),
  finish: __('Finish'),
  skip: __('Skip for now'),
  ...props.labels,
}))

const current = ref(0)
const completed = ref(false)
const answers = reactive({})

const total = computed(() => props.questions.length)
const question = computed(() => props.questions[current.value])
const percent = computed(() => {
  if (completed.value) return 100
  return total.value ? Math.floor((current.value / total.value) * 100) : 0
})

const answered = computed(() => {
  const value = answers[question.value.key]
  if (question.value.multiple) return Array.isArray(value) && value.length > 0
  return value !== undefined
})
const canProceed = computed(() => question.value.optional || answered.value)

// Single required questions auto-advance; multi/optional wait for Next/Finish.
const autoAdvance = (q) => !q.multiple && !q.optional

function isSelected(option) {
  const value = answers[question.value.key]
  if (question.value.multiple) {
    return Array.isArray(value) && value.includes(option.value)
  }
  return value === option.value
}

function select(option) {
  if (completed.value) return
  const key = question.value.key
  if (question.value.multiple) {
    const value = Array.isArray(answers[key]) ? [...answers[key]] : []
    const index = value.indexOf(option.value)
    index === -1 ? value.push(option.value) : value.splice(index, 1)
    answers[key] = value
    return
  }
  answers[key] = option.value
  if (autoAdvance(question.value) && current.value < total.value - 1) advance()
}

function advance() {
  if (current.value < total.value - 1) current.value += 1
}

function next() {
  if (!canProceed.value) return
  advance()
}

function back() {
  if (current.value > 0) current.value -= 1
}

function finish() {
  if (!canProceed.value || completed.value) return
  completed.value = true
  setTimeout(() => emit('submit', { ...answers }), 700)
}

function focusQuestion(el) {
  el.focus()
}
</script>

<style scoped>
.q-fade-enter-active,
.q-fade-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}
.q-fade-enter-from {
  opacity: 0;
  transform: translateY(6px);
}
.q-fade-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}
</style>
