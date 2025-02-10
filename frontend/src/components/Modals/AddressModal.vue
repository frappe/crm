<template>
  <Dialog v-model="show" :options="dialogOptions">
    <template #body>
      <div class="bg-surface-modal px-4 pb-6 pt-5 sm:px-6">
        <div class="mb-5 flex items-center justify-between">
          <div>
            <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">
              {{ __(dialogOptions.title) || __('Untitled') }}
            </h3>
          </div>
          <div class="flex items-center gap-1">
            <Button
              v-if="isManager() && !isMobileView"
              variant="ghost"
              class="w-7"
              @click="openQuickEntryModal"
            >
              <EditIcon class="h-4 w-4" />
            </Button>
            <Button variant="ghost" class="w-7" @click="show = false">
              <FeatherIcon name="x" class="h-4 w-4" />
            </Button>
          </div>
        </div>
        <div v-if="tabs.data">
          <FieldLayout :tabs="tabs.data" :data="_address" doctype="Address" />
          <ErrorMessage class="mt-2" :message="error" />
        </div>
      </div>
      <div class="px-4 pb-7 pt-4 sm:px-6">
        <div class="space-y-2">
          <Button
            class="w-full"
            v-for="action in dialogOptions.actions"
            :key="action.label"
            v-bind="action"
            :label="__(action.label)"
            :loading="loading"
          />
        </div>
      </div>
    </template>
  </Dialog>
  <QuickEntryModal
    v-if="showQuickEntryModal"
    v-model="showQuickEntryModal"
    doctype="Address"
  />
</template>

<script setup>
import QuickEntryModal from '@/components/Modals/QuickEntryModal.vue'
import FieldLayout from '@/components/FieldLayout/FieldLayout.vue'
import EditIcon from '@/components/Icons/EditIcon.vue'
import { usersStore } from '@/stores/users'
import { isMobileView } from '@/composables/settings'
import { capture } from '@/telemetry'
import { FeatherIcon, createResource, ErrorMessage } from 'frappe-ui'
import { ref, nextTick, watch, computed } from 'vue'

const props = defineProps({
  options: {
    type: Object,
    default: {
      afterInsert: () => {},
    },
  },
})

const { isManager } = usersStore()

const show = defineModel()
const address = defineModel('address')

const loading = ref(false)
const error = ref(null)
const title = ref(null)
const editMode = ref(false)

let _address = ref({
  name: '',
  address_title: '',
  address_type: 'Office',
  address_line1: '',
  address_line2: '',
  city: '',
  county: '',
  state: '',
  country: '',
  countryLabel: '',
  pincode: '',
  links: []
})

const countryCodeMap = {
  'RU': 'Russian Federation',
  'US': 'United States',
  'GB': 'United Kingdom',
  // Add more as needed
}

const defaultCountry = createResource({
  url: 'frappe.client.get_value',
  params: {
    doctype: 'System Settings',
    fieldname: 'country'
  },
  transform(data) {
    const systemCountry = data?.message?.country
    if (systemCountry) return systemCountry

    try {
      const locale = new Intl.Locale(navigator.language)
      const region = locale.maximize().region
      return region || ''
    } catch (e) {
      return ''
    }
  },
  auto: true
})

const countryMap = createResource({
  url: 'frappe.desk.search.search_link',
  method: 'POST',
  params: {
    doctype: 'Country',
    txt: '',
    filters: null
  },
  transform(data) {
    // Create a map where key is translated name and value is original name
    const translationMap = {}
    data.forEach(country => {
      translationMap[__(country.value)] = country.value
    })
    return translationMap
  },
  auto: true
})

const dialogOptions = computed(() => {
  let title = !editMode.value
    ? __('New Address')
    : _address.value.address_title
  let size = 'xl'
  let actions = [
    {
      label: editMode.value ? __('Save') : __('Create'),
      variant: 'solid',
      onClick: () =>
        editMode.value ? updateAddress() : createAddress.submit(),
    },
  ]

  return { title, size, actions }
})

