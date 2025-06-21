<template>
  <LayoutHeader v-if="visit.data">
    <header class="relative flex h-10.5 items-center justify-between gap-2 py-2.5 pl-2">
      <Breadcrumbs :items="breadcrumbs">
        <template #prefix="{ item }">
          <Icon v-if="item.icon" :icon="item.icon" class="mr-2 h-4" />
        </template>
      </Breadcrumbs>
      <div class="absolute right-0">
        <Dropdown :options="visitStatusOptions">
          <template #default="{ open }">
            <Button :label="visit.data.status || 'Planned'">
              <template #prefix>
                <IndicatorIcon :class="getStatusColor(visit.data.status)" />
              </template>
              <template #suffix>
                <FeatherIcon :name="open ? 'chevron-up' : 'chevron-down'" class="h-4" />
              </template>
            </Button>
          </template>
        </Dropdown>
      </div>
    </header>
  </LayoutHeader>
  <div v-if="visit.data" class="flex h-12 items-center justify-between gap-2 border-b px-3 py-2.5">
    <AssignTo v-model="visit.data._assignedTo" :data="visit.data" doctype="CRM Site Visit" />
    <div class="flex items-center gap-2">
      <CustomActions v-if="visit.data._customActions?.length" :actions="visit.data._customActions" />
      <!-- Check-in/Check-out buttons -->
      <Button v-if="visit.data.status === 'Planned' && isApp" :label="__('Check In')" variant="solid" size="sm"
        @click="checkIn" />
      <Button v-else-if="visit.data.status === 'In Progress' && isApp" :label="__('Check Out')" variant="solid"
        size="sm" @click="checkOut" />
      <Button v-else-if="visit.data.status === 'Completed' && visit.data.docstatus == 0" :label="__('Submit')"
        variant="solid" size="sm" @click="submit" />
    </div>
  </div>
  <div v-if="visit.data" class="flex h-full overflow-hidden">
    <Tabs as="div" v-model="tabIndex" :tabs="tabs" class="overflow-auto">
      <TabList class="!px-3" />
      <TabPanel v-slot="{ tab }">
        <div v-if="tab.name == 'Details'">
          <!-- Visit-specific mobile view -->
          <div class="p-4 space-y-4">
            <!-- Quick Actions -->
            <div class="bg-gray-50 rounded-lg p-3">
              <h3 class="text-sm font-medium text-gray-700 mb-2">{{ __('Quick Actions') }}</h3>
              <div class="grid grid-cols-2 gap-2">
                <Button v-if="visit.data.contact_phone" size="sm" variant="outline"
                  @click="makeCall(visit.data.contact_phone)">
                  <template #prefix>
                    <PhoneIcon class="h-4 w-4" />
                  </template>
                  {{ __('Call') }}
                </Button>
                <Button v-if="(visit.data.latitude && visit.data.longitude) || (visit.data.visit_address)" size="sm" variant="outline"
                  @click="openLocation">
                  <template #prefix>
                    <LinkIcon class="h-4 w-4" />
                  </template>
                  {{ __('Location') }}
                </Button>
              </div>
            </div>

            <!-- Visit Status Card -->
            <div class="bg-white border rounded-lg p-3">
              <div class="flex items-center justify-between mb-2">
                <h3 class="text-sm font-medium text-gray-700">{{ __('Visit Status') }}</h3>
                <span class="px-2 py-1 text-xs rounded-full" :class="getStatusBadgeClass(visit.data.status)">
                  {{ visit.data.status || 'Planned' }}
                </span>
              </div>
              <div class="space-y-1 text-sm">
                <div v-if="visit.data.check_in_time">
                  <span class="text-gray-500">{{ __('Checked in at:') }}</span>
                  <span class="font-medium">{{ formatDateTime(visit.data.check_in_time) }}</span>
                </div>
                <div v-if="visit.data.check_out_time">
                  <span class="text-gray-500">{{ __('Checked out at:') }}</span>
                  <span class="font-medium">{{ formatDateTime(visit.data.check_out_time) }}</span>
                </div>
                <div v-if="visit.data.visit_duration">
                  <span class="text-gray-500">{{ __('Duration:') }}</span>
                  <span class="font-medium">{{ visit.data.visit_duration }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Standard side panel layout -->
          <div v-if="sections.data" class="flex flex-1 flex-col justify-between overflow-hidden">
            <SidePanelLayout :sections="sections.data" doctype="CRM Site Visit" :docname="visit.data.name"
              @reload="sections.reload" />
          </div>
        </div>
        <Activities v-else doctype="CRM Site Visit" :tabs="tabs" v-model:reload="reload" v-model:tabIndex="tabIndex"
          v-model="visit" />
      </TabPanel>
    </Tabs>
  </div>
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
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import LinkIcon from '@/components/Icons/LinkIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import Activities from '@/components/Activities/Activities.vue'
import AssignTo from '@/components/AssignTo.vue'
import SidePanelLayout from '@/components/SidePanelLayout.vue'
import CustomActions from '@/components/CustomActions.vue'
import { setupAssignees, setupCustomizations } from '@/utils'
import { getView } from '@/utils/view'
import { getSettings } from '@/stores/settings'
import { globalStore } from '@/stores/global'
import { getMeta } from '@/stores/meta'
import { callEnabled, isMobileView } from '@/composables/settings'
import { useActiveTabManager } from '@/composables/useActiveTabManager'
import {
  createResource,
  Dropdown,
  Tabs,
  TabList,
  TabPanel,
  Breadcrumbs,
  call,
  usePageMeta,
  toast,
} from 'frappe-ui'
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const { brand } = getSettings()
const { $dialog, $socket, makeCall } = globalStore()
const { doctypeMeta } = getMeta('CRM Site Visit')

const route = useRoute()
const router = useRouter()
const isApp = window.isApp || false

const props = defineProps({
  visitId: {
    type: String,
    required: true,
  },
})

const visit = createResource({
  url: 'crm.fcrm.doctype.crm_site_visit.api.get_visit',
  params: { name: props.visitId },
  cache: ['visit', props.visitId],
  auto: true,
  onSuccess: (data) => {
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
})

onMounted(() => {
  if (visit.data) return
  visit.fetch()
})

const reload = ref(false)

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
  return visit.data?.[t] || props.visitId
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
  ]
  return tabOptions.filter((tab) => (tab.condition ? tab.condition() : true))
})

