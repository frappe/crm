<template>
  <div class="flex flex-col">
    <h1 class="text-2xl-semibold text-ink-gray-9">
      {{ __("You're all set") }}
    </h1>
    <p class="mt-2 text-p-base text-ink-gray-6">
      {{ __('Before you dive in, tell us how setup went.') }}
    </p>

    <fieldset class="mt-8 rounded-xl border border-outline-gray-2 p-5">
      <legend class="px-1 text-base font-medium text-ink-gray-9">
        {{ __('How easy was the setup?') }}
      </legend>
      <div class="mt-2 flex items-center justify-center gap-3">
        <span class="text-sm text-ink-gray-5">{{ __('Difficult') }}</span>
        <div
          class="flex gap-1"
          role="radiogroup"
          :aria-label="__('Setup rating')"
        >
          <button
            v-for="value in 5"
            :key="value"
            type="button"
            role="radio"
            class="rounded p-1 transition-colors hover:text-ink-amber-5"
            :class="value <= rating ? 'text-ink-amber-5' : 'text-ink-gray-4'"
            :aria-checked="value === rating"
            :aria-label="__('{0} out of 5', [value])"
            @click="rating = value"
          >
            <LucideStar
              class="size-6"
              :class="{ 'fill-current': value <= rating }"
            />
          </button>
        </div>
        <span class="text-sm text-ink-gray-5">{{ __('Easy') }}</span>
      </div>
      <FormControl
        v-model="comment"
        class="mt-5"
        type="textarea"
        :rows="3"
        :label="__('Anything we could do better? (optional)')"
        :placeholder="__('Share what was confusing or missing')"
      />
    </fieldset>

    <Button
      variant="solid"
      size="md"
      class="mt-auto"
      :label="__('Go to CRM')"
      :loading="finishing"
      @click="finish"
    />
  </div>
</template>

<script setup>
import LucideStar from '~icons/lucide/star'
import { Button, FormControl } from 'frappe-ui'
import { ref } from 'vue'

const emit = defineEmits(['finish'])

const rating = ref(0)
const comment = ref('')
const finishing = ref(false)

function finish() {
  finishing.value = true
  emit('finish', {
    rating: rating.value || null,
    comment: comment.value.trim() || null,
  })
}
</script>
