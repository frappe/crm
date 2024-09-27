<template>
  <ActivityHeader
    v-model="tabIndex"
    v-model:showWhatsappTemplates="showWhatsappTemplates"
    v-model:showFilesUploader="showFilesUploader"
    :tabs="tabs"
    :title="title"
    :doc="doc"
    :emailBox="emailBox"
    :whatsappBox="whatsappBox"
    :modalRef="modalRef"
  />
  <FadedScrollableDiv
    :maskHeight="30"
    class="flex flex-col flex-1 overflow-y-auto"
  >
    <div
      v-if="all_activities?.loading"
      class="flex flex-1 flex-col items-center justify-center gap-3 text-xl font-medium text-gray-500"
    >
      <LoadingIndicator class="h-6 w-6" />
      <span>{{ __('Loading...') }}</span>
    </div>
    <div
      v-else-if="
        activities?.length ||
        (whatsappMessages.data?.length && title == 'WhatsApp')
      "
      class="activities"
    >
      <div v-if="title == 'WhatsApp' && whatsappMessages.data?.length">
        <WhatsAppArea
          class="px-3 sm:px-10"
          v-model="whatsappMessages"
          v-model:reply="replyMessage"
          :messages="whatsappMessages.data"
        />
      </div>
      <div
        v-else-if="title == 'Notes'"
        class="grid grid-cols-1 gap-4 px-3 pb-3 sm:px-10 sm:pb-5 lg:grid-cols-2 xl:grid-cols-3"
      >
        <div v-for="note in activities" @click="modalRef.showNote(note)">
          <NoteArea :note="note" v-model="all_activities" />
        </div>
      </div>
      <div v-else-if="title == 'Comments'" class="pb-5">
        <div v-for="(comment, i) in activities">
          <div
            class="activity grid grid-cols-[30px_minmax(auto,_1fr)] gap-2 px-3 sm:gap-4 sm:px-10"
          >
            <div
              class="relative flex justify-center after:absolute after:left-[50%] after:top-0 after:-z-10 after:border-l after:border-gray-200"
              :class="i != activities.length - 1 ? 'after:h-full' : 'after:h-4'"
            >
              <div
                class="z-10 flex h-8 w-7 items-center justify-center bg-white"
              >
                <CommentIcon class="text-gray-800" />
              </div>
            </div>
            <CommentArea class="mb-4" :activity="comment" />
          </div>
        </div>
      </div>
      <div v-else-if="title == 'Tasks'" class="px-3 pb-3 sm:px-10 sm:pb-5">
        <TaskArea :modalRef="modalRef" :tasks="activities" :doctype="doctype" />
      </div>
      <div v-else-if="title == 'Calls'" class="activity">
        <div v-for="(call, i) in activities">
          <div
            class="activity grid grid-cols-[30px_minmax(auto,_1fr)] gap-4 px-3 sm:px-10"
          >
            <div
              class="relative flex justify-center after:absolute after:left-[50%] after:top-0 after:-z-10 after:border-l after:border-gray-200"
              :class="i != activities.length - 1 ? 'after:h-full' : 'after:h-4'"
            >
              <div
                class="z-10 flex h-8 w-7 items-center justify-center bg-white text-gray-800"
              >
                <MissedCallIcon
                  v-if="call.status == 'No Answer'"
                  class="text-red-600"
                />
                <DeclinedCallIcon v-else-if="call.status == 'Busy'" />
                <component
                  v-else
                  :is="
                    call.type == 'Incoming' ? InboundCallIcon : OutboundCallIcon
                  "
                />
              </div>
            </div>
            <CallArea class="mb-4" :activity="call" />
          </div>
        </div>
      </div>
      <div
        v-else-if="title == 'Attachments'"
        class="px-3 pb-3 sm:px-10 sm:pb-5"
      >
        <AttachmentArea
          :attachments="activities"
          @reload="all_activities.reload() && scroll()"
        />
      </div>
      <div
        v-else
        v-for="(activity, i) in activities"
        class="activity px-3 sm:px-10"
        :class="
          ['Activity', 'Emails'].includes(title)
            ? 'grid grid-cols-[30px_minmax(auto,_1fr)] gap-2 sm:gap-4'
            : ''
        "
      >
        <div
          v-if="['Activity', 'Emails'].includes(title)"
          class="relative flex justify-center before:absolute before:left-[50%] before:top-0 before:-z-10 before:border-l before:border-gray-200"
          :class="[i != activities.length - 1 ? 'before:h-full' : 'before:h-4']"
        >
          <div
            class="z-10 flex h-7 w-7 items-center justify-center bg-white"
            :class="{
              'mt-2.5': ['communication'].includes(activity.activity_type),
              'bg-white': ['added', 'removed', 'changed'].includes(
                activity.activity_type,
              ),
              'h-8': [
                'comment',
                'communication',
                'incoming_call',
                'outgoing_call',
              ].includes(activity.activity_type),
            }"
          >
            <UserAvatar
              v-if="activity.activity_type == 'communication'"
              :user="activity.data.sender"
              size="md"
            />
            <MissedCallIcon
              v-else-if="
                ['incoming_call', 'outgoing_call'].includes(
                  activity.activity_type,
                ) && activity.status == 'No Answer'
              "
              class="text-red-600"
            />
            <DeclinedCallIcon
              v-else-if="
                ['incoming_call', 'outgoing_call'].includes(
                  activity.activity_type,
                ) && activity.status == 'Busy'
              "
            />
            <component
              v-else
              :is="activity.icon"
              :class="
                ['added', 'removed', 'changed'].includes(activity.activity_type)
                  ? 'text-gray-500'
                  : 'text-gray-800'
              "
            />
          </div>
        </div>
        <div
          v-if="activity.activity_type == 'communication'"
          class="pb-5 mt-px"
        >
          <EmailArea :activity="activity" :emailBox="emailBox" />
        </div>
        <div
          class="mb-4"
          :id="activity.name"
          v-else-if="activity.activity_type == 'comment'"
        >
          <CommentArea :activity="activity" />
        </div>
        <div
          class="mb-4 flex flex-col gap-2 py-1.5"
          :id="activity.name"
          v-else-if="activity.activity_type == 'attachment_log'"
        >
          <div class="flex items-center justify-stretch gap-2 text-base">
            <div
              class="inline-flex items-center flex-wrap gap-1.5 text-gray-800 font-medium"
            >
              <span class="font-medium">{{ activity.owner_name }}</span>
              <span class="text-gray-600">{{ __(activity.data.type) }}</span>
              <a
                v-if="activity.data.file_url"
                :href="activity.data.file_url"
                target="_blank"
              >
                <span>{{ activity.data.file_name }}</span>
              </a>
              <span v-else>{{ activity.data.file_name }}</span>
              <FeatherIcon
                v-if="activity.data.is_private"
                name="lock"
                class="size-3"
              />
            </div>
            <div class="ml-auto whitespace-nowrap">
              <Tooltip :text="dateFormat(activity.creation, dateTooltipFormat)">
                <div class="text-sm text-gray-600">
                  {{ __(timeAgo(activity.creation)) }}
                </div>
              </Tooltip>
            </div>
          </div>
        </div>
        <div
          v-else-if="
            activity.activity_type == 'incoming_call' ||
            activity.activity_type == 'outgoing_call'
          "
          class="mb-4"
        >
          <CallArea :activity="activity" />
        </div>
        <div v-else class="mb-4 flex flex-col gap-2 py-1.5">
          <div class="flex items-center justify-stretch gap-2 text-base">
            <div
              v-if="activity.other_versions"
              class="inline-flex flex-wrap gap-1.5 text-gray-800 font-medium"
            >
              <span>{{ activity.show_others ? __('Hide') : __('Show') }}</span>
              <span> +{{ activity.other_versions.length + 1 }} </span>
              <span>{{ __('changes from') }}</span>
              <span>{{ activity.owner_name }}</span>
              <Button
                class="!size-4"
                variant="ghost"
                @click="activity.show_others = !activity.show_others"
              >
                <template #icon>
                  <SelectIcon />
                </template>
              </Button>
            </div>
            <div
              v-else
              class="inline-flex items-center flex-wrap gap-1 text-gray-600"
            >
              <span class="font-medium text-gray-800">
                {{ activity.owner_name }}
              </span>
              <span v-if="activity.type">{{ __(activity.type) }}</span>
              <span
                v-if="activity.data.field_label"
                class="max-w-xs truncate font-medium text-gray-800"
              >
                {{ __(activity.data.field_label) }}
              </span>
              <span v-if="activity.value">{{ __(activity.value) }}</span>
              <span
                v-if="activity.data.old_value"
                class="max-w-xs font-medium text-gray-800"
              >
                <div
                  class="flex items-center gap-1"
                  v-if="activity.options == 'User'"
                >
                  <UserAvatar :user="activity.data.old_value" size="xs" />
                  {{ getUser(activity.data.old_value).full_name }}
                </div>
                <div class="truncate" v-else>
                  {{ activity.data.old_value }}
                </div>
              </span>
              <span v-if="activity.to">{{ __('to') }}</span>
              <span
                v-if="activity.data.value"
                class="max-w-xs font-medium text-gray-800"
              >
                <div
                  class="flex items-center gap-1"
                  v-if="activity.options == 'User'"
                >
                  <UserAvatar :user="activity.data.value" size="xs" />
                  {{ getUser(activity.data.value).full_name }}
                </div>
                <div class="truncate" v-else>
                  {{ activity.data.value }}
                </div>
              </span>
            </div>

            <div class="ml-auto whitespace-nowrap">
              <Tooltip :text="dateFormat(activity.creation, dateTooltipFormat)">
                <div class="text-sm text-gray-600">
                  {{ __(timeAgo(activity.creation)) }}
                </div>
              </Tooltip>
            </div>
          </div>
          <div
            v-if="activity.other_versions && activity.show_others"
            class="flex flex-col gap-0.5"
          >
            <div
              v-for="activity in [activity, ...activity.other_versions]"
              class="flex items-start justify-stretch gap-2 py-1.5 text-base"
            >
              <div class="inline-flex flex-wrap gap-1 text-gray-600">
                <span
                  v-if="activity.data.field_label"
                  class="max-w-xs truncate text-gray-600"
                >
                  {{ __(activity.data.field_label) }}
                </span>
                <FeatherIcon
                  name="arrow-right"
                  class="mx-1 h-4 w-4 text-gray-600"
                />
                <span v-if="activity.type">
                  {{ startCase(__(activity.type)) }}
                </span>
                <span
                  v-if="activity.data.old_value"
                  class="max-w-xs font-medium text-gray-800"
                >
                  <div
                    class="flex items-center gap-1"
                    v-if="activity.options == 'User'"
                  >
                    <UserAvatar :user="activity.data.old_value" size="xs" />
                    {{ getUser(activity.data.old_value).full_name }}
                  </div>
                  <div class="truncate" v-else>
                    {{ activity.data.old_value }}
                  </div>
                </span>
                <span v-if="activity.to">{{ __('to') }}</span>
                <span
                  v-if="activity.data.value"
                  class="max-w-xs font-medium text-gray-800"
                >
                  <div
                    class="flex items-center gap-1"
                    v-if="activity.options == 'User'"
                  >
                    <UserAvatar :user="activity.data.value" size="xs" />
                    {{ getUser(activity.data.value).full_name }}
                  </div>
                  <div class="truncate" v-else>
                    {{ activity.data.value }}
                  </div>
                </span>
              </div>

              <div class="ml-auto whitespace-nowrap">
                <Tooltip
                  :text="dateFormat(activity.creation, dateTooltipFormat)"
                >
                  <div class="text-sm text-gray-600">
                    {{ __(timeAgo(activity.creation)) }}
                  </div>
                </Tooltip>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div
      v-else
      class="flex flex-1 flex-col items-center justify-center gap-3 text-xl font-medium text-gray-500"
    >
      <component :is="emptyTextIcon" class="h-10 w-10" />
      <span>{{ __(emptyText) }}</span>
      <Button
        v-if="title == 'Calls'"
        :label="__('Make a Call')"
        @click="makeCall(doc.data.mobile_no)"
      />
      <Button
        v-else-if="title == 'Notes'"
        :label="__('Create Note')"
        @click="modalRef.showNote()"
      />
      <Button
        v-else-if="title == 'Emails'"
        :label="__('New Email')"
        @click="emailBox.show = true"
      />
      <Button
        v-else-if="title == 'Comments'"
        :label="__('New Comment')"
        @click="emailBox.showComment = true"
      />
      <Button
        v-else-if="title == 'Tasks'"
        :label="__('Create Task')"
        @click="modalRef.showTask()"
      />
      <Button
        v-else-if="title == 'Attachments'"
        :label="__('Upload Attachment')"
        @click="showFilesUploader = true"
      />
    </div>
  </FadedScrollableDiv>
  <div>
    <CommunicationArea
      ref="emailBox"
      v-if="['Emails', 'Comments', 'Activity'].includes(title)"
      v-model="doc"
      v-model:reload="reload_email"
      :doctype="doctype"
      @scroll="scroll"
    />
    <WhatsAppBox
      ref="whatsappBox"
      v-if="title == 'WhatsApp'"
      v-model="doc"
      v-model:reply="replyMessage"
      v-model:whatsapp="whatsappMessages"
      :doctype="doctype"
      @scroll="scroll"
    />
  </div>
  <WhatsappTemplateSelectorModal
    v-if="whatsappEnabled"
    v-model="showWhatsappTemplates"
    :doctype="doctype"
    @send="(t) => sendTemplate(t)"
  />
  <AllModals
    ref="modalRef"
    v-model="all_activities"
    :doctype="doctype"
    :doc="doc"
  />
  <FilesUploader
    v-if="doc.data?.name"
    v-model="showFilesUploader"
    :doctype="doctype"
    :docname="doc.data.name"
    @after="
      () => {
        all_activities.reload()
        changeTabTo('attachments')
      }
    "
  />
