<template>
  <div class="flex flex-1 flex-col overflow-hidden">
    <!-- Tabs Header -->
    <div class="flex items-center justify-between border-b px-5 min-h-[45px] bg-surface-base">
      <div class="flex items-center gap-6 overflow-x-auto">
        <button
          v-for="tab in tabList"
          :key="tab.value"
          type="button"
          class="flex items-center gap-2 border-b-2 py-3 text-sm font-medium transition-colors whitespace-nowrap"
          :class="[
            activeTab === tab.value
              ? 'border-surface-gray-9 text-ink-gray-9 font-semibold'
              : 'border-transparent text-ink-gray-6 hover:text-ink-gray-8',
          ]"
          @click="activeTab = tab.value"
        >
          <component :is="tab.icon" class="size-4" />
          <span>{{ __(tab.label) }}</span>
          <Badge
            variant="solid"
            size="sm"
            :class="[activeTab === tab.value ? 'bg-surface-gray-9 text-surface-white' : 'bg-surface-gray-4 text-ink-gray-7']"
          >
            {{ tab.count }}
          </Badge>
        </button>
      </div>

      <!-- Action Button Area -->
      <div class="flex items-center gap-2 py-1.5">
        <!-- All Activity tab actions: Dropdown -->
        <Dropdown
          v-if="activeTab === 'all_activity'"
          :options="allActivityActionOptions"
        >
          <template #default="{ open }">
            <Button
              variant="solid"
              :label="__('New Activity')"
              iconLeft="lucide-plus"
              :iconRight="open ? 'lucide-chevron-up' : 'lucide-chevron-down'"
            />
          </template>
        </Dropdown>

        <!-- Emails Tab Action: Email composition disabled on Contact detail page (read-only), enabled on My Tasks -->
        <Button
          v-else-if="activeTab === 'emails' && props.allowEmail"
          variant="solid"
          :label="__('New Email')"
          iconLeft="lucide-mail"
          @click="openEmailModal"
        />

        <!-- Calls Tab Action -->
        <Button
          v-else-if="activeTab === 'calls'"
          variant="solid"
          :label="__('Log Call')"
          iconLeft="lucide-phone"
          @click="showCallModal = true"
        />

        <!-- Notes Tab Action -->
        <Button
          v-else-if="activeTab === 'notes'"
          variant="solid"
          :label="__('New Note')"
          iconLeft="lucide-plus"
          @click="showNoteModal = true"
        />

        <!-- Meetings Tab Action -->
        <Button
          v-else-if="activeTab === 'meetings'"
          variant="solid"
          :label="__('Schedule Meeting')"
          iconLeft="lucide-calendar"
          @click="showMeetingModal = true"
        />

        <!-- Deals Tab Action -->
        <Button
          v-else-if="activeTab === 'deals'"
          variant="solid"
          :label="__('New Deal')"
          iconLeft="lucide-plus"
          @click="emit('newDeal')"
        />
      </div>
    </div>

    <!-- Tab Content Area -->
    <div class="flex-1 overflow-y-auto p-5">
      <!-- Loading State -->
      <div
        v-if="activitiesResource.loading && !activitiesResource.data"
        class="flex h-64 items-center justify-center gap-3 text-ink-gray-5"
      >
        <div class="size-6 animate-spin rounded-full border-2 border-surface-gray-7 border-t-transparent" />
        <span class="text-sm font-medium">{{ __('Loading activities...') }}</span>
      </div>

      <!-- TAB 1: ALL ACTIVITY -->
      <div v-else-if="activeTab === 'all_activity'" class="space-y-4 max-w-4xl">
        <div v-if="allActivities.length" class="space-y-3">
          <div
            v-for="item in allActivities"
            :key="item.activity_type + item.name"
            class="rounded-lg border border-outline-gray-2 bg-surface-white p-4 shadow-xs hover:border-outline-gray-3 transition-colors"
          >
            <!-- Email Activity Card -->
            <div v-if="item.activity_type === 'email'" class="flex flex-col gap-2">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2.5">
                  <span
                    class="flex size-7 items-center justify-center rounded-full"
                    :class="item.sent_or_received === 'Received' ? 'bg-surface-purple-2 text-ink-purple-4' : 'bg-surface-blue-2 text-ink-blue-4'"
                  >
                    <EmailIcon class="size-4" />
                  </span>
                  <div class="text-sm font-semibold text-ink-gray-9">
                    {{ item.activity_title }}
                  </div>
                </div>
                <div class="flex items-center gap-2">
                  <Badge
                    v-if="item.sent_or_received === 'Received'"
                    variant="subtle"
                    theme="purple"
                  >
                    {{ __('Incoming') }}
                  </Badge>
                  <div class="text-xs text-ink-gray-5">
                    {{ formatActivityDate(item.date) }}
                  </div>
                </div>
              </div>

              <div class="pl-9.5 flex flex-col gap-1.5">
                <div class="text-sm font-medium text-ink-gray-8">
                  {{ item.subject }}
                </div>
                <div class="text-xs text-ink-gray-5 flex items-center gap-3">
                  <span><span class="font-medium text-ink-gray-7">From:</span> {{ item.sender }}</span>
                  <span><span class="font-medium text-ink-gray-7">To:</span> {{ item.recipients }}</span>
                </div>
                <div class="text-xs text-ink-gray-6 line-clamp-2">
                  {{ item.snippet }}
                </div>

                <!-- Expanded Email Content -->
                <div v-if="expandedEmails[item.name]" class="mt-3 rounded-md bg-surface-gray-1 p-3 text-xs space-y-2 border border-outline-gray-2">
                  <div class="flex items-center justify-between border-b pb-2">
                    <span class="font-medium text-ink-gray-8">{{ __('Full Email Content') }}</span>
                    <Badge variant="subtle" :theme="getDeliveryStatusTheme(item.delivery_status)">{{ item.delivery_status }}</Badge>
                  </div>
                  <div v-if="item.cc" class="text-ink-gray-6">
                    <span class="font-medium">CC:</span> {{ item.cc }}
                  </div>
                  <div v-if="item.bcc" class="text-ink-gray-6">
                    <span class="font-medium">BCC:</span> {{ item.bcc }}
                  </div>
                  <!-- eslint-disable vue/no-v-html -->
                  <div
                    class="prose prose-xs max-w-none text-ink-gray-8"
                    v-html="sanitizeHTML(item.content)"
                  />
                  <!-- eslint-enable vue/no-v-html -->
                  <div v-if="item.attachments && item.attachments.length" class="mt-2 border-t pt-2">
                    <div class="font-medium text-ink-gray-7 mb-1">{{ __('Attachments:') }}</div>
                    <div class="flex flex-wrap gap-2">
                      <a
                        v-for="att in item.attachments"
                        :key="att.name"
                        :href="att.file_url"
                        target="_blank"
                        class="inline-flex items-center gap-1 rounded bg-surface-gray-2 px-2 py-1 text-ink-blue-4 hover:underline"
                      >
                        <span class="lucide-paperclip size-3" />
                        <span>{{ att.file_name }}</span>
                      </a>
                    </div>
                  </div>
                </div>

                <div>
                  <button
                    type="button"
                    class="text-xs font-medium text-ink-blue-4 hover:underline inline-flex items-center gap-1"
                    @click="toggleEmailExpand(item.name)"
                  >
                    <span>{{ expandedEmails[item.name] ? __('Hide email content') : __('View complete email') }}</span>
                    <span :class="expandedEmails[item.name] ? 'lucide-chevron-up' : 'lucide-chevron-down'" class="size-3" />
                  </button>
                </div>
              </div>
            </div>

            <!-- Call Activity Card -->
            <div v-else-if="item.activity_type === 'call'" class="flex flex-col gap-2">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2.5">
                  <span
                    class="flex size-7 items-center justify-center rounded-full"
                    :class="item.status === 'No Answer' ? 'bg-surface-red-2 text-ink-red-4' : 'bg-surface-green-2 text-ink-green-4'"
                  >
                    <PhoneIcon class="size-4" />
                  </span>
                  <div class="text-sm font-semibold text-ink-gray-9">
                    {{ item.activity_title }}
                  </div>
                </div>
                <div class="text-xs text-ink-gray-5">
                  {{ formatActivityDate(item.date) }}
                </div>
              </div>

              <div class="pl-9.5 flex flex-col gap-2">
                <div class="flex flex-wrap items-center gap-2">
                  <Badge variant="subtle" theme="gray">{{ item.type }} Call</Badge>
                  <Badge variant="subtle" theme="blue">
                    <template #prefix><span class="lucide-user size-3 mr-1" /></template>
                    {{ item.user_name }}
                  </Badge>
                  <Badge variant="subtle" theme="gray">
                    <template #prefix><span class="lucide-phone size-3 mr-1" /></template>
                    {{ item.phone }}
                  </Badge>
                  <Badge variant="subtle" theme="gray">
                    <template #prefix><span class="lucide-clock size-3 mr-1" /></template>
                    {{ __('Duration:') }} {{ item.duration_formatted }}
                  </Badge>
                  <Badge
                    variant="solid"
                    :theme="item.status === 'Completed' ? 'green' : item.status === 'No Answer' ? 'red' : 'gray'"
                  >
                    {{ item.status }}
                  </Badge>
                </div>

                <div v-if="item.note" class="rounded-md bg-surface-gray-1 p-2.5 text-xs text-ink-gray-7 border border-outline-gray-2">
                  <span class="font-medium text-ink-gray-8">{{ __('Call Notes:') }} </span>
                  <!-- eslint-disable vue/no-v-html -->
                  <span v-html="sanitizeHTML(item.note)" />
                  <!-- eslint-enable vue/no-v-html -->
                </div>

                <div v-if="item.recording_url" class="mt-1">
                  <AudioPlayer :src="item.recording_url" />
                </div>
              </div>
            </div>

            <!-- Note Activity Card -->
            <div v-else-if="item.activity_type === 'note'" class="flex flex-col gap-2">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2.5">
                  <span class="flex size-7 items-center justify-center rounded-full bg-surface-amber-2 text-ink-amber-5">
                    <NoteIcon class="size-4" />
                  </span>
                  <div class="text-sm font-semibold text-ink-gray-9">
                    {{ item.activity_title }}
                  </div>
                  <span v-if="item.pinned" class="lucide-pin size-3.5 text-ink-amber-5" title="Pinned" />
                </div>
                <div class="text-xs text-ink-gray-5">
                  {{ formatActivityDate(item.date) }}
                </div>
              </div>

              <div class="pl-9.5 flex flex-col gap-1.5">
                <div v-if="item.title && item.title !== 'Note'" class="text-sm font-medium text-ink-gray-8">
                  {{ item.title }}
                </div>
                <!-- eslint-disable vue/no-v-html -->
                <div
                  class="prose prose-xs max-w-none text-ink-gray-7 rounded-md bg-surface-gray-1 p-3 border border-outline-gray-2"
                  v-html="sanitizeHTML(item.content)"
                />
                <!-- eslint-enable vue/no-v-html -->
              </div>
            </div>

            <!-- Meeting Activity Card -->
            <div v-else-if="item.activity_type === 'meeting'" class="flex flex-col gap-2">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2.5">
                  <span class="flex size-7 items-center justify-center rounded-full bg-surface-purple-2 text-ink-purple-4">
                    <CalendarIcon class="size-4" />
                  </span>
                  <div class="text-sm font-semibold text-ink-gray-9">
                    {{ item.activity_title }}
                  </div>
                </div>
                <div class="text-xs text-ink-gray-5">
                  {{ formatActivityDate(item.date) }}
                </div>
              </div>

              <div class="pl-9.5 flex flex-col gap-2">
                <div class="text-sm font-medium text-ink-gray-9">
                  {{ item.title }}
                </div>
                <div class="flex flex-wrap items-center gap-2 text-xs">
                  <Badge variant="subtle" theme="purple">
                    <template #prefix><span class="lucide-calendar size-3 mr-1" /></template>
                    {{ item.date }}
                  </Badge>
                  <Badge variant="subtle" theme="gray">
                    <template #prefix><span class="lucide-clock size-3 mr-1" /></template>
                    {{ formatTimeRange(item.starts_on, item.ends_on) }}
                  </Badge>
                  <Badge variant="subtle" theme="blue">
                    <template #prefix><span class="lucide-user size-3 mr-1" /></template>
                    {{ __('Organizer:') }} {{ item.organizer_name }}
                  </Badge>
                  <Badge
                    variant="solid"
                    :theme="item.status === 'Open' ? 'blue' : item.status === 'Completed' ? 'green' : 'gray'"
                  >
                    {{ item.status }}
                  </Badge>
                </div>

                <div v-if="item.participants && item.participants.length" class="text-xs text-ink-gray-6">
                  <span class="font-medium text-ink-gray-7">{{ __('Participants:') }}</span>
                  {{ item.participants.join(', ') }}
                </div>

                <div v-if="item.description" class="rounded-md bg-surface-gray-1 p-2.5 text-xs text-ink-gray-7 border border-outline-gray-2">
                  <span class="font-medium text-ink-gray-8">{{ __('Notes:') }} </span>
                  <!-- eslint-disable vue/no-v-html -->
                  <span v-html="sanitizeHTML(item.description)" />
                  <!-- eslint-enable vue/no-v-html -->
                </div>
              </div>
            </div>
          </div>
        </div>

        <EmptyState
          v-else
          name="Activities"
          :title="__('No activity yet')"
          :description="__('Activities like emails, calls, notes, and meetings will appear here.')"
          :icon="ActivityIcon"
        />
      </div>

      <!-- TAB 2: EMAILS -->
      <div v-else-if="activeTab === 'emails'" class="space-y-4 max-w-4xl">
        <div v-if="emailsList.length" class="space-y-3">
          <div
            v-for="email in emailsList"
            :key="email.name"
            class="rounded-lg border border-outline-gray-2 bg-surface-white p-4 shadow-xs"
          >
            <div class="flex items-center justify-between border-b pb-2 mb-3">
              <div class="flex items-center gap-2">
                <Avatar :label="email.sender_full_name" size="lg" />
                <div>
                  <div class="text-sm font-semibold text-ink-gray-9">{{ email.sender_full_name }}</div>
                  <div class="text-xs text-ink-gray-5">{{ email.sender }}</div>
                </div>
              </div>
              <div class="flex items-center gap-2">
                <Badge
                  v-if="email.sent_or_received === 'Received'"
                  variant="subtle"
                  theme="purple"
                >
                  {{ __('Incoming') }}
                </Badge>
                <Badge variant="subtle" :theme="getDeliveryStatusTheme(email.delivery_status)">{{ email.delivery_status }}</Badge>
                <span class="text-xs text-ink-gray-5">{{ formatActivityDate(email.date) }}</span>
              </div>
            </div>

            <div class="space-y-2 text-xs">
              <div class="text-base font-semibold text-ink-gray-9">{{ email.subject }}</div>
              <div class="text-ink-gray-6 flex flex-wrap gap-4">
                <span><span class="font-medium text-ink-gray-8">To:</span> {{ email.recipients }}</span>
                <span v-if="email.cc"><span class="font-medium text-ink-gray-8">CC:</span> {{ email.cc }}</span>
                <span v-if="email.bcc"><span class="font-medium text-ink-gray-8">BCC:</span> {{ email.bcc }}</span>
              </div>

              <!-- Full email body -->
              <!-- eslint-disable vue/no-v-html -->
              <div
                class="prose prose-sm max-w-none text-ink-gray-8 rounded-md bg-surface-gray-1 p-4 border border-outline-gray-2 mt-3"
                v-html="sanitizeHTML(email.content)"
              />
              <!-- eslint-enable vue/no-v-html -->

              <!-- Attachments if any -->
              <div v-if="email.attachments && email.attachments.length" class="mt-2 border-t pt-2">
                <div class="font-medium text-ink-gray-7 mb-1">{{ __('Attachments:') }}</div>
                <div class="flex flex-wrap gap-2">
                  <a
                    v-for="att in email.attachments"
                    :key="att.name"
                    :href="att.file_url"
                    target="_blank"
                    class="inline-flex items-center gap-1 rounded bg-surface-gray-2 px-2.5 py-1 text-ink-blue-4 hover:underline font-medium"
                  >
                    <span class="lucide-paperclip size-3.5" />
                    <span>{{ att.file_name }}</span>
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>

        <EmptyState
          v-else
          name="Emails"
          :title="__('No emails yet')"
          :description="__('Emails sent to or received from this contact will appear here.')"
          :icon="EmailIcon"
          :onCreate="props.allowEmail ? openEmailModal : null"
        />
      </div>

      <!-- TAB 3: CALLS -->
      <div v-else-if="activeTab === 'calls'" class="space-y-4 max-w-4xl">
        <div v-if="callsList.length" class="space-y-3">
          <div
            v-for="call in callsList"
            :key="call.name"
            class="rounded-lg border border-outline-gray-2 bg-surface-white p-4 shadow-xs flex flex-col gap-2.5"
          >
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <span
                  class="flex size-7 items-center justify-center rounded-full"
                  :class="call.status === 'No Answer' ? 'bg-surface-red-2 text-ink-red-4' : 'bg-surface-green-2 text-ink-green-4'"
                >
                  <component :is="call.type === 'Incoming' ? InboundCallIcon : OutboundCallIcon" class="size-4" />
                </span>
                <span class="text-sm font-semibold text-ink-gray-9">{{ call.type }} Call</span>
                <Badge
                  variant="solid"
                  size="sm"
                  :theme="call.status === 'Completed' ? 'green' : call.status === 'No Answer' ? 'red' : 'gray'"
                >
                  {{ call.status }}
                </Badge>
              </div>
              <span class="text-xs text-ink-gray-5">{{ formatActivityDate(call.date) }}</span>
            </div>

            <div class="grid grid-cols-2 gap-3 sm:grid-cols-4 rounded-md bg-surface-gray-1 p-3 text-xs border border-outline-gray-2">
              <div>
                <span class="text-ink-gray-5 block">{{ __('Agent / User:') }}</span>
                <span class="font-medium text-ink-gray-9">{{ call.user_name }}</span>
              </div>
              <div>
                <span class="text-ink-gray-5 block">{{ __('Contact:') }}</span>
                <span class="font-medium text-ink-gray-9">{{ call.prospect_name }}</span>
              </div>
              <div>
                <span class="text-ink-gray-5 block">{{ __('Phone Number:') }}</span>
                <span class="font-medium text-ink-gray-9">{{ call.phone }}</span>
              </div>
              <div>
                <span class="text-ink-gray-5 block">{{ __('Duration:') }}</span>
                <span class="font-medium text-ink-gray-9">{{ call.duration_formatted }}</span>
              </div>
            </div>

            <div v-if="call.note" class="rounded-md bg-surface-gray-1 p-3 text-xs text-ink-gray-8 border border-outline-gray-2">
              <span class="font-semibold block mb-1 text-ink-gray-7">{{ __('Call Notes & Details:') }}</span>
              <!-- eslint-disable vue/no-v-html -->
              <div v-html="sanitizeHTML(call.note)" />
              <!-- eslint-enable vue/no-v-html -->
            </div>

            <div v-if="call.recording_url" class="mt-1">
              <AudioPlayer :src="call.recording_url" />
            </div>
          </div>
        </div>

        <EmptyState
          v-else
          name="Calls"
          :title="__('No calls yet')"
          :description="__('Calls logged for this contact will appear here.')"
          :icon="PhoneIcon"
          :onCreate="() => (showCallModal = true)"
        />
      </div>

      <!-- TAB 4: NOTES -->
      <div v-else-if="activeTab === 'notes'" class="space-y-4 max-w-4xl">
        <div v-if="notesList.length" class="space-y-3">
          <div
            v-for="note in notesList"
            :key="note.name"
            class="rounded-lg border border-outline-gray-2 bg-surface-white p-4 shadow-xs flex flex-col gap-2"
          >
            <div class="flex items-center justify-between border-b pb-2">
              <div class="flex items-center gap-2">
                <span class="text-base font-semibold text-ink-gray-9">{{ note.title }}</span>
                <span v-if="note.pinned" class="lucide-pin size-3.5 text-ink-amber-5" title="Pinned" />
              </div>
              <div class="text-xs text-ink-gray-5">
                {{ formatActivityDate(note.date) }}
              </div>
            </div>

            <!-- Full note content -->
            <!-- eslint-disable vue/no-v-html -->
            <div
              class="prose prose-sm max-w-none text-ink-gray-8 py-2"
              v-html="sanitizeHTML(note.content)"
            />
            <!-- eslint-enable vue/no-v-html -->

            <div class="flex items-center justify-between border-t pt-2 text-xs text-ink-gray-5">
              <div class="flex items-center gap-1.5">
                <Avatar :label="note.author_name" size="sm" />
                <span>{{ __('Created by') }} <span class="font-medium text-ink-gray-8">{{ note.author_name }}</span></span>
              </div>
              <div v-if="note.modified && note.modified !== note.creation">
                {{ __('Updated') }} {{ formatActivityDate(note.modified) }}
              </div>
            </div>
          </div>
        </div>

        <EmptyState
          v-else
          name="Notes"
          :title="__('No notes yet')"
          :description="__('Notes created for this contact will appear here.')"
          :icon="NoteIcon"
          :onCreate="() => (showNoteModal = true)"
        />
      </div>

      <!-- TAB 5: MEETINGS -->
      <div v-else-if="activeTab === 'meetings'" class="space-y-4 max-w-4xl">
        <div v-if="meetingsList.length" class="space-y-3">
          <div
            v-for="meeting in meetingsList"
            :key="meeting.name"
            class="rounded-lg border border-outline-gray-2 bg-surface-white p-4 shadow-xs flex flex-col gap-2.5"
          >
            <div class="flex items-center justify-between">
              <span class="text-base font-semibold text-ink-gray-9">{{ meeting.title }}</span>
              <Badge
                variant="solid"
                size="sm"
                :theme="meeting.status === 'Open' ? 'blue' : meeting.status === 'Completed' ? 'green' : 'gray'"
              >
                {{ meeting.status }}
              </Badge>
            </div>

            <div class="grid grid-cols-2 gap-3 sm:grid-cols-4 rounded-md bg-surface-gray-1 p-3 text-xs border border-outline-gray-2">
              <div>
                <span class="text-ink-gray-5 block">{{ __('Date:') }}</span>
                <span class="font-medium text-ink-gray-9">{{ meeting.date }}</span>
              </div>
              <div>
                <span class="text-ink-gray-5 block">{{ __('Time:') }}</span>
                <span class="font-medium text-ink-gray-9">{{ formatTimeRange(meeting.starts_on, meeting.ends_on) }}</span>
              </div>
              <div>
                <span class="text-ink-gray-5 block">{{ __('Organizer:') }}</span>
                <span class="font-medium text-ink-gray-9">{{ meeting.organizer_name }}</span>
              </div>
              <div>
                <span class="text-ink-gray-5 block">{{ __('Participants:') }}</span>
                <span class="font-medium text-ink-gray-9 truncate">{{ meeting.participants.join(', ') }}</span>
              </div>
            </div>

            <div v-if="meeting.description" class="rounded-md bg-surface-gray-1 p-3 text-xs text-ink-gray-8 border border-outline-gray-2">
              <span class="font-semibold block mb-1 text-ink-gray-7">{{ __('Meeting Notes & Details:') }}</span>
              <!-- eslint-disable vue/no-v-html -->
              <div v-html="sanitizeHTML(meeting.description)" />
              <!-- eslint-enable vue/no-v-html -->
            </div>
          </div>
        </div>

        <EmptyState
          v-else
          name="Meetings"
          :title="__('No meetings yet')"
          :description="__('Meetings scheduled with this contact will appear here.')"
          :icon="CalendarIcon"
          :onCreate="() => (showMeetingModal = true)"
        />
      </div>

      <!-- TAB 6: DEALS (SECONDARY TAB) -->
      <div v-else-if="activeTab === 'deals'" class="h-full">
        <DealsListView
          v-if="dealRows && dealRows.length"
          :rows="dealRows"
          :columns="dealColumns"
          :options="{ selectable: false, showTooltip: false }"
        />
        <EmptyState
          v-else
          name="Deals"
          :title="__('No deals yet')"
          :description="__('Use New Deal to create a deal for this contact.')"
          :icon="DealsIcon"
          :onCreate="() => emit('newDeal')"
        />
      </div>
    </div>

    <!-- ============================================== -->
    <!-- MODALS FOR CREATING ACTIVITIES -->
    <!-- Note: Email sending is intentionally disabled on Contact detail page -->
    <!-- ============================================== -->

    <!-- 1. Log Call Modal -->
    <Dialog v-model:open="showCallModal" :size="'lg'">
      <template #title>
        <div class="text-lg font-semibold text-ink-gray-9">{{ __('Log Call with {0}', [contact?.full_name || 'Contact']) }}</div>
      </template>
      <template #default>
        <div class="space-y-3 py-2 text-sm">
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-medium text-ink-gray-6 mb-1">{{ __('Call Type:') }}</label>
              <select
                v-model="callForm.type"
                class="w-full rounded-md border border-outline-gray-2 bg-surface-white px-3 py-1.5 text-sm focus:border-surface-gray-7 focus:outline-none"
              >
                <option value="Outgoing">{{ __('Outgoing Call') }}</option>
                <option value="Incoming">{{ __('Incoming Call') }}</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-medium text-ink-gray-6 mb-1">{{ __('Status:') }}</label>
              <select
                v-model="callForm.status"
                class="w-full rounded-md border border-outline-gray-2 bg-surface-white px-3 py-1.5 text-sm focus:border-surface-gray-7 focus:outline-none"
              >
                <option value="Completed">{{ __('Completed') }}</option>
                <option value="No Answer">{{ __('No Answer') }}</option>
                <option value="Busy">{{ __('Busy') }}</option>
                <option value="Failed">{{ __('Failed') }}</option>
              </select>
            </div>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-medium text-ink-gray-6 mb-1">{{ __('Phone Number:') }}</label>
              <input
                v-model="callForm.phone"
                type="text"
                class="w-full rounded-md border border-outline-gray-2 bg-surface-white px-3 py-1.5 text-sm focus:border-surface-gray-7 focus:outline-none"
                placeholder="+1 234 567 8900"
              />
            </div>
            <div>
              <label class="block text-xs font-medium text-ink-gray-6 mb-1">{{ __('Duration (seconds or mm:ss):') }}</label>
              <input
                v-model="callForm.duration"
                type="text"
                class="w-full rounded-md border border-outline-gray-2 bg-surface-white px-3 py-1.5 text-sm focus:border-surface-gray-7 focus:outline-none"
                placeholder="272 or 04:32"
              />
            </div>
          </div>
          <div>
            <label class="block text-xs font-medium text-ink-gray-6 mb-1">{{ __('Call Notes & Details:') }}</label>
            <textarea
              v-model="callForm.note"
              rows="4"
              class="w-full rounded-md border border-outline-gray-2 bg-surface-white px-3 py-2 text-sm focus:border-surface-gray-7 focus:outline-none"
              placeholder="Discussed requirements, customer feedback, next steps..."
            />
          </div>
        </div>
      </template>
      <template #actions>
        <div class="flex justify-end gap-2">
          <Button variant="subtle" :label="__('Cancel')" @click="showCallModal = false" />
          <Button
            variant="solid"
            :label="__('Log Call')"
            :loading="actionLoading"
            :disabled="!callForm.phone || actionLoading"
            @click="submitCall"
          />
        </div>
      </template>
    </Dialog>

    <!-- 3. New Note Modal -->
    <Dialog v-model:open="showNoteModal" :size="'md'">
      <template #title>
        <div class="text-lg font-semibold text-ink-gray-9">{{ __('Add Note for {0}', [contact?.full_name || 'Contact']) }}</div>
      </template>
      <template #default>
        <div class="space-y-3 py-2 text-sm">
          <div>
            <label class="block text-xs font-medium text-ink-gray-6 mb-1">{{ __('Title:') }}</label>
            <input
              v-model="noteForm.title"
              type="text"
              class="w-full rounded-md border border-outline-gray-2 bg-surface-white px-3 py-1.5 text-sm focus:border-surface-gray-7 focus:outline-none"
              placeholder="Note title..."
            />
          </div>
          <div>
            <label class="block text-xs font-medium text-ink-gray-6 mb-1">{{ __('Content:') }}</label>
            <textarea
              v-model="noteForm.content"
              rows="5"
              class="w-full rounded-md border border-outline-gray-2 bg-surface-white px-3 py-2 text-sm focus:border-surface-gray-7 focus:outline-none"
              placeholder="Write note here..."
            />
          </div>
          <div class="flex items-center gap-2 pt-1">
            <input
              id="pinnedCheck"
              v-model="noteForm.pinned"
              type="checkbox"
              class="rounded border-outline-gray-3 text-ink-gray-9 focus:ring-surface-gray-7"
            />
            <label for="pinnedCheck" class="text-xs text-ink-gray-7 cursor-pointer">{{ __('Pin to top of notes') }}</label>
          </div>
        </div>
      </template>
      <template #actions>
        <div class="flex justify-end gap-2">
          <Button variant="subtle" :label="__('Cancel')" @click="showNoteModal = false" />
          <Button
            variant="solid"
            :label="__('Save Note')"
            :loading="actionLoading"
            :disabled="!noteForm.content || actionLoading"
            @click="submitNote"
          />
        </div>
      </template>
    </Dialog>

    <!-- 4. Schedule Meeting Modal -->
    <Dialog v-model:open="showMeetingModal" :size="'lg'">
      <template #title>
        <div class="text-lg font-semibold text-ink-gray-9">{{ __('Schedule Meeting with {0}', [contact?.full_name || 'Contact']) }}</div>
      </template>
      <template #default>
        <div class="space-y-3 py-2 text-sm">
          <div>
            <label class="block text-xs font-medium text-ink-gray-6 mb-1">{{ __('Meeting Title / Subject:') }}</label>
            <input
              v-model="meetingForm.title"
              type="text"
              class="w-full rounded-md border border-outline-gray-2 bg-surface-white px-3 py-1.5 text-sm focus:border-surface-gray-7 focus:outline-none"
              placeholder="Product Demo / Discovery Call..."
            />
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-medium text-ink-gray-6 mb-1">{{ __('Starts On:') }}</label>
              <input
                v-model="meetingForm.starts_on"
                type="datetime-local"
                class="w-full rounded-md border border-outline-gray-2 bg-surface-white px-3 py-1.5 text-sm focus:border-surface-gray-7 focus:outline-none"
              />
            </div>
            <div>
              <label class="block text-xs font-medium text-ink-gray-6 mb-1">{{ __('Ends On:') }}</label>
              <input
                v-model="meetingForm.ends_on"
                type="datetime-local"
                class="w-full rounded-md border border-outline-gray-2 bg-surface-white px-3 py-1.5 text-sm focus:border-surface-gray-7 focus:outline-none"
              />
            </div>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-medium text-ink-gray-6 mb-1">{{ __('Status:') }}</label>
              <select
                v-model="meetingForm.status"
                class="w-full rounded-md border border-outline-gray-2 bg-surface-white px-3 py-1.5 text-sm focus:border-surface-gray-7 focus:outline-none"
              >
                <option value="Open">{{ __('Open') }}</option>
                <option value="Completed">{{ __('Completed') }}</option>
                <option value="Cancelled">{{ __('Cancelled') }}</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-medium text-ink-gray-6 mb-1">{{ __('Location / Video Link:') }}</label>
              <input
                v-model="meetingForm.location"
                type="text"
                class="w-full rounded-md border border-outline-gray-2 bg-surface-white px-3 py-1.5 text-sm focus:border-surface-gray-7 focus:outline-none"
                placeholder="Google Meet, Zoom, or Office..."
              />
            </div>
          </div>
          <div>
            <label class="block text-xs font-medium text-ink-gray-6 mb-1">{{ __('Meeting Notes / Description:') }}</label>
            <textarea
              v-model="meetingForm.description"
              rows="4"
              class="w-full rounded-md border border-outline-gray-2 bg-surface-white px-3 py-2 text-sm focus:border-surface-gray-7 focus:outline-none"
              placeholder="Agenda, discussion points..."
            />
          </div>
        </div>
      </template>
      <template #actions>
        <div class="flex justify-end gap-2">
          <Button variant="subtle" :label="__('Cancel')" @click="showMeetingModal = false" />
          <Button
            variant="solid"
            :label="__('Schedule Meeting')"
            :loading="actionLoading"
            :disabled="!meetingForm.title || !meetingForm.starts_on || actionLoading"
            @click="submitMeeting"
          />
        </div>
      </template>
    </Dialog>

    <!-- 5. Email Composer Modal (Only available in My Tasks context when allowEmail=true) -->
    <Dialog v-if="props.allowEmail" v-model:open="showEmailModal" :size="'xl'">
      <template #title>
        <div class="flex items-center justify-between pr-6">
          <div class="text-lg font-semibold text-ink-gray-9">
            {{ __('New Email to {0}', [contact?.full_name || 'Prospect']) }}
          </div>
          <button
            type="button"
            class="text-xs font-medium text-ink-blue-4 hover:underline"
            @click="showCcBcc = !showCcBcc"
          >
            {{ showCcBcc ? __('Hide CC/BCC') : __('Add CC/BCC') }}
          </button>
        </div>
      </template>
      <template #default>
        <div class="space-y-3 py-2 text-sm">
          <div>
            <label class="block text-xs font-medium text-ink-gray-6 mb-1">
              {{ __('To:') }} <span class="text-red-500">*</span>
            </label>
            <input
              v-model="emailForm.recipient"
              type="email"
              class="w-full rounded-md border border-outline-gray-2 bg-surface-white px-3 py-1.5 text-sm focus:border-surface-gray-7 focus:outline-none"
              placeholder="prospect@company.com"
            />
          </div>

          <div v-if="showCcBcc" class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-medium text-ink-gray-6 mb-1">{{ __('CC:') }}</label>
              <input
                v-model="emailForm.cc"
                type="text"
                class="w-full rounded-md border border-outline-gray-2 bg-surface-white px-3 py-1.5 text-sm focus:border-surface-gray-7 focus:outline-none"
                placeholder="cc@company.com"
              />
            </div>
            <div>
              <label class="block text-xs font-medium text-ink-gray-6 mb-1">{{ __('BCC:') }}</label>
              <input
                v-model="emailForm.bcc"
                type="text"
                class="w-full rounded-md border border-outline-gray-2 bg-surface-white px-3 py-1.5 text-sm focus:border-surface-gray-7 focus:outline-none"
                placeholder="bcc@company.com"
              />
            </div>
          </div>

          <!-- Unified Visual Email Editor -->
          <VisualEmailEditor
            ref="activityVisualEditorRef"
            v-model:subject="emailForm.subject"
            v-model:content="emailForm.content"
            v-model:templateName="emailForm.templateName"
            v-model:isBranded="emailForm.isBranded"
            :recipientCount="1"
            :sampleRecipient="{
              full_name: contact?.full_name || 'Prospect',
              first_name: contact?.first_name || contact?.full_name?.split(' ')[0] || 'there',
              organization: contact?.company_name || 'Organization',
              email: emailForm.recipient,
            }"
            :contactName="props.contactId || null"
            defaultMode="edit"
          />

          <!-- Attachments Section -->
          <div class="space-y-2 border-t pt-2">
            <div class="flex items-center justify-between">
              <span class="text-xs font-medium text-ink-gray-6">{{ __('Attachments') }}</span>
              <FileUploader @success="handleAttachmentUpload">
                <template #default="{ openFileSelector, uploading }">
                  <Button
                    variant="subtle"
                    size="sm"
                    iconLeft="lucide-paperclip"
                    :loading="uploading"
                    :label="__('Attach File')"
                    @click="openFileSelector"
                  />
                </template>
              </FileUploader>
            </div>
            <div v-if="emailForm.attachments.length" class="flex flex-wrap gap-2">
              <div
                v-for="(att, idx) in emailForm.attachments"
                :key="idx"
                class="inline-flex items-center gap-1.5 rounded-md bg-surface-gray-2 px-2.5 py-1 text-xs text-ink-gray-8 border border-outline-gray-2"
              >
                <span class="lucide-paperclip size-3 text-ink-gray-5" />
                <span class="max-w-[200px] truncate">{{ att.file_name }}</span>
                <button
                  type="button"
                  class="ml-1 text-ink-gray-5 hover:text-ink-red-3"
                  @click="removeAttachment(idx)"
                >
                  &times;
                </button>
              </div>
            </div>
          </div>
        </div>
      </template>
      <template #actions>
        <div class="flex items-center justify-between w-full">
          <div>
            <Button
              v-if="activityVisualEditorRef?.activeMode === 'edit'"
              variant="outline"
              size="sm"
              iconLeft="lucide-eye"
              :label="__('Preview')"
              @click="activityVisualEditorRef?.switchToPreview()"
            />
            <Button
              v-else
              variant="outline"
              size="sm"
              iconLeft="lucide-pen"
              :label="__('Edit')"
              @click="activityVisualEditorRef && (activityVisualEditorRef.activeMode = 'edit')"
            />
          </div>
          <div class="flex items-center gap-2">
            <Button
              variant="subtle"
              :label="__('Discard')"
              @click="showEmailModal = false"
            />
            <Button
              variant="solid"
              :label="__('Send Email')"
              :loading="emailSending"
              :disabled="!emailForm.recipient || !emailForm.subject || !emailForm.content || emailSending"
              @click="submitEmail"
            />
          </div>
        </div>
      </template>
    </Dialog>

    <!-- 6. Email Templates Modal -->
    <Dialog v-if="props.allowEmail" v-model:open="showTemplateModal" :size="'lg'">
      <template #title>
        <div class="text-lg font-semibold text-ink-gray-9">
          {{ __('Select Email Template') }}
        </div>
      </template>
      <template #default>
        <div class="space-y-3 py-2">
          <!-- Search Bar -->
          <div class="relative">
            <input
              v-model="templateSearchQuery"
              type="text"
              class="w-full rounded-md border border-outline-gray-2 bg-surface-white px-3 py-2 text-xs focus:border-surface-gray-7 focus:outline-none placeholder:text-ink-gray-4"
              :placeholder="__('Search email templates by name, subject, or content...')"
            />
          </div>

          <!-- Templates List -->
          <div v-if="filteredTemplates.length" class="max-h-96 space-y-2.5 overflow-y-auto pr-1">
            <div
              v-for="tpl in filteredTemplates"
              :key="tpl.name"
              class="rounded-lg border border-outline-gray-2 bg-surface-white p-3.5 hover:border-outline-gray-4 transition-colors cursor-pointer group"
              @click="selectTemplate(tpl)"
            >
              <div class="flex items-center justify-between mb-1">
                <span class="text-sm font-semibold text-ink-gray-9 group-hover:text-ink-primary">
                  {{ tpl.name }}
                </span>
                <Button
                  variant="subtle"
                  size="sm"
                  :label="__('Use Template')"
                  @click.stop="selectTemplate(tpl)"
                />
              </div>
              <div v-if="tpl.subject" class="text-xs font-medium text-ink-gray-7 mb-1">
                <span class="text-ink-gray-5">{{ __('Subject:') }}</span> {{ tpl.subject }}
              </div>
              <div v-if="tpl.preview" class="text-xs text-ink-gray-6 line-clamp-2">
                {{ tpl.preview }}
              </div>
            </div>
          </div>

          <!-- Empty State -->
          <div
            v-else
            class="flex flex-col items-center justify-center p-8 text-center text-ink-gray-5"
          >
            <span class="text-sm font-medium">{{ __('No email templates found') }}</span>
            <span class="text-xs text-ink-gray-4 mt-1">{{ __('Try adjusting your search query.') }}</span>
          </div>
        </div>
      </template>
      <template #actions>
        <div class="flex justify-end">
          <Button variant="subtle" :label="__('Close')" @click="showTemplateModal = false" />
        </div>
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import ActivityIcon from '@/components/Icons/ActivityIcon.vue'
import EmailIcon from '@/components/Icons/EmailIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import CalendarIcon from '@/components/Icons/CalendarIcon.vue'
import DealsIcon from '@/components/Icons/DealsIcon.vue'
import OutboundCallIcon from '@/components/Icons/OutboundCallIcon.vue'
import InboundCallIcon from '@/components/Icons/InboundCallIcon.vue'
import EmptyState from '@/components/ListViews/EmptyState.vue'
import DealsListView from '@/components/ListViews/DealsListView.vue'
import AudioPlayer from '@/components/Activities/AudioPlayer.vue'
import VisualEmailEditor from '@/components/VisualEmailEditor.vue'
import { Badge, Button, Dialog, Dropdown, Avatar, FileUploader, toast, createResource, call } from 'frappe-ui'
import { Editor, EditorContent, EditorFixedMenu } from 'frappe-ui/editor'
import { buildEditorExtensions, formToolbar } from '@/components/editor/config'
import { formatDate, sanitizeHTML } from '@/utils'
import { ref, reactive, computed, watch } from 'vue'

