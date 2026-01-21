<template>
  <Combobox :multiple="true">
    <Popover placement="bottom-end">
      <template #target="{ togglePopover }">
        <Button
          variant="subtle"
          icon-left="plus"
          @click="togglePopover()"
          :label="__('Add assignee')"
        />
      </template>
      <template #body="{ togglePopover }">
        <div class="mt-1 rounded-lg bg-white py-1 text-base shadow-2xl w-60">
          <div class="relative px-1.5 pt-0.5">
            <ComboboxInput
              ref="search"
              class="form-input w-full"
              type="text"
              @change="(e) => debouncedQuery(e.target.value)"
              :value="query"
              autocomplete="off"
              :placeholder="__('Search')"
            />
            <button
              class="absolute right-1.5 inline-flex h-7 w-7 items-center justify-center"
              @click="query = ''"
            >
              <FeatherIcon name="x" class="w-4" />
            </button>
          </div>
          <ComboboxOptions class="my-2 max-h-64 overflow-y-auto px-1.5" static>
            <ComboboxOption
              v-show="usersList.length > 0"
              v-for="user in usersList"
              :key="user.username"
              :value="user"
              as="template"
              v-slot="{ active }"
              @click="
                (e) => {
                  e.stopPropagation()
                  addAssignee(user)
                }
              "
            >
              <li
                class="flex items-center rounded p-1.5 w-full text-base"
                :class="{ 'bg-gray-100': active }"
              >
                <div class="flex gap-2 items-center w-full select-none">
                  <Avatar
                    :shape="'circle'"
                    :image="user.user_image"
                    :label="user.full_name"
                    size="lg"
                  />
                  <div class="flex flex-col gap-1">
                    <div class="font-semibold text-ink-gray-7">
                      {{ user.full_name }}
                    </div>
                    <div class="text-ink-gray-6">{{ user.email }}</div>
                  </div>
                </div>
              </li>
            </ComboboxOption>
            <li
              v-if="usersList.length == 0"
              class="mt-1.5 rounded-md p-1.5 text-base text-gray-600"
            >
              {{ __('No results found') }}
            </li>
          </ComboboxOptions>
          <div class="border-t p-1.5 pb-0.5 *:w-full">
            <Button
              variant="ghost"
              icon-left="plus"
              class="w-full"
              :label="__('Invite agent')"
              @click="
                () => {
                  inviteAgent()
                  togglePopover()
                }
              "
            />
          </div>
        </div>
      </template>
    </Popover>
  </Combobox>
</template>

<script setup>
import {
  Combobox,
  ComboboxInput,
  ComboboxOption,
  ComboboxOptions,
} from '@headlessui/vue'
import { useDebounceFn } from '@vueuse/core'
import { Avatar, Popover } from 'frappe-ui'
import { computed, inject, ref } from 'vue'
import { usersStore } from '@/stores/users'
import { globalStore } from '@/stores/global'
import { activeSettingsPage } from '@/composables/settings'

const emit = defineEmits(['addAssignee'])
const query = ref('')
const { users } = usersStore()
const { $dialog } = globalStore()
const assignmentRuleData = inject('assignmentRuleData')

const debouncedQuery = useDebounceFn((val) => {
  query.value = val
}, 300)

const usersList = computed(() => {
  let filteredUsers =
    users.data?.crmUsers?.filter((user) => user.name !== 'Administrator') || []

  return filteredUsers
    .filter(
      (user) =>
        user.name?.includes(query.value) ||
        user.full_name?.includes(query.value),
    )
    .filter((user) => {
      return !assignmentRuleData.value.users.some((u) => u.user === user.email)
    })
})

const addAssignee = (user) => {
  const userExists = assignmentRuleData.value.users.some(
    (u) => u.user === user.user,
  )
  if (!userExists) {
    assignmentRuleData.value.users.push({
      full_name: user.full_name,
      email: user.email,
      user_image: user.user_image,
      user: user.email,
    })
    emit('addAssignee', user)
  }
}

const inviteAgent = () => {
  $dialog({
    title: __('Invite agent'),
    message: __(
      'You will be redirected to invite user page, unsaved changes will be lost.',
    ),
    variant: 'solid',
    actions: [
      {
        label: __('Go to invite page'),
        variant: 'solid',
        onClick: (close) => {
          activeSettingsPage.value = 'Invite User'
          close()
        },
      },
    ],
  })
}
</script>
