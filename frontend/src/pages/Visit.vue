<template>
  <LayoutHeader v-if="visit?.data">
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs">
        <template #prefix="{ item }">
          <Icon v-if="item.icon" :icon="item.icon" class="mr-2 h-4" />
        </template>
      </Breadcrumbs>
    </template>
    <template #right-header>
      <CustomActions
        v-if="visit.data._customActions?.length"
        :actions="visit.data._customActions"
      />
      <AssignTo
        v-model="visit.data._assignedTo"
        :data="visit.data"
        doctype="CRM Site Visit"
      />
      <Dropdown
        :options="visitStatusOptions"
      >
        <template #default="{ open }">
          <Button :label="visit.data.status || 'Planned'">
            <template #prefix>
              <IndicatorIcon :class="getStatusColor(visit.data.status)" />
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
    </template>
  </LayoutHeader>
  <div v-if="visit?.data" class="flex h-full overflow-hidden">
    <Tabs as="div" v-model="tabIndex" :tabs="tabs">
      <template #tab-panel>
        <Activities
          ref="activities"
          doctype="CRM Site Visit"
          :tabs="tabs"
          v-model:reload="reload"
          v-model:tabIndex="tabIndex"
          v-model="visit"
        />
      </template>
    </Tabs>
    <Resizer class="flex flex-col justify-between border-l" side="right">
      <div
        class="flex h-10.5 cursor-copy items-center border-b px-5 py-2.5 text-lg font-medium text-ink-gray-9"
        @click="copyToClipboard(visit.data.name)"
      >
        {{ __(visit.data.name) }}
      </div>
      <div class="flex items-center justify-start gap-5 border-b p-5">
        <div class="group relative size-12">
          <Avatar
            size="3xl"
            class="size-12"
            :label="title"
            :image="null"
          />
        </div>
        <div class="flex flex-col gap-2.5 truncate">
          <Tooltip :text="visit.data.visit_to || __('Visit Title')">
            <div class="truncate text-2xl font-medium text-ink-gray-9">
              {{ title }}
            </div>
          </Tooltip>
          <div class="flex gap-1.5">
            <Tooltip v-if="callEnabled" :text="__('Make a call')">
              <div>
                <Button
                  class="h-7 w-7"
                  @click="
                    () =>
                      visit.data.contact_phone
                        ? makeCall(visit.data.contact_phone)
                        : toast.error(__('No phone number set'))
                  "
                >
                  <PhoneIcon class="h-4 w-4" />
                </Button>
              </div>
            </Tooltip>
            <Tooltip :text="__('Send an email')">
              <div>
                <Button class="h-7 w-7">
                  <Email2Icon
                    class="h-4 w-4"
                    @click="
                      visit.data.contact_email
                        ? openEmailBox()
                        : toast.error(__('No email set'))
                    "
                  />
                </Button>
              </div>
            </Tooltip>
            <Tooltip :text="__('Check Location')">
              <div>
                <Button class="h-7 w-7">
                  <LinkIcon
                    class="h-4 w-4"
                    @click="
                      visit.data.latitude && visit.data.longitude
                        ? openLocation()
                        : toast.error(__('No location set'))
                    "
                  />
                </Button>
              </div>
            </Tooltip>
            <Tooltip :text="__('Attach a file')">
              <div>
                <Button class="h-7 w-7" @click="showFilesUploader = true">
                  <AttachmentIcon class="h-4 w-4" />
                </Button>
              </div>
            </Tooltip>
          </div>
        </div>
      </div>
      <div
        v-if="sections.data"
        class="flex flex-1 flex-col justify-between overflow-hidden"
      >
        <SidePanelLayout
          :sections="sections.data"
          doctype="CRM Site Visit"
          :docname="visit.data.name"
          @reload="sections.reload"
        />
      </div>
    </Resizer>
  </div>
  <ErrorPage
    v-else-if="errorTitle"
    :errorTitle="errorTitle"
    :errorMessage="errorMessage"
  />
  <FilesUploader
    v-if="visit.data?.name"
    v-model="showFilesUploader"
    doctype="CRM Site Visit"
    :docname="visit.data.name"
    @after="
      () => {
        activities?.all_activities?.reload()
        changeTabTo('attachments')
      }
    "
  />
</template>

<script setup>
import ErrorPage from '@/components/ErrorPage.vue'
import Icon from '@/components/Icon.vue'
import Resizer from '@/components/Resizer.vue'
import ActivityIcon from '@/components/Icons/ActivityIcon.vue'
import EmailIcon from '@/components/Icons/EmailIcon.vue'
import Email2Icon from '@/components/Icons/Email2Icon.vue'
import CommentIcon from '@/components/Icons/CommentIcon.vue'
import DetailsIcon from '@/components/Icons/DetailsIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import LinkIcon from '@/components/Icons/LinkIcon.vue'
import AttachmentIcon from '@/components/Icons/AttachmentIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import Activities from '@/components/Activities/Activities.vue'
import AssignTo from '@/components/AssignTo.vue'
import FilesUploader from '@/components/FilesUploader/FilesUploader.vue'
import SidePanelLayout from '@/components/SidePanelLayout.vue'
import CustomActions from '@/components/CustomActions.vue'
import {
  setupAssignees,
  setupCustomizations,
  copyToClipboard,
} from '@/utils'
import { getView } from '@/utils/view'
import { getSettings } from '@/stores/settings'
import { globalStore } from '@/stores/global'
import { statusesStore } from '@/stores/statuses'
import { getMeta } from '@/stores/meta'
import { callEnabled } from '@/composables/settings'
import {
  createResource,
  createDocumentResource,
  Dropdown,
  Tooltip,
  Avatar,
  Tabs,
  Breadcrumbs,
  call,
  Button,
  usePageMeta,
  toast,
} from 'frappe-ui'
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useActiveTabManager } from '@/composables/useActiveTabManager'