</template>
<script setup>
import ActivityHeader from '@/components/Activities/ActivityHeader.vue'
import EmailArea from '@/components/Activities/EmailArea.vue'
import CommentArea from '@/components/Activities/CommentArea.vue'
import CallArea from '@/components/Activities/CallArea.vue'
import NoteArea from '@/components/Activities/NoteArea.vue'
import TaskArea from '@/components/Activities/TaskArea.vue'
import AttachmentArea from '@/components/Activities/AttachmentArea.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import ActivityIcon from '@/components/Icons/ActivityIcon.vue'
import Email2Icon from '@/components/Icons/Email2Icon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import AttachmentIcon from '@/components/Icons/AttachmentIcon.vue'
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'
import WhatsAppArea from '@/components/Activities/WhatsAppArea.vue'
import WhatsAppBox from '@/components/Activities/WhatsAppBox.vue'
import LoadingIndicator from '@/components/Icons/LoadingIndicator.vue'
import LeadsIcon from '@/components/Icons/LeadsIcon.vue'
import DealsIcon from '@/components/Icons/DealsIcon.vue'
import DotIcon from '@/components/Icons/DotIcon.vue'
import CommentIcon from '@/components/Icons/CommentIcon.vue'
import SelectIcon from '@/components/Icons/SelectIcon.vue'
import MissedCallIcon from '@/components/Icons/MissedCallIcon.vue'
import DeclinedCallIcon from '@/components/Icons/DeclinedCallIcon.vue'
import InboundCallIcon from '@/components/Icons/InboundCallIcon.vue'
import OutboundCallIcon from '@/components/Icons/OutboundCallIcon.vue'
import FadedScrollableDiv from '@/components/FadedScrollableDiv.vue'
import CommunicationArea from '@/components/CommunicationArea.vue'
import WhatsappTemplateSelectorModal from '@/components/Modals/WhatsappTemplateSelectorModal.vue'
import AllModals from '@/components/Activities/AllModals.vue'
import FilesUploader from '@/components/FilesUploader/FilesUploader.vue'
import {
  timeAgo,
  dateFormat,
  dateTooltipFormat,
  secondsToDuration,
  startCase,
} from '@/utils'
import { globalStore } from '@/stores/global'
import { usersStore } from '@/stores/users'
import { contactsStore } from '@/stores/contacts'
import { whatsappEnabled } from '@/composables/settings'
import { capture } from '@/telemetry'
import { Button, Tooltip, createResource } from 'frappe-ui'
import { useElementVisibility } from '@vueuse/core'
import {
  ref,
  computed,
  h,
  markRaw,
  watch,
  nextTick,
  onMounted,
  onBeforeUnmount,
} from 'vue'
import { useRoute } from 'vue-router'

