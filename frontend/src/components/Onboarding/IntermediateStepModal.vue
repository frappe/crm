<template>
  <Dialog v-model="show" :options="options">
    <template #boday-header>
      <slot name="body-header"></slot>
    </template>
    <template #body-content>
      <slot>
        <div class="flex flex-col gap-2 text-ink-gray-9 text-base">
          <div v-if="currentStep.message">{{ currentStep.message }}</div>
          <video
            v-if="currentStep.videoURL"
            class="w-full rounded"
            controls
            autoplay
            muted
          >
            <source :src="currentStep.videoURL" type="video/mp4" />
            {{ __('Your browser does not support the video tag.') }}
          </video>
        </div>
      </slot>
    </template>
    <template #actions>
      <slot name="actions"></slot>
    </template>
  </Dialog>
</template>

<script setup>
import { Dialog } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  currentStep: {
    type: Object,
    default: () => ({
      title: 'Title',
      message: 'Message',
      videoURL: '',
      buttonLabel: 'Button Label',
      onClick: () => {},
    }),
  },
  dialogOptions: {
    type: Object,
    default: () => ({}),
  },
})

const show = defineModel({
  type: Boolean,
  default: false,
})

const options = computed(() => {
  if (props.dialogOptions && Object.keys(props.dialogOptions).length) {
    return props.dialogOptions
  }

  return {
    title: props.currentStep.title,
    size: '2xl',
    actions: [
      {
        label: props.currentStep.buttonLabel,
        variant: 'solid',
        onClick: props.currentStep.onClick,
      },
    ],
  }
})
</script>
