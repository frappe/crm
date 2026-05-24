<template>
  <div class="flex flex-col h-full px-3 sm:px-10 py-5">
    <!-- No evaluation template configured -->
    <div
      v-if="!evaluationTemplate"
      class="flex flex-1 flex-col items-center justify-center gap-3 text-ink-gray-5"
    >
      <ClipboardIcon class="h-10 w-10" />
      <p class="text-base font-medium text-ink-gray-7">
        {{ __('No Evaluation template found for lead') + ' ' + docname }}
      </p>
    </div>

    <!-- Loading -->
    <div
      v-else-if="evaluationData.loading"
      class="flex flex-1 flex-col items-center justify-center gap-3 text-ink-gray-4"
    >
      <LoadingIndicator class="h-6 w-6" />
      <span class="text-xl font-medium">{{ __('Loading...') }}</span>
    </div>

    <!-- Evaluation form -->
    <div v-else-if="evaluationData.data" class="space-y-6 pb-6">
      <!-- Header -->
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-lg font-semibold text-ink-gray-9">
            {{ evaluationData.data.quiz.title }}
          </h2>
          <p class="text-sm text-ink-gray-5 mt-0.5">
            {{ __('Questions:') + ' ' + evaluationData.data.questions.length }}
          </p>
        </div>
        <div class="flex items-center gap-2">
          <div
            v-if="existingSubmission && evaluationData.data.submission_score"
            class="flex items-center gap-1.5 rounded-md bg-surface-gray-2 px-3 py-1.5 text-sm"
          >
            <span class="text-ink-gray-5">{{ __('Score:') }}</span>
            <span class="font-semibold text-ink-gray-9">
              {{ evaluationData.data.submission_score.score }}
              /
              {{ evaluationData.data.submission_score.score_out_of }}
            </span>
            <span class="text-ink-gray-5 ml-1">
              ({{ Math.round(evaluationData.data.submission_score.percentage) }}%)
            </span>
          </div>
          <Badge
            v-if="existingSubmission"
            :label="__('Saved')"
            theme="green"
            variant="subtle"
          >
            <template #prefix>
              <CheckCircleIcon class="h-3 w-3 mr-1 text-ink-green-3" />
            </template>
          </Badge>
          <Button
            variant="solid"
            :loading="saving"
            :disabled="!hasAnswers"
            @click="saveEvaluation"
          >
            {{ existingSubmission ? __('Update Evaluation') : __('Save Evaluation') }}
          </Button>
        </div>
      </div>

      <!-- Questions -->
      <div
        v-for="(question, idx) in evaluationData.data.questions"
        :key="question.name"
        class="rounded-lg border border-outline-gray-modals bg-surface-white p-5 space-y-3"
      >
        <!-- Question text and number -->
        <div class="flex items-start justify-between gap-2">
          <div>
            <span class="text-xs font-medium text-ink-gray-5 uppercase tracking-wide">
              {{ __('Q') + (idx + 1) }}
            </span>
            <div
              class="mt-1 font-medium text-ink-gray-9 leading-snug"
              v-html="question.question"
            />
          </div>
          <span
            v-if="question.marks"
            class="shrink-0 text-xs font-semibold text-ink-gray-5 bg-surface-gray-2 rounded px-2 py-0.5"
          >
            {{ question.marks }} {{ question.marks == 1 ? __('mark') : __('marks') }}
          </span>
        </div>

        <!-- Choice question -->
        <div v-if="question.type === 'Choices'" class="space-y-2">
          <label
            v-for="n in 4"
            v-show="question[`option_${n}`]"
            :key="n"
            class="flex items-center gap-3 rounded-md bg-surface-gray-2 px-3 py-2.5 cursor-pointer hover:bg-surface-gray-3 transition-colors"
            :class="{
              'ring-2 ring-outline-blue-3 bg-surface-blue-1':
                question.multiple
                  ? selectedAnswers[question.name]?.includes(question[`option_${n}`])
                  : selectedAnswers[question.name] === question[`option_${n}`],
            }"
          >
            <input
              v-if="!question.multiple"
              type="radio"
              :name="question.name"
              :value="question[`option_${n}`]"
              v-model="selectedAnswers[question.name]"
              class="w-3.5 h-3.5 text-ink-blue-3 focus:ring-outline-blue-3"
            />
            <input
              v-else
              type="checkbox"
              :value="question[`option_${n}`]"
              :checked="selectedAnswers[question.name]?.includes(question[`option_${n}`])"
              @change="toggleCheckbox(question.name, question[`option_${n}`])"
              class="w-3.5 h-3.5 text-ink-blue-3 rounded-sm focus:ring-outline-blue-3"
            />
            <span class="text-sm text-ink-gray-9" v-html="question[`option_${n}`]" />
          </label>
        </div>

        <!-- Open Ended / User Input question -->
        <div v-else>
          <FormControl
            type="textarea"
            :placeholder="__('Write your answer here...')"
            :rows="3"
            v-model="selectedAnswers[question.name]"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, reactive } from 'vue'