const props = defineProps({
  contact: { type: Object, default: () => ({}) },
  contactId: { type: String, required: true },
  dealRows: { type: Array, default: () => [] },
  dealColumns: { type: Array, default: () => [] },
  allowEmail: { type: Boolean, default: false },
  taskId: { type: [String, Number], default: null },
})

const emit = defineEmits(['newDeal', 'taskStatusUpdated'])

const activeTab = ref('all_activity')
const expandedEmails = reactive({})
const actionLoading = ref(false)

// Modals visibility
const showCallModal = ref(false)
const showNoteModal = ref(false)
const showMeetingModal = ref(false)
const showEmailModal = ref(false)
const showTemplateModal = ref(false)
const showCcBcc = ref(false)
const emailSending = ref(false)
const emailComposerMode = ref('edit')
const editorExtensions = buildEditorExtensions()
const editorToolbar = formToolbar

const templateSearchQuery = ref('')
const templatesList = ref([])

async function openTemplateModal() {
  templateSearchQuery.value = ''
  showTemplateModal.value = true
  try {
    const res = await call('crm.api.daily_allocation.get_email_templates')
    templatesList.value = res || []
  } catch (err) {
    console.error('Failed to load email templates:', err)
  }
}

const filteredTemplates = computed(() => {
  const q = templateSearchQuery.value.trim().toLowerCase()
  if (!q) return templatesList.value
  return templatesList.value.filter(
    (t) =>
      t.name?.toLowerCase().includes(q) ||
      t.subject?.toLowerCase().includes(q) ||
      t.preview?.toLowerCase().includes(q),
  )
})