const tabs = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_fields_layout',
  cache: ['QuickEntry', 'Address'],
  params: { doctype: 'Address', type: 'Quick Entry' },
  auto: true,
  transform(data) {
    return data.map(tab => {
      if (tab.sections) {
        tab.sections = tab.sections.map(section => {
          if (section.fields) {
            section.fields = section.fields.map(field => {
              // Get translated field label
              const translatedLabel = __(field.label || field.name.split('_').map(word => 
                word.charAt(0).toUpperCase() + word.slice(1)).join(' '))

              // Determine placeholder verb based on field type
              const getPlaceholderVerb = (fieldtype) => {
                switch(fieldtype?.toLowerCase()) {
                  case 'select':
                  case 'link':
                    return __('Select')
                  case 'date':
                  case 'datetime':
                    return __('Set')
                  default:
                    return __('Enter')
                }
              }

              const verb = getPlaceholderVerb(field.fieldtype)
              return {
                ...field,
                placeholder: `${verb} ${translatedLabel}`,
                mandatory: field.name === 'address_type' ? false : field.mandatory
              }
            })
          }
          return section
        })
      }
      return tab
    })
  }
})

let doc = ref({})

function updateAddress() {
  error.value = null
  const old = { ...doc.value }
  const newAddress = { ..._address.value }

  const dirty = JSON.stringify(old) !== JSON.stringify(newAddress)
  const values = newAddress

  if (!dirty) {
    show.value = false
    return
  }

  loading.value = true
  updateAddressValues.submit({
    doctype: 'Address',
    name: _address.value.name,
    fieldname: values,
  })
}

const updateAddressValues = createResource({
  url: 'frappe.client.set_value',
  onSuccess(doc) {
    loading.value = false
    if (doc.name) {
      handleAddressUpdate(doc)
    }
  },
  onError(err) {
    loading.value = false
    error.value = err
  },
})

const createAddress = createResource({
  url: 'frappe.client.insert',
  makeParams() {
    if (!_address.value.address_line1) {
      error.value = __('Address Line 1 is mandatory')
      return
    }

    // Get original country name from translation map
    const originalCountry = countryMap.data?.[_address.value.country] || _address.value.country

    // Create default address title from city and address line 1
    const defaultTitle = _address.value.city ? 
      `${_address.value.city}, ${_address.value.address_line1}` : 
      _address.value.address_line1

    return {
      doc: {
        doctype: 'Address',
        ..._address.value,
        country: originalCountry,
        address_title: _address.value.address_title || defaultTitle,
      },
    }
  },
  onSuccess(doc) {
    loading.value = false
    if (doc.name) {
      capture('address_created')
      handleAddressUpdate(doc)
    }
  },
  async onError(err) {
    // Try to handle duplicate entry error
    const handled = await handleDuplicateEntry(err, 'Address', () => createAddress.submit())
    if (!handled) {
      loading.value = false
      error.value = err
    }
  },
})

function handleAddressUpdate(doc) {
  show.value = false
  props.options.afterInsert && props.options.afterInsert(doc)
}

watch(
  () => show.value,
  async (value) => {
    if (!value) return
    editMode.value = false
    
    // Wait for both resources to load if needed
    if (!defaultCountry.data) {
      await defaultCountry.reload()
    }
    if (!countryMap.data) {
      await countryMap.reload()
    }
    
    nextTick(() => {
      doc.value = address.value?.doc || address.value || {}
      const isNewAddress = !doc.value.name
      let countryValue = doc.value.country
      
      // For new address, convert country code to full name and translate
      if (isNewAddress && defaultCountry.data) {
        const originalValue = countryMap.data?.[defaultCountry.data] || 
                            countryCodeMap[defaultCountry.data] || 
                            'Russian Federation'
        countryValue = __(originalValue)
      } else if (doc.value.country) {
        // For existing address, translate the stored value
        countryValue = __(doc.value.country)
      }
      
      _address.value = { 
        ...doc.value,
        country: countryValue || ''
      }
      if (_address.value.name) {
        editMode.value = true
      }
    })
  },
)

const showQuickEntryModal = ref(false)

function openQuickEntryModal() {
  showQuickEntryModal.value = true
  nextTick(() => {
    show.value = false
  })
}
</script>
