<template>
  <div class="flex h-full flex-col gap-6 p-6 text-ink-gray-8">
    <div class="flex justify-between px-2 pt-2">
      <div class="flex w-9/12 flex-col gap-1">
        <h2 class="flex h-5 text-2xl-semibold leading-none">
          {{ __('Booking Pages') }}
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{
            __(
              'Share a link where people pick a free time on your calendar and book a meeting.',
            )
          }}
        </p>
      </div>
      <div class="flex w-3/12 justify-end">
        <Button
          :label="__('New')"
          icon-left="lucide-plus"
          variant="solid"
          @click="openCreate"
        />
      </div>
    </div>

    <div class="flex h-full flex-col overflow-y-auto">
      <div
        v-if="pages.loading && !pages.data"
        class="mt-12 flex items-center justify-center"
      >
        <LoadingIndicator class="w-4" />
      </div>
      <EmptyState
        v-else-if="!pages.data?.length"
        :title="__('No booking pages yet')"
        :description="__('Create one to let people book time with you.')"
        :icon="h(CalendarIcon)"
      />
      <div v-else class="w-full">
        <div class="flex items-center p-2 text-sm text-ink-gray-5">
          <div class="w-6/12">{{ __('Page') }}</div>
          <div class="w-3/12">{{ __('Hosts') }}</div>
          <div class="w-3/12">{{ __('Status') }}</div>
        </div>
        <div class="mx-2 h-px border-t border-outline-elevation-2" />
        <template v-for="(page, i) in pages.data" :key="page.name">
          <div
            class="flex w-full items-center rounded-4 px-2 py-3 hover:bg-surface-gray-2"
          >
            <div
              class="w-6/12 min-w-0 cursor-pointer"
              @click="emit('open', page.name)"
            >
              <div class="truncate text-base-medium text-ink-gray-7">
                {{ page.title }}
              </div>
              <div class="mt-0.5 truncate text-p-base text-ink-gray-5">
                {{ __('{0} min', [page.duration]) }} ·
                {{
                  page.document_type === 'CRM Deal' ? __('Deal') : __('Lead')
                }}
                · {{ ROUTE_PREFIX }}{{ page.route }}
              </div>
            </div>
            <div class="w-3/12 cursor-pointer" @click="emit('open', page.name)">
              <MultipleAvatar
                class="w-fit"
                :avatars="page.hosts.map((u: string) => hostAvatar(u))"
                size="sm"
              />
            </div>
            <div class="flex w-3/12 items-center justify-between">
              <Badge
                :theme="page.enabled ? 'green' : 'gray'"
                variant="outline"
                size="md"
                :label="page.enabled ? __('Live') : __('Off')"
              />
              <Dropdown
                align="end"
                :options="rowOptions(page)"
                @update:open="
                  (open: boolean) => open && (isConfirmingDelete = false)
                "
              >
                <Button icon="lucide-more-horizontal" variant="ghost" />
              </Dropdown>
            </div>
          </div>
          <hr v-if="pages.data.length !== i + 1" class="mx-2" />
        </template>
      </div>
    </div>
  </div>

  <Dialog v-model:open="showCreate" :title="__('New booking page')">
    <div class="flex flex-col gap-4">
      <FormControl
        v-model="draft.title"
        type="text"
        :label="__('Title')"
        :placeholder="__('30 minute intro call')"
        @update:model-value="onTitleInput"
      />
      <div>
        <div class="mb-1.5 text-sm text-ink-gray-5">{{ __('Route') }}</div>
        <div
          class="flex h-7 items-center rounded-4 border border-transparent bg-surface-gray-2 px-2.5 text-base focus-within:border-outline-gray-4 focus-within:bg-surface-base"
        >
          <span class="shrink-0 text-ink-gray-4">{{ ROUTE_PREFIX }}</span>
          <input
            v-model="draft.route"
            :placeholder="__('intro-call')"
            class="min-w-0 flex-1 border-0 bg-transparent p-0 text-base text-ink-gray-8 placeholder:text-ink-gray-4 focus:outline-none focus:ring-0"
            @input="routeEdited = true"
          />
        </div>
      </div>
      <FormControl
        v-model="draft.document_type"
        type="select"
        :label="__('Each booking creates a')"
        :options="createsOptions"
      />
      <ErrorMessage v-if="createError" :message="createError" />
    </div>
    <template #actions>
      <Button
        class="w-full"
        variant="solid"
        :label="__('Create page')"
        :loading="creating"
        @click="createPage"
      />
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import EmptyState from '@/components/ListViews/EmptyState.vue'
import MultipleAvatar from '@/components/MultipleAvatar.vue'
import CalendarIcon from '@/components/Icons/CalendarIcon.vue'
import { usersStore } from '@/stores/users'
import { ConfirmDelete } from '@/utils'
import { createDialog } from '@/utils/dialogs'
import {
  Badge,
  Button,
  Dialog,
  Dropdown,
  ErrorMessage,
  FormControl,
  LoadingIndicator,
  call,
  createResource,
  toast,
} from 'frappe-ui'
import { h, reactive, ref } from 'vue'
import { ROUTE_PREFIX, copyPageLink, pageUrl, slugify } from './bookingPages'

