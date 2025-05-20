<template>
  <div class="flex h-full flex-col gap-8 p-8 text-ink-gray-9">
    <div class="flex-1 flex flex-col gap-8 mt-2 overflow-y-auto">
      <div v-if="profile" class="flex w-full items-center justify-between">
        <div class="flex items-center gap-4">
          <Avatar
            class="!size-16"
            :image="profile.user_image"
            :label="profile.full_name"
          />
          <div class="flex flex-col gap-1">
            <span class="text-2xl font-semibold text-ink-gray-9">{{
              profile.full_name
            }}</span>
            <span class="text-base text-ink-gray-7">{{ profile.email }}</span>
          </div>
        </div>
        <Button
          :label="__('Edit profile photo')"
          @click="showEditProfilePhotoModal = true"
        />
        <Dialog
          :options="{ title: __('Edit profile photo') }"
          v-model="showEditProfilePhotoModal"
        >
          <template #body-content>
            <ProfileImageEditor v-model="profile" />
          </template>
          <template #actions>
            <Button
              variant="solid"
              class="w-full"
              :loading="loading"
              @click="updateUser"
              :label="__('Save')"
            />
          </template>
        </Dialog>
      </div>
      <div class="flex flex-col gap-4">
        <div class="flex justify-between gap-4">
          <FormControl
            class="w-full"
            label="First name"
            v-model="profile.first_name"
          />
          <FormControl
            class="w-full"
            label="Last name"
            v-model="profile.last_name"
          />
        </div>
        <div class="flex justify-between gap-4">
          <FormControl
            class="w-full"
            label="Email"
            v-model="profile.email"
            :disabled="true"
          />
          <FormControl
            class="w-full"
            label="Set new password"
            v-model="profile.new_password"
          />
        </div>
      </div>
    </div>
    <div class="flex justify-between flex-row-reverse">
      <Button
        variant="solid"
        :label="__('Update')"
        :loading="loading"
        @click="updateUser"
      />
      <ErrorMessage :message="error" />
    </div>
  </div>
</template>
<script setup>
import ProfileImageEditor from '@/components/Settings/ProfileImageEditor.vue'
import { usersStore } from '@/stores/users'
import { createToast } from '@/utils'
import { Dialog, Avatar, createResource, ErrorMessage } from 'frappe-ui'
import { ref, computed, onMounted } from 'vue'

const { getUser, users } = usersStore()

const user = computed(() => getUser() || {})

const showEditProfilePhotoModal = ref(false)

const profile = ref({})
const loading = ref(false)
const error = ref('')

function updateUser() {
  loading.value = true
  const fieldname = {
    first_name: profile.value.first_name,
    last_name: profile.value.last_name,
    user_image: profile.value.user_image,
    email: profile.value.email,
    new_password: profile.value.new_password,
  }
  createResource({
    url: 'frappe.client.set_value',
    params: {
      doctype: 'User',
      name: user.value.name,
      fieldname,
    },
    auto: true,
    onSuccess: () => {
      loading.value = false
      error.value = ''
      profile.value.new_password = ''
      showEditProfilePhotoModal.value = false
      createToast({
        title: __('Profile updated successfully'),
        icon: 'check',
        iconClasses: 'text-ink-green-3',
      })
      users.reload()
    },
    onError: (err) => {
      loading.value = false
      error.value = err.message
    },
  })
}

onMounted(() => {
  profile.value = { ...user.value }
})
</script>
