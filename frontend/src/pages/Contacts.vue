<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs" />
    </template>
    <template #right-header>
      <Button variant="solid" label="Create" @click="showContactModal = true">
        <template #prefix><FeatherIcon name="plus" class="h-4" /></template>
      </Button>
    </template>
  </LayoutHeader>
  <div class="flex h-full overflow-hidden">
    <div class="flex flex-col overflow-y-auto border-r">
      <router-link
        :to="{ name: 'Contact', params: { contactId: contact.name } }"
        v-for="(contact, i) in contacts.data"
        :key="i"
        :class="[
          currentContact?.name === contact.name
            ? 'bg-gray-50 hover:bg-gray-100'
            : 'hover:bg-gray-50',
        ]"
      >
        <div class="flex w-[352px] items-center gap-3 border-b px-5 py-4">
          <Avatar :image="contact.image" :label="contact.full_name" size="xl" />
          <div class="flex flex-col items-start gap-1">
            <span class="text-base font-medium text-gray-900">
              {{ contact.full_name }}
            </span>
            <span class="text-sm text-gray-700">{{ contact.email_id }}</span>
          </div>
        </div>
      </router-link>
    </div>
    <div class="flex-1">
      <router-view v-if="currentContact" :contact="currentContact" />
      <div
        v-else
        class="grid h-full place-items-center text-xl font-medium text-gray-500"
      >
        <div class="flex flex-col items-center justify-center space-y-2">
          <ContactsIcon class="h-10 w-10" />
          <div>No contact selected</div>
        </div>
      </div>
    </div>
  </div>
  <ContactModal
    v-model="showContactModal"
    v-model:reloadContacts="contacts"
    :contact="{}"
  />
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import ContactModal from '@/components/ContactModal.vue'
import ContactsIcon from '@/components/Icons/ContactsIcon.vue'
import { FeatherIcon, Breadcrumbs, Avatar } from 'frappe-ui'
import { contactsStore } from '@/stores/contacts.js'
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'

const { contacts } = contactsStore()
const route = useRoute()

const showContactModal = ref(false)

const currentContact = computed(() => {
  return contacts.data.find(
    (contact) => contact.name === route.params.contactId
  )
})

const breadcrumbs = computed(() => {
  let items = [{ label: 'Contacts', route: { name: 'Contacts' } }]
  if (!currentContact.value) return items
  items.push({
    label: currentContact.value.full_name,
    route: {
      name: 'Contact',
      params: { contactId: currentContact.value.name },
    },
  })
  return items
})

onMounted(() => {
  const el = document.querySelector('.router-link-active')
  if (el)
    setTimeout(() => {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' })
    })
})
</script>
