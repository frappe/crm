<template>
  <!-- Empty + editable -->
  <div
    v-if="!value && !disabled"
    :class="[containerClasses, 'cursor-pointer']"
    @click="showUploader = true"
  >
    <FeatherIcon name="paperclip" :class="[iconClasses, 'text-ink-gray-5']" />
    <span class="whitespace-nowrap text-ink-gray-4">{{
      __('Attach file…')
    }}</span>
  </div>

  <!-- Empty + disabled -->
  <div v-else-if="!value && disabled" :class="containerClasses">
    <span class="text-ink-gray-4">—</span>
  </div>

  <!-- Has value -->
  <div v-else :class="[containerClasses, '!pr-1']">
    <FeatherIcon name="paperclip" :class="[iconClasses, 'text-ink-gray-7']" />
    <Tooltip class="min-w-0 flex-1">
      <template #body>
        <div v-if="isImage" class="overflow-hidden rounded shadow-xl">
          <img
            :src="value"
            class="max-h-40 max-w-xs object-contain"
            :alt="filename"
          />
        </div>
        <div
          v-else
          class="rounded bg-surface-gray-7 px-2 py-1.5 text-xs text-ink-white shadow-xl"
        >
          {{ filename }}
        </div>
      </template>
      <a
        class="block min-w-0 truncate text-ink-gray-8 hover:underline"
        :href="value"
        target="_blank"
        rel="noopener noreferrer"
      >
        {{ filename }}
      </a>
    </Tooltip>
    <button
      v-if="!disabled"
      class="ml-auto flex h-5 w-5 shrink-0 items-center justify-center rounded text-ink-gray-4 hover:bg-surface-gray-2 hover:text-ink-gray-7 dark:hover:bg-surface-gray-4"
      :title="__('Clear')"
      @click.prevent="clearAttachment"
    >
      <FeatherIcon name="x" class="h-3 w-3" />
    </button>
  </div>

  <FilesUploader
    v-if="showUploader"
    v-model="showUploader"
    :doctype="doctype"
    :docname="docname"
    :fieldname="fieldname"
    :options="uploaderOptions"
    @after="onAfterUpload"
  />
</template>

<script setup>
import { ref, computed, useAttrs } from 'vue'
import { Tooltip, FeatherIcon } from 'frappe-ui'
import FilesUploader from '@/components/FilesUploader/FilesUploader.vue'

defineOptions({ inheritAttrs: false })

const IMAGE_EXTENSIONS =
  /\.(jpe?g|png|gif|webp|svg|avif|bmp|ico|tiff?)(\?.*)?$/i

const props = defineProps({
  value: { type: String, default: null },
  doctype: { type: String, default: '' },
  docname: { type: String, default: '' },
  fieldname: { type: String, default: '' },
  disabled: { type: Boolean, default: false },
  imageOnly: { type: Boolean, default: false },
})

const emit = defineEmits(['change'])
const attrs = useAttrs()

const showUploader = ref(false)

// Mirror frappe-ui TextInput size classes
const sizeClasses = computed(
  () =>
    ({
      sm: 'h-7 text-base rounded',
      md: 'h-8 text-base rounded',
      lg: 'h-10 text-lg rounded-md',
      xl: 'h-10 text-xl rounded-md',
    })[attrs.size || 'sm'],
)

// Mirror frappe-ui TextInput padding by size
const paddingClasses = computed(
  () =>
    ({
      sm: 'px-2',
      md: 'px-2.5',
      lg: 'px-3',
      xl: 'px-3',
    })[attrs.size || 'sm'],
)

// Mirror frappe-ui TextInput variant + disabled classes
const variantClasses = computed(() => {
  if (props.disabled) {
    return [
      'border bg-surface-gray-1 text-ink-gray-5',
      (attrs.variant || 'subtle') === 'outline'
        ? 'border-outline-gray-2'
        : 'border-transparent',
    ].join(' ')
  }
  return {
    subtle:
      'border border-[--surface-gray-2] bg-surface-gray-2 hover:border-outline-gray-modals hover:bg-surface-gray-3',
    outline:
      'border border-outline-gray-2 bg-surface-white hover:border-outline-gray-3 hover:shadow-sm',
    ghost: 'border-0',
  }[attrs.variant || 'subtle']
})

const containerClasses = computed(() =>
  [
    'flex w-full items-center gap-1.5 overflow-hidden transition-colors',
    sizeClasses.value,
    paddingClasses.value,
    variantClasses.value,
    attrs.class,
  ]
    .filter(Boolean)
    .join(' '),
)

const iconClasses = computed(
  () =>
    ({
      sm: 'h-3 w-3 shrink-0',
      md: 'h-3.5 w-3.5 shrink-0',
      lg: 'h-4 w-4 shrink-0',
      xl: 'h-4 w-4 shrink-0',
    })[attrs.size || 'sm'],
)

const uploaderOptions = computed(() => {
  return {
    folder: 'Home/Attachments',
    allowMultiple: false,
    restrictions: {
      maxNumberOfFiles: 1,
      ...(props.imageOnly ? { allowedFileTypes: ['image/*'] } : {}),
    },
  }
})

const filename = computed(() => {
  if (!props.value) return ''
  const clean = props.value.split('?')[0].split('#')[0]
  const raw = clean.split('/').pop() || props.value
  try {
    return decodeURIComponent(raw)
  } catch {
    return raw
  }
})

const isImage = computed(() => IMAGE_EXTENSIONS.test(props.value || ''))

function onAfterUpload(uploadedFiles) {
  if (uploadedFiles && uploadedFiles.length) {
    emit('change', uploadedFiles[0].file_url)
  }
}

function clearAttachment() {
  emit('change', null)
}
</script>
