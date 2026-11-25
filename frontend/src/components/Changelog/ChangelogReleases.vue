<template>
  <div class="space-y-10">
    <section
      v-for="release in changelogReleases"
      :key="release.version ?? 'unreleased'"
    >
      <div class="mb-4 flex items-baseline gap-2 text-sm text-ink-gray-5">
        <span class="text-sm-medium text-ink-gray-7">
          {{ release.version ? `v${release.version}` : __('Next release') }}
        </span>
        <span v-if="release.date">{{ formatDate(release.date) }}</span>
      </div>

      <article
        v-for="entry in release.entries"
        :key="entry.id"
        class="mb-8 last:mb-0"
      >
        <h3 class="mb-3 text-lg-semibold text-ink-gray-9">
          {{ entry.title }}
        </h3>
        <video
          v-if="entry.media?.kind === 'video'"
          :src="mediaUrl(entry.media)"
          class="mb-4 w-full rounded-7 border bg-surface-gray-1"
          :aria-label="entry.title"
          autoplay
          loop
          muted
          playsinline
        />
        <img
          v-else-if="entry.media"
          :src="mediaUrl(entry.media)"
          :alt="entry.title"
          class="mb-4 w-full rounded-7 border bg-surface-gray-1"
          loading="lazy"
        />
        <div
          class="prose prose-sm max-w-none text-ink-gray-7 prose-p:my-3"
          v-html="marked.parse(entry.body, { async: false })"
        />
      </article>
    </section>
  </div>
</template>

<script setup>
import { dayjsLocal, useColorScheme } from 'frappe-ui'
import { marked } from 'marked'
import { changelogReleases } from '@/data/changelog'

const { resolvedColorScheme } = useColorScheme()

function mediaUrl(media) {
  return resolvedColorScheme.value === 'dark' && media.darkUrl
    ? media.darkUrl
    : media.url
}

function formatDate(date) {
  return dayjsLocal(date).format('D MMM YYYY')
}
</script>
