<!-- The body of CRM Call Log's record dialog: who spoke to whom and for how long, the recording, and the
     deal or lead, note and tasks the call led to, as one list. -->
<template>
	<div v-if="log" class="flex flex-col gap-5 pb-1 text-base">
		<div class="grid grid-cols-[1fr_auto_1fr] items-center gap-x-3 gap-y-2.5 pt-1">
			<template v-for="(party, i) in parties" :key="i">
				<div v-if="i" class="col-start-2 row-start-1 flex w-36 flex-col items-center gap-1 text-ink-gray-5">
					<span class="h-5 text-base font-medium tabular-nums text-ink-gray-8">
						{{ answered ? spoken(doc.duration) : '' }}
					</span>
					<div class="flex w-full items-center">
						<div class="flex-1 border-t border-outline-gray-3" />
						<span class="lucide-chevron-right -ml-2 size-4 text-ink-gray-4" aria-hidden="true" />
					</div>
					<span class="h-5 text-p-sm leading-5">{{ __(doc.status) }}</span>
				</div>
				<div class="row-start-1 flex justify-center" :class="i ? 'col-start-3' : 'col-start-1'">
					<Avatar v-if="party.named" :image="party.image" :label="party.name" size="3xl" />
					<Avatar v-else size="3xl" label="#">
						<span class="lucide-phone size-5" aria-hidden="true" />
					</Avatar>
				</div>
				<div
					class="row-start-2 flex min-w-0 flex-col items-center gap-1 text-center"
					:class="i ? 'col-start-3' : 'col-start-1'"
				>
					<span class="max-w-full truncate font-medium text-ink-gray-8">{{ party.name }}</span>
					<span class="h-4 text-p-sm text-ink-gray-5">{{ party.named ? party.phone : '' }}</span>
				</div>
			</template>
		</div>

		<div class="flex flex-col gap-2">
			<RecordingPlayer v-if="log.recording_url_path" :src="log.recording_url_path" :duration="doc.duration" />
			<div class="divide-y divide-outline-gray-1 rounded-4 border border-outline-gray-2">
				<button
					v-for="row in rows"
					:key="row.key"
					type="button"
					class="flex h-11 w-full items-center gap-2.5 px-3 text-left first:rounded-t-4 last:rounded-b-4 hover:bg-surface-gray-1"
					@click="page.open(row.doctype, row.name)"
				>
					<span class="size-4 shrink-0 text-ink-gray-6" :class="row.icon" aria-hidden="true" />
					<span class="truncate text-ink-gray-8" :class="row.text && 'max-w-[55%] shrink-0'">
						{{ row.title }}
					</span>
					<span class="min-w-0 flex-1 truncate text-ink-gray-5">{{ row.text }}</span>
					<span class="shrink-0 text-p-sm text-ink-gray-5">{{ row.meta }}</span>
				</button>
				<div v-if="!log._reference" class="flex h-11 items-center gap-2.5 pl-3 pr-1.5">
					<span class="lucide-link-2-off size-4 shrink-0 text-ink-gray-6" aria-hidden="true" />
					<span class="flex-1 truncate text-ink-gray-5">{{ __('Not linked to a lead or deal') }}</span>
					<Button
						v-if="canCreateLead"
						:label="__('Create Lead')"
						:loading="creatingLead"
						@click="createLead"
					/>
				</div>
			</div>
		</div>
	</div>
	<div v-else-if="failed" class="py-6 text-center text-base text-ink-gray-5">
		{{ __('The call could not be loaded.') }}
	</div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { Avatar, Button, dayjs } from 'frappe-ui'
import { currentSession } from '@framework/ui'
import { __ } from 'frappe/i18n'
import { callApi } from '../../../../frontend/telephony/callApi.js'
import { formatPhone, spoken } from './callFormat.js'
import RecordingPlayer from './RecordingPlayer.vue'

const CALL_LOG = 'crm.fcrm.doctype.crm_call_log.crm_call_log'
const TASK_ICONS = {
	Backlog: 'lucide-circle-dashed',
	Todo: 'lucide-circle',
	'In Progress': 'lucide-circle-dot',
	Done: 'lucide-circle-check',
	Canceled: 'lucide-circle-x',
}

