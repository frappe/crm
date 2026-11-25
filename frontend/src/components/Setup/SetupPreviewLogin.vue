<template>
  <SetupPreviewLogin
    :email="session.user"
    :password-length="state.passwordLength || 0"
    :ready="state.passwordReady"
    :email-link="false"
    :labels="labels"
  >
    <template #logo>
      <CRMLogo class="rounded-6" />
    </template>
  </SetupPreviewLogin>
</template>

<script setup>
import CRMLogo from '@/components/Icons/CRMLogo.vue'
import { sessionStore } from '@/stores/session'
import { SetupPreviewLogin } from '@framework/ui/components/SetupFlow'

defineProps({
  state: { type: Object, required: true },
})

const session = sessionStore()

const labels = {
  title: __('Sign In'),
  subtitle: __('Welcome! Please sign in to continue.'),
  email: __('Email'),
  password: __('Password'),
  forgot: __('Forgot password?'),
  submit: __('Continue'),
}
</script>
