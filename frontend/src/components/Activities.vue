<template>
  <div class="flex items-center justify-between px-10 py-5 text-lg font-medium">
    <div class="flex h-7 items-center text-xl font-semibold text-gray-800">
      {{ title }}
    </div>
    <Button
      v-if="title == 'Emails'"
      variant="solid"
      @click="$refs.emailBox.show = true"
    >
      <template #prefix>
        <FeatherIcon name="plus" class="h-4 w-4" />
      </template>
      <span>New Email</span>
    </Button>
    <Button
      v-else-if="title == 'Calls'"
      variant="solid"
      @click="makeCall(doc.data.mobile_no)"
    >
      <template #prefix>
        <PhoneIcon class="h-4 w-4" />
      </template>
      <span>Make a Call</span>
    </Button>
    <Button v-else-if="title == 'Notes'" variant="solid" @click="showNote()">
      <template #prefix>
        <FeatherIcon name="plus" class="h-4 w-4" />
      </template>
      <span>New Note</span>
    </Button>
    <Button v-else-if="title == 'Tasks'" variant="solid" @click="showTask()">
      <template #prefix>
        <FeatherIcon name="plus" class="h-4 w-4" />
      </template>
      <span>New Task</span>
    </Button>
    <Dropdown
      v-else
      :options="[
        {
          icon: h(EmailIcon, { class: 'h-4 w-4' }),
          label: 'New Email',
          onClick: () => ($refs.emailBox.show = true),
        },
        {
          icon: h(PhoneIcon, { class: 'h-4 w-4' }),
          label: 'Make a Call',
          onClick: () => makeCall(doc.data.mobile_no),
        },
        {
          icon: h(NoteIcon, { class: 'h-4 w-4' }),
          label: 'New Note',
          onClick: () => showNote(),
        },
        {
          icon: h(TaskIcon, { class: 'h-4 w-4' }),
          label: 'New Task',
          onClick: () => showTask(),
        },
      ]"
      @click.stop
    >
      <template v-slot="{ open }">
        <Button variant="solid" class="flex items-center gap-1">
          <template #prefix>
            <FeatherIcon name="plus" class="h-4 w-4" />
          </template>
          <span>New</span>
          <template #suffix>
            <FeatherIcon
              :name="open ? 'chevron-up' : 'chevron-down'"
              class="h-4 w-4"
            />
          </template>
        </Button>
      </template>
    </Dropdown>
  </div>
  <div v-if="activities?.length" class="activities flex-1 overflow-y-auto">
    <div
      v-if="title == 'Notes'"
      class="activity grid grid-cols-3 gap-4 px-10 pb-5"
    >
      <div
        v-for="note in activities"
        class="group flex h-48 cursor-pointer flex-col justify-between gap-2 rounded-md bg-gray-50 px-4 py-3 hover:bg-gray-100"
        @click="showNote(note)"
      >
        <div class="flex items-center justify-between">
          <div class="truncate text-lg font-medium">
            {{ note.title }}
          </div>
          <Dropdown
            :options="[
              {
                icon: 'trash-2',
                label: 'Delete',
                onClick: () => deleteNote(note.name),
              },
            ]"
            @click.stop
            class="h-6 w-6"
          >
            <Button
              icon="more-horizontal"
              variant="ghosted"
              class="!h-6 !w-6 hover:bg-gray-100"
            />
          </Dropdown>
        </div>
        <TextEditor
          v-if="note.content"
          :content="note.content"
          :editable="false"
          editor-class="!prose-sm max-w-none !text-sm text-gray-600 focus:outline-none"
          class="flex-1 overflow-hidden"
        />
        <div class="mt-1 flex items-center justify-between gap-2">
          <div class="flex items-center gap-2">
            <UserAvatar :user="note.owner" size="xs" />
            <div class="text-sm text-gray-800">
              {{ getUser(note.owner).full_name }}
            </div>
          </div>
          <Tooltip :text="dateFormat(note.modified, dateTooltipFormat)">
            <div class="text-sm text-gray-700">
              {{ timeAgo(note.modified) }}
            </div>
          </Tooltip>
        </div>
      </div>
    </div>
    <div v-else-if="title == 'Tasks'" class="activity px-10 pb-5">
      <div v-for="(task, i) in activities">
        <div
          class="flex cursor-pointer gap-6 rounded p-2.5 duration-300 ease-in-out hover:bg-gray-50"
          @click="showTask(task)"
        >
          <div class="flex flex-1 flex-col gap-1.5 text-base">
            <div class="font-medium text-gray-900">
              {{ task.title }}
            </div>
            <div class="flex gap-1.5 text-gray-800">
              <div class="flex items-center gap-1.5">
                <UserAvatar :user="task.assigned_to" size="xs" />
                {{ getUser(task.assigned_to).full_name }}
              </div>
              <div
                v-if="task.due_date"
                class="flex items-center justify-center"
              >
                <DotIcon class="h-2.5 w-2.5 text-gray-600" :radius="2" />
              </div>
              <div v-if="task.due_date" class="flex gap-2">
                <CalendarIcon />
                <Tooltip :text="dateFormat(task.due_date, 'ddd, MMM D, YYYY')">
                  {{ dateFormat(task.due_date, 'D MMM') }}
                </Tooltip>
              </div>
              <div class="flex items-center justify-center">
                <DotIcon class="h-2.5 w-2.5 text-gray-600" :radius="2" />
              </div>
              <div class="flex gap-2">
                <TaskPriorityIcon class="!h-2 !w-2" :priority="task.priority" />
                {{ task.priority }}
              </div>
            </div>
          </div>
          <div class="flex items-center gap-1">
            <Dropdown
              :options="taskStatusOptions(updateTaskStatus, task)"
              @click.stop
            >
              <Tooltip text="Change Status">
                <Button variant="ghosted" class="hover:bg-gray-300">
                  <TaskStatusIcon :status="task.status" />
                </Button>
              </Tooltip>
            </Dropdown>
            <Dropdown
              :options="[
                {
                  icon: 'trash-2',
                  label: 'Delete',
                  onClick: () => {
                    $dialog({
                      title: 'Delete Task',
                      message: 'Are you sure you want to delete this task?',
                      actions: [
                        {
                          label: 'Delete',
                          theme: 'red',
                          variant: 'solid',
                          onClick(close) {
                            deleteTask(task.name)
                            close()
                          },
                        },
                      ],
                    })
                  },
                },
              ]"
              @click.stop
            >
              <Button
                icon="more-horizontal"
                variant="ghosted"
                class="hover:bg-gray-300"
              />
            </Dropdown>
          </div>
        </div>
        <div
          v-if="i < activities.length - 1"
          class="mx-2 h-px border-t border-gray-200"
        />
      </div>
    </div>
    <div v-else-if="title == 'Calls'" class="activity">
      <div v-for="(call, i) in activities">
        <div class="grid grid-cols-[30px_minmax(auto,_1fr)] gap-4 px-10">
          <div
            class="relative flex justify-center after:absolute after:left-[50%] after:top-0 after:-z-10 after:border-l after:border-gray-200"
            :class="i != activities.length - 1 ? 'after:h-full' : 'after:h-4'"
          >
            <div
              class="z-10 mt-[15px] flex h-7 w-7 items-center justify-center rounded-full bg-gray-100"
            >
              <component
                :is="
                  call.type == 'Incoming' ? InboundCallIcon : OutboundCallIcon
                "
                class="text-gray-800"
              />
            </div>
          </div>
          <div
            class="mb-3 flex max-w-[70%] flex-col gap-3 rounded-md bg-gray-50 p-4"
          >
            <div class="flex items-center justify-between">
              <div>
                {{ call.type == 'Incoming' ? 'Inbound' : 'Outbound' }} Call
              </div>
              <div>
                <Tooltip
                  class="text-sm text-gray-600"
                  :text="dateFormat(call.creation, dateTooltipFormat)"
                >
                  {{ timeAgo(call.creation) }}
                </Tooltip>
              </div>
            </div>
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-1">
                <DurationIcon class="h-4 w-4 text-gray-600" />
                <div class="text-sm text-gray-600">Duration</div>
                <div class="text-sm">
                  {{ call.duration }}
                </div>
              </div>
              <div
                class="flex cursor-pointer select-none items-center gap-1"
                @click="call.show_recording = !call.show_recording"
              >
                <PlayIcon class="h-4 w-4 text-gray-600" />
                <div class="text-sm text-gray-600">
                  {{
                    call.show_recording ? 'Hide Recording' : 'Listen to Call'
                  }}
                </div>
              </div>
            </div>
            <div
              v-if="call.show_recording"
              class="flex items-center justify-between rounded border"
            >
              <audio class="audio-control" controls :src="call.recording_url" />
            </div>
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-1">
                <Avatar
                  :image="call.caller.image"
                  :label="call.caller.label"
                  size="xl"
                />
                <div class="ml-1 flex flex-col gap-1">
                  <div class="text-base font-medium">
                    {{ call.caller.label }}
                  </div>
                  <div class="text-xs text-gray-600">
                    {{ call.from }}
                  </div>
                </div>
                <FeatherIcon
                  name="arrow-right"
                  class="mx-2 h-5 w-5 text-gray-600"
                />
                <Avatar
                  :image="call.receiver.image"
                  :label="call.receiver.label"
                  size="xl"
                />
                <div class="ml-1 flex flex-col gap-1">
                  <div class="text-base font-medium">
                    {{ call.receiver.label }}
                  </div>
                  <div class="text-xs text-gray-600">
                    {{ call.to }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div v-else v-for="(activity, i) in activities" class="activity">
      <div class="grid grid-cols-[30px_minmax(auto,_1fr)] gap-4 px-10">
        <div
          class="relative flex justify-center before:absolute before:left-[50%] before:top-0 before:-z-10 before:border-l before:border-gray-200"
          :class="[
            i != activities.length - 1 ? 'before:h-full' : 'before:h-4',
            activity.other_versions
              ? 'after:translate-y-[calc(-50% - 4px)] after:absolute after:bottom-9 after:left-[50%] after:top-0 after:-z-10 after:w-8 after:rounded-bl-xl after:border-b after:border-l after:border-gray-200'
              : '',
          ]"
        >
          <div
            class="z-10 flex h-7 w-7 items-center justify-center rounded-full bg-gray-100"
            :class="{
              'mt-3': [
                'communication',
                'incoming_call',
                'outgoing_call',
              ].includes(activity.activity_type),
              'bg-white': ['added', 'removed', 'changed'].includes(
                activity.activity_type
              ),
            }"
          >
            <component
              :is="activity.icon"
              :class="
                ['added', 'removed', 'changed'].includes(activity.activity_type)
                  ? 'text-gray-600'
                  : 'text-gray-800'
              "
            />
          </div>
        </div>
        <div v-if="activity.activity_type == 'communication'" class="pb-6">
          <div
            class="cursor-pointer rounded-md bg-gray-50 p-3 text-base leading-6 transition-all duration-300 ease-in-out"
          >
            <div class="mb-1 flex items-center justify-between gap-2">
              <div class="flex items-center gap-2">
                <UserAvatar :user="activity.data.sender" size="md" />
                <span>{{ activity.data.sender_full_name }}</span>
                <span>&middot;</span>
                <Tooltip
                  class="text-sm text-gray-600"
                  :text="dateFormat(activity.creation, dateTooltipFormat)"
                >
                  {{ timeAgo(activity.creation) }}
                </Tooltip>
              </div>
              <div class="flex gap-0.5">
                <Button
                  variant="ghost"
                  class="text-gray-700"
                  @click="reply(activity.data)"
                >
                  <ReplyIcon class="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  class="text-gray-700"
                  @click="reply(activity.data, true)"
                >
                  <ReplyAllIcon class="h-4 w-4" />
                </Button>
              </div>
            </div>
            <div class="text-sm leading-5 text-gray-600">
              {{ activity.data.subject }}
            </div>
            <div class="mb-3 text-sm leading-5 text-gray-600">
              <span class="mr-1 text-2xs font-bold text-gray-500">TO:</span>
              <span>{{ activity.data.recipients }}</span>
              <span v-if="activity.data.cc">, </span>
              <span
                v-if="activity.data.cc"
                class="mr-1 text-2xs font-bold text-gray-500"
              >
                CC:
              </span>
              <span v-if="activity.data.cc">{{ activity.data.cc }}</span>
              <span v-if="activity.data.bcc">, </span>
              <span
                v-if="activity.data.bcc"
                class="mr-1 text-2xs font-bold text-gray-500"
              >
                BCC:
              </span>
              <span v-if="activity.data.bcc">{{ activity.data.bcc }}</span>
            </div>
            <span class="prose-f" v-html="activity.data.content" />
            <div class="flex flex-wrap gap-2">
              <AttachmentItem
                v-for="a in activity.data.attachments"
                :key="a.file_url"
                :label="a.file_name"
                :url="a.file_url"
              />
            </div>
          </div>
        </div>
        <div
          class="mb-4"
          :id="activity.name"
          v-else-if="activity.activity_type == 'comment'"
        >
          <div
            class="mb-0.5 flex items-start justify-stretch gap-2 py-1.5 text-base"
          >
            <div class="inline-flex flex-wrap gap-1 text-gray-600">
              <span class="font-medium text-gray-800">
                {{ activity.owner_name }}
              </span>
              <span>added a</span>
              <span class="max-w-xs truncate font-medium text-gray-800">
                comment
              </span>
            </div>
            <div class="ml-auto whitespace-nowrap">
              <Tooltip
                :text="dateFormat(activity.creation, dateTooltipFormat)"
                class="text-gray-600"
              >
                {{ timeAgo(activity.creation) }}
              </Tooltip>
            </div>
          </div>
          <div
            class="cursor-pointer rounded bg-gray-50 px-4 py-3 text-base leading-6 transition-all duration-300 ease-in-out"
            v-html="activity.content"
          />
        </div>
        <div
          v-else-if="
            activity.activity_type == 'incoming_call' ||
            activity.activity_type == 'outgoing_call'
          "
          class="mb-3 flex max-w-[70%] flex-col gap-3 rounded-md bg-gray-50 p-4"
        >
          <div class="flex items-center justify-between">
            <div>
              {{ activity.type == 'Incoming' ? 'Inbound' : 'Outbound' }} Call
            </div>
            <div>
              <Tooltip
                class="text-sm text-gray-600"
                :text="dateFormat(activity.creation, dateTooltipFormat)"
              >
                {{ timeAgo(activity.creation) }}
              </Tooltip>
            </div>
          </div>
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-1">
              <DurationIcon class="h-4 w-4 text-gray-600" />
              <div class="text-sm text-gray-600">Duration</div>
              <div class="text-sm">
                {{ activity.duration }}
              </div>
            </div>
            <div
              class="flex cursor-pointer select-none items-center gap-1"
              @click="activity.show_recording = !activity.show_recording"
            >
              <PlayIcon class="h-4 w-4 text-gray-600" />
              <div class="text-sm text-gray-600">
                {{
                  activity.show_recording ? 'Hide Recording' : 'Listen to Call'
                }}
              </div>
            </div>
          </div>
          <div
            v-if="activity.show_recording"
            class="flex items-center justify-between rounded border"
          >
            <audio
              class="audio-control"
              controls
              :src="activity.recording_url"
            ></audio>
          </div>
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-1">
              <Avatar
                :image="activity.caller.image"
                :label="activity.caller.label"
                size="xl"
              />
              <div class="ml-1 flex flex-col gap-1">
                <div class="text-base font-medium">
                  {{ activity.caller.label }}
                </div>
                <div class="text-xs text-gray-600">
                  {{ activity.from }}
                </div>
              </div>
              <FeatherIcon
                name="arrow-right"
                class="mx-2 h-5 w-5 text-gray-600"
              />
              <Avatar
                :image="activity.receiver.image"
                :label="activity.receiver.label"
                size="xl"
              />
              <div class="ml-1 flex flex-col gap-1">
                <div class="text-base font-medium">
                  {{ activity.receiver.label }}
                </div>
                <div class="text-xs text-gray-600">
                  {{ activity.to }}
                </div>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="mb-4 flex flex-col gap-5 py-1.5">
          <div class="flex items-start justify-stretch gap-2 text-base">
            <div class="inline-flex flex-wrap gap-1 text-gray-600">
              <span class="font-medium text-gray-800">{{
                activity.owner_name
              }}</span>
              <span v-if="activity.type">{{ activity.type }}</span>
              <span
                v-if="activity.data.field_label"
                class="max-w-xs truncate font-medium text-gray-800"
              >
                {{ activity.data.field_label }}
              </span>
              <span v-if="activity.value">{{ activity.value }}</span>
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
              <span v-if="activity.to">to</span>
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
                class="text-gray-600"
              >
                {{ timeAgo(activity.creation) }}
              </Tooltip>
            </div>
          </div>
          <div
            v-if="activity.other_versions && activity.show_others"
            v-for="activity in activity.other_versions"
            class="flex items-start justify-stretch gap-2 text-base"
          >
            <div class="flex items-start gap-1 text-gray-600">
              <div class="flex flex-1 items-center gap-1">
                <span
                  v-if="activity.data.field_label"
                  class="max-w-xs truncate text-gray-600"
                >
                  {{ activity.data.field_label }}
                </span>
                <FeatherIcon
                  name="arrow-right"
                  class="mx-1 h-4 w-4 text-gray-600"
                />
              </div>
              <div class="flex flex-wrap items-center gap-1">
                <span v-if="activity.type">{{ startCase(activity.type) }}</span>
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
                <span v-if="activity.to">to</span>
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
            </div>

            <div class="ml-auto whitespace-nowrap">
              <Tooltip
                :text="dateFormat(activity.creation, dateTooltipFormat)"
                class="text-gray-600"
              >
                {{ timeAgo(activity.creation) }}
              </Tooltip>
            </div>
          </div>
          <div v-if="activity.other_versions">
            <Button
              :label="
                activity.show_others ? 'Hide all Changes' : 'Show all Changes'
              "
              variant="outline"
              @click="activity.show_others = !activity.show_others"
            >
              <template #suffix>
                <FeatherIcon
                  :name="activity.show_others ? 'chevron-up' : 'chevron-down'"
                  class="h-4 text-gray-600"
                />
              </template>
            </Button>
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
    <span>{{ emptyText }}</span>
    <Button
      v-if="title == 'Calls'"
      label="Make a Call"
      @click="makeCall(doc.data.mobile_no)"
    />
    <Button
      v-else-if="title == 'Notes'"
      label="Create Note"
      @click="showNote()"
    />
    <Button
      v-else-if="title == 'Emails'"
      label="New Email"
      @click="$refs.emailBox.show = true"
    />
    <Button
      v-else-if="title == 'Tasks'"
      label="Create Task"
      @click="showTask()"
    />
  </div>
  <CommunicationArea
    ref="emailBox"
    v-if="['Emails', 'Activity'].includes(title)"
    v-model="doc"
    v-model:reload="reload_email"
    :doctype="doctype"
    @scroll="scroll"
  />
  <NoteModal
    v-model="showNoteModal"
    v-model:reloadNotes="notes"
    :note="note"
    :doctype="doctype"
    :doc="doc.data?.name"
  />
  <TaskModal
    v-model="showTaskModal"
    v-model:reloadTasks="tasks"
    :task="task"
    :doctype="doctype"
    :doc="doc.data?.name"
  />