const { makeCall, $socket } = globalStore()
const { getUser } = usersStore()
const { getContact, getLeadContact } = contactsStore()

const props = defineProps({
  doctype: {
    type: String,
    default: 'CRM Lead',
  },
  tabs: {
    type: Array,
    default: () => [],
  },
})

const route = useRoute()

const doc = defineModel()
const reload = defineModel('reload')
const tabIndex = defineModel('tabIndex')

const reload_email = ref(false)
const modalRef = ref(null)
const showFilesUploader = ref(false)

const title = computed(() => props.tabs?.[tabIndex.value]?.name || 'Activity')

const changeTabTo = (tabName) => {
  const tabNames = props.tabs?.map((tab) => tab.name?.toLowerCase())
  const index = tabNames?.indexOf(tabName)
  if (index == -1) return
  tabIndex.value = index
}

const all_activities = createResource({
  url: 'crm.api.activities.get_activities',
  params: { name: doc.value.data.name },
  cache: ['activity', doc.value.data.name],
  auto: true,
  transform: ([versions, calls, notes, tasks, attachments]) => {
    if (calls?.length) {
      calls.forEach((doc) => {
        doc.show_recording = false
        doc.activity_type =
          doc.type === 'Incoming' ? 'incoming_call' : 'outgoing_call'
        doc.duration = secondsToDuration(doc.duration)
        if (doc.type === 'Incoming') {
          doc.caller = {
            label:
              getContact(doc.from)?.full_name ||
              getLeadContact(doc.from)?.full_name ||
              'Unknown',
            image:
              getContact(doc.from)?.image || getLeadContact(doc.from)?.image,
          }
          doc.receiver = {
            label: getUser(doc.receiver).full_name,
            image: getUser(doc.receiver).user_image,
          }
        } else {
          doc.caller = {
            label: getUser(doc.caller).full_name,
            image: getUser(doc.caller).user_image,
          }
          doc.receiver = {
            label:
              getContact(doc.to)?.full_name ||
              getLeadContact(doc.to)?.full_name ||
              'Unknown',
            image: getContact(doc.to)?.image || getLeadContact(doc.to)?.image,
          }
        }
      })
    }
    return { versions, calls, notes, tasks, attachments }
  },
})