const { brand } = getSettings()
const { $dialog, $socket, makeCall } = globalStore()
const { statusOptions } = statusesStore()
const { doctypeMeta } = getMeta('CRM Site Visit')

const route = useRoute()
const router = useRouter()

const props = defineProps({
  visitId: {
    type: String,
    required: true,
  },
})

const errorTitle = ref('')
const errorMessage = ref('')


const visit = createResource({
  url: 'crm.fcrm.doctype.crm_site_visit.api.get_visit',
  params: { name: props.visitId },
  cache: ['visit', props.visitId],
  auto: true,
  onSuccess: (data) => {
    console.log("Visit data fetched successfully:", data);
    errorTitle.value = ''
    errorMessage.value = ''
    setupAssignees(visit)
    setupCustomizations(visit, {
      doc: data,
      $dialog,
      $socket,
      router,
      toast,
      updateField,
      createToast: toast.create,
      deleteDoc: deleteVisit,
      resource: { visit, sections },
      call,
    })
  },
  onError: (err) => {
    if (err.messages?.[0]) {
      errorTitle.value = __('Not permitted')
      errorMessage.value = __(err.messages?.[0])
    } else {
      router.push({ name: 'Visits' })
    }
  },
})

onMounted(() => {
  if (visit?.data) return
  visit.fetch()
  console.log("Visit mounted, fetching data for ID:", props.visitId);
  
})

const reload = ref(false)
const showFilesUploader = ref(false)

function updateVisit(fieldname, value, callback) {
  value = Array.isArray(fieldname) ? '' : value

  if (!Array.isArray(fieldname) && validateRequired(fieldname, value)) return

  createResource({
    url: 'frappe.client.set_value',
    params: {
      doctype: 'CRM Site Visit',
      name: props.visitId,
      fieldname,
      value,
    },
    auto: true,
    onSuccess: () => {
      visit.reload()
      reload.value = true
      toast.success(__('Visit updated successfully'))
      callback?.()
    },
    onError: (err) => {
      toast.error(err.messages?.[0] || __('Error updating visit'))
    },
  })
}

function validateRequired(fieldname, value) {
  let meta = visit.data.fields_meta || {}
  if (meta[fieldname]?.reqd && !value) {
    toast.error(__('{0} is a required field', [meta[fieldname].label]))
    return true
  }
  return false
}

const breadcrumbs = computed(() => {
  let items = [{ label: __('Visits'), route: { name: 'Visits' } }]

  if (route.query.view || route.query.viewType) {
    let view = getView(route.query.view, route.query.viewType, 'CRM Site Visit')
    if (view) {
      items.push({
        label: __(view.label),
        icon: view.icon,
        route: {
          name: 'Visits',
          params: { viewType: route.query.viewType },
          query: { view: route.query.view },
        },
      })
    }
  }

  items.push({
    label: title.value,
    route: { name: 'Visit', params: { visitId: visit.data.name } },
  })
  return items
})

const title = computed(() => {
  let t = doctypeMeta['CRM Site Visit']?.title_field || 'name'
  return visit?.data?.[t] || props.visitId
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
  ]
  return tabOptions
})

const { tabIndex, changeTabTo } = useActiveTabManager(tabs, 'lastVisitTab')

const sections = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_sidepanel_sections',
  cache: ['sidePanelSections', 'CRM Site Visit'],
  params: { doctype: 'CRM Site Visit' },
  auto: true,
})

// Visit status options
const visitStatusOptions = computed(() => [
  {
    label: __('Planned'),
    onClick: () => updateField('status', 'Planned'),
  },
  {
    label: __('In Progress'),
    onClick: () => updateField('status', 'In Progress'),
  },
  {
    label: __('Completed'),
    onClick: () => updateField('status', 'Completed'),
  },
  {
    label: __('Cancelled'),
    onClick: () => updateField('status', 'Cancelled'),
  },
])

function getStatusColor(status) {
  const colors = {
    'Planned': 'text-blue-600',
    'In Progress': 'text-orange-600',
    'Completed': 'text-green-600',
    'Cancelled': 'text-red-600',
  }
  return colors[status] || 'text-gray-600'
}

function updateField(name, value, callback) {
  updateVisit(name, value, () => {
    visit.data[name] = value
    callback?.()
  })
}

async function deleteVisit(name) {
  await call('frappe.client.delete', {
    doctype: 'CRM Site Visit',
    name,
  })
  router.push({ name: 'Visits' })
}

const activities = ref(null)

function openEmailBox() {
  activities.value.emailBox.show = true
}

function openLocation() {
  if (visit.data.latitude && visit.data.longitude) {
    const url = `https://www.google.com/maps?q=${visit.data.latitude},${visit.data.longitude}`
    window.open(url, '_blank')
  }
}
</script>