const { tabIndex } = useActiveTabManager(tabs, 'lastVisitTab')

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

function getStatusBadgeClass(status) {
  const classes = {
    'Planned': 'bg-blue-100 text-blue-800',
    'In Progress': 'bg-orange-100 text-orange-800',
    'Completed': 'bg-green-100 text-green-800',
    'Cancelled': 'bg-red-100 text-red-800',
  }
  return classes[status] || 'bg-gray-100 text-gray-800'
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

function formatDateTime(dateTime) {
  if (!dateTime) return ''
  return new Date(dateTime).toLocaleString()
}

function openLocation() {
  if (visit.data.latitude && visit.data.longitude) {
    const url = `https://www.google.com/maps?q=${visit.data.latitude},${visit.data.longitude}`
    window.openWindow(url, '_blank')
  } else if (visit.data.visit_address) {
    const address = encodeURIComponent(visit.data.visit_address)
    const url = `https://www.google.com/maps/search/?api=1&query=${address}`
    window.openWindow(url, '_blank')
  } else {
    toast.error(__('No location available for this visit.'))
  }
}

// Mobile-optimized check-in/check-out functions
async function checkIn() {
  try {
    if (window.isApp && typeof nativeInterface !== 'undefined' && nativeInterface.execute) {
      // Call native interface to get location
      const location = await nativeInterface.execute("getLocation").catch((err) => {
        toast.error(__('Failed to get location: {0}', [err.message]))
      });
      const { coords, mocked } = location;
      const { latitude, longitude, accuracy } = coords;
      if (mocked) {
        toast.error(__('Location appears to be mocked. Please disable mock location services.'));
      }
      await call('crm.api.site_visit.quick_checkin', {
        visit_id: props.visitId,
        latitude,
        longitude,
        accuracy,
      });
      visit.reload()
      toast.success(__('Checked in successfully!'))
    }
    // // Get current location
    // else if (navigator.geolocation) {
    //   navigator.geolocation.getCurrentPosition(
    //     async (position) => {
    //       const { latitude, longitude, accuracy } = position.coords

    //       await call('crm.api.site_visit.quick_checkin', {
    //         visit_id: props.visitId,
    //         latitude,
    //         longitude,
    //         accuracy,
    //       })

    //       visit.reload()
    //       toast.success(__('Checked in successfully!'))
    //     },
    //     (error) => {
    //       // Fallback for location error
    //       toast.error(__('Location access denied. Please enable location services.'))
    //     },
    //     {
    //       enableHighAccuracy: true,
    //       timeout: 10000,
    //       maximumAge: 60000,
    //     }
    //   )
    // } 
    else {

      toast.error(__('Geolocation is not supported by this device.'))
    }
  } catch (error) {
    toast.error(__('Check-in failed: {0}', [error.message]))
  }
}

async function checkOut() {
  try {
    if (window.isApp && typeof nativeInterface !== 'undefined' && nativeInterface.execute) {
      // Call native interface to get location
      const location = await nativeInterface.execute("getLocation").catch((err) => {
        toast.error(__('Failed to get location: {0}', [err.message]));
      });
      const { coords, mocked } = location;
      const { latitude, longitude, accuracy } = coords;
      if (mocked) {
        toast.error(__('Location appears to be mocked. Please disable mock location services.'));
      }

      await call('crm.api.site_visit.quick_checkout', {
        visit_id: props.visitId,
        latitude,
        longitude,
        visit_summary: '', // Could add a quick summary modal
        lead_quality: '', // Placeholder for lead quality
      });

      visit.reload()
      toast.success(__('Checked out successfully!'))
    }
    // // Get current location
    // if (navigator.geolocation) {
    //   navigator.geolocation.getCurrentPosition(
    //     async (position) => {
    //       const { latitude, longitude } = position.coords

    //       await call('crm.api.site_visit.quick_checkout', {
    //         visit_id: props.visitId,
    //         latitude,
    //         longitude,
    //         visit_summary: '', // Could add a quick summary modal
    //       })

    //       visit.reload()
    //       toast.success(__('Checked out successfully!'))
    //     },
    //     (error) => {
    //       toast.error(__('Location access denied. Please enable location services.'))
    //     },
    //     {
    //       enableHighAccuracy: true,
    //       timeout: 10000,
    //       maximumAge: 60000,
    //     }
    //   )
    // } 
    else {
      toast.error(__('Geolocation is not supported by this device.'))
    }
  } catch (error) {
    toast.error(__('Check-out failed: {0}', [error.message]))
  }
}

async function submit() {
  try {
    await call('crm.fcrm.doctype.crm_site_visit.crm_site_visit.submit_visit', {visit_id: props.visitId})
    visit.reload()
    toast.success(__('Visit submitted successfully!'))
  } catch (error) {
    toast.error(__('Failed to submit visit: {0}', [error.message]))
  }
}
</script>
