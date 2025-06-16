<template>
  <LayoutHeader v-if="lead.data">
    <header
      class="relative flex h-10.5 items-center justify-between gap-2 py-2.5 pl-2"
    >
      <Breadcrumbs :items="breadcrumbs">
        <template #prefix="{ item }">
          <Icon v-if="item.icon" :icon="item.icon" class="mr-2 h-4" />
        </template>
      </Breadcrumbs>
      <div class="absolute right-0">
        <Dropdown
          v-if="document.doc"
          :options="
            statusOptions(
              'lead',
              document,
              lead.data._customStatuses,
              triggerOnChange,
            )
          "
        >
          <template #default="{ open }">
            <Button :label="document.doc.status">
              <template #prefix>
                <IndicatorIcon
                  :class="getLeadStatus(document.doc.status).color"
                />
              </template>
              <template #suffix>
                <FeatherIcon
                  :name="open ? 'chevron-up' : 'chevron-down'"
                  class="h-4"
                />
              </template>
            </Button>
          </template>
        </Dropdown>
      </div>
    </header>
  </LayoutHeader>
  <div
    v-if="lead.data"
    class="flex h-12 items-center justify-between gap-2 border-b px-3 py-2.5"
  >
    <AssignTo
      v-model="assignees.data"
      :data="document.doc"
      doctype="CRM Lead"
    />
    <div class="flex items-center gap-2">
      <CustomActions
        v-if="lead.data._customActions?.length"
        :actions="lead.data._customActions"
      />
      <CustomActions
        v-if="document.actions?.length"
        :actions="document.actions"
      />
      <Button
        :label="__('Convert')"
        variant="solid"
        @click="showConvertToDealModal = true"
      />
    </div>
  </div>
  <div v-if="lead?.data" class="flex h-full overflow-hidden">
    <Tabs as="div" v-model="tabIndex" :tabs="tabs" class="overflow-auto">
      <TabList class="!px-3" />
      <TabPanel v-slot="{ tab }">
        <div v-if="tab.name == 'Details'">
          <SLASection
            v-if="lead.data.sla_status"
            v-model="lead.data"
            @updateField="updateField"
          />
          <div
            v-if="sections.data"
            class="flex flex-1 flex-col justify-between overflow-hidden"
          >
            <SidePanelLayout
              :sections="sections.data"
              doctype="CRM Lead"
              :docname="lead.data.name"
              @reload="sections.reload"
              @afterFieldChange="reloadAssignees"
            />
          </div>
        </div>
        <Activities
          v-else
          doctype="CRM Lead"
          :tabs="tabs"
          v-model:reload="reload"
          v-model:tabIndex="tabIndex"
          v-model="lead"
        />
      </TabPanel>
    </Tabs>
  </div>
  <Dialog
    v-model="showConvertToDealModal"
    :options="{
      title: __('Convert to Deal'),
      size: 'xl',
      actions: [
        {
          label: __('Convert'),
          variant: 'solid',
          onClick: convertToDeal,
        },
      ],
    }"
  >
    <template #body-content>
      <div class="mb-4 flex items-center gap-2 text-ink-gray-5">
        <OrganizationsIcon class="h-4 w-4" />
        <label class="block text-base">{{ __('Organization') }}</label>
      </div>
      <div class="ml-6">
        <div class="flex items-center justify-between text-base">
          <div>{{ __('Choose Existing') }}</div>
          <Switch v-model="existingOrganizationChecked" />
        </div>
        <Link
          v-if="existingOrganizationChecked"
          class="form-control mt-2.5"
          variant="outline"
          size="md"
          :value="existingOrganization"
          doctype="CRM Organization"
          @change="(data) => (existingOrganization = data)"
        />
        <div v-else class="mt-2.5 text-base">
          {{
            __(
              'New organization will be created based on the data in details section',
            )
          }}
        </div>
      </div>

      <div class="mb-4 mt-6 flex items-center gap-2 text-ink-gray-5">
        <ContactsIcon class="h-4 w-4" />
        <label class="block text-base">{{ __('Contact') }}</label>
      </div>
      <div class="ml-6">
        <div class="flex items-center justify-between text-base">
          <div>{{ __('Choose Existing') }}</div>
          <Switch v-model="existingContactChecked" />
        </div>
        <Link
          v-if="existingContactChecked"
          class="form-control mt-2.5"
          variant="outline"
          size="md"
          :value="existingContact"
          doctype="Contact"
          @change="(data) => (existingContact = data)"
        />
        <div v-else class="mt-2.5 text-base">
          {{ __("New contact will be created based on the person's details") }}
        </div>
      </div>
    </template>
  </Dialog>
