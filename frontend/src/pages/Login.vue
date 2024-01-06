<template>
  <div class="flex h-screen w-screen justify-center bg-gray-100">
    <div class="mt-32 w-full px-4">
      <CRMLogo class="mx-auto h-10" />
      <div class="mt-6 flex items-center justify-center space-x-1.5">
        <span class="text-3xl font-semibold text-gray-900">Login to CRM</span>
      </div>
      <div class="mx-auto mt-6 w-full px-4 sm:w-96">
        <form
          v-if="showEmailLogin"
          method="POST"
          action="/api/method/login"
          @submit.prevent="submit"
        >
          <div>
            <FormControl
              variant="outline"
              size="md"
              :type="
                (email || '').toLowerCase() === 'administrator'
                  ? 'text'
                  : 'email'
              "
              label="Email"
              v-model="email"
              placeholder="jane@example.com"
              :disabled="session.login.loading"
            />
          </div>
          <div class="mt-4">
            <FormControl
              variant="outline"
              size="md"
              label="Password"
              v-model="password"
              placeholder="••••••"
              :disabled="session.login.loading"
              type="password"
            />
          </div>
          <ErrorMessage class="mt-2" :message="session.login.error" />
          <Button
            variant="solid"
            class="mt-6 w-full"
            :loading="session.login.loading"
          >
            Login
          </Button>
          <button
            v-if="authProviders.data.length"
            class="mt-2 w-full py-2 text-base text-gray-600"
            @click="showEmailLogin = false"
          >
            Login using other methods
          </button>
        </form>
        <div
          class="mx-auto space-y-2"
          v-if="authProviders.data && !showEmailLogin"
        >
          <Button @click="showEmailLogin = true" variant="solid" class="w-full">
            Login via email
          </Button>
          <a
            class="flex justify-center items-center gap-2 w-full rounded border bg-gray-900 px-3 py-1 text-center text-base h-7 focus:outline-none focus:ring-2 focus:ring-gray-400 text-white transition-colors hover:bg-gray-700"
            v-for="provider in authProviders.data"
            :key="provider.name"
            :href="provider.auth_url"
          >
            <div v-if="provider.icon" v-html="provider.icon" />
            Login via {{ provider.provider_name }}
          </a>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import CRMLogo from '@/components/Icons/CRMLogo.vue';
import { sessionStore } from '@/stores/session'
import { createResource } from 'frappe-ui'
import { ref } from 'vue'

const session = sessionStore()
let showEmailLogin = ref(false)
let email = ref('')
let password = ref('')

let authProviders = createResource({
  url: 'crm.api.auth.oauth_providers',
  auto: true,
  onSuccess(data) {
    showEmailLogin.value = data.length === 0
  },
})
authProviders.fetch()

function submit() {
  session.login.submit({
    usr: email.value,
    pwd: password.value,
  })
}
</script>
