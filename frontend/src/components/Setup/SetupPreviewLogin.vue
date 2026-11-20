<template>
  <div class="flex h-full justify-center bg-surface-base pt-[80px]">
    <div class="flex w-[360px] flex-col gap-6">
      <div class="flex flex-col items-center gap-3">
        <CRMLogo class="size-10 rounded-6" />
        <p class="text-2xl font-semibold text-ink-gray-9">
          {{ __('Login to Frappe CRM') }}
        </p>
      </div>
      <div class="flex flex-col gap-4">
        <div class="flex flex-col gap-1.5">
          <p class="text-sm text-ink-gray-5">{{ __('Email') }}</p>
          <div
            class="flex h-7 items-center rounded-4 border border-outline-gray-2 bg-surface-gray-2 px-2 text-base text-ink-gray-8"
          >
            {{ session.user }}
          </div>
        </div>
        <div class="flex flex-col gap-1.5">
          <p class="text-sm text-ink-gray-5">{{ __('Password') }}</p>
          <div
            class="flex h-7 items-center gap-[3px] rounded-4 border border-outline-gray-4 bg-surface-base px-2"
          >
            <TransitionGroup
              enter-active-class="transition duration-150 motion-reduce:transition-none"
              enter-from-class="scale-0"
            >
              <span
                v-for="n in dots"
                :key="n"
                class="size-[5px] rounded-full bg-surface-gray-8"
              />
            </TransitionGroup>
            <span
              class="ms-px h-3.5 w-px animate-pulse bg-surface-gray-9 motion-reduce:animate-none"
            />
            <span class="lucide-eye ms-auto size-4 text-ink-gray-5" />
          </div>
        </div>
        <Button
          variant="solid"
          class="mt-2 w-full"
          :label="__('Login')"
          tabindex="-1"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import CRMLogo from '@/components/Icons/CRMLogo.vue'
import { sessionStore } from '@/stores/session'
import { Button } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  state: { type: Object, required: true },
})

const session = sessionStore()
const dots = computed(() => Math.min(props.state.passwordLength || 0, 22))
</script>
