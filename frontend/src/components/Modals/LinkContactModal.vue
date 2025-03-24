<template>
  <Dialog
    v-model="show"
    :options="{
      title: __('Add Contact'),
      size: 'xl',
      actions: [
        {
          label: 'Add',
          variant: 'solid',
          onClick: addContact,
        },
      ],
    }"
  >
    <template #body-content>
      <div class="mb-4 mt-6 flex items-center gap-2 text-ink-gray-5">
        <ContactsIcon class="h-4 w-4" />
        <label class="block text-base">{{ __('Contact') }}</label>
      </div>
      <div class="ml-6">
        <div class="flex items-center justify-between text-base">
          <div>{{ __('Choose Existing') }}</div>
        </div>
        <Link
          class="form-control mt-2.5"
          variant="subtle"
          size="md"
          :value="existingContact"
          doctype="Contact"
          @change="(data) => (existingContact = data)"
        />
      </div>
      <div class="ml-6 mt-3">
        <div class="flex items-center justify-between text-base">
          <div>{{ __('Create New') }}</div>
          <Button
            variant="ghost"
            @click="
              show = false
              showNewContactModal = true
            "
          >
            <ArrowUpRightIcon class="h-4 w-4" />
          </Button>
        </div>
      </div>
    </template>
  </Dialog>
  <ContactModal v-model="showNewContactModal" />
</template>
<script setup>
import ContactModal from '@/components/Modals/ContactModal.vue'
import ContactsIcon from '@/components/Icons/ContactsIcon.vue'
import { ref } from 'vue'
import { call } from 'frappe-ui'
import Link from '@/components/Controls/Link.vue'
import ArrowUpRightIcon from '@/components/Icons/ArrowUpRightIcon.vue'
import { createToast } from '@/utils'

const show = defineModel()
const showNewContactModal = ref(false)
const existingContact = ref()

const props = defineProps({
  doctype: {
    type: String,
    default: '',
  },
  docname: {
    type: String,
    default: '',
  },
  options: {
    type: Object,
    default: {
      afterAddContact: () => {},
    },
  },
})

async function addContact() {
  try {
    const contact = await call('next_crm.api.contact.link_contact_to_doc', {
      contact: existingContact.value,
      doctype: props.doctype,
      docname: props.docname,
    })
    show.value = false
    props.options.afterAddContact(contact)
  } catch (error) {
    createToast({
      title: __('Error'),
      text: error,
      icon: 'x',
      iconClasses: 'text-ink-red-4',
    })
  }
}
</script>