interface BookingPageRow {
  name: string
  title: string
  route: string
  enabled: 0 | 1
  duration: number
  document_type?: 'CRM Lead' | 'CRM Deal'
  hosts: string[]
  bookings: number
}

const emit = defineEmits<{ open: [name: string] }>()
const { getUser, isManager } = usersStore()

// only managers and a page's own hosts may change it (CRM Booking Page.validate_editor)
function canChange(page: BookingPageRow) {
  return isManager() || page.hosts.includes(getUser().name)
}

const pages = createResource({ url: 'crm.api.booking.list_pages', auto: true })
const isConfirmingDelete = ref(false)

function hostAvatar(email: string) {
  const user = getUser(email)
  return {
    name: email,
    label: user?.full_name || email,
    image: user?.user_image,
  }
}

const showCreate = ref(false)
const creating = ref(false)
const createError = ref('')
const draft = reactive({ title: '', route: '', document_type: 'CRM Lead' })
const createsOptions = [
  { label: __('Lead'), value: 'CRM Lead' },
  { label: __('Deal'), value: 'CRM Deal' },
]
let routeEdited = false

function openCreate() {
  draft.title = ''
  draft.route = ''
  draft.document_type = 'CRM Lead'
  routeEdited = false
  createError.value = ''
  showCreate.value = true
}

function onTitleInput(value: string) {
  if (!routeEdited) draft.route = slugify(value)
}

async function createPage() {
  const route = slugify(draft.route || draft.title)
  if (!draft.title || !route) {
    createError.value = __('Title and route are required')
    return
  }
  creating.value = true
  createError.value = ''
  try {
    const name = await call('crm.api.booking.create_page', {
      title: draft.title,
      route,
      document_type: draft.document_type,
    })
    showCreate.value = false
    emit('open', name)
  } catch (e) {
    createError.value =
      (e as { messages?: string[] })?.messages?.[0] ||
      __('Could not create the page')
  } finally {
    creating.value = false
  }
}

async function setEnabled(page: BookingPageRow, enabled: boolean) {
  try {
    await call('frappe.client.set_value', {
      doctype: 'CRM Booking Page',
      name: page.name,
      fieldname: 'enabled',
      value: enabled ? 1 : 0,
    })
    pages.reload()
  } catch (e) {
    toast.error(
      (e as { messages?: string[] })?.messages?.[0] ||
        __('Could not change the page'),
    )
  }
}

// a page with bookings is kept, so its bookings keep their history; it can be turned off
async function deletePage(page: BookingPageRow) {
  if (page.bookings) {
    createDialog({
      title: __("This page can't be deleted"),
      message:
        page.bookings === 1
          ? __(
              'It has 1 booking, which keeps its link to the page. Turn the page off instead so nobody new can book.',
            )
          : __(
              'It has {0} bookings, which keep their link to the page. Turn the page off instead so nobody new can book.',
              [page.bookings],
            ),
      size: 'sm',
      actions: [
        {
          label: page.enabled ? __('Turn off') : __('OK'),
          variant: 'solid',
          onClick: ({ close }: { close: () => void }) => {
            close()
            if (page.enabled) setEnabled(page, false)
          },
        },
      ],
    })
    return
  }
  try {
    await call('frappe.client.delete', {
      doctype: 'CRM Booking Page',
      name: page.name,
    })
    pages.reload()
    toast.success(__('Page deleted'))
  } catch (e) {
    toast.error(
      (e as { messages?: string[] })?.messages?.[0] ||
        __('Could not delete the page'),
    )
  }
}

function rowOptions(page: BookingPageRow) {
  return [
    {
      label: canChange(page) ? __('Edit') : __('View'),
      icon: canChange(page) ? 'lucide-edit-2' : 'lucide-eye',
      onClick: () => emit('open', page.name),
    },
    {
      label: page.enabled ? __('Turn off') : __('Turn on'),
      icon: page.enabled ? 'lucide-eye-off' : 'lucide-eye',
      onClick: () => setEnabled(page, !page.enabled),
      condition: () => canChange(page),
    },
    {
      label: __('Copy link'),
      icon: 'lucide-link',
      onClick: () => copyPageLink(page.route),
    },
    {
      label: __('Open page'),
      icon: 'lucide-external-link',
      onClick: () => window.open(pageUrl(page.route), '_blank'),
    },
    ...(canChange(page)
      ? ConfirmDelete({
          isConfirmingDelete,
          onConfirmDelete: () => deletePage(page),
        })
      : []),
  ]
}

defineExpose({ reload: () => pages.reload() })
</script>