</template>
<script setup>
import Icon from '@/components/Icon.vue'
import DetailsIcon from '@/components/Icons/DetailsIcon.vue'
import ActivityIcon from '@/components/Icons/ActivityIcon.vue'
import EmailIcon from '@/components/Icons/EmailIcon.vue'
import CommentIcon from '@/components/Icons/CommentIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import AttachmentIcon from '@/components/Icons/AttachmentIcon.vue'
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import OrganizationsIcon from '@/components/Icons/OrganizationsIcon.vue'
import ContactsIcon from '@/components/Icons/ContactsIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import Activities from '@/components/Activities/Activities.vue'
import AssignTo from '@/components/AssignTo.vue'
import Link from '@/components/Controls/Link.vue'
import SidePanelLayout from '@/components/SidePanelLayout.vue'
import SLASection from '@/components/SLASection.vue'
import CustomActions from '@/components/CustomActions.vue'
import { setupCustomizations } from '@/utils'
import { getView } from '@/utils/view'
import { getSettings } from '@/stores/settings'
import { globalStore } from '@/stores/global'
import { statusesStore } from '@/stores/statuses'
import { getMeta } from '@/stores/meta'
import { useDocument } from '@/data/document'
import {
  whatsappEnabled,
  callEnabled,
  isMobileView,
} from '@/composables/settings'
import { capture } from '@/telemetry'
import { useActiveTabManager } from '@/composables/useActiveTabManager'
import {
  createResource,
  Dropdown,
  Tabs,
  TabList,
  TabPanel,
  Switch,
  Breadcrumbs,
  call,
  usePageMeta,
  toast,
} from 'frappe-ui'
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const { brand } = getSettings()
const { $dialog, $socket } = globalStore()
const { statusOptions, getLeadStatus } = statusesStore()
const { doctypeMeta } = getMeta('CRM Lead')
const route = useRoute()
const router = useRouter()

const props = defineProps({
  leadId: {
    type: String,
    required: true,
  },
})

const lead = createResource({
  url: 'crm.fcrm.doctype.crm_lead.api.get_lead',
  params: { name: props.leadId },
  cache: ['lead', props.leadId],
  onSuccess: (data) => {
    setupCustomizations(lead, {
      doc: data,
      $dialog,
      $socket,
      router,
      toast,
      updateField,
      createToast: toast.create,
      deleteDoc: deleteLead,
      resource: {
        lead,
        sections,
      },
      call,
    })
  },
})

onMounted(() => {
  if (lead.data) return
  lead.fetch()
})

const reload = ref(false)

function updateLead(fieldname, value, callback) {
  value = Array.isArray(fieldname) ? '' : value

  if (!Array.isArray(fieldname) && validateRequired(fieldname, value)) return

  createResource({
    url: 'frappe.client.set_value',
    params: {
      doctype: 'CRM Lead',
      name: props.leadId,
      fieldname,
      value,
    },
    auto: true,
    onSuccess: () => {
      lead.reload()
      reload.value = true
      toast.success(__('Lead updated successfully'))
      callback?.()
    },
    onError: (err) => {
      toast.error(__(err.messages?.[0] || 'Error updating lead'))
    },
  })
}

function validateRequired(fieldname, value) {
  let meta = lead.data.fields_meta || {}
  if (meta[fieldname]?.reqd && !value) {
    toast.error(__('{0} is a required field', [meta[fieldname].label]))
    return true
  }
  return false
}

