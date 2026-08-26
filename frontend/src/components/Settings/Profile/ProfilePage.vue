<template>
  <ProfileSettings
    v-if="step === 'profile-settings'"
    @updateStep="updateStep"
  />
  <UserEmailSettings
    v-else-if="step === 'user-email-settings'"
    @updateStep="updateStep"
  />
</template>
<script setup>
import ProfileSettings from './ProfileSettings.vue'
import UserEmailSettings from './UserEmailSettings.vue'
import { ref } from 'vue'

const step = ref('profile-settings')

function updateStep(newStep) {
  step.value = newStep
}
</script>