const showWhatsappTemplates = ref(false)

const whatsappMessages = createResource({
  url: 'crm.api.whatsapp.get_whatsapp_messages',
  cache: ['whatsapp_messages', doc.value.data.name],
  params: {
    reference_doctype: props.doctype,
    reference_name: doc.value.data.name,
  },
  auto: true,
  transform: (data) => sortByCreation(data),
  onSuccess: () => nextTick(() => scroll()),
})

onBeforeUnmount(() => {
  $socket.off('whatsapp_message')
})

onMounted(() => {
  $socket.on('whatsapp_message', (data) => {
    if (
      data.reference_doctype === props.doctype &&
      data.reference_name === doc.value.data.name
    ) {
      whatsappMessages.reload()
    }
  })

  nextTick(() => {
    const hash = route.hash.slice(1) || null
    let tabNames = props.tabs?.map((tab) => tab.name)
    if (!tabNames?.includes(hash)) {
      scroll(hash)
    }
  })
})

function sendTemplate(template) {
  showWhatsappTemplates.value = false
  capture('send_whatsapp_template', { doctype: props.doctype })
  createResource({
    url: 'crm.api.whatsapp.send_whatsapp_template',
    params: {
      reference_doctype: props.doctype,
      reference_name: doc.value.data.name,
      to: doc.value.data.mobile_no,
      template,
    },
    auto: true,
  })
}