async function selectTemplate(tpl) {
  try {
    const res = await call('crm.api.daily_allocation.render_email_template', {
      template_name: tpl.name,
      contact: props.contactId,
    })
    if (res) {
      if (res.subject) emailForm.subject = res.subject
      if (res.content) emailForm.content = res.content
      emailComposerMode.value = 'preview'
      showTemplateModal.value = false
      toast.success(__('Template "{0}" applied', [tpl.name]))
    }
  } catch (err) {
    toast.error(err.messages?.[0] || err.message || __('Failed to apply template'))
  }
}

// Form states
const activityVisualEditorRef = ref(null)
const emailForm = reactive({
  recipient: '',
  cc: '',
  bcc: '',
  subject: '',
  content: '',
  templateName: '',
  isBranded: false,
  attachments: [],
})

function openEmailModal() {
  const c = props.contact || {}
  emailForm.recipient = c.email_id || (c.email_ids?.[0]?.email_id || '')
  emailForm.subject = c.full_name ? `Follow-up: ${c.full_name}` : ''
  emailForm.content = ''
  emailForm.cc = ''
  emailForm.bcc = ''
  emailForm.templateName = ''
  emailForm.isBranded = false
  emailForm.attachments = []
  showCcBcc.value = false
  showEmailModal.value = true
}