const breadcrumbs = computed(() => {
  let items = [{ label: __('Leads'), route: { name: 'Leads' } }]

  if (route.query.view || route.query.viewType) {
    let view = getView(route.query.view, route.query.viewType, 'CRM Lead')
    if (view) {
      items.push({
        label: __(view.label),
        icon: view.icon,
        route: {
          name: 'Leads',
          params: { viewType: route.query.viewType },
          query: { view: route.query.view },
        },
      })
    }
  }

  items.push({
    label: title.value,
    route: { name: 'Lead', params: { leadId: lead.data.name } },
  })
  return items
})

const title = computed(() => {
  let t = doctypeMeta['CRM Lead']?.title_field || 'name'
  return lead.data?.[t] || props.leadId
})

usePageMeta(() => {
  return {
    title: title.value,
    icon: brand.favicon,
  }
})

const tabs = computed(() => {
  let tabOptions = [
    {
      name: 'Details',
      label: __('Details'),
      icon: DetailsIcon,
      condition: () => isMobileView.value,
    },
    {
      name: 'Activity',
      label: __('Activity'),
      icon: ActivityIcon,
    },
    {
      name: 'Emails',
      label: __('Emails'),
      icon: EmailIcon,
    },
    {
      name: 'Comments',
      label: __('Comments'),
      icon: CommentIcon,
    },
    {
      name: 'Data',
      label: __('Data'),
      icon: DetailsIcon,
    },
    {
      name: 'Calls',
      label: __('Calls'),
      icon: PhoneIcon,
      condition: () => callEnabled.value,
    },
    {
      name: 'Tasks',
      label: __('Tasks'),
      icon: TaskIcon,
    },
    {
      name: 'Notes',
      label: __('Notes'),
      icon: NoteIcon,
    },
    {
      name: 'Attachments',
      label: __('Attachments'),
      icon: AttachmentIcon,
    },
    {
      name: 'WhatsApp',
      label: __('WhatsApp'),
      icon: WhatsAppIcon,
      condition: () => whatsappEnabled.value,
    },
  ]
  return tabOptions.filter((tab) => (tab.condition ? tab.condition() : true))
})
const { tabIndex } = useActiveTabManager(tabs, 'lastLeadTab')

watch(tabs, (value) => {
  if (value && route.params.tabName) {
    let index = value.findIndex(
      (tab) => tab.name.toLowerCase() === route.params.tabName.toLowerCase(),
    )
    if (index !== -1) {
      tabIndex.value = index
    }
  }
})

const sections = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_sidepanel_sections',
  cache: ['sidePanelSections', 'CRM Lead'],
  params: { doctype: 'CRM Lead' },
  auto: true,
})

function updateField(name, value, callback) {
  updateLead(name, value, () => {
    lead.data[name] = value
    callback?.()
  })
}

async function deleteLead(name) {
  await call('frappe.client.delete', {
    doctype: 'CRM Lead',
    name,
  })
  router.push({ name: 'Leads' })
}

// Convert to Deal
const showConvertToDealModal = ref(false)
const existingContactChecked = ref(false)
const existingOrganizationChecked = ref(false)

const existingContact = ref('')
const existingOrganization = ref('')

async function convertToDeal() {
  if (existingContactChecked.value && !existingContact.value) {
    toast.error(__('Please select an existing contact'))
    return
  }

  if (existingOrganizationChecked.value && !existingOrganization.value) {
    toast.error(__('Please select an existing organization'))
    return
  }

  if (!existingContactChecked.value && existingContact.value) {
    existingContact.value = ''
  }

  if (!existingOrganizationChecked.value && existingOrganization.value) {
    existingOrganization.value = ''
  }

  let deal = await call('crm.fcrm.doctype.crm_lead.crm_lead.convert_to_deal', {
    lead: lead.data.name,
    deal: {},
    existing_contact: existingContact.value,
    existing_organization: existingOrganization.value,
  })
  if (deal) {
    showConvertToDealModal.value = false
    existingContactChecked.value = false
    existingOrganizationChecked.value = false
    existingContact.value = ''
    existingOrganization.value = ''
    capture('convert_lead_to_deal')
    router.push({ name: 'Deal', params: { dealId: deal } })
  }
}

const { assignees, document, triggerOnChange } = useDocument(
  'CRM Lead',
  props.leadId,
)

function reloadAssignees(data) {
  if (data?.hasOwnProperty('lead_owner')) {
    assignees.reload()
  }
}
</script>
