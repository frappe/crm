<template>
  <div>
    <div v-if="videoUrl" class="mb-6">
      <div class="aspect-video bg-surface-gray-2 rounded-xl overflow-hidden flex items-center justify-center">
        <iframe
          v-if="isValidUrl(videoUrl)"
          :src="embedUrl"
          class="w-full h-full"
          frameborder="0"
          allowfullscreen
        />
        <div v-else class="flex flex-col items-center gap-2 text-ink-gray-5">
          <VideoIcon class="w-8 h-8" />
          <a :href="videoUrl" target="_blank" class="text-p-sm underline">{{ __('Open Video') }}</a>
        </div>
      </div>
    </div>
    <div v-if="content" class="prose prose-sm max-w-none text-ink-gray-7 leading-relaxed" v-html="content" />
  </div>
</template>

<script setup>
import VideoIcon from '~icons/lucide/video'

const props = defineProps({
  content: { type: String, default: '' },
  videoUrl: { type: String, default: '' },
})

const embedUrl = computed(() => {
  if (!props.videoUrl) return ''
  const url = props.videoUrl
  // YouTube
  const ytMatch = url.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]+)/)
  if (ytMatch) return `https://www.youtube.com/embed/${ytMatch[1]}`
  // Vimeo
  const vimeoMatch = url.match(/vimeo\.com\/(\d+)/)
  if (vimeoMatch) return `https://player.vimeo.com/video/${vimeoMatch[1]}`
  return url
})

import { computed } from 'vue'

function isValidUrl(str) {
  try { return Boolean(new URL(str)) } catch { return false }
}
</script>
