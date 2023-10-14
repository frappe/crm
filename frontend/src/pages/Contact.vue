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
        <div class="flex items-center gap-1.5">
          <EmailIcon class="h-4 w-4" />
          <span class="">{{ contact.email_id }}</span>
        </div>
        <span class="text-3xl leading-[0] text-gray-600">&middot;</span>
        <div class="flex items-center gap-1.5">
          <PhoneIcon class="h-4 w-4" />
          <span class="">{{ contact.mobile_no }}</span>
        </div>
      </div>
      <div class="mt-1 flex gap-2">
        <Button label="Edit" size="sm">
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
  </div>
</template>

<script setup>
import { FeatherIcon, Avatar } from 'frappe-ui'
import EmailIcon from '@/components/Icons/EmailIcon.vue'
import EditIcon from '@/components/Icons/EditIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'

const props = defineProps({
  contact: {
    type: Object,
    required: true,
  },
})
</script>
