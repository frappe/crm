<template>
  <SettingsLayoutBase
    :title="__('Profile')"
    :description="__('Manage your profile information.')"
  >
    <template #content>
      <div class="flex items-center justify-between gap-2">
        <FileUploader
          :validateFile="validateIsImageFile"
          @success="(file) => updateImage(file.file_url)"
        >
          <template #default="{ openFileSelector, error: _error, uploading }">
            <div class="flex items-center justify-center gap-2">
              <div class="group relative !size-14">
                <Avatar
                  class="!size-14"
                  :image="profile.user_image"
                  :label="profile.full_name"
                />
                <component
                  :is="profile.user_image ? Dropdown : 'div'"
                  v-bind="
                    profile.user_image
                      ? {
                          options: [
                            {
                              icon: 'upload',
                              label: profile.user_image
                                ? __('Change Image')
                                : __('Upload Image'),
                              onClick: openFileSelector,
                            },
                            {
                              icon: 'trash-2',
                              label: __('Remove Image'),
                              onClick: () => updateImage(),
                            },
                          ],
                        }
                      : { onClick: openFileSelector }
                  "
                >
                  <div
                    class="z-1 absolute top-0 left-0 flex h-9 cursor-pointer items-center justify-center rounded-full bg-black bg-opacity-40 opacity-0 duration-300 ease-in-out group-hover:opacity-100 !size-14"
                  >
                    <CameraIcon class="size-4 cursor-pointer text-white" />
                  </div>
                </component>
                <div
                  v-if="uploading"
                  class="w-full h-full top-0 left-0 absolute bg-black bg-opacity-20 rounded-full flex items-center justify-center"
                >
                  <LoadingIndicator class="size-4" />
                </div>
              </div>
              <div class="flex flex-col gap-1">
                <div class="flex flex-col gap-1">
                  <span
                    class="text-lg sm:text-xl !font-semibold text-ink-gray-8"
                  >
                    {{ profile.full_name }}
                  </span>
                  <span class="text-p-sm text-ink-gray-6">
                    {{ profile.email }}
                  </span>
                </div>
                <ErrorMessage :message="__(_error)" />
              </div>
            </div>
          </template>
        </FileUploader>
      </div>
      <hr class="my-6" />
      <div>
        <div class="flex items-center justify-between">
          <div class="flex gap-2 items-center">
            <div class="text-base font-semibold text-ink-gray-9">
              {{ __('Account Info & Security') }}
            </div>
            <Badge
              v-if="dirty || isLanguageChanged"
              :variant="'subtle'"
              :theme="'orange'"
              size="sm"
              :label="__('Not Saved')"
            />
          </div>
          <Button
            :label="__('Save')"
            :loading="setUser.loading || saveLanguageResource.loading"
            :disabled="!dirty && !isLanguageChanged"
            @click="onSave"
          />
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-5 mt-6">
          <FormControl
            v-model="profile.first_name"
            class="w-full"
            :label="__('First Name')"
            maxlength="40"
          />
          <FormControl
            v-model="profile.last_name"
            class="w-full"
            :label="__('Last Name')"
            maxlength="40"
          />
        </div>
        <div class="flex items-center justify-between mt-6">
          <div class="flex flex-col gap-1">
            <span class="text-base font-medium text-ink-gray-8">
              {{ __('Password') }}
            </span>
            <span class="text-p-sm text-ink-gray-6">
              {{ __('Change your account password for security.') }}
            </span>
          </div>
          <Button
            icon-left="lock"
            :label="__('Change Password')"
            @click="showChangePasswordModal = true"
          />
        </div>
        <div class="flex items-center justify-between mt-6">
          <div class="flex flex-col gap-1">
            <span class="text-base font-medium text-ink-gray-8">
              {{ __('Language') }}
            </span>
            <span class="text-p-sm text-ink-gray-6">
              {{ __('Change language of the application.') }}
            </span>
          </div>
          <Link
            :model-value="language"
            doctype="Language"
            class="w-40"
            @update:modelValue="language = $event || user.language"
          />
        </div>
      </div>
    </template>
  </SettingsLayoutBase>
  <ChangePasswordModal
    v-if="showChangePasswordModal"
    v-model="showChangePasswordModal"
  />
</template>

<script setup>
import SettingsLayoutBase from '@/components/Layouts/SettingsLayoutBase.vue'
import ChangePasswordModal from '@/components/Modals/ChangePasswordModal.vue'
import Link from '@/components/Controls/Link.vue'
import CameraIcon from '~icons/lucide/camera'
import { usersStore } from '@/stores/users'
import { validateIsImageFile } from '@/utils'
import {
  Avatar,
  Badge,
  Button,
  Dropdown,
  FileUploader,
  LoadingIndicator,
  createResource,
  toast,
} from 'frappe-ui'
import { ref, computed } from 'vue'
import { clearCache } from '../../utils'

const { getUser, users } = usersStore()

const user = computed(() => getUser() || {})

const profile = ref({ ...user.value })
const showChangePasswordModal = ref(false)
const language = ref(user.value.language)

const dirty = computed(() => {
  return (
    profile.value.first_name !== user.value.first_name ||
    profile.value.last_name !== user.value.last_name
  )
})

const isLanguageChanged = computed(() => {
  return language.value !== user.value.language
})

const setUser = createResource({
  url: 'frappe.client.set_value',
  makeParams() {
    return {
      doctype: 'User',
      name: user.value.name,
      fieldname: {
        first_name: profile.value.first_name,
        last_name: profile.value.last_name,
        user_image: profile.value.user_image,
      },
    }
  },
  async onSuccess() {
    await users.reload()
    profile.value = { ...user.value }
    toast.success(__('Profile Updated'))
  },
  onError: (err) => {
    toast.error(err.messages?.[0] || __('Failed to update profile'))
  },
})

const saveLanguageResource = createResource({
  url: 'frappe.client.set_value',
  makeParams() {
    return {
      doctype: 'User',
      name: user.value.name,
      fieldname: {
        language: language.value,
      },
    }
  },
  onSuccess() {
    toast.success(__('Language Updated'))
    clearCache()
    window.location.reload()
  },
})

const onSave = () => {
  if (dirty.value) {
    setUser.submit()
  }
  if (isLanguageChanged.value) {
    saveLanguageResource.submit()
  }
}

function updateImage(fileUrl = '') {
  profile.value.user_image = fileUrl
  setUser.submit()
}
</script>
