<template>
    <Dialog v-model="show" :options="{ size: 'xl' }">
      <template #body>
        <div class="bg-surface-modal px-4 pb-6 pt-5 sm:px-6">
          <div class="mb-5 flex items-center justify-between">
            <div>
              <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">
                {{ __('New Property') }}
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
          <FieldLayout
            v-if="tabs.data?.length"
            :tabs="tabs.data"
            :data="_property "
            doctype="Item"
          />
          <!-- Global Error Message -->
          <div v-if="globalError" class="text-sm text-red-500 mt-4">
            {{ globalError }}
          </div>
        </div>
        <div class="px-4 pb-7 pt-4 sm:px-6">
          <div class="space-y-2">
            <Button
              class="w-full"
              variant="solid"
              :label="__('Create')"
              :loading="loading"
              @click="createProperty"
            />
          </div>
        </div>
      </template>
    </Dialog>
  </template>

  <script setup>
  import FieldLayout from '@/components/FieldLayout/FieldLayout.vue'
  import EditIcon from '@/components/Icons/EditIcon.vue'
  import { usersStore } from '@/stores/users'
  import { isMobileView } from '@/composables/settings'
  import { capture } from '@/telemetry'
  import { call, FeatherIcon, createResource } from 'frappe-ui'
  import { ref, nextTick, watch } from 'vue'
  import { useRouter } from 'vue-router'

  const props = defineProps({
    options: {
      type: Object,
      default: {
        redirect: true,
        afterInsert: () => {},
      },
    },
  })

  const emit = defineEmits(['openAddressModal'])

  const { isManager } = usersStore()

  const router = useRouter()
  const show = defineModel()
  const property = defineModel('property')

  const loading = ref(false)
  const title = ref(null)

  const globalError = ref('')

  let _property  = ref({
    item_code: '',
    item_name: '',
    item_group: '',
    item_group: '',
    custom_location:'',
  })

  let doc = ref({})

  // Function to validate mandatory fields
  function validateForm() {
    globalError.value = '' // Clear previous error

    // Get all mandatory fields from the tabs
    const mandatoryFields = []
    tabs.data?.forEach((tab) => {
      tab.sections.forEach((section) => {
        section.columns.forEach((column) => {
          column.fields.forEach((field) => {
            if (field.reqd && !_property.value[field.fieldname]) {
              if (field.label != 'Default Unit of Measure'){
                mandatoryFields.push(field.label || field.fieldname)
              }
            }
          })
        })
      })
    })

    // If mandatory fields are missing, set the error message
    if (mandatoryFields.length > 0) {
      globalError.value = `The following fields are required: ${mandatoryFields.join(', ')}`
      return false
    }

    return true
  }

  async function createProperty() {
    // Validate the form before submission
    if (!validateForm()) {
      return // Stop submission if validation fails
    }

    loading.value = true
    try {
      const doc = await call('frappe.client.insert', {
        doc: {
          doctype: 'Item',
          ..._property.value,
        },
      })
      loading.value = false
      if (doc.name) {
        capture('property_created')
        handlePropertyUpdate(doc)
      }
    } catch (error) {
      loading.value = false
      globalError.value = error.message // Display backend error message
    }
  }

  function handlePropertyUpdate(doc) {
      if (doc.name && props.options.redirect) {
      router.push({
        name: 'Property',
        params: { propertyId: doc.name },
      })
    } else {
      property.value?.reload?.()
    }
    show.value = false
    props.options.afterInsert && props.options.afterInsert(doc)
  }

  const tabs = createResource({
    url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_fields_layout',
    cache: ['QuickEntry', 'Item'],
    params: { doctype: 'Item', type: 'Quick Entry' },
    auto: true,
    transform: (_tabs) => {
      return _tabs.forEach((tab) => {
        tab.sections.forEach((section) => {
          section.columns.forEach((column) => {
            column.fields.forEach((field) => {
              if (field.fieldname == 'address') {
                field.create = (value, close) => {
                  _property.value.address = value
                  emit('openAddressModal')
                  show.value = false
                  close()
                }
                field.edit = (address) => {
                  emit('openAddressModal', address)
                  show.value = false
                }
              } else if (field.fieldtype === 'Table') {
                _property.value[field.fieldname] = []
              }
            })
          })
        })
      })
    },
  })

  watch(
    () => show.value,
    (value) => {
      if (!value) return
      nextTick(() => {
        doc.value = property.value?.doc || property.value || {}
        _property.value = { ...doc.value }
      })
    },
  )

  const showQuickEntryModal = defineModel('showQuickEntryModal')

  function openQuickEntryModal() {
    showQuickEntryModal.value = true
    nextTick(() => (show.value = false))
  }
  </script>

