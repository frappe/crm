<template>
  <EnquiryPage :enquiryId="enquiryId" />
</template>

<script setup>
import EnquiryPage from '@/pages/Enquiry.vue'

const props = defineProps({
  enquiryId: {
    type: String,
    required: true,
  },
})
</script>
