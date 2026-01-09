<template>
  <Dialog v-model="show" :options="{ size: '3xl' }">
    <template #body>
      <div class="bg-surface-modal px-4 pb-6 pt-5 sm:px-6">
        <div class="mb-5 flex items-center justify-between">
          <div>
            <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">
              {{ __('Create Lead') }}
            </h3>
          </div>
          <div class="flex items-center gap-1">
            <Button
              v-if="isManager() && !isMobileView"
              variant="ghost"
              class="w-7"
              :tooltip="__('Edit fields layout')"
              :icon="EditIcon"
              @click="openQuickEntryModal"
            />
            <Button
              variant="ghost"
              class="w-7"
              @click="show = false"
              icon="x"
            />
          </div>
        </div>
        <div>
          <FieldLayout v-if="tabs.data" :tabs="tabs.data" :data="lead.doc" />
          <div
            class="mt-6 rounded-lg border border-outline-gray-2 bg-surface-white p-4"
          >
            <div class="flex flex-col gap-1">
              <div class="text-lg font-semibold leading-6 text-ink-gray-9">
                {{ __('Assign Task (required)') }}
              </div>
              <div class="text-sm leading-5 text-ink-gray-6">
                {{
                  __(
                    'Every new lead needs an assigned task. It will be created along with the lead.',
                  )
                }}
              </div>
            </div>
            <div class="mt-4 grid gap-4 sm:grid-cols-2">
              <div class="sm:col-span-2">
                <div class="mb-1.5 text-xs text-ink-gray-5">
                  {{ __('Task Title') }}
                </div>
                <TextInput
                  v-model="task.title"
                  :placeholder="__('Call with John Doe')"
                  required
                />
              </div>
              <div>
                <div class="mb-1.5 text-xs text-ink-gray-5">
                  {{ __('Assign To') }}
                </div>
                <Link
                  class="form-control"
                  :value="getUser(task.assigned_to).full_name"
                  doctype="User"
                  @change="(option) => (task.assigned_to = option)"
                  :placeholder="__('John Doe')"
                  :filters="{
                    name: ['in', users.data.crmUsers?.map((user) => user.name)],
                  }"
                  :hideMe="true"
                >
                  <template #prefix>
                    <UserAvatar
                      class="mr-2 !h-4 !w-4"
                      :user="task.assigned_to"
                    />
                  </template>
                  <template #item-prefix="{ option }">
                    <UserAvatar class="mr-2" :user="option.value" size="sm" />
                  </template>
                  <template #item-label="{ option }">
                    <div class="cursor-pointer text-ink-gray-9">
                      {{ getUser(option.value).full_name }}
                    </div>
                  </template>
                </Link>
              </div>
              <div>
                <div class="mb-1.5 text-xs text-ink-gray-5">
                  {{ __('Due Date (optional)') }}
                </div>
                <DateTimePicker
                  class="datepicker"
                  v-model="task.due_date"
                  :placeholder="__('01/04/2024 11:30 PM')"
                  :format="dateTimeFormat"
                  input-class="border-none"
                />
              </div>
            </div>
          </div>
          <ErrorMessage class="mt-4" v-if="error" :message="__(error)" />
        </div>
      </div>
      <div class="px-4 pb-7 pt-4 sm:px-6">
        <div class="flex flex-row-reverse gap-2">
          <Button
            variant="solid"
            :label="__('Create')"
            :loading="isLeadCreating"
            @click="createNewLead"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import EditIcon from '@/components/Icons/EditIcon.vue'
import FieldLayout from '@/components/FieldLayout/FieldLayout.vue'
import Link from '@/components/Controls/Link.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import { usersStore } from '@/stores/users'
import { statusesStore } from '@/stores/statuses'
import { sessionStore } from '@/stores/session'
import { isMobileView } from '@/composables/settings'
import { showQuickEntryModal, quickEntryProps } from '@/composables/modals'
import { capture } from '@/telemetry'
import { TextInput, DateTimePicker, createResource, call } from 'frappe-ui'
import { useOnboarding } from 'frappe-ui/frappe'
import { getFormat } from '@/utils'
import { useDocument } from '@/data/document'
import { computed, onMounted, reactive, ref, nextTick } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  defaults: Object,
})

const { user } = sessionStore()
const { getUser, isManager, users, getUserRole } = usersStore()
const { getLeadStatus, statusOptions } = statusesStore()
const { updateOnboardingStep } = useOnboarding('frappecrm')

const show = defineModel()
const router = useRouter()
const error = ref(null)
const isLeadCreating = ref(false)

const task = reactive({
  title: '',
  assigned_to: '',
  due_date: '',
  status: 'Backlog',
  priority: 'Low',
})

const dateTimeFormat = getFormat('', '', true, true, false)
const canChangeLeadOwner = computed(() => {
  const role = getUserRole(user)
  if (isManager(user)) return true
  return role === 'Sales Master Manager'
})

const { document: lead, triggerOnBeforeCreate } = useDocument('CRM Lead')