const props = defineProps({
	page: { type: Object, required: true },
	edit: { type: Function, required: true },
	header: { type: Function, required: true },
})

const log = ref(null)
const failed = ref(false)
const creatingLead = ref(false)

const doc = computed(() => props.page.doc)
// Linking a note or task writes to the call log.
const canWrite = computed(() => Boolean(props.page.perms.write))
const canCreateLead = computed(() => canWrite.value && !log.value._deal && !log.value._lead)
const isIncoming = computed(() => doc.value.type === 'Incoming')
const answered = computed(() => doc.value.status === 'Completed' && doc.value.duration > 0)
// Stored on the site clock, which the session carries.
const started = computed(() => {
	const at = (value) => dayjs.tz(value, currentSession()?.timezone).local()
	return doc.value.start_time
		? at(doc.value.start_time)
		: at(doc.value.end_time || doc.value.creation).subtract(doc.value.duration || 0, 'second')
})

// The server names a number with no contact "Unknown": show the number instead.
const parties = computed(() =>
	[
		[log.value._caller, doc.value.from],
		[log.value._receiver, doc.value.to],
	].map(([party, number]) => {
		const named = Boolean(party?.label) && party.label !== 'Unknown'
		return {
			named,
			image: party?.image,
			name: named ? party.label : formatPhone(number),
			phone: formatPhone(number),
		}
	})
)

const rows = computed(() => {
	const reference = log.value._reference
	return [
		reference && {
			key: reference.name,
			doctype: reference.doctype,
			name: reference.name,
			icon: reference.doctype === 'CRM Deal' ? 'lucide-handshake' : 'lucide-user-round',
			title: reference.title,
			text: [reference.doctype === 'CRM Deal' ? __('Deal') : __('Lead'), reference.subtitle]
				.filter(Boolean)
				.join(' · '),
			meta: reference.status,
		},
		...unique(log.value._notes).map((note) => ({
			key: note.name,
			doctype: 'FCRM Note',
			name: note.name,
			icon: 'lucide-notebook-pen',
			title: note.title || __('Untitled note'),
			text: text(note.content),
			meta: __('Note'),
		})),
		...unique(log.value._tasks).map((task) => ({
			key: task.name,
			doctype: 'CRM Task',
			name: task.name,
			icon: TASK_ICONS[task.status] || 'lucide-circle',
			title: task.title,
			text: task.due_date ? __('Due {0}', [dayjs(task.due_date).format('ddd, MMM D')]) : '',
			meta: __(task.status),
		})),
	].filter(Boolean)
})

props.header(() => ({
	title: isIncoming.value ? __('Incoming Call') : __('Outgoing Call'),
	subtitle: started.value.format('ddd, MMM D, YYYY · h:mm A'),
	buttons: canWrite.value
		? [
				{
					label: __('Edit Call Log'),
					icon: 'lucide-pencil',
					onClick: props.edit,
				},
		  ]
		: [],
	menu:
		canWrite.value && log.value
			? [
					{
						label: __('Add Note'),
						icon: 'lucide-notebook-pen',
						onClick: () => add('FCRM Note'),
					},
					{
						label: __('Add Task'),
						icon: 'lucide-square-check',
						onClick: () => add('CRM Task'),
					},
			  ]
			: [],
	save: false,
}))

onMounted(load)

async function load() {
	try {
		log.value = await props.page.call(`${CALL_LOG}.get_call_log`, {
			name: props.page.docname,
		})
	} catch {
		failed.value = true
	}
}

// The server lists the call's `note` field again among its links.
function unique(records) {
	return records.filter((record, i) => records.findIndex((other) => other.name === record.name) === i)
}

// A note's content is HTML: the summary shows its text.
function text(html) {
	return html ? new DOMParser().parseFromString(html, 'text/html').body.textContent.trim() : ''
}

async function add(doctype) {
	const reference = log.value._reference
	const values = reference
		? {
				reference_doctype: reference.doctype,
				reference_docname: reference.name,
		  }
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