function handleAttachmentUpload(file) {
  if (file && file.file_url) {
    emailForm.attachments.push({
      file_name: file.file_name || file.name || 'attachment',
      file_url: file.file_url,
    })
    toast.success(__('File attached'))
  }
}

function removeAttachment(index) {
  emailForm.attachments.splice(index, 1)
}

async function submitEmail() {
  if (!emailForm.recipient || !emailForm.subject || !emailForm.content) {
    toast.error(__('Please fill in all required fields (To, Subject, Message)'))
    return
  }

  emailSending.value = true
  try {
    const res = await call('crm.api.daily_allocation.send_task_email', {
      task_name: props.taskId || null,
      contact: props.contactId,
      recipient: emailForm.recipient,
      subject: emailForm.subject,
      content: emailForm.content,
      cc: emailForm.cc || null,
      bcc: emailForm.bcc || null,
      template_name: emailForm.templateName || null,
      is_branded: emailForm.isBranded,
      attachments: emailForm.attachments.length ? emailForm.attachments : null,
    })

    const isSent = res?.delivery_status === 'Sent' || res?.queue_status === 'Sent'
    toast.success(res?.message || (isSent ? __('Email sent successfully') : __('Email queued successfully')))
    showEmailModal.value = false
    emailForm.content = ''
    emailForm.attachments = []
    activitiesResource.reload()
    emit('taskStatusUpdated', res?.task_status || 'In Progress')
  } catch (err) {
    toast.error(err.messages?.[0] || err.message || __('Failed to send email'))
  } finally {
    emailSending.value = false
  }
}