const replyMessage = ref({})

function get_activities() {
  if (!all_activities.data?.versions) return []
  if (!all_activities.data?.calls.length)
    return all_activities.data.versions || []
  return [...all_activities.data.versions, ...all_activities.data.calls]
}

const activities = computed(() => {
  let _activities = []
  if (title.value == 'Activity') {
    _activities = get_activities()
  } else if (title.value == 'Emails') {
    if (!all_activities.data?.versions) return []
    _activities = all_activities.data.versions.filter(
      (activity) => activity.activity_type === 'communication',
    )
  } else if (title.value == 'Comments') {
    if (!all_activities.data?.versions) return []
    _activities = all_activities.data.versions.filter(
      (activity) => activity.activity_type === 'comment',
    )
  } else if (title.value == 'Calls') {
    if (!all_activities.data?.calls) return []
    return sortByCreation(all_activities.data.calls)
  } else if (title.value == 'Tasks') {
    if (!all_activities.data?.tasks) return []
    return sortByCreation(all_activities.data.tasks)
  } else if (title.value == 'Notes') {
    if (!all_activities.data?.notes) return []
    return sortByCreation(all_activities.data.notes)
  } else if (title.value == 'Attachments') {
    if (!all_activities.data?.attachments) return []
    return sortByCreation(all_activities.data.attachments)
  }

  _activities.forEach((activity) => {
    activity.icon = timelineIcon(activity.activity_type, activity.is_lead)

    if (
      activity.activity_type == 'incoming_call' ||
      activity.activity_type == 'outgoing_call' ||
      activity.activity_type == 'communication'
    )
      return

    update_activities_details(activity)

    if (activity.other_versions) {
      activity.show_others = false
      activity.other_versions.forEach((other_version) => {
        update_activities_details(other_version)
      })
    }
  })
  return sortByCreation(_activities)
})

