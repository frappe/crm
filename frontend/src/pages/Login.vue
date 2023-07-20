<template>
  <div class="flex h-screen w-screen justify-center bg-gray-100">
    <div class="mt-32 w-full px-4">
      <div class="mx-auto mt-6 w-full px-4 sm:w-96">
        <form method="POST" action="/api/method/login" @submit.prevent="submit">
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
        </form>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref } from 'vue'
import { FormControl, ErrorMessage } from 'frappe-ui'
import { sessionStore } from '@/stores/session'

const session = sessionStore()
let email = ref('')
let password = ref('')

function submit() {
  session.login.submit({
    usr: email.value,
    pwd: password.value,
  })
}
</script>
