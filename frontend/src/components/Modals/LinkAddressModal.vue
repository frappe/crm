<template>
  <Dialog
    v-model="show"
    :options="{
      title: __('Add Address'),
      size: 'xl',
      actions: [
        {
          label: 'Add',
          variant: 'solid',
          onClick: addAddress,
        },
      ],
    }"
  >
    <template #body-content>
      <div class="mb-4 mt-6 flex items-center gap-2 text-ink-gray-5">
        <AddressIcon class="h-4 w-4" />
        <label class="block text-base">{{ __('Address') }}</label>
      </div>
      <div class="ml-6">
        <div class="flex items-center justify-between text-base">
          <div>{{ __('Choose Existing') }}</div>
        </div>
        <Link
          class="form-control mt-2.5"
          variant="subtle"
          size="md"
          :value="existingAddress"
          doctype="Address"
          @change="(data) => (existingAddress = data)"
        />
      </div>
      <div class="ml-6 mt-3">
        <div class="flex items-center justify-between text-base">
          <div>{{ __('Create New') }}</div>
          <Button
            variant="ghost"
            @click="
              show = false
              showNewAddressModal = true
            "
          >
            <ArrowUpRightIcon class="h-4 w-4" />
          </Button>
        </div>
      </div>
    </template>
  </Dialog>
  <AddressModal
    v-model="showNewAddressModal"
    :options="{
      afterInsert: addNewAddress,
    }"
  />
</template>
<script setup>
import AddressModal from '@/components/Modals/AddressModal.vue'
import AddressIcon from '@/components/Icons/AddressIcon.vue'
import { ref } from 'vue'
import { call } from 'frappe-ui'
import Link from '@/components/Controls/Link.vue'
import ArrowUpRightIcon from '@/components/Icons/ArrowUpRightIcon.vue'
import { createToast } from '@/utils'

const show = defineModel()
const showNewAddressModal = ref(false)
const existingAddress = ref()

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
      afterAddAddress: () => {},
    },
  },
})

async function addAddress() {
  try {
    const address = await call('next_crm.api.address.link_address_to_doc', {
      address: existingAddress.value,
      doctype: props.doctype,
      docname: props.docname,
    })
    show.value = false
    props.options.afterAddAddress(address)
  } catch (error) {
    createToast({
      title: __('Error'),
      text: error,
      icon: 'x',
      iconClasses: 'text-ink-red-4',
    })
  }
}

function addNewAddress(doc) {
  existingAddress.value = doc.name
  addAddress()
}
</script>
