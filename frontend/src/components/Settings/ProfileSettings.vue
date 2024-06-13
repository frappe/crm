<template>
  <div v-if="profile" class="flex w-full items-center justify-between p-12 pt-14">
    <div class="flex items-center gap-4">
      <Avatar
        class="!size-16"
        :image="profile.user_image"
        :label="profile.full_name"
      />
      <div class="flex flex-col gap-1">
        <span class="text-2xl font-semibold">{{ profile.full_name }}</span>
        <span class="text-base text-gray-700">{{ profile.email }}</span>
      </div>
    </div>
    <Button :label="__('Edit profile')" @click="showProfileModal = true" />
    <Dialog
      :options="{ title: __('Edit Profile') }"
      v-model="showProfileModal"
      @after-leave="editingProfilePhoto = false"
    >
      <template #body-content>
        <div v-if="user" class="space-y-4">
          <ProfileImageEditor v-model="profile" v-if="editingProfilePhoto" />
          <template v-else>
            <div class="flex items-center gap-4">
              <Avatar
                size="lg"
                :image="profile.user_image"
                :label="profile.full_name"
              />
              <Button
                :label="__('Edit Profile Photo')"
                @click="editingProfilePhoto = true"
              />
            </div>
            <FormControl label="First Name" v-model="profile.first_name" />
            <FormControl label="Last Name" v-model="profile.last_name" />
          </template>
        </div>
      </template>
      <template #actions>
        <Button
          v-if="editingProfilePhoto"
          class="mb-2 w-full"
          @click="editingProfilePhoto = false"
          :label="__('Back')"
        />
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
</template>
<script setup>
import ProfileImageEditor from '@/components/Settings/ProfileImageEditor.vue'
import { usersStore } from '@/stores/users'
import { Dialog, Avatar, createResource } from 'frappe-ui'
import { ref, computed, onMounted } from 'vue'

const { getUser, users } = usersStore()

const user = computed(() => getUser() || {})

const showProfileModal = ref(false)

const editingProfilePhoto = ref(false)
const profile = ref({})
const loading = ref(false)

function updateUser() {
  loading.value = true
  const fieldname = {
    first_name: profile.value.first_name,
    last_name: profile.value.last_name,
    user_image: profile.value.user_image,
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
      showProfileModal.value = false
      users.reload()
    },
  })
}

onMounted(() => {
  profile.value = { ...user.value }
})
</script>