function sortByCreation(list) {
  return list.sort((a, b) => new Date(a.creation) - new Date(b.creation))
}

function update_activities_details(activity) {
  activity.owner_name = getUser(activity.owner).full_name
  activity.type = ''
  activity.value = ''
  activity.to = ''

  if (activity.activity_type == 'creation') {
    activity.type = activity.data
  } else if (activity.activity_type == 'added') {
    activity.type = 'added'
    activity.value = 'as'
  } else if (activity.activity_type == 'removed') {
    activity.type = 'removed'
    activity.value = 'value'
  } else if (activity.activity_type == 'changed') {
    activity.type = 'changed'
    activity.value = 'from'
    activity.to = 'to'
  }
}

const emptyText = computed(() => {
  let text = 'No Activities'
  if (title.value == 'Emails') {
    text = 'No Email Communications'
  } else if (title.value == 'Comments') {
    text = 'No Comments'
  } else if (title.value == 'Calls') {
    text = 'No Call Logs'
  } else if (title.value == 'Notes') {
    text = 'No Notes'
  } else if (title.value == 'Tasks') {
    text = 'No Tasks'
  } else if (title.value == 'Attachments') {
    text = 'No Attachments'
  } else if (title.value == 'WhatsApp') {
    text = 'No WhatsApp Messages'
  }
  return text
})

const emptyTextIcon = computed(() => {
  let icon = ActivityIcon
  if (title.value == 'Emails') {
    icon = Email2Icon
  } else if (title.value == 'Comments') {
    icon = CommentIcon
  } else if (title.value == 'Calls') {
    icon = PhoneIcon
  } else if (title.value == 'Notes') {
    icon = NoteIcon
  } else if (title.value == 'Tasks') {
    icon = TaskIcon
  } else if (title.value == 'Attachments') {
    icon = AttachmentIcon
  } else if (title.value == 'WhatsApp') {
    icon = WhatsAppIcon
  }
  return h(icon, { class: 'text-gray-500' })
})

function timelineIcon(activity_type, is_lead) {
  let icon
  switch (activity_type) {
    case 'creation':
      icon = is_lead ? LeadsIcon : DealsIcon
      break
    case 'deal':
      icon = DealsIcon
      break
    case 'comment':
      icon = CommentIcon
      break
    case 'incoming_call':
      icon = InboundCallIcon
      break
    case 'outgoing_call':
      icon = OutboundCallIcon
      break
    case 'attachment_log':
      icon = AttachmentIcon
      break
    default:
      icon = DotIcon
  }

  return markRaw(icon)
}

const emailBox = ref(null)
const whatsappBox = ref(null)

watch([reload, reload_email], ([reload_value, reload_email_value]) => {
  if (reload_value || reload_email_value) {
    all_activities.reload()
    reload.value = false
    reload_email.value = false
  }
})

function scroll(hash) {
  if (['tasks', 'notes'].includes(route.hash?.slice(1))) return
  setTimeout(() => {
    let el
    if (!hash) {
      let e = document.getElementsByClassName('activity')
      el = e[e.length - 1]
    } else {
      el = document.getElementById(hash)
    }
    if (el && !useElementVisibility(el).value) {
      el.scrollIntoView({ behavior: 'smooth' })
      el.focus()
    }
  }, 500)
}

defineExpose({ emailBox, all_activities })
</script>