// Form states
const callForm = reactive({
  type: 'Outgoing',
  phone: '',
  duration: '04:32',
  status: 'Completed',
  note: '',
})

const noteForm = reactive({
  title: '',
  content: '',
  pinned: false,
})

const meetingForm = reactive({
  title: '',
  starts_on: '',
  ends_on: '',
  status: 'Open',
  location: '',
  description: '',
})

// Initialize form defaults when contact changes
watch(
  () => props.contact,
  (c) => {
    if (c) {
      callForm.phone = c.mobile_no || (c.phone_nos?.[0]?.phone || '')
    }
  },
  { immediate: true },
)

// Fetch activities resource
const activitiesResource = createResource({
  url: 'crm.api.contact.get_contact_activities',
  params: { contact: props.contactId },
  cache: ['contact_activities', props.contactId],
  auto: true,
})

const activitiesData = computed(() => activitiesResource.data || {})
const allActivities = computed(() => activitiesData.value.all_activities || [])
const emailsList = computed(() => activitiesData.value.emails || [])
const callsList = computed(() => activitiesData.value.calls || [])
const notesList = computed(() => activitiesData.value.notes || [])
const meetingsList = computed(() => activitiesData.value.meetings || [])

const tabList = computed(() => [
  {
    value: 'all_activity',
    label: __('All Activity'),
    icon: ActivityIcon,
    count: activitiesData.value.counts?.all_activity || 0,
  },
  {
    value: 'emails',
    label: __('Emails'),
    icon: EmailIcon,
    count: activitiesData.value.counts?.emails || 0,
  },
  {
    value: 'calls',
    label: __('Calls'),
    icon: PhoneIcon,
    count: activitiesData.value.counts?.calls || 0,
  },
  {
    value: 'notes',
    label: __('Notes'),
    icon: NoteIcon,
    count: activitiesData.value.counts?.notes || 0,
  },
  {
    value: 'meetings',
    label: __('Meetings'),
    icon: CalendarIcon,
    count: activitiesData.value.counts?.meetings || 0,
  },
  {
    value: 'deals',
    label: __('Deals'),
    icon: DealsIcon,
    count: props.dealRows?.length || 0,
  },
])

