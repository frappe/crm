<template>
  <Dialog v-model="show" :options="{ size: 'xl' }">
    <template #body>
      <div class="bg-surface-modal px-4 pb-6 pt-5 sm:px-6">
        <div class="mb-5 flex items-center justify-between">
          <div class="flex gap-2 items-center">
            <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">
              {{
                editMode
                  ? __('Edit ' + (doctypeTitle || doctype))
                  : __('Create ' + (doctypeTitle || doctype))
              }}
            </h3>
          </div>
          <div class="flex items-center gap-1">
            <CustomActions
              v-if="document.actions?.length"
              :actions="document.actions"
              :close="() => (show = false)"
            />
            <Button
              v-if="isManager() && !isMobileView"
              variant="ghost"
              class="w-7"
              :tooltip="__('Edit Fields Layout')"
              :icon="EditIcon"
              @click="openQuickEntryModal"
            />
            <Button
              variant="ghost"
              class="w-7"
              icon="x"
              @click="show = false"
            />
          </div>
        </div>
        <div>
          <FieldLayout
            v-if="layout.data"
            :tabs="layout.data"
            :data="doc"
            :doctype="doctype"
          />
		  <div
            v-if="doctype === 'FCRM Note' && document.doc?.custom_latitude"
            class="mt-2"
          >
            <a
              :href="`https://www.google.com/maps?q=${document.doc.custom_latitude},${document.doc.custom_longitude}`"
              target="_blank"
              rel="noopener"
              class="flex items-center gap-1.5 text-sm text-ink-blue-3 hover:underline"
            >
              <FeatherIcon name="map-pin" class="h-3.5 w-3.5" />
              {{ document.doc.custom_address || `${document.doc.custom_latitude}, ${document.doc.custom_longitude}` }}
            </a>
          </div>
          <ErrorMessage v-if="error" class="mt-4" :message="__(error)" />
        </div>
      </div>
      <div class="px-4 pb-7 pt-4 sm:px-6">
        <div class="flex flex-row-reverse gap-2">
          <Button
            variant="solid"
            :label="editMode ? __('Update') : __('Create')"
            :loading="editMode ? document.save.loading : _create.loading"
            @click="editMode ? update() : create()"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import EditIcon from '@/components/Icons/EditIcon.vue'
import FieldLayout from '@/components/FieldLayout/FieldLayout.vue'
import CustomActions from '@/components/CustomActions.vue'
import { useDocument } from '@/data/document'
import { globalStore } from '@/stores/global'
import { usersStore } from '@/stores/users'
import { showQuickEntryModal, quickEntryProps } from '@/composables/modals'
import { isMobileView } from '@/composables/settings'
import { setupCustomizations } from '@/utils'
import { call, createResource, toast } from 'frappe-ui'
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  doctypeTitle: { type: String, default: '' },
  doctype: { type: String, default: '' },
  docname: { type: String, default: '' },
  defaults: { type: Object, default: () => ({}) },
})

const show = defineModel({ type: Boolean })

const emit = defineEmits(['afterInsert', 'afterUpdate'])

const router = useRouter()

const { isManager } = usersStore()
const { $dialog, $socket } = globalStore()

const { document, scripts, triggerOnRender, triggerOnBeforeCreate } =
  useDocument(props.doctype, props.docname || null)

const doc = computed(() => document.doc || {})

const layout = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_fields_layout',
  cache: ['Quick Entry', props.doctype],
  params: { doctype: props.doctype, type: 'Quick Entry' },
  auto: true,
})

const error = ref(null)
const editMode = computed(() => Boolean(document.doc?.name))