import {
  Button,
  Badge,
  FormControl,
  LoadingIndicator,
  createResource,
  call,
  toast,
} from 'frappe-ui'
import CheckCircleIcon from '@/components/Icons/CheckCircleIcon.vue'
import ClipboardIcon from '@/components/Icons/NoteIcon.vue'

const props = defineProps({
  docname: { type: String, required: true },
  doc: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['updateField'])

const saving = ref(false)
const selectedAnswers = reactive({})

// Local copy of submission name so that after creation we track it without
// needing the parent to immediately reload
const localSubmission = ref(null)

const evaluationTemplate = computed(() => props.doc?.custom_evaluation_template || null)
const existingSubmission = computed(
  () => localSubmission.value || props.doc?.custom_submission || null,
)

// Load evaluation data (questions + existing answers if submission exists)
const evaluationData = createResource({
  url: 'quiz_crm.quiz_crm.api.get_evaluation_data',
  makeParams() {
    return {
      quiz_name: evaluationTemplate.value,
      submission_name: existingSubmission.value || null,
    }
  },
  auto: false,
  onSuccess(data) {
    populateAnswers(data)
  },
})

function populateAnswers(data) {
  const answers = data.answers || {}
  for (const question of data.questions) {
    if (answers[question.name] !== undefined) {
      if (question.type === 'Choices' && question.multiple) {
        // Stored as comma-separated string
        const raw = answers[question.name]
        selectedAnswers[question.name] = raw
          ? raw
              .split(',')
              .map((s) => s.trim())
              .filter(Boolean)
          : []
      } else {
        selectedAnswers[question.name] = answers[question.name] ?? ''
      }
    } else {
      selectedAnswers[question.name] = question.type === 'Choices' && question.multiple ? [] : ''
    }
  }
}

// Watch for the template to change and reload
watch(
  evaluationTemplate,
  (val) => {
    if (val) evaluationData?.reload()
  },
  { immediate: true },
)

watch(
  existingSubmission,
  () => {
    if (evaluationTemplate.value) evaluationData.reload()
  },
)

const hasAnswers = computed(() => {
  return Object.values(selectedAnswers).some((v) =>
    Array.isArray(v) ? v.length > 0 : v && v.trim?.() !== '',
  )
})

function toggleCheckbox(questionName, optionValue) {
  if (!selectedAnswers[questionName]) {
    selectedAnswers[questionName] = []
  }
  const idx = selectedAnswers[questionName].indexOf(optionValue)
  if (idx >= 0) {
    selectedAnswers[questionName].splice(idx, 1)
  } else {
    selectedAnswers[questionName].push(optionValue)
  }
}

function buildAnswersList() {
  const questions = evaluationData.data?.questions || []
  return questions.map((q) => {
    let answer = selectedAnswers[q.name]
    if (Array.isArray(answer)) {
      answer = answer.join(', ')
    }
    return {
      question_name: q.name,
      question: q.question,
      answer: answer ?? '',
    }
  })
}

async function saveEvaluation() {
  saving.value = true
  try {
    const answers = buildAnswersList()
    const result = await call('quiz_crm.quiz_crm.api.save_evaluation', {
      quiz_name: evaluationTemplate.value,
      lead_name: props.docname,
      answers: JSON.stringify(answers),
      submission_name: existingSubmission.value || null,
    })

    if (!localSubmission.value && !props.doc?.custom_submission && result?.submission) {
      localSubmission.value = result.submission
      // Notify parent to update the lead doc fields
      emit('updateField', 'custom_submission', result.submission)
    }
    // Reload to get updated score from the saved submission
    evaluationData.reload()
    toast.success(existingSubmission.value ? __('Evaluation updated') : __('Evaluation saved'))
  } catch (err) {
    toast.error(err?.messages?.[0] || __('Error saving evaluation'))
  } finally {
    saving.value = false
  }
}
</script>
