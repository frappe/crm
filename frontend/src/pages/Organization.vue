<template>
  <div>
    <div class="flex gap-6 p-5">
      <FileUploader
        @success="changeOrganizationImage"
        :validateFile="validateFile"
      >
        <template #default="{ openFileSelector, error }">
          <div class="group relative h-24 w-24">
            <Avatar
              size="3xl"
              :image="organization.organization_logo"
              :label="organization.name"
              class="!h-24 !w-24"
            />
            <component
              :is="organization.organization_logo ? Dropdown : 'div'"
              v-bind="
                organization.organization_logo
                  ? {
                      options: [
                        {
                          icon: 'upload',
                          label: organization.organization_logo
                            ? 'Change image'
                            : 'Upload image',
                          onClick: openFileSelector,
                        },
                        {
                          icon: 'trash-2',
                          label: 'Remove image',
                          onClick: () => changeOrganizationImage(''),
                        },
                      ],
                    }
                  : { onClick: openFileSelector }
              "
              class="!absolute bottom-0 left-0 right-0"
            >
              <div
                class="z-1 absolute bottom-0 left-0 right-0 flex h-13 cursor-pointer items-center justify-center rounded-b-full bg-black bg-opacity-40 pt-3 opacity-0 duration-300 ease-in-out group-hover:opacity-100"
                style="
                  -webkit-clip-path: inset(12px 0 0 0);
                  clip-path: inset(12px 0 0 0);
                "
              >
                <CameraIcon class="h-6 w-6 cursor-pointer text-white" />
              </div>
            </component>
            <ErrorMessage class="mt-2" :message="error" />
          </div>
        </template>
      </FileUploader>
      <div class="flex flex-col justify-center gap-2">
        <div class="text-3xl font-semibold text-gray-900">
          {{ organization.name }}
        </div>
        <div class="flex items-center gap-2 text-base text-gray-700">
          <div v-if="organization.website" class="flex items-center gap-1.5">
            <WebsiteIcon class="h-4 w-4" />
            <span class="">{{ website(organization.website) }}</span>
          </div>
          <span
            v-if="organization.email_id"
            class="text-3xl leading-[0] text-gray-600"
            >&middot;</span
          >
          <div v-if="organization.email_id" class="flex items-center gap-1.5">
            <EmailIcon class="h-4 w-4" />
            <span class="">{{ organization.email_id }}</span>
          </div>
          <span
            v-if="
              (organization.name || organization.email_id) &&
              organization.mobile_no
            "
            class="text-3xl leading-[0] text-gray-600"
            >&middot;</span
          >
          <div v-if="organization.mobile_no" class="flex items-center gap-1.5">
            <PhoneIcon class="h-4 w-4" />
            <span class="">{{ organization.mobile_no }}</span>
          </div>
        </div>
        <div class="mt-1 flex gap-2">
          <Button label="Edit" size="sm" @click="showOrganizationModal = true">
            <template #prefix>
              <EditIcon class="h-4 w-4" />
            </template>
          </Button>
          <Button
            label="Delete"
            theme="red"
            size="sm"
            @click="deleteOrganization"
          >
            <template #prefix>
              <FeatherIcon name="trash-2" class="h-4 w-4" />
            </template>
          </Button>
          <!-- <Button label="Add lead" size="sm">
              <template #prefix>
                <FeatherIcon name="plus" class="h-4 w-4" />
              </template>
            </Button>
            <Button label="Add deal" size="sm">
              <template #prefix>
                <FeatherIcon name="plus" class="h-4 w-4" />
              </template>
            </Button> -->
        </div>
      </div>
    </div>
    <Tabs v-model="tabIndex" v-slot="{ tab }" :tabs="tabs">
      {{ tab.label }}
    </Tabs>
    <!-- <OrganizationModal
      v-model="showOrganizationModal"
      v-model:reloadOrganizations="organizations"
      :organization="organization"
      /> -->
  </div>
</template>

<script setup>
import {
  FeatherIcon,
  Avatar,
  FileUploader,
  ErrorMessage,
  Dropdown,
  call,
  Tabs,
} from 'frappe-ui'
// import OrganizationModal from '@/components/OrganizationModal.vue'
import WebsiteIcon from '@/components/Icons/WebsiteIcon.vue'
import EmailIcon from '@/components/Icons/EmailIcon.vue'
import EditIcon from '@/components/Icons/EditIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import CameraIcon from '@/components/Icons/CameraIcon.vue'
import LeadsIcon from '@/components/Icons/LeadsIcon.vue'
import DealsIcon from '@/components/Icons/DealsIcon.vue'
import ContactsIcon from '@/components/Icons/ContactsIcon.vue'
import { organizationsStore } from '@/stores/organizations.js'
import { h, ref } from 'vue'
const props = defineProps({
  organization: {
    type: Object,
    required: true,
  },
})
const { organizations } = organizationsStore()
const showOrganizationModal = ref(false)
function validateFile(file) {
  let extn = file.name.split('.').pop().toLowerCase()
  if (!['png', 'jpg', 'jpeg'].includes(extn)) {
    return 'Only PNG and JPG images are allowed'
  }
}
async function changeOrganizationImage(file) {
  await call('frappe.client.set_value', {
    doctype: 'Organization',
    name: props.organization.name,
    fieldname: 'image',
    value: file?.file_url || '',
  })
  organizations.reload()
}
async function deleteOrganization() {
  $dialog({
    title: 'Delete organization',
    message: 'Are you sure you want to delete this organization?',
    actions: [
      {
        label: 'Delete',
        theme: 'red',
        variant: 'solid',
        async onClick({ close }) {
          await call('frappe.client.delete', {
            doctype: 'Organization',
            name: props.organization.name,
          })
          organizations.reload()
          close()
        },
      },
    ],
  })
}
function website(url) {
  return url.replace(/^(?:https?:\/\/)?(?:www\.)?/i, '')
}
const tabIndex = ref(0)
const tabs = [
  {
    label: 'Leads',
    icon: h(LeadsIcon, { class: 'h-4 w-4' }),
  },
  {
    label: 'Deals',
    icon: h(DealsIcon, { class: 'h-4 w-4' }),
  },
  {
    label: 'Contacts',
    icon: h(ContactsIcon, { class: 'h-4 w-4' }),
  },
]
</script>