const leadStatuses = computed(() => {
  let statuses = statusOptions('lead')
  if (!lead.doc.status) {
    lead.doc.status = statuses?.[0]?.value
  }
  return statuses
})

const tabs = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_fields_layout',
  cache: ['QuickEntry', 'CRM Lead'],
  params: { doctype: 'CRM Lead', type: 'Quick Entry' },
  auto: true,
  transform: (_tabs) => {
    return _tabs.forEach((tab) => {
      tab.sections.forEach((section) => {
        section.columns.forEach((column) => {
          column.fields.forEach((field) => {
            if (field.fieldname == 'status') {
              field.fieldtype = 'Select'
              field.options = leadStatuses.value
              field.prefix = getLeadStatus(lead.doc.status).color
            }
            if (field.fieldname === 'lead_owner' && !canChangeLeadOwner.value) {
              field.read_only = true
              lead.doc[field.fieldname] = getUser().name
            }

            if (field.fieldtype === 'Table') {
              lead.doc[field.fieldname] = []
            }
          })
        })
      })
    })
  },
})

const createLead = createResource({
  url: 'frappe.client.insert',
})

async function createNewLead() {
  task.assigned_to = task.assigned_to || getUser().name
  if (!canChangeLeadOwner.value) {
    lead.doc.lead_owner = getUser().name
  }

  if (lead.doc.website && !lead.doc.website.startsWith('http')) {
    lead.doc.website = 'https://' + lead.doc.website
  }

  await triggerOnBeforeCreate?.()

  createLead.submit(
    {
      doc: {
        doctype: 'CRM Lead',
        ...lead.doc,
      },
    },
    {
      validate() {
        error.value = null
        if (!task.title || !task.title.trim()) {
          error.value = __('Task Title is mandatory')
          return error.value
        }
        if (!lead.doc.first_name) {
          error.value = __('First Name is mandatory')
          return error.value
        }
        if (lead.doc.annual_revenue) {
          if (typeof lead.doc.annual_revenue === 'string') {
            lead.doc.annual_revenue = lead.doc.annual_revenue.replace(/,/g, '')
          } else if (isNaN(lead.doc.annual_revenue)) {
            error.value = __('Annual Revenue should be a number')
            return error.value
          }
        }
        if (
          lead.doc.mobile_no &&
          isNaN(lead.doc.mobile_no.replace(/[-+() ]/g, ''))
        ) {
          error.value = __('Mobile No should be a number')
          return error.value
        }
        if (lead.doc.email && !lead.doc.email.includes('@')) {
          error.value = __('Invalid Email')
          return error.value
        }
        if (!lead.doc.status) {
          error.value = __('Status is required')
          return error.value
        }
        isLeadCreating.value = true
      },
      async onSuccess(data) {
        try {
          await createTaskForLead(data.name)
          capture('lead_created')
          show.value = false
          router.push({ name: 'Lead', params: { leadId: data.name } })
          updateOnboardingStep('create_first_lead', true, false, () => {
            localStorage.setItem('firstLead' + user, data.name)
          })
        } catch (taskError) {
          await rollbackLeadCreation(data.name)
          error.value =
            taskError?.message ||
            __('Task could not be created. Lead was not saved.')
          return
        } finally {
          isLeadCreating.value = false
        }
      },
      onError(err) {
        isLeadCreating.value = false
        if (!err.messages) {
          error.value = err.message
          return
        }
        error.value = err.messages.join('\n')
      },
    },
  )
}

async function createTaskForLead(leadName) {
  const payload = {
    doctype: 'CRM Task',
    reference_doctype: 'CRM Lead',
    reference_docname: leadName,
    title: task.title?.trim(),
    assigned_to: task.assigned_to || getUser().name,
    due_date: task.due_date || null,
    status: task.status,
    priority: task.priority,
  }

  try {
    return await call('frappe.client.insert', { doc: payload })
  } catch (err) {
    if (err?.messages?.length) {
      throw new Error(err.messages.join('\n'))
    }
    throw new Error(err?.message || __('Failed to create task'))
  }
}

async function rollbackLeadCreation(leadName) {
  try {
    await call('frappe.client.delete', {
      doctype: 'CRM Lead',
      name: leadName,
    })
  } catch (rollbackError) {
    console.error(
      'Failed to rollback lead after task creation failure',
      rollbackError,
    )
  }
}

function openQuickEntryModal() {
  showQuickEntryModal.value = true
  quickEntryProps.value = { doctype: 'CRM Lead' }
  nextTick(() => (show.value = false))
}

onMounted(() => {
  lead.doc = { no_of_employees: '1-10' }
  Object.assign(lead.doc, props.defaults)

  if (!lead.doc?.lead_owner) {
    lead.doc.lead_owner = getUser().name
  }
  if (!canChangeLeadOwner.value) {
    lead.doc.lead_owner = getUser().name
  }
  if (!lead.doc?.status && leadStatuses.value[0]?.value) {
    lead.doc.status = leadStatuses.value[0].value
  }
  if (!task.assigned_to) {
    task.assigned_to = getUser().name
  }
})
</script>
