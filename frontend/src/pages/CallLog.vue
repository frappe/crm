<template>
  <LayoutHeader v-if="callLog.doc">
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs" />
    </template>
    <template #right-header>
      <Button v-if="!callLog.doc.lead" variant="solid" label="Create lead" @click="createLead">
        <template #prefix><FeatherIcon name="plus" class="h-4" /></template>
      </Button>
    </template>
  </LayoutHeader>
  <div class="border-b"></div>
  <div v-if="callLog.doc" class="p-3">
    <div class="px-3 pb-1 text-base font-medium">{{ details.label }}</div>
    <div class="grid grid-cols-5 gap-4 p-3">
      <div
        v-for="field in details.fields"
        :key="field.key"
        class="flex flex-col gap-2"
      >
        <div class="text-sm text-gray-500">{{ field.label }}</div>
        <div class="text-sm text-gray-900">{{ callLog.doc[field.key] }}</div>
      </div>
    </div>
    <!-- <div class="px-3 pb-1 text-base font-medium mt-3">Call note</div>
    <div v-if="callNote?.doc" class="flex flex-col p-3">
      <TextInput
        type="text"
        class="text-base bg-white border-none !pl-0 hover:bg-white focus:!shadow-none focus-visible:!ring-0"
        v-model="callNote.doc.title"
        placeholder="Untitled note"
      />
      <TextEditor
        ref="content"
        editor-class="!prose-sm !leading-5 max-w-none p-2 pl-0 overflow-auto focus:outline-none"
        :bubbleMenu="true"
        :content="callNote.doc.content"
        @change="(val) => (callNote.doc.content = val)"
        placeholder="Type something and press enter"
      />
    </div> -->
  </div>
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import Breadcrumbs from '@/components/Breadcrumbs.vue'
import {
  createDocumentResource,
  TextInput,
  TextEditor,
  FeatherIcon,
  call,
} from 'frappe-ui'
import { usersStore } from '@/stores/users'
import { computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const { getUser } = usersStore()

const props = defineProps({
  callLogId: {
    type: String,
    required: true,
  },
})

const callLog = createDocumentResource({
  doctype: 'CRM Call Log',
  name: props.callLogId,
  setValue: {},
})

const breadcrumbs = computed(() => [
  { label: 'Call Logs', route: { name: 'Call Logs' } },
  { label: callLog.doc?.from },
])

const details = {
  label: 'Call Details',
  fields: [
    {
      label: 'From',
      key: 'from',
      type: 'data',
    },
    {
      label: 'To',
      key: 'to',
      type: 'data',
    },
    {
      label: 'Duration',
      key: 'duration',
      type: 'data',
    },
    {
      label: 'Start Time',
      key: 'start_time',
      type: 'data',
    },
    {
      label: 'End Time',
      key: 'end_time',
      type: 'data',
    },
    {
      label: 'Type',
      key: 'type',
      type: 'data',
    },
    {
      label: 'Status',
      key: 'status',
      type: 'data',
    },
  ],
}

// const callNote = computed(() => {
//   return createDocumentResource({
//     doctype: 'CRM Note',
//     name: callLog.doc?.note,
//     auto: true,
//     setValue: {},
//   })
// })

async function createLead() {
  let d = await call('frappe.client.insert', {
    doc: {
      doctype: 'CRM Lead',
      first_name: "Lead from " + callLog.doc.from,
      mobile_no: callLog.doc.from,
      lead_owner: getUser().name,
    },
  })
  if (d.name) {
    await update_call_log(d.name)
    await update_note(d.name)
    router.push({ name: 'Lead', params: { leadId: d.name } })
  }
}

async function update_note(lead) {
  await call('frappe.client.set_value', {
    doctype: 'CRM Note',
    name: callLog.doc?.note,
    fieldname: 'lead',
    value: lead,
  })
}

async function update_call_log(lead) {
  callLog.setValue.submit({ lead: lead })
}
</script>
