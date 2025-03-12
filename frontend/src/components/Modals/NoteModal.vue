<template>
  <Dialog
    v-model="show"
    :options="{
      size: 'xl',
      actions: [
        {
          label: editMode ? __('Update') : __('Create'),
          variant: 'solid',
          onClick: () => updateNote(),
        },
      ],
    }"
  >
    <template #body-title>
      <div class="flex items-center gap-3">
        <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">
          {{ editMode ? __('Edit Note') : __('Create Note') }}
        </h3>
        <Button
          v-if="_note?.parent"
          size="sm"
          :label="_note.parenttype == 'Opportunity' ? __('Open Opportunity') : __('Open Lead')"
          @click="redirect()"
        >
          <template #suffix>
            <ArrowUpRightIcon class="h-4 w-4" />
          </template>
        </Button>
      </div>
    </template>
    <template #body-content>
      <div class="flex flex-col gap-4">
        <div>
          <FormControl
            ref="title"
            :label="__('Title')"
            v-model="_note.custom_title"
            :placeholder="__('Call with John Doe')"
          />
        </div>
        <div>
          <div class="mb-1.5 text-xs text-ink-gray-5">{{ __('Content') }}</div>
          <TextEditor
            variant="outline"
            ref="content"
            editor-class="!prose-sm overflow-auto min-h-[180px] max-h-80 py-1.5 px-2 rounded-b border border-[--surface-gray-2] bg-surface-gray-2 placeholder-ink-gray-4 hover:border-outline-gray-modals hover:bg-surface-gray-3 hover:shadow-sm focus:bg-surface-white focus:border-outline-gray-4 focus:shadow-sm focus:ring-0 focus-visible:ring-2 focus-visible:ring-outline-gray-3 text-ink-gray-8 transition-colors"
            :fixed-menu="true"
            :content="_note.note"
            @change="(val) => (_note.note = val)"
            :placeholder="__('Took a call with John Doe and discussed the new project.')"
            :mentions="users"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import ArrowUpRightIcon from '@/components/Icons/ArrowUpRightIcon.vue'
import { capture } from '@/telemetry'
import { TextEditor, call } from 'frappe-ui'
import { ref, computed, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { usersStore } from '@/stores/users'

const props = defineProps({
  note: {
    type: Object,
    default: {},
  },
  doctype: {
    type: String,
    default: 'Lead',
  },
  doc: {
    type: String,
    default: '',
  },
})

const show = defineModel()
const notes = defineModel('reloadNotes')

const emit = defineEmits(['after'])

const { users: usersList, getUser } = usersStore()
import { dateFormat } from '@/utils'

const router = useRouter()

const title = ref(null)
const editMode = ref(false)
let _note = ref({})

async function updateNote() {
  if (props.note.custom_title === _note.value.custom_title && props.note.note === _note.value.note) return

  if (_note.value.name) {
    let d = await call('frappe.client.set_value', {
      doctype: 'CRM Note',
      name: _note.value.name,
      fieldname: _note.value,
    })
    if (d.name) {
      notes.value?.reload()
      emit('after', d)
    }
  } else {
    let d = await call('frappe.client.insert', {
      doc: {
        doctype: 'CRM Note',
        custom_title: _note.value.custom_title,
        note: _note.value.note,
        parenttype: props.doctype,
        parent: props.doc || '',
        parentfield: 'notes',
        owner: getUser().email,
        added_by: getUser().email,
        added_on: dateFormat(new Date(), 'YYYY_MM_DD_HH_mm_ss'),
      },
    })
    if (d.name) {
      capture('note_created')
      notes.value?.reload()
      emit('after', d, true)
    }
  }
  show.value = false
}

function redirect() {
  console.log(props.note)
  if (!props.note?.parent) return
  let name = props.note.parenttype == 'Opportunity' ? 'Opportunity' : 'Lead'
  let params = { leadId: props.note.parent }
  if (name == 'Opportunity') {
    params = { opportunityId: props.note.parent }
  }
  router.push({ name: name, params: params })
}

const users = computed(() => {
  return (
    usersList.data
      ?.filter((user) => user.enabled)
      .map((user) => ({
        label: user.full_name.trimEnd(),
        value: user.name,
      })) || []
  )
})

watch(
  () => show.value,
  (value) => {
    if (!value) return
    editMode.value = false
    nextTick(() => {
      title.value?.el?.focus()
      _note.value = { ...props.note }
      if (_note.value.custom_title || _note.value.note) {
        editMode.value = true
      }
    })
  },
)
</script>
