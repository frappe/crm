<!-- The body of CRM Call Log's record dialog: the call as a read-only summary, as CRM v1's call details. -->
<template>
	<div v-if="log" class="flex flex-col gap-4">
		<div class="flex flex-col gap-3.5 text-base text-ink-gray-8">
			<div class="flex min-h-7 items-center gap-2">
				<span
					class="size-4 shrink-0 text-ink-gray-6"
					:class="isIncoming ? 'lucide-phone-incoming' : 'lucide-phone-outgoing'"
					aria-hidden="true"
				/>
				<span>{{ isIncoming ? __('Incoming Call') : __('Outgoing Call') }}</span>
				<Badge
					class="ml-auto"
					:theme="STATUS_THEMES[doc.status] || 'gray'"
					:label="__(doc.status)"
				/>
			</div>
			<div class="flex min-h-7 items-center gap-2">
				<span class="lucide-users size-4 shrink-0 text-ink-gray-6" aria-hidden="true" />
				<Avatar :image="log._caller?.image" :label="log._caller?.label" size="sm" />
				<span class="truncate">{{ log._caller?.label }}</span>
				<span
					class="lucide-arrow-right size-4 shrink-0 text-ink-gray-5"
					aria-hidden="true"
				/>
				<Avatar :image="log._receiver?.image" :label="log._receiver?.label" size="sm" />
				<span class="truncate">{{ log._receiver?.label }}</span>
			</div>
			<div v-if="reference" class="flex min-h-7 items-center gap-2">
				<span class="lucide-link size-4 shrink-0 text-ink-gray-6" aria-hidden="true" />
				<Button
					variant="ghost"
					class="-ml-2"
					:label="`${reference.label} ${reference.name}`"
					icon-right="lucide-arrow-up-right"
					@click="page.open(reference.doctype, reference.name)"
				/>
			</div>
			<div class="flex min-h-7 items-center gap-2">
				<span class="lucide-calendar size-4 shrink-0 text-ink-gray-6" aria-hidden="true" />
				<TimeAgo :timestamp="doc.creation" />
			</div>
			<div v-if="log._duration" class="flex min-h-7 items-center gap-2">
				<span class="lucide-timer size-4 shrink-0 text-ink-gray-6" aria-hidden="true" />
				<span>{{ log._duration }}</span>
			</div>
			<div v-if="log.recording_url_path" class="flex min-h-7 items-center gap-2">
				<span
					class="lucide-circle-play size-4 shrink-0 text-ink-gray-6"
					aria-hidden="true"
				/>
				<audio
					v-if="!recordingFailed"
					class="w-full"
					controls
					:src="log.recording_url_path"
					@error="recordingFailed = true"
				/>
				<span v-else class="text-ink-gray-5">{{ __('Recording not available') }}</span>
			</div>
		</div>
		<div v-for="section in sections" :key="section.doctype" class="flex flex-col gap-2">
			<div v-for="record in section.records" :key="record.name">
				<button
					type="button"
					class="flex w-full flex-col gap-1 rounded-1 border px-2.5 py-2 text-left hover:bg-surface-gray-2"
					@click="page.open(section.doctype, record.name)"
				>
					<span class="flex items-center gap-1.5 text-base font-medium text-ink-gray-8">
						<span
							class="size-4 shrink-0 text-ink-gray-6"
							:class="section.icon"
							aria-hidden="true"
						/>
						<span class="truncate">{{ record.title }}</span>
					</span>
					<span
						v-if="text(record[section.body])"
						class="line-clamp-3 text-base text-ink-gray-7"
						>{{ text(record[section.body]) }}</span
					>
				</button>
			</div>
		</div>
		<div class="flex items-center gap-2">
			<Button :label="__('Edit')" icon-left="lucide-pencil" @click="edit" />
			<Button
				:label="__('Add Note')"
				icon-left="lucide-notebook-pen"
				:loading="adding === 'FCRM Note'"
				@click="add('FCRM Note')"
			/>
			<Button
				:label="__('Add Task')"
				icon-left="lucide-square-check"
				:loading="adding === 'CRM Task'"
				@click="add('CRM Task')"
			/>
		</div>
	</div>
	<div v-else-if="failed" class="py-6 text-center text-base text-ink-gray-5">
		{{ __('The call could not be loaded.') }}
	</div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { Avatar, Badge, Button } from 'frappe-ui'
import { TimeAgo } from '@framework/ui/ActivityTimeline'
import { __ } from 'frappe/i18n'
import { callApi } from '../../../../frontend/telephony/callApi.js'

const GET_CALL_LOG = 'crm.fcrm.doctype.crm_call_log.crm_call_log.get_call_log'
const STATUS_THEMES = {
	Completed: 'green',
	Failed: 'red',
	Busy: 'red',
	'No Answer': 'orange',
	Canceled: 'orange',
}

const props = defineProps({
	page: { type: Object, required: true },
	edit: { type: Function, required: true },
})

const log = ref(null)
const failed = ref(false)
const adding = ref('')
const recordingFailed = ref(false)

const doc = computed(() => props.page.doc)
const isIncoming = computed(() => doc.value.type === 'Incoming')
const reference = computed(() => {
	const [doctype, name, label] = log.value._deal
		? ['CRM Deal', log.value._deal, __('Deal')]
		: log.value._lead
			? ['CRM Lead', log.value._lead, __('Lead')]
			: []
	return doctype && { doctype, name, label }
})
const sections = computed(() => [
	{
		doctype: 'FCRM Note',
		icon: 'lucide-notebook-pen',
		body: 'content',
		records: unique(log.value._notes),
	},
	{
		doctype: 'CRM Task',
		icon: 'lucide-square-check',
		body: 'description',
		records: unique(log.value._tasks),
	},
])

onMounted(load)

async function load() {
	try {
		log.value = await props.page.call(GET_CALL_LOG, { name: props.page.docname })
	} catch {
		failed.value = true
	}
}

// The server lists the call's `note` field again among its links.
const unique = (records) =>
	records.filter((record, i) => records.findIndex((other) => other.name === record.name) === i)

// A note's content and a task's description are HTML: the summary shows their text.
function text(html) {
	return html ? new DOMParser().parseFromString(html, 'text/html').body.textContent.trim() : ''
}

async function add(doctype) {
	const { _lead, _deal } = log.value
	const values = _deal
		? { reference_doctype: 'CRM Deal', reference_docname: _deal }
		: _lead
			? { reference_doctype: 'CRM Lead', reference_docname: _lead }
			: {}
	adding.value = doctype
	try {
		const created = await props.page.create(doctype, { values })
		if (!created) return
		await callApi.link(props.page.docname, doctype, created.name)
		await load()
	} catch (error) {
		props.page.toast.error(error.message)
	} finally {
		adding.value = ''
	}
}
</script>
