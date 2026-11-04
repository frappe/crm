<!-- The body of CRM Call Log's record dialog: the call as a read-only summary, as CRM v1's call details. -->
<template>
	<div v-if="log" class="flex flex-col gap-3.5 text-base text-ink-gray-8">
		<div v-for="row in rows" :key="row.key" class="flex gap-2">
			<div class="grid size-7 shrink-0 place-content-center">
				<span class="size-4 text-ink-gray-6" :class="row.icon" aria-hidden="true" />
			</div>
			<div class="flex min-h-7 min-w-0 flex-1 items-center gap-2">
				<template v-if="row.key === 'parties'">
					<template v-for="(party, i) in parties" :key="i">
						<span
							v-if="i"
							class="lucide-arrow-right size-4 shrink-0 text-ink-gray-5"
							aria-hidden="true"
						/>
						<Avatar
							v-if="party.image || party.named"
							:image="party.image"
							:label="party.label"
							size="sm"
						/>
						<span class="truncate">{{ party.label }}</span>
					</template>
				</template>
				<template v-else-if="row.key === 'reference'">
					<span class="truncate">{{ reference.name }}</span>
					<Button
						variant="ghost"
						icon="lucide-arrow-up-right"
						:tooltip="__('Open {0}', [reference.label])"
						:aria-label="__('Open {0}', [reference.label])"
						@click="page.open(reference.doctype, reference.name)"
					/>
				</template>
				<Tooltip v-else-if="row.key === 'time'" :text="stamp.fromNow()">
					<span>{{ stamp.local().format('ddd, MMM D, YYYY h:mm A') }}</span>
				</Tooltip>
				<Badge
					v-else-if="row.key === 'status'"
					:theme="STATUS_THEMES[doc.status] || 'gray'"
					:label="__(doc.status)"
				/>
				<template v-else-if="row.key === 'recording'">
					<audio
						v-if="!recordingFailed"
						class="w-full"
						controls
						:src="log.recording_url_path"
						@error="recordingFailed = true"
					/>
					<span v-else class="text-ink-gray-5">{{ __('Recording not available') }}</span>
				</template>
				<button
					v-else-if="row.record"
					type="button"
					class="flex w-full flex-col gap-1 rounded-4 border border-outline-gray-2 px-2.5 py-2 text-left text-ink-gray-7 hover:bg-surface-gray-1"
					@click="page.open(row.doctype, row.record.name)"
				>
					<span class="truncate font-medium text-ink-gray-8">{{ row.record.title }}</span>
					<span v-if="row.text" class="line-clamp-3">{{ row.text }}</span>
				</button>
				<span v-else>{{ row.text }}</span>
			</div>
		</div>
		<Button
			v-if="canCreateLead"
			class="mt-1.5 w-full"
			variant="solid"
			:label="__('Create Lead')"
			:loading="creatingLead"
			@click="createLead"
		/>
	</div>
	<div v-else-if="failed" class="py-6 text-center text-base text-ink-gray-5">
		{{ __('The call could not be loaded.') }}
	</div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { Avatar, Badge, Button, Tooltip, dayjs } from 'frappe-ui'
import { currentSession } from '@framework/ui'
import { __ } from 'frappe/i18n'
import { callApi } from '../../../../frontend/telephony/callApi.js'

const CALL_LOG = 'crm.fcrm.doctype.crm_call_log.crm_call_log'
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
	header: { type: Function, required: true },
})

const log = ref(null)
const failed = ref(false)
const recordingFailed = ref(false)
const creatingLead = ref(false)

const doc = computed(() => props.page.doc)
// Linking a note or task writes to the call log.
const canWrite = computed(() => Boolean(props.page.perms.write))
const canCreateLead = computed(() => canWrite.value && !log.value._deal && !log.value._lead)
const isIncoming = computed(() => doc.value.type === 'Incoming')
// Stored on the site clock, which the session carries.
const stamp = computed(() => dayjs.tz(doc.value.creation, currentSession()?.timezone))
const reference = computed(() => {
	const [doctype, name, label] = log.value._deal
		? ['CRM Deal', log.value._deal, __('Deal')]
		: log.value._lead
			? ['CRM Lead', log.value._lead, __('Lead')]
			: []
	return doctype && { doctype, name, label }
})
// The server names a number with no contact "Unknown": show the number instead.
const parties = computed(() =>
	[
		[log.value._caller, doc.value.from],
		[log.value._receiver, doc.value.to],
	].map(([party, number]) => {
		const named = Boolean(party?.label) && party.label !== 'Unknown'
		return { named, image: party?.image, label: named ? party.label : number }
	}),
)
const rows = computed(() =>
	[
		{
			key: 'type',
			icon: isIncoming.value ? 'lucide-phone-incoming' : 'lucide-phone-outgoing',
			text: isIncoming.value ? __('Incoming Call') : __('Outgoing Call'),
		},
		{ key: 'parties', icon: 'lucide-users' },
		reference.value && {
			key: 'reference',
			icon: log.value._deal ? 'lucide-handshake' : 'lucide-user-round',
		},
		{ key: 'time', icon: 'lucide-calendar' },
		log.value._duration && { key: 'duration', icon: 'lucide-timer', text: log.value._duration },
		{ key: 'status', icon: 'lucide-circle-check' },
		log.value.recording_url_path && { key: 'recording', icon: 'lucide-circle-play' },
		...linked('FCRM Note', 'lucide-notebook-pen', log.value._notes, 'content'),
		...linked('CRM Task', 'lucide-square-check', log.value._tasks, 'description'),
	].filter(Boolean),
)

props.header(() => ({
	title: __('Call Details'),
	buttons: canWrite.value
		? [{ label: __('Edit Call Log'), icon: 'lucide-pencil', onClick: props.edit }]
		: [],
	menu:
		canWrite.value && log.value
			? [
					{ label: __('Add Note'), icon: 'lucide-notebook-pen', onClick: () => add('FCRM Note') },
					{ label: __('Add Task'), icon: 'lucide-square-check', onClick: () => add('CRM Task') },
				]
			: [],
	save: false,
}))

onMounted(load)

async function load() {
	try {
		log.value = await props.page.call(`${CALL_LOG}.get_call_log`, { name: props.page.docname })
	} catch {
		failed.value = true
	}
}

// The server lists the call's `note` field again among its links.
function linked(doctype, icon, records, body) {
	return records
		.filter((record, i) => records.findIndex((other) => other.name === record.name) === i)
		.map((record) => ({ key: record.name, doctype, icon, record, text: text(record[body]) }))
}

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
	try {
		const created = await props.page.create(doctype, { values })
		if (!created) return
		await callApi.link(props.page.docname, doctype, created.name)
		await load()
	} catch (error) {
		props.page.toast.error(error.message)
	}
}

async function createLead() {
	creatingLead.value = true
	try {
		const lead = await props.page.call(`${CALL_LOG}.create_lead_from_call_log`, {
			call_log: props.page.docname,
		})
		props.page.open('CRM Lead', lead)
	} catch (error) {
		props.page.toast.error(error.message)
	} finally {
		creatingLead.value = false
	}
}
</script>
