<template>
  <div class="flex flex-col gap-1 pt-3 text-base text-ink-gray-8">
    <div
      v-for="field in visibleFields"
      :key="field.fieldname"
      class="group flex items-center gap-1 pl-1"
    >
      <component :is="field.icon" class="h-4 w-4 shrink-0" />
      <div class="relative min-w-0 flex-1">
        <PrimaryDropdown
          v-if="contact.can_write"
          :value="contactDoc.doc[field.fieldname]"
          :placeholder="field.placeholder"
          :itemPlaceholder="field.itemPlaceholder"
          :options="field.options"
          :validate="field.validate"
          :onCreate="field.onCreate"
          :label="field.label"
        />
        <div v-else class="truncate px-2.5 py-1.5">
          {{ contactDoc.doc[field.fieldname] }}
        </div>
        <!-- Floats over the dropdown, left of its chevron, so the chevron
          keeps its place. Left visible on touch, which has no hover. -->
        <Button
          v-if="contactDoc.doc[field.fieldname]"
          variant="ghost"
          icon="lucide-copy"
          class="absolute top-1/2 -translate-y-1/2 transition-opacity focus-visible:opacity-100 [@media(hover:hover)]:opacity-0 [@media(hover:hover)]:group-hover:opacity-100"
          :class="contact.can_write ? 'right-7' : 'right-1'"
          :tooltip="field.copyLabel"
          :aria-label="field.copyLabel"
          @click="copyToClipboard(contactDoc.doc[field.fieldname])"
        />
      </div>
    </div>
    <div
      v-if="!visibleFields.length"
      class="flex items-center justify-center py-4 text-sm text-ink-gray-4"
    >
      {{ __('No Details Added') }}
    </div>
  </div>
</template>

<script setup>
import PrimaryDropdown from '@/components/PrimaryDropdown.vue'
import Email2Icon from '@/components/Icons/Email2Icon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import { useContactFields } from '@/composables/useContactFields'
import { copyToClipboard } from '@/utils'
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
    copyLabel: __('Copy email'),
  },
  {
    ...transformField({ fieldname: 'mobile_no', label: __('Mobile No') }),
    icon: PhoneIcon,
    placeholder: __('Add mobile no...'),
    copyLabel: __('Copy mobile no'),
  },
])

// Without Contact write access there is nothing to add, so empty rows go
const visibleFields = computed(() =>
  props.contact.can_write
    ? fields.value
    : fields.value.filter((field) => contactDoc.doc[field.fieldname]),
)
</script>
