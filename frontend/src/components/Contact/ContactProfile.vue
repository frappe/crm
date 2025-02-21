<template>
  <div class="border-b">
    <FileUploader @success="handleImageChange" :validateFile="validateFile">
      <template #default="{ openFileSelector }">
        <div class="flex flex-col items-start justify-start gap-4 p-5">

          <div class="relative group cursor-pointer" @click="openFileSelector">
            <Avatar
              :image="contact.image"
              :label="contact.full_name"
              size="2xl"
              class="rounded-full transition-all duration-200 group-hover:opacity-75"
            />
            <div class="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
              <div class="p-2 bg-black bg-opacity-50 rounded-full">
                <FeatherIcon name="camera" class="w-5 h-5 text-white" />
              </div>
            </div>
          </div>

          <div class="flex gap-2 w-full">
            <Button
              v-if="callEnabled && contact.mobile_no"
              class="w-full"
              variant="solid"
              @click="makeCall"
            >
              <template #prefix>
                <FeatherIcon name="phone" class="w-4 h-4" />
              </template>
              {{ __('Call') }}
            </Button>
          </div>
        </div>
      </template>
    </FileUploader>
  </div>
</template>

<script setup>
import { Avatar, FileUploader, Button, FeatherIcon } from 'frappe-ui'
import { callEnabled } from '@/composables/settings'

const props = defineProps({
  contact: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['update'])

function validateFile(file) {
  let extn = file.name.split('.').pop().toLowerCase()
  if (!['png', 'jpg', 'jpeg'].includes(extn)) {
    return __('Only PNG and JPG images are allowed')
  }
}

async function handleImageChange(file) {
  await call('frappe.client.set_value', {
    doctype: 'Contact',
    name: props.contact.name,
    fieldname: 'image',
    value: file?.file_url || '',
  })
  emit('update')
}

function makeCall() {
  if (props.contact.mobile_no) {
    window.location.href = `tel:${props.contact.mobile_no}`
  }
}
</script>

<style scoped>
.group:hover .group-hover\:opacity-75 {
  opacity: 0.75;
}

.group:hover .group-hover\:opacity-100 {
  opacity: 1;
}
</style> 