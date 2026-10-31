<template>
	<ol v-if="calls.length" class="flex flex-col pb-2">
		<li v-for="row in calls" :key="row.name" class="flex gap-2 py-1.5">
			<span class="w-7 shrink-0 text-right font-mono text-sm tabular-nums text-ink-gray-5">{{ row.line }}</span>
			<div class="flex min-w-0 flex-col gap-1">
				<a
					:href="row.guide"
					target="_blank"
					rel="noopener"
					class="truncate font-mono text-sm text-ink-gray-8 hover:underline"
					:title="row.call"
				>
					{{ row.call }}
				</a>
				<span v-if="row.verb" class="text-sm text-ink-gray-6">{{ row.verb }}</span>
				<Badge v-else class="self-start" theme="orange" size="sm" :label="__('No counterpart')" />
				<template v-if="row.gap">
					<a
						v-if="row.gap.url"
						:href="row.gap.url"
						target="_blank"
						rel="noopener"
						class="text-sm text-ink-gray-6 underline"
					>
						{{ row.gap.label }}
					</a>
					<span v-else class="text-sm text-ink-gray-5">{{ row.gap.label }}</span>
				</template>
			</div>
		</li>
	</ol>
	<p v-else class="pb-3 text-base text-ink-gray-5">{{ __('No v1 calls') }}</p>
</template>

<script setup>
import { Badge } from 'frappe-ui'
import { __ } from 'frappe/i18n'

defineProps({
	calls: { type: Array, default: () => [] },
})
</script>
