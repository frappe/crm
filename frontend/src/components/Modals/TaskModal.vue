<template>
  <Dialog v-model="show" :options="{ size: 'xl' }">
    <template #body>
      <div class="bg-surface-modal px-4 pb-6 pt-5 sm:px-6">
        <div class="mb-5 flex items-center justify-between">
          <div class="flex gap-2 items-center">
            <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">
              {{ editMode ? __('Edit Task') : __('Create Task') }}
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
            doctype="CRM Task"
          />
          <ErrorMessage v-if="error" class="mt-4" :message="__(error)" />
        </div>
      </div>
      <div class="px-4 pb-7 pt-4 sm:px-6">
        <div class="flex flex-row-reverse gap-2">
          <Button
            variant="solid"
            :label="editMode ? __('Update') : __('Create')"
            :loading="editMode ? document.save.loading : createTask.loading"
            @click="updateTask"
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
  task: { type: Object, default: () => {} },
  doctype: { type: String, default: 'CRM Lead' },
  docname: { type: String, default: '' },
})

const show = defineModel({ type: Boolean })
const tasks = defineModel('reloadTasks', { type: Object, default: () => ({}) })

const emit = defineEmits(['after'])

const router = useRouter()

const { isManager } = usersStore()
const { updateOnboardingStep } = useOnboarding('frappecrm')
const { capture } = useTelemetry()
const { $dialog, $socket } = globalStore()

const { document, scripts, triggerOnRender } = useDocument(
  'CRM Task',
  props.task?.name || null,
)

const doc = computed(() => document.doc || {})

const tabs = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_fields_layout',
  cache: ['Quick Entry', 'CRM Task'],
  params: { doctype: 'CRM Task', type: 'Quick Entry' },
  auto: true,
})

const error = ref(null)
const editMode = computed(() => Boolean(document.doc?.name))

const createTask = createResource({
  url: 'frappe.client.insert',
})

function updateTask() {
  if (document.doc.name) {
    document.save.submit(null, {
      onSuccess: (d) => {
        tasks.value?.reload?.()
        emit('after', d)
        show.value = false
      },
      onError: (err) => {
        error.value = err.messages?.[0] || 'Something went wrong'
      },
    })
  } else {
    createTask.submit(
      {
        doc: {
          doctype: 'CRM Task',
          ...document.doc,
        },
      },
      {
        onSuccess: (d) => {
          updateOnboardingStep('create_first_task')
          capture('task_created')
          document.doc = {}
          tasks.value?.reload?.()
          emit('after', d, true)
          show.value = false
        },
        onError: (err) => {
          if (err.exc_type == 'MandatoryError') {
            const fieldName = err.messages
              .map((msg) => {
                let arr = msg.split(': ')
                return arr[arr.length - 1].trim()
              })
              .join(', ')
            error.value = __('Mandatory field error: {0}', [fieldName])
            return
          }
          error.value = err.messages?.[0] || 'Something went wrong'
        },
      },
    )
  }
}

function redirect() {
  if (!props.task?.reference_docname) return
  let name = props.task.reference_doctype == 'CRM Deal' ? 'Deal' : 'Lead'
  let params = { leadId: props.task.reference_docname }
  if (name == 'Deal') {
    params = { dealId: props.task.reference_docname }
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
  quickEntryProps.value = { doctype: 'CRM Task' }
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

<style scoped>
:deep(.datepicker svg) {
  width: 0.875rem;
  height: 0.875rem;
}
</style>
