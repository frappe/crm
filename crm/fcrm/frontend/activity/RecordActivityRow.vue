<!-- An Activity row for a Task, Note or Call Log of the page's record; it opens the record. -->
<template>
	<div class="flex flex-1 flex-col text-sm leading-6 text-ink-gray-6">
		<button
			type="button"
			class="flex min-w-0 items-start gap-1.5 rounded-2 py-0.5 ps-[13px] pe-1 text-left hover:bg-surface-gray-2 focus-visible:bg-surface-gray-2 focus-visible:outline-none"
			@click="page.open(doctype, record)"
		>
			<span class="mt-1 size-4 shrink-0 text-ink-gray-5" :class="icon" aria-hidden="true" />
			<span class="min-w-0 break-words">
				<span class="font-medium text-ink-gray-8">{{ label }}</span>
				<span v-if="title" class="ms-1 text-ink-gray-7">{{ title }}</span>
				<span v-if="detail" class="ms-1 text-ink-gray-5">· {{ detail }}</span>
			</span>
			<TimeAgo :timestamp="timestamp" class="ml-auto shrink-0 text-sm" />
		</button>
	</div>
</template>

<script setup>
import { TimeAgo } from '@framework/ui/ActivityTimeline'

defineProps({
	page: { type: Object, required: true },
	doctype: { type: String, required: true },
	record: { type: String, required: true },
	icon: { type: String, required: true },
	label: { type: String, required: true },
	title: { type: String, default: '' },
	detail: { type: String, default: '' },
	timestamp: { type: String, required: true },
})
</script>
