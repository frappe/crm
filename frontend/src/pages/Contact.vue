<template>
  <div class="flex gap-6 p-5">
    <Avatar
      size="3xl"
      :image="contact.image"
      :label="contact.full_name"
      class="!h-24 !w-24"
    />
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
import { FeatherIcon, Avatar } from 'frappe-ui'
import ContactModal from '@/components/ContactModal.vue'
import EmailIcon from '@/components/Icons/EmailIcon.vue'
import EditIcon from '@/components/Icons/EditIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
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
</script>
