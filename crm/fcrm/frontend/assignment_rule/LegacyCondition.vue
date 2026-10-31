<!-- A condition written in Python on `/apps/crm`: what the builder cannot read, and what a save replaces. -->
<template>
	<div class="flex flex-col gap-2 rounded-5 border border-outline-gray-2 p-3 text-p-sm text-ink-gray-7">
		<template v-if="inUse">
			<span>{{ __('This condition is written in Python, which the condition builder cannot read. Rebuild it in the builder to edit it here.') }}</span>
			<Button
				v-if="page.perms?.write"
				class="self-start"
				:label="__('Use the condition builder')"
				@click="switchToBuilder(page, pair)"
			/>
		</template>
		<template v-else>
			<span>{{ __('Saving replaces this Python condition:') }}</span>
			<code class="whitespace-pre-wrap break-words text-ink-gray-8">{{ page.saved[pair.python] }}</code>
		</template>
	</div>
</template>

<script setup>
import { computed } from 'vue'
import { Button } from 'frappe-ui'
import { __ } from 'frappe/i18n'
import { isLegacy, switchToBuilder } from './assignmentRule.js'

const props = defineProps({
	page: { type: Object, required: true },
	pair: { type: Object, required: true },
})

const inUse = computed(() => isLegacy(props.page.doc, props.pair))
</script>