const allActivityActionOptions = computed(() => {
  const options = []
  if (props.allowEmail) {
    options.push({
      label: __('Send Email'),
      icon: 'lucide-mail',
      onClick: () => openEmailModal(),
    })
  }
  options.push(
    {
      label: __('Log Call'),
      icon: 'lucide-phone',
      onClick: () => (showCallModal.value = true),
    },
    {
      label: __('Add Note'),
      icon: 'lucide-file-text',
      onClick: () => (showNoteModal.value = true),
    },
    {
      label: __('Schedule Meeting'),
      icon: 'lucide-calendar',
      onClick: () => (showMeetingModal.value = true),
    },
  )
  return options
})

function toggleEmailExpand(name) {
  expandedEmails[name] = !expandedEmails[name]
}

function formatActivityDate(d) {
  if (!d) return ''
  try {
    return formatDate(d, 'D MMM YYYY, h:mm a')
  } catch {
    return d
  }
}

function formatTimeRange(start, end) {
  if (!start) return ''
  try {
    const s = formatDate(start, 'h:mm a')
    const e = end ? formatDate(end, 'h:mm a') : ''
    return e ? `${s} – ${e}` : s
  } catch {
    return `${start} – ${end || ''}`
  }
}

function getDeliveryStatusTheme(status) {
  if (!status) return 'gray'
  const s = String(status).toLowerCase()
  if (s === 'replied') return 'teal'
  if (s === 'sent') return 'green'
  if (s === 'sending' || s === 'queued' || s === 'scheduled') return 'blue'
  if (s === 'error' || s === 'rejected' || s === 'bounced' || s === 'soft-bounced') return 'red'
  if (s === 'read' || s === 'opened' || s === 'clicked') return 'purple'
  return 'gray'
}

