<template>
  <Dialog v-model="show" :options="{ size: 'xl' }">
    <template #body>
      <div class="bg-surface-modal px-4 pb-6 pt-5 sm:px-6">
        <div class="mb-5 flex items-center justify-between">
          <div class="flex gap-2 items-center">
            <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">
              {{ editMode ? __('Edit Note') : __('Create Note') }}
            </h3>
            <Button
              v-if="doc?.reference_docname"
              size="sm"
              :label="
                doc?.reference_doctype == 'CRM Deal'
                  ? __('Open Deal')
                  : __('Open Lead')
              "
              :iconRight="ArrowUpRightIcon"
              @click="redirect()"
            />
          </div>
          <div class="flex items-center gap-1">
            <Button
              v-if="isManager() && !isMobileView"
              variant="ghost"
              class="w-7"
              :tooltip="__('Edit Fields Layout')"
              :icon="EditIcon"
              @click="openQuickEntryModal"
            />
            <Button
              variant="ghost"
              class="w-7"
              icon="x"
              @click="show = false"
            />
          </div>
        </div>
        <div>
          <FieldLayout
            v-if="tabs.data"
            :tabs="tabs.data"
            :data="doc"
            doctype="FCRM Note"
          />
          <ErrorMessage v-if="error" class="mt-4" :message="__(error)" />
        </div>
      </div>
      <div class="px-4 pb-7 pt-4 sm:px-6">
        <div class="flex flex-row-reverse gap-2">
          <Button
            variant="solid"
            :label="editMode ? __('Update') : __('Create')"
            :loading="editMode ? document.save.loading : createNote.loading"
            @click="updateNote"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import EditIcon from '@/components/Icons/EditIcon.vue'
import ArrowUpRightIcon from '@/components/Icons/ArrowUpRightIcon.vue'
import FieldLayout from '@/components/FieldLayout/FieldLayout.vue'
import { useDocument } from '@/data/document'
import { globalStore } from '@/stores/global'
import { usersStore } from '@/stores/users'
import { showQuickEntryModal, quickEntryProps } from '@/composables/modals'
import { isMobileView } from '@/composables/settings'
import { setupCustomizations } from '@/utils'
import { call, createResource, toast } from 'frappe-ui'
import { useOnboarding, useTelemetry } from 'frappe-ui/frappe'
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  note: { type: Object, default: () => {} },
  doctype: { type: String, default: 'CRM Lead' },
  docname: { type: String, default: '' },
})

const show = defineModel({ type: Boolean })
const notes = defineModel('reloadNotes', { type: Object, default: () => ({}) })

const emit = defineEmits(['after'])

const router = useRouter()

const { isManager } = usersStore()
const { updateOnboardingStep } = useOnboarding('frappecrm')
const { capture } = useTelemetry()
const { $dialog, $socket } = globalStore()

const { document, scripts, triggerOnRender } = useDocument(
  'FCRM Note',
  props.note?.name || null,
)

const doc = computed(() => document.doc || {})

const tabs = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_fields_layout',
  cache: ['Quick Entry', 'FCRM Note'],
  params: { doctype: 'FCRM Note', type: 'Quick Entry' },
  auto: true,
})

const error = ref(null)
const editMode = computed(() => Boolean(document.doc?.name))

const createNote = createResource({
  url: 'frappe.client.insert',
})

function updateNote() {
  if (document.doc.name) {
    document.save.submit(null, {
      onSuccess: (d) => {
        notes.value?.reload?.()
        emit('after', d)
        show.value = false
      },
      onError: (err) => {
        error.value = err.message || 'Something went wrong'
      },
    })
  } else {
    createNote.submit(
      {
        doc: {
          doctype: 'FCRM Note',
          ...document.doc,
        },
      },
      {
        onSuccess: (d) => {
          updateOnboardingStep('create_first_note')
          capture('note_created')
          document.doc = {}
          notes.value?.reload?.()
          emit('after', d, true)
          show.value = false
        },
        onError: (err) => {
          error.value = err.message || 'Something went wrong'
        },
      },
    )
  }
}

function redirect() {
  if (!props.note?.reference_docname) return
  let name = props.note.reference_doctype == 'CRM Deal' ? 'Deal' : 'Lead'
  let params = { leadId: props.note.reference_docname }
  if (name == 'Deal') {
    params = { dealId: props.note.reference_docname }
  }
  router.push({ name: name, params: params })
}

watch(
  () => document.doc,
  async (_doc) => {
    if (scripts.data?.length) {
      setupCustomizations(scripts.data, {
        doc: _doc,
        $dialog,
        $socket,
        router,
        toast,
        updateField,
        createToast: toast.create,
        call,
      })
    }
  },
  { once: true },
)

function updateField(name, value) {
  value = Array.isArray(name) ? '' : value
  let oldValues = Array.isArray(name) ? {} : doc.value[name]

  if (Array.isArray(name)) {
    name.forEach((field) => (doc.value[field] = value))
  } else {
    doc.value[name] = value
  }

  document.save.submit(null, {
    onError: (err) => {
      if (Array.isArray(name)) {
        name.forEach((field) => (doc.value[field] = oldValues[field]))
      } else {
        doc.value[name] = oldValues
      }
      toast.error(err.messages?.[0] || __('Error updating field'))
    },
  })
}

function openQuickEntryModal() {
  showQuickEntryModal.value = true
  quickEntryProps.value = { doctype: 'FCRM Note' }
  nextTick(() => (show.value = false))
}

onMounted(async () => {
  document.doc = {
    ...document.doc,
    reference_doctype: props.doctype,
    reference_docname: props.docname,
  }
  await triggerOnRender()
})
</script>
