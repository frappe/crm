<template>
	<div class="flex items-center">
		<Button v-if="readOnly" :label="__(page.doc.status)" disabled>
			<template #prefix><StatusDot :color="current?.color" /></template>
		</Button>
		<Dropdown v-else :options="options" align="start">
			<template #default="{ open }">
				<Button :label="__(page.doc.status)" :iconRight="open ? 'lucide-chevron-up' : 'lucide-chevron-down'">
					<template #prefix><StatusDot :color="current?.color" /></template>
				</Button>
			</template>
			<template #item-prefix="{ item }">
				<StatusDot :color="item.color" />
			</template>
		</Dropdown>
	</div>
</template>

<script setup>
import { computed, h } from 'vue'
import { Button, Dropdown } from 'frappe-ui'
import { __ } from 'frappe/i18n'
import { findStatus, statusInk, statusPicker } from './statusChange.js'

const props = defineProps({
	page: { type: Object, required: true },
	statuses: { type: Array, default: undefined },
	readOnly: { type: Boolean, default: false },
})

const StatusDot = (dot) =>
	h('span', { class: ['flex size-4 shrink-0 items-center justify-center', statusInk(dot.color)] }, [
		h('span', { class: 'size-2 rounded-full bg-current' }),
	])
StatusDot.props = ['color']

const { busy, pick } = statusPicker(props.page)

const current = computed(() => findStatus(props.statuses, props.page.doc.status))

const options = computed(() =>
	(props.statuses ?? []).map((status) => ({
		label: __(status.name),
		color: status.color,
		selected: status.name === props.page.doc.status,
		disabled: busy.value,
		onClick: () => pick(status),
	})),
)
</script>