// -------------------------------------------------------------
// ACTION SUBMIT HANDLERS
// -------------------------------------------------------------

async function submitCall() {
  actionLoading.value = true
  try {
    // Parse duration if mm:ss
    let durationSeconds = 0
    if (String(callForm.duration).includes(':')) {
      const [m, s] = String(callForm.duration).split(':').map((n) => parseInt(n) || 0)
      durationSeconds = m * 60 + s
    } else {
      durationSeconds = parseInt(callForm.duration) || 0
    }

    await call('crm.api.contact.log_contact_call', {
      contact: props.contactId,
      call_type: callForm.type,
      phone: callForm.phone,
      duration: durationSeconds,
      status: callForm.status,
      note: callForm.note || null,
    })
    toast.success(__('Call logged successfully'))
    showCallModal.value = false
    callForm.note = ''
    activitiesResource.reload()
    if (callForm.status === 'Completed') {
      emit('taskStatusUpdated', 'In Progress')
    }
  } catch (err) {
    toast.error(err.messages?.[0] || err.message || __('Failed to log call'))
  } finally {
    actionLoading.value = false
  }
}

async function submitNote() {
  actionLoading.value = true
  try {
    await call('crm.api.contact.add_contact_note', {
      contact: props.contactId,
      title: noteForm.title,
      content: noteForm.content,
      pinned: noteForm.pinned ? 1 : 0,
    })
    toast.success(__('Note saved successfully'))
    showNoteModal.value = false
    noteForm.title = ''
    noteForm.content = ''
    noteForm.pinned = false
    activitiesResource.reload()
  } catch (err) {
    toast.error(err.messages?.[0] || err.message || __('Failed to save note'))
  } finally {
    actionLoading.value = false
  }
}

async function submitMeeting() {
  actionLoading.value = true
  try {
    await call('crm.api.contact.schedule_contact_meeting', {
      contact: props.contactId,
      title: meetingForm.title,
      starts_on: meetingForm.starts_on.replace('T', ' ') + ':00',
      ends_on: meetingForm.ends_on ? meetingForm.ends_on.replace('T', ' ') + ':00' : meetingForm.starts_on.replace('T', ' ') + ':00',
      description: meetingForm.description || null,
      status: meetingForm.status,
      location: meetingForm.location || null,
    })
    toast.success(__('Meeting scheduled successfully'))
    showMeetingModal.value = false
    meetingForm.title = ''
    meetingForm.description = ''
    activitiesResource.reload()
  } catch (err) {
    toast.error(err.messages?.[0] || err.message || __('Failed to schedule meeting'))
  } finally {
    actionLoading.value = false
  }
}

defineExpose({
  reload: () => activitiesResource.reload(),
  openEmailModal,
})
</script>

