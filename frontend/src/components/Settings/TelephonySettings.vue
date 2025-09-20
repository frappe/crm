<template>
  <div class="flex h-full flex-col gap-6 p-8">
    <div class="flex justify-between">
      <div class="flex flex-col gap-1 w-9/12">
        <h2
          class="flex gap-2 text-xl font-semibold leading-none h-5 text-ink-gray-8"
        >
          {{ __('Telephony settings') }}
          <Badge
            v-if="twilio.isDirty || exotel.isDirty || ringcentral.isDirty || mediumChanged"
            :label="__('Not Saved')"
            variant="subtle"
            theme="orange"
          />
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{ __('Configure telephony settings for your CRM') }}
        </p>
      </div>
      <div class="flex item-center space-x-2 w-3/12 justify-end">
        <Button
          :loading="twilio.save.loading || exotel.save.loading || ringcentral.save.loading"
          :label="__('Update')"
          variant="solid"
          @click="update"
        />
      </div>
    </div>
    <div
      v-if="!twilio.get.loading || !exotel.get.loading || !ringcentral.get.loading"
      class="flex-1 flex flex-col gap-8 overflow-y-auto"
    >
      <!-- General -->
      <FormControl
        type="select"
        v-model="defaultCallingMedium"
        :label="__('Default medium')"
        :options="[
          { label: __(''), value: '' },
          { label: __('Twilio'), value: 'Twilio' },
          { label: __('Exotel'), value: 'Exotel' },
          { label: __('RingCentral'), value: 'RingCentral' },

        ]"
        class="w-1/2"
        :description="__('Default calling medium for logged in user')"
      />

      <!-- Twilio -->
      <div v-if="isManager()" class="flex flex-col justify-between gap-4">
        <span class="text-base font-semibold text-ink-gray-8">
          {{ __('Twilio') }}
        </span>
        <FieldLayout
          v-if="twilio?.doc && twilioTabs"
          :tabs="twilioTabs"
          :data="twilio.doc"
          doctype="CRM Twilio Settings"
        />
      </div>

      <!-- Exotel -->
      <div v-if="isManager()" class="flex flex-col justify-between gap-4">
        <span class="text-base font-semibold text-ink-gray-8">
          {{ __('Exotel') }}
        </span>
        <FieldLayout
          v-if="exotel?.doc && exotelTabs"
          :tabs="exotelTabs"
          :data="exotel.doc"
          doctype="CRM Exotel Settings"
        />
      </div>

      <!-- RingCentral -->
      <div v-if="isManager()" class="flex flex-col justify-between gap-4">
        <div class="flex items-center justify-between">
        <span class="text-base font-semibold text-ink-gray-8">
          {{ __('RingCentral') }}
        </span>
        <Button
          v-if="ringcentral?.doc?.enabled && !isRingCentralAuthorized"
          :loading="authorizationInProgress"
          :label="__('Authorize RingCentral')"
          variant="solid"
          theme="gray"
          @click="startOAuthFlow"
        />
        <Badge
          v-else-if="ringcentral?.doc?.enabled && isRingCentralAuthorized"
          :label="__('Authorized')"
          variant="subtle"
          theme="green"
        />
        </div>

        <FieldLayout
          v-if="ringcentral?.doc && ringcentralTabs"
          :tabs="ringcentralTabs"
          :data="ringcentral.doc"
          doctype="CRM RingCentral Settings"
        />
      </div>
    </div>
    <div v-else class="flex flex-1 items-center justify-center">
      <Spinner class="size-8" />
    </div>
    <ErrorMessage :message="twilio.save.error || exotel.save.error || error || ringcentral.save.error" />
  </div>
</template>
<script setup>
import FieldLayout from '@/components/FieldLayout/FieldLayout.vue'
import {
  createDocumentResource,
  createResource,
  FormControl,
  Spinner,
  Badge,
  ErrorMessage,
  call,
} from 'frappe-ui'
import { defaultCallingMedium } from '@/composables/settings'
import { usersStore } from '@/stores/users'
import { toast } from 'frappe-ui'
import { getRandom } from '@/utils'
import { ref, computed, watch } from 'vue'
import { useRingCentralAuth } from '@/composables/useRingCentralAuth'

