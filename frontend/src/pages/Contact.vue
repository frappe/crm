<template>
  <div class="flex gap-6 p-5">
    <FileUploader @success="changeContactImage" :validateFile="validateFile">
      <template #default="{ openFileSelector, error }">
        <div class="group relative h-24 w-24">
          <Avatar
            size="3xl"
            :image="contact.image"
            :label="contact.full_name"
            class="!h-24 !w-24"
          />
          <component
            :is="contact.image ? Dropdown : 'div'"
            v-bind="
              contact.image
                ? {
                    options: [
                      {
                        icon: 'upload',
                        label: contact.image ? 'Change image' : 'Upload image',
                        onClick: openFileSelector,
                      },
                      {
                        icon: 'trash-2',
                        label: 'Remove image',
                        onClick: () => changeContactImage(''),
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
        {{ contact.salutation + ' ' + contact.full_name }}
      </div>
      <div class="flex items-center gap-2 text-base text-gray-700">
        <div v-if="contact.email_id" class="flex items-center gap-1.5">
          <EmailIcon class="h-4 w-4" />
          <span class="">{{ contact.email_id }}</span>
        </div>
        <span
          v-if="contact.mobile_no"
          class="text-3xl leading-[0] text-gray-600"
          >&middot;</span
        >
        <div v-if="contact.mobile_no" class="flex items-center gap-1.5">
          <PhoneIcon class="h-4 w-4" />
          <span class="">{{ contact.mobile_no }}</span>
        </div>
        <span
          v-if="(contact.email_id || contact.mobile_no) && contact.company_name"
          class="text-3xl leading-[0] text-gray-600"
          >&middot;</span
        >
        <div v-if="contact.company_name" class="flex items-center gap-1.5">
          <Avatar :label="contact.company_name" size="xs" />
          <span class="">{{ contact.company_name }}</span>
        </div>
      </div>
      <div class="mt-1 flex gap-2">
        <Button label="Edit" size="sm" @click="showContactModal = true">
          <template #prefix>
            <EditIcon class="h-4 w-4" />
          </template>
        </Button>
        <Button label="Add lead" size="sm">
          <template #prefix>
            <FeatherIcon name="plus" class="h-4 w-4" />
          </template>
        </Button>
        <Button label="Add deal" size="sm">
          <template #prefix>
            <FeatherIcon name="plus" class="h-4 w-4" />
          </template>
        </Button>
      </div>
    </div>
    <ContactModal
      v-model="showContactModal"
      v-model:reloadContacts="contacts"
      :contact="contact"
    />
  </div>
</template>

<script setup>
import {
  FeatherIcon,
  Avatar,
  FileUploader,
  createResource,
  ErrorMessage,
  Dropdown,
} from 'frappe-ui'
import ContactModal from '@/components/ContactModal.vue'
import EmailIcon from '@/components/Icons/EmailIcon.vue'
import EditIcon from '@/components/Icons/EditIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import CameraIcon from '@/components/Icons/CameraIcon.vue'
import { contactsStore } from '@/stores/contacts.js'
import { ref } from 'vue'

const props = defineProps({
  contact: {
    type: Object,
    required: true,
  },
})

const { contacts } = contactsStore()

const showContactModal = ref(false)

function validateFile(file) {
  let extn = file.name.split('.').pop().toLowerCase()
  if (!['png', 'jpg', 'jpeg'].includes(extn)) {
    return 'Only PNG and JPG images are allowed'
  }
}

function changeContactImage(file) {
  createResource({
    url: 'frappe.client.set_value',
    params: {
      doctype: 'Contact',
      name: props.contact.name,
      fieldname: 'image',
      value: file?.file_url || '',
    },
    auto: true,
    onSuccess: () => {
      contacts.reload()
    },
  })
}
</script>
