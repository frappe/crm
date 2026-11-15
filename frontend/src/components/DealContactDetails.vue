<template>
  <div class="flex flex-col gap-1 pt-3 text-base text-ink-gray-8">
    <div
      v-for="field in fields"
      :key="field.fieldname"
      class="flex items-center gap-1 pl-1"
    >
      <component :is="field.icon" class="h-4 w-4 shrink-0" />
      <div class="min-w-0 flex-1">
        <PrimaryDropdown
          :value="contactDoc.doc[field.fieldname]"
          :placeholder="field.placeholder"
          :itemPlaceholder="field.itemPlaceholder"
          :options="field.options"
          :validate="field.validate"
          :onCreate="field.onCreate"
          :label="field.label"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import PrimaryDropdown from '@/components/PrimaryDropdown.vue'
import Email2Icon from '@/components/Icons/Email2Icon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import { useContactFields } from '@/composables/useContactFields'
import { computed, reactive, watch } from 'vue'

// Email and mobile rows of a deal's contact, edited with the same dropdown as
// the Contact page: pick a primary, edit, delete or add a value in place.
const props = defineProps({
  // A row from get_deal_contacts
  contact: { type: Object, required: true },
  // Reloads the deal's contacts (and the deal, whose email/mobile follow the
  // primary contact's) after a change
  reload: { type: Function, required: true },
})

// Shaped like the Contact document useContactFields expects. Reactive, so a
// deleted value drops out of the dropdown before the reload lands.
const contactDoc = reactive({ doc: {}, reload: () => props.reload() })

watch(
  () => props.contact,
  (contact) => {
    contactDoc.doc = {
      name: contact.name,
      email_id: contact.email,
      mobile_no: contact.mobile_no,
      email_ids: contact.email_ids || [],
      phone_nos: contact.phone_nos || [],
    }
  },
  { immediate: true, deep: true },
)

const transformField = useContactFields(contactDoc)

const fields = computed(() => [
  {
    ...transformField({ fieldname: 'email_id', label: __('Email') }),
    icon: Email2Icon,
    placeholder: __('Add email...'),
  },
  {
    ...transformField({ fieldname: 'mobile_no', label: __('Mobile No') }),
    icon: PhoneIcon,
    placeholder: __('Add mobile no...'),
  },
])
</script>