const { isManager, isTelephonyAgent } = usersStore()

const {
  isRingCentralAuthorized,
  authorizationInProgress,
  log,
  startOAuthFlow,
  handleOAuthCallback,
  checkAuthStatus,
} = useRingCentralAuth()

const twilioFields = createResource({
  url: 'crm.api.doc.get_fields',
  cache: ['fields', 'CRM Twilio Settings'],
  params: {
    doctype: 'CRM Twilio Settings',
    allow_all_fieldtypes: true,
  },
  auto: true,
})

const exotelFields = createResource({
  url: 'crm.api.doc.get_fields',
  cache: ['fields', 'CRM Exotel Settings'],
  params: {
    doctype: 'CRM Exotel Settings',
    allow_all_fieldtypes: true,
  },
  auto: true,
})

const ringcentralFields = createResource({
  url: 'crm.api.doc.get_fields',
  cache: ['fields', 'CRM RingCentral Settings'],
  params: {
    doctype: 'CRM RingCentral Settings',
    allow_all_fieldtypes: true,
  },
  auto: true,
})

const twilio = createDocumentResource({
  doctype: 'CRM Twilio Settings',
  name: 'CRM Twilio Settings',
  fields: ['*'],
  auto: true,
  setValue: {
    onSuccess: () => {
      toast.success(__('Twilio settings updated successfully'))
    },
    onError: (err) => {
      toast.error(err.message + ': ' + err.messages[0])
    },
  },
})

const exotel = createDocumentResource({
  doctype: 'CRM Exotel Settings',
  name: 'CRM Exotel Settings',
  fields: ['*'],
  auto: true,
  setValue: {
    onSuccess: () => {
      toast.success(__('Exotel settings updated successfully'))
    },
    onError: (err) => {
      toast.error(err.message + ': ' + err.messages[0])
    },
  },
})

const ringcentral = createDocumentResource({
  doctype: 'CRM RingCentral Settings',
  name: 'CRM RingCentral Settings',
  fields: ['*'],
  auto: true,
  setValue: {
    onSuccess: () => {
      toast.success(__('RingCentral settings updated successfully'))
    },
    onError: (err) => {
      toast.error(err.message + ': ' + err.messages[0])
    },
  },
})

const twilioTabs = computed(() => {
  if (!twilioFields.data) return []
  let _tabs = []
  let fieldsData = twilioFields.data

  if (fieldsData[0].type != 'Tab Break') {
    let _sections = []
    if (fieldsData[0].type != 'Section Break') {
      _sections.push({
        name: 'first_section',
        columns: [{ name: 'first_column', fields: [] }],
      })
    }
    _tabs.push({ name: 'first_tab', sections: _sections })
  }

  fieldsData.forEach((field) => {
    let last_tab = _tabs[_tabs.length - 1]
    let _sections = _tabs.length ? last_tab.sections : []
    if (field.fieldtype === 'Tab Break') {
      _tabs.push({
        label: field.label,
        name: field.fieldname,
        sections: [
          {
            name: 'section_' + getRandom(),
            columns: [{ name: 'column_' + getRandom(), fields: [] }],
          },
        ],
      })
    } else if (field.fieldtype === 'Section Break') {
      _sections.push({
        label: field.label,
        name: field.fieldname,
        hideBorder: field.hide_border,
        columns: [{ name: 'column_' + getRandom(), fields: [] }],
      })
    } else if (field.fieldtype === 'Column Break') {
      _sections[_sections.length - 1].columns.push({
        name: field.fieldname,
        fields: [],
      })
    } else {
      let last_section = _sections[_sections.length - 1]
      let last_column = last_section.columns[last_section.columns.length - 1]
      last_column.fields.push(field)
    }
  })

  return _tabs
})

