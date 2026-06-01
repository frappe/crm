<template>
  <!-- Dialog/Button are registered globally in main.js, so no import needed. -->
  <Dialog v-model="show" :options="{ title, size: 'lg' }">
    <template #body-content>
      <!-- media preview -->
      <div class="flex justify-center rounded-md bg-surface-gray-2 p-2">
        <img
          v-if="type === 'image'"
          :src="file?.file_url"
          class="max-h-80 rounded-md object-contain"
        />
        <video
          v-else-if="type === 'video'"
          :src="file?.file_url"
          controls
          class="max-h-80 rounded-md"
        />
        <div v-else class="flex w-full items-center gap-2 p-2">
          <DocumentIcon class="size-10 flex-shrink-0 text-ink-gray-4" />
          <div class="flex min-w-0 flex-col">
            <div class="truncate text-ink-gray-8">{{ file?.file_name }}</div>
            <div v-if="file?.file_size" class="text-sm text-ink-gray-5">
              {{ convertSize(file.file_size) }}
            </div>
          </div>
        </div>
      </div>

      <!-- caption (negative bottom margin trims the Dialog body's default pb-6) -->
      <div class="-mb-4 mt-3 flex items-end gap-2">
        <IconPicker
          v-slot="{ togglePopover }"
          v-model="emoji"
          @update:modelValue="() => (caption += emoji)"
        >
          <SmileIcon
            class="size-5 cursor-pointer text-ink-gray-4"
            @click="togglePopover"
          />
        </IconPicker>
        <Textarea
          ref="captionRef"
          v-model="caption"
          class="w-full"
          :rows="1"
          :placeholder="__('Add a caption...')"
          @keydown.enter.stop="onEnter"
        />
      </div>
    </template>
    <template #actions>
      <div class="flex justify-end gap-2">
        <Button :label="__('Cancel')" @click="show = false" />
        <Button
          :label="__('Send')"
          variant="solid"
          :loading="loading"
          @click="submit"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import IconPicker from '@/components/IconPicker.vue'
import SmileIcon from '@/components/Icons/SmileIcon.vue'
import DocumentIcon from '@/components/Icons/DocumentIcon.vue'
import { convertSize } from '@/utils'
import { Textarea } from 'frappe-ui'
import { computed, nextTick, ref, watch } from 'vue'

const props = defineProps({
  file: { type: Object, default: () => ({}) },
  type: { type: String, default: 'image' },
  loading: { type: Boolean, default: false },
})

const show = defineModel({ type: Boolean })
const emit = defineEmits(['send'])

const caption = ref('')
const emoji = ref('')
const captionRef = ref(null)

const title = computed(() => {
  if (props.type === 'image') return __('Send an image')
  if (props.type === 'video') return __('Send a video')
  return __('Send a file')
})

function submit() {
  emit('send', caption.value)
  show.value = false
}

function onEnter(event) {
  if (event.shiftKey) return
  submit()
}

// Reset the caption each time the dialog opens, and focus the input.
watch(show, (value) => {
  if (value) {
    caption.value = ''
    nextTick(() => captionRef.value?.el?.focus())
  }
})
</script>