const _create = createResource({
  url: 'frappe.client.insert',
  onSuccess: (d) => {
    // Link the uploaded file to the note silently in background
    if (props.doctype === 'FCRM Note' && document.doc?.custom_file) {
      linkFileToDoc(document.doc.custom_file, d.name).catch(() => {})
    }
    document.doc = {}
    emit('afterInsert', d)
    show.value = false
  },
  onError: (err) => {
    if (err.exc_type == 'MandatoryError') {
      const fieldName = err.messages
        .map((msg) => {
          let arr = msg.split(': ')
          return arr[arr.length - 1].trim()
        })
        .join(', ')
      error.value = __('Mandatory field error: {0}', [fieldName])
      return
    }
    error.value = err.messages?.[0] || 'Could not create document'
  },
})

async function linkFileToDoc(fileUrl, docname) {
  const files = await call('frappe.client.get_list', {
    doctype: 'File',
    filters: { file_url: fileUrl },
    fields: ['name'],
    limit: 1,
  })
  if (files?.length) {
    await call('frappe.client.set_value', {
      doctype: 'File',
      name: files[0].name,
      fieldname: {
        attached_to_doctype: 'FCRM Note',
        attached_to_name: docname,
        fieldname: 'custom_file',
      },
    })
  }
}

async function create() {
  await triggerOnBeforeCreate?.()

  _create.submit({
    doc: {
      doctype: props.doctype,
      ...document.doc,
    },
  })
}

function update() {
  document.save.submit(null, {
    onSuccess: (d) => {
      emit('afterUpdate', d)
      show.value = false
    },
    onError: (err) => {
      error.value = err.messages?.[0] || 'Could not update document'
    },
  })
}

function openQuickEntryModal() {
  showQuickEntryModal.value = true
  quickEntryProps.value = { doctype: props.doctype }
  nextTick(() => (show.value = false))
}

watch(
  () => document.doc,
  async (_doc) => {
    if (scripts.data?.length) {
      setupCustomizations(scripts.data, {
        doc: _doc,
        $dialog,
        $socket,
        router,
        toast,
        call,
      })
    }
  },
  { once: true },
)

onMounted(async () => {
  document.doc = {
    ...document.doc,
    ...props.defaults,
  }
  await triggerOnRender()
})

// ─── GEO TAGGING ──────────────────────────────────────────
// When custom_file is set via the native attach field,
// silently fetch GPS and store in the geo fields.

let watchId         = null
let locationTimeout = null

watch(
  () => document.doc?.custom_file,
  (newVal, oldVal) => {
    if (newVal && newVal !== oldVal) {
      fetchGeoLocation()
    }
  },
)

function fetchGeoLocation() {
  if (!navigator.geolocation) return

  navigator.geolocation.getCurrentPosition(
    (pos) => applyPosition(pos),
    () => {
      let bestPos = null

      watchId = navigator.geolocation.watchPosition(
        (pos) => {
          if (!bestPos || pos.coords.accuracy < bestPos.coords.accuracy) bestPos = pos
          if (pos.coords.accuracy <= 100) {
            navigator.geolocation.clearWatch(watchId)
            watchId = null
            clearTimeout(locationTimeout)
            applyPosition(pos)
          }
        },
        () => { if (bestPos) applyPosition(bestPos) },
        { enableHighAccuracy: true, timeout: 20000, maximumAge: 0 },
      )

      locationTimeout = setTimeout(() => {
        if (watchId != null) { navigator.geolocation.clearWatch(watchId); watchId = null }
        if (bestPos) applyPosition(bestPos)
      }, 15000)
    },
    { enableHighAccuracy: true, timeout: 3000, maximumAge: 30000 },
  )
}

function applyPosition(pos) {
  if (!document.doc) return
  document.doc.custom_latitude  = pos.coords.latitude
  document.doc.custom_longitude = pos.coords.longitude
  document.doc.custom_accuracy  = pos.coords.accuracy

  fetch(
    `https://nominatim.openstreetmap.org/reverse?lat=${pos.coords.latitude}&lon=${pos.coords.longitude}&format=json`,
    { headers: { 'Accept-Language': 'en' } },
  )
    .then((r) => r.json())
    .then((data) => { document.doc.custom_address = data.display_name || null })
    .catch(() => {})
}
</script>