const exotelTabs = computed(() => {
  if (!exotelFields.data) return []
  let _tabs = []
  let fieldsData = exotelFields.data

  if (fieldsData[0].type != 'Tab Break') {
    let _sections = []
    if (fieldsData[0].type != 'Section Break') {
      _sections.push({
        name: 'first_section',
        columns: [{ name: 'first_column', fields: [] }],
      })
    }
    _tabs.push({ name: 'first_tab', sections: _sections })
  }

  fieldsData.forEach((field) => {
    let last_tab = _tabs[_tabs.length - 1]
    let _sections = _tabs.length ? last_tab.sections : []
    if (field.fieldtype === 'Tab Break') {
      _tabs.push({
        label: field.label,
        name: field.fieldname,
        sections: [
          {
            name: 'section_' + getRandom(),
            columns: [{ name: 'column_' + getRandom(), fields: [] }],
          },
        ],
      })
    } else if (field.fieldtype === 'Section Break') {
      _sections.push({
        label: field.label,
        name: field.fieldname,
        hideBorder: field.hide_border,
        columns: [{ name: 'column_' + getRandom(), fields: [] }],
      })
    } else if (field.fieldtype === 'Column Break') {
      _sections[_sections.length - 1].columns.push({
        name: field.fieldname,
        fields: [],
      })
    } else {
      let last_section = _sections[_sections.length - 1]
      let last_column = last_section.columns[last_section.columns.length - 1]
      last_column.fields.push(field)
    }
  })

  return _tabs
})

const ringcentralTabs = computed(() => {
  if (!ringcentralFields.data) return []
  let _tabs = []
  let fieldsData = ringcentralFields.data

  if (fieldsData[0].type != 'Tab Break') {
    let _sections = []
    if (fieldsData[0].type != 'Section Break') {
      _sections.push({
        name: 'first_section',
        columns: [{ name: 'first_column', fields: [] }],
      })
    }
    _tabs.push({ name: 'first_tab', sections: _sections })
  }

  fieldsData.forEach((field) => {
    let last_tab = _tabs[_tabs.length - 1]
    let _sections = _tabs.length ? last_tab.sections : []
    if (field.fieldtype === 'Tab Break') {
      _tabs.push({
        label: field.label,
        name: field.fieldname,
        sections: [
          {
            name: 'section_' + getRandom(),
            columns: [{ name: 'column_' + getRandom(), fields: [] }],
          },
        ],
      })
    } else if (field.fieldtype === 'Section Break') {
      _sections.push({
        label: field.label,
        name: field.fieldname,
        hideBorder: field.hide_border,
        columns: [{ name: 'column_' + getRandom(), fields: [] }],
      })
    } else if (field.fieldtype === 'Column Break') {
      _sections[_sections.length - 1].columns.push({
        name: field.fieldname,
        fields: [],
      })
    } else {
      let last_section = _sections[_sections.length - 1]
      let last_column = last_section.columns[last_section.columns.length - 1]
      last_column.fields.push(field)
    }
  })

  return _tabs
})
const mediumChanged = ref(false)

watch(defaultCallingMedium, () => {
  mediumChanged.value = true
})

function update() {
  if (!validateIfDefaultMediumIsEnabled()) return
  if (mediumChanged.value) {
    updateMedium()
  }

  if (!isManager()) return

  if (twilio.isDirty) {
    twilio.save.submit()
  }
  if (exotel.isDirty) {
    exotel.save.submit()
  }
  if (ringcentral.isDirty) {
  ringcentral.save.submit()
  }
}

async function updateMedium() {
  await call('crm.integrations.api.set_default_calling_medium', {
    medium: defaultCallingMedium.value,
  })
  mediumChanged.value = false
  error.value = ''
  toast.success(__('Default calling medium updated successfully'))
}

const error = ref('')

function validateIfDefaultMediumIsEnabled() {
  if (isTelephonyAgent() && !isManager()) return true

  if (defaultCallingMedium.value === 'Twilio' && !twilio.doc.enabled) {
    error.value = __('Twilio is not enabled')
    return false
  }
  if (defaultCallingMedium.value === 'Exotel' && !exotel.doc.enabled) {
    error.value = __('Exotel is not enabled')
    return false
  }
  if (defaultCallingMedium.value === 'RingCentral' && !ringcentral.doc.enabled) {
    error.value = __('RingCentral is not enabled')
    return false
  }
  return true
}
</script>