</template>
<script setup>
import UserAvatar from '@/components/UserAvatar.vue'
import EmailIcon from '@/components/Icons/EmailIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import DurationIcon from '@/components/Icons/DurationIcon.vue'
import CalendarIcon from '@/components/Icons/CalendarIcon.vue'
import TaskStatusIcon from '@/components/Icons/TaskStatusIcon.vue'
import TaskPriorityIcon from '@/components/Icons/TaskPriorityIcon.vue'
import PlayIcon from '@/components/Icons/PlayIcon.vue'
import LeadsIcon from '@/components/Icons/LeadsIcon.vue'
import DealsIcon from '@/components/Icons/DealsIcon.vue'
import DotIcon from '@/components/Icons/DotIcon.vue'
import CommentIcon from '@/components/Icons/CommentIcon.vue'
import EmailAtIcon from '@/components/Icons/EmailAtIcon.vue'
import InboundCallIcon from '@/components/Icons/InboundCallIcon.vue'
import OutboundCallIcon from '@/components/Icons/OutboundCallIcon.vue'
import ReplyIcon from '@/components/Icons/ReplyIcon.vue'
import ReplyAllIcon from '@/components/Icons/ReplyAllIcon.vue'
import AttachmentItem from '@/components/AttachmentItem.vue'
import CommunicationArea from '@/components/CommunicationArea.vue'
import NoteModal from '@/components/Modals/NoteModal.vue'
import TaskModal from '@/components/Modals/TaskModal.vue'
import {
  timeAgo,
  dateFormat,
  dateTooltipFormat,
  secondsToDuration,
  startCase,
  taskStatusOptions,
} from '@/utils'
import { globalStore } from '@/stores/global'
import { usersStore } from '@/stores/users'
import { contactsStore } from '@/stores/contacts'
import {
  Button,
  Tooltip,
  Dropdown,
  TextEditor,
  Avatar,
  createResource,
  createListResource,
  call,
} from 'frappe-ui'
import { useElementVisibility } from '@vueuse/core'
import { ref, computed, h, defineModel, markRaw, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'

const { makeCall } = globalStore()
const { getUser } = usersStore()
const { getContact, getLeadContact } = contactsStore()

const props = defineProps({
  title: {
    type: String,
    default: 'Activity',
  },
  doctype: {
    type: String,
    default: 'CRM Lead',
  },
})

const doc = defineModel()
const reload = defineModel('reload')

const reload_email = ref(false)

const versions = createResource({
  url: 'crm.api.activities.get_activities',
  params: { name: doc.value.data.name },
  cache: ['activity', doc.value.data.name],
  auto: true,
})

const calls = createListResource({
  type: 'list',
  doctype: 'CRM Call Log',
  cache: ['Call Logs', doc.value.data.name],
  fields: [
    'name',
    'caller',
    'receiver',
    'from',
    'to',
    'duration',
    'start_time',
    'end_time',
    'status',
    'type',
    'recording_url',
    'creation',
    'note',
  ],
  filters: { reference_docname: doc.value.data.name },
  orderBy: 'creation desc',
  pageLength: 999,
  auto: true,
  transform: (docs) => {
    docs.forEach((doc) => {
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
          image: getContact(doc.from)?.image || getLeadContact(doc.from)?.image,
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
    return docs
  },
})

const notes = createListResource({
  type: 'list',
  doctype: 'CRM Note',
  cache: ['Notes', doc.value.data.name],
  fields: ['name', 'title', 'content', 'owner', 'modified'],
  filters: { reference_docname: doc.value.data.name },
  orderBy: 'modified desc',
  pageLength: 999,
  auto: true,
})

const tasks = createListResource({
  type: 'list',
  doctype: 'CRM Task',
  cache: ['Tasks', doc.value.data.name],
  fields: [
    'name',
    'title',
    'description',
    'assigned_to',
    'assigned_to',
    'due_date',
    'priority',
    'status',
    'modified',
  ],
  filters: { reference_docname: doc.value.data.name },
  orderBy: 'modified desc',
  pageLength: 999,
  auto: true,
})

function all_activities() {
  if (!versions.data) return []
  if (!calls.data) return versions.data
  return [...versions.data, ...calls.data].sort(
    (a, b) => new Date(a.creation) - new Date(b.creation)
  )
}

const activities = computed(() => {
  let activities = []
  if (props.title == 'Activity') {
    activities = all_activities()
  } else if (props.title == 'Emails') {
    if (!versions.data) return []
    activities = versions.data
      .filter((activity) => activity.activity_type === 'communication')
      .sort((a, b) => new Date(a.creation) - new Date(b.creation))
  } else if (props.title == 'Calls') {
    return calls.data.sort(
      (a, b) => new Date(a.creation) - new Date(b.creation)
    )
  } else if (props.title == 'Tasks') {
    return tasks.data.sort(
      (a, b) => new Date(a.creation) - new Date(b.creation)
    )
  } else if (props.title == 'Notes') {
    return notes.data.sort(
      (a, b) => new Date(a.creation) - new Date(b.creation)
    )
  }
  activities.forEach((activity) => {
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
  return activities
})

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
  let text = 'No Email Communications'
  if (props.title == 'Calls') {
    text = 'No Call Logs'
  } else if (props.title == 'Notes') {
    text = 'No Notes'
  } else if (props.title == 'Tasks') {
    text = 'No Tasks'
  }
  return text
})

const emptyTextIcon = computed(() => {
  let icon = EmailIcon
  if (props.title == 'Calls') {
    icon = PhoneIcon
  } else if (props.title == 'Notes') {
    icon = NoteIcon
  } else if (props.title == 'Tasks') {
    icon = TaskIcon
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
    case 'communication':
      icon = EmailAtIcon
      break
    case 'incoming_call':
      icon = InboundCallIcon
      break
    case 'outgoing_call':
      icon = OutboundCallIcon
      break
    default:
      icon = DotIcon
  }

  return markRaw(icon)
}

// Notes
const showNoteModal = ref(false)
const note = ref({})
const emailBox = ref(null)

function showNote(n) {
  note.value = n || {
    title: '',
    content: '',
  }
  showNoteModal.value = true
}

async function deleteNote(name) {
  await call('frappe.client.delete', {
    doctype: 'CRM Note',
    name,
  })
  notes.reload()
}

// Tasks
const showTaskModal = ref(false)
const task = ref({})

function showTask(t) {
  task.value = t || {
    title: '',
    description: '',
    assigned_to: '',
    due_date: '',
    priority: 'Low',
    status: 'Backlog',
  }
  showTaskModal.value = true
}

async function deleteTask(name) {
  await call('frappe.client.delete', {
    doctype: 'CRM Task',
    name,
  })
  tasks.reload()
}

function updateTaskStatus(status, task) {
  call('frappe.client.set_value', {
    doctype: 'CRM Task',
    name: task.name,
    fieldname: 'status',
    value: status,
  }).then(() => {
    tasks.reload()
  })
}

// Email
function reply(email, reply_all = false) {
  emailBox.value.show = true
  let editor = emailBox.value.editor
  let message = email.content
  let recipients = email.recipients.split(',').map((r) => r.trim())
  editor.toEmails = recipients
  editor.cc = editor.bcc = false
  editor.ccEmails = []
  editor.bccEmails = []

  if (reply_all) {
    let cc = email.cc?.split(',').map((r) => r.trim())
    let bcc = email.bcc?.split(',').map((r) => r.trim())

    editor.cc = cc ? true : false
    editor.bcc = bcc ? true : false

    editor.ccEmails = cc
    editor.bccEmails = bcc
  }

  editor.editor
    .chain()
    .clearContent()
    .insertContent(message)
    .focus('all')
    .setBlockquote()
    .insertContentAt(0, { type: 'paragraph' })
    .focus('start')
    .run()
}

watch([reload, reload_email], ([reload_value, reload_email_value]) => {
  if (reload_value || reload_email_value) {
    versions.reload()
    reload.value = false
    reload_email.value = false
  }
})

function scroll(hash) {
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

defineExpose({ emailBox })

const route = useRoute()

nextTick(() => {
  const hash = route.hash.slice(1) || null
  scroll(hash)
})
</script>

<style scoped>
.audio-control {
  width: 100%;
  height: 40px;
  outline: none;
  border: none;
  background: none;
  cursor: pointer;
}

.audio-control::-webkit-media-controls-panel {
  background-color: white;
}
</style>
