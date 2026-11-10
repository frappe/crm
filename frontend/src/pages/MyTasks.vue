<template>
  <div class="flex h-full flex-col overflow-y-auto bg-surface-white dark:bg-surface-gray-9">
    <!-- Header -->
    <header class="flex flex-wrap items-center justify-between gap-3 border-b border-outline-gray-2 px-6 py-3.5 dark:border-outline-gray-7">
      <div class="flex items-center gap-3">
        <div class="flex size-8 items-center justify-center rounded bg-surface-gray-2 text-ink-gray-7 dark:bg-surface-gray-8 dark:text-ink-gray-3">
          <TaskIcon class="size-4.5" />
        </div>
        <div>
          <h1 class="text-lg font-semibold text-ink-gray-9 dark:text-ink-white">
            {{ __('My Tasks') }}
          </h1>
          <p class="text-xs text-ink-gray-5">
            {{ __('Manage and execute your daily allocated prospect outreach') }}
          </p>
        </div>
      </div>

      <div class="flex flex-wrap items-center gap-2">
        <!-- Admin-only User Switcher -->
        <div v-if="isAdmin" class="flex items-center gap-1.5 rounded border border-outline-gray-2 bg-surface-base px-2.5 py-1 text-xs dark:border-outline-gray-7">
          <span class="font-medium text-ink-gray-5">{{ __('User:') }}</span>
          <select
            v-model="selectedUser"
            class="bg-transparent text-xs font-semibold text-ink-gray-9 focus:outline-none dark:text-ink-white"
            @change="fetchTasks"
          >
            <option value="all">{{ __('All Users') }}</option>
            <option
              v-for="u in assignableUsers"
              :key="u.name"
              :value="u.name"
            >
              {{ u.full_name }} ({{ u.email }})
            </option>
          </select>
        </div>

        <!-- Date Filter Toggle -->
        <div class="flex items-center gap-1 rounded border border-outline-gray-2 bg-surface-base px-2 py-1 text-xs dark:border-outline-gray-7">
          <span class="font-medium text-ink-gray-5">{{ __('Date:') }}</span>
          <select
            v-model="dateFilterMode"
            class="bg-transparent text-xs font-semibold text-ink-gray-9 focus:outline-none dark:text-ink-white"
            @change="handleDateModeChange"
          >
            <option value="all">{{ __('All Dates') }}</option>
            <option value="today">{{ __('Today') }} ({{ todayStr }})</option>
            <option value="custom">{{ __('Specific Date') }}</option>
          </select>
          <input
            v-if="dateFilterMode === 'custom'"
            v-model="customDate"
            type="date"
            class="ml-1 bg-transparent text-xs text-ink-gray-9 focus:outline-none dark:text-ink-white"
            @change="fetchTasks"
          />
        </div>

        <Button
          variant="subtle"
          iconLeft="lucide-rotate-cw"
          :loading="loading"
          @click="fetchTasks"
        />
      </div>
    </header>

    <!-- Main Content -->
    <div class="flex-1 space-y-6 p-6">
      <!-- Status Summary Badges Bar -->
      <div class="flex flex-wrap items-center gap-3">
        <div
          v-for="st in statusPills"
          :key="st.value"
          class="flex cursor-pointer items-center gap-2 rounded border p-3 transition-all"
          :class="[
            currentStatus === st.value
              ? 'border-ink-gray-9 bg-surface-gray-2 shadow-xs dark:border-ink-white dark:bg-surface-gray-8'
              : 'border-outline-gray-2 bg-surface-base hover:border-outline-gray-4 dark:border-outline-gray-7',
          ]"
          @click="currentStatus = st.value"
        >
          <div class="text-xs font-medium text-ink-gray-7 dark:text-ink-gray-3">
            {{ st.label }}
          </div>
          <Badge
            variant="solid"
            size="sm"
            :class="st.badgeClass"
          >
            {{ getCountForStatus(st.value) }}
          </Badge>
        </div>
      </div>

      <!-- Tasks Section -->
      <div class="rounded border border-outline-gray-2 bg-surface-base shadow-sm dark:border-outline-gray-7">
        <!-- Search & Info Toolbar with Bulk Actions -->
        <div class="flex flex-wrap items-center justify-between gap-3 border-b border-outline-gray-2 px-5 py-3 dark:border-outline-gray-7">
          <div class="flex items-center gap-2">
            <h2 class="text-sm font-semibold text-ink-gray-9 dark:text-ink-white">
              {{ __('Tasks List') }}
            </h2>
            <Badge variant="outline" size="sm">
              {{ filteredTasks.length }} {{ __('tasks') }}
            </Badge>

            <!-- Selected items indicator & Three-Dot Bulk Actions -->
            <template v-if="selectedTaskIds.length">
              <Badge
                variant="solid"
                size="sm"
                class="bg-surface-gray-9 text-surface-white dark:bg-surface-white dark:text-ink-gray-9"
              >
                {{ selectedTaskIds.length }} {{ __('selected') }}
              </Badge>

              <!-- Three-Dot Bulk Actions Dropdown -->
              <Dropdown :options="bulkActionOptions">
                <Button
                  icon="lucide-more-horizontal"
                  variant="ghost"
                  class="!size-7 p-1 text-ink-gray-7 hover:text-ink-gray-9 dark:text-ink-gray-3"
                />
              </Dropdown>
            </template>
          </div>

          <div class="w-full sm:w-72">
            <input
              v-model="searchQuery"
              type="text"
              :placeholder="__('Search prospect, company, email, country, timezone...')"
              class="w-full rounded border border-outline-gray-2 bg-surface-white px-3 py-1.5 text-xs text-ink-gray-9 placeholder:text-ink-gray-4 focus:border-outline-gray-4 focus:outline-none dark:border-outline-gray-7 dark:bg-surface-gray-9 dark:text-ink-white"
            />
          </div>
        </div>

        <!-- Task Table -->
        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs">
            <thead class="bg-surface-gray-1 text-ink-gray-5 border-b border-outline-gray-2 dark:bg-surface-gray-8 dark:border-outline-gray-7">
              <tr>
                <th class="w-10 px-4 py-3 text-center">
                  <input
                    ref="headerCheckboxRef"
                    type="checkbox"
                    :checked="isAllSelected"
                    :disabled="!filteredTasks.length"
                    class="size-4 cursor-pointer rounded border-outline-gray-3 text-ink-primary focus:ring-0 disabled:opacity-40"
                    @change="toggleSelectAll"
                  />
                </th>
                <th class="px-5 py-3 font-medium uppercase tracking-wider">{{ __('Prospect') }}</th>
                <th class="px-5 py-3 font-medium uppercase tracking-wider">{{ __('Organization') }}</th>
                <th class="px-5 py-3 font-medium uppercase tracking-wider">{{ __('Contact Details') }}</th>
                <th class="px-5 py-3 font-medium uppercase tracking-wider">{{ __('Allocation Date') }}</th>
                <th v-if="isAdmin" class="px-5 py-3 font-medium uppercase tracking-wider">{{ __('Assigned To') }}</th>
                <th class="px-5 py-3 font-medium uppercase tracking-wider">{{ __('Status') }}</th>
                <th class="px-5 py-3 font-medium uppercase tracking-wider">{{ __('Country') }}</th>
                <th class="px-5 py-3 font-medium uppercase tracking-wider">{{ __('Timezone') }}</th>
                <th class="px-5 py-3 font-medium uppercase tracking-wider text-right">{{ __('Actions') }}</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-outline-gray-2 dark:divide-outline-gray-7">
              <tr
                v-for="task in filteredTasks"
                :key="task.name"
                class="transition-colors hover:bg-surface-gray-1/60 dark:hover:bg-surface-gray-8/50"
                :class="{ 'bg-surface-gray-1/40 dark:bg-surface-gray-8/30': selectedTaskIds.includes(task.name) }"
              >
                <!-- Row Checkbox -->
                <td class="w-10 px-4 py-3.5 text-center">
                  <input
                    type="checkbox"
                    :value="task.name"
                    v-model="selectedTaskIds"
                    class="size-4 cursor-pointer rounded border-outline-gray-3 text-ink-primary focus:ring-0"
                  />
                </td>

                <!-- Prospect -->
                <td class="px-5 py-3.5">
                  <router-link
                    :to="{
                      name: 'TaskProspect',
                      params: { contactId: task.contact },
                      query: { taskId: task.name },
                    }"
                    class="font-semibold text-ink-gray-9 hover:underline hover:text-ink-primary dark:text-ink-white"
                  >
                    {{ task.contact_name }}
                  </router-link>
                  <div class="text-[11px] text-ink-gray-4">
                    {{ __('Allocated by') }}: {{ task.allocated_by_name || task.allocated_by }}
                  </div>
                </td>

                <!-- Organization -->
                <td class="px-5 py-3.5 font-medium text-ink-gray-8 dark:text-ink-gray-2">
                  {{ task.organization || '-' }}
                </td>

                <!-- Contact Details -->
                <td class="px-5 py-3.5">
                  <div v-if="task.email">
                    <a :href="`mailto:${task.email}`" class="text-ink-gray-7 hover:underline dark:text-ink-gray-3">
                      {{ task.email }}
                    </a>
                  </div>
                  <div v-if="task.mobile_no" class="text-[11px]">
                    <a :href="`tel:${task.mobile_no}`" class="text-ink-gray-5 hover:underline">
                      {{ task.mobile_no }}
                    </a>
                  </div>
                  <div v-if="!task.email && !task.mobile_no" class="text-ink-gray-4">-</div>
                </td>

                <!-- Allocation Date -->
                <td class="px-5 py-3.5">
                  <div class="font-medium text-ink-gray-8 dark:text-ink-gray-2">
                    {{ task.allocation_date }}
                  </div>
                  <div v-if="task.allocation_date === todayStr" class="text-[10px] font-semibold text-ink-green-3">
                    {{ __('Today') }}
                  </div>
                </td>

                <!-- Assigned User (Admin view) -->
                <td v-if="isAdmin" class="px-5 py-3.5">
                  <div class="flex items-center gap-1.5">
                    <UserAvatar :user="task.assigned_to" size="xs" />
                    <span class="text-ink-gray-8 dark:text-ink-gray-2">{{ task.assigned_to_name }}</span>
                  </div>
                </td>

                <!-- Status Select -->
                <td class="px-5 py-3.5">
                  <select
                    :value="task.status"
                    class="rounded-md border border-outline-gray-2 bg-surface-white px-2 py-1 text-xs font-semibold focus:outline-none dark:border-outline-gray-7 dark:bg-surface-gray-9"
                    :class="getStatusBadgeClass(task.status)"
                    @change="handleStatusChange(task, $event.target.value)"
                  >
                    <option value="To Do">{{ __('To Do') }}</option>
                    <option value="In Progress">{{ __('In Progress') }}</option>
                    <option value="Pending">{{ __('Pending') }}</option>
                    <option value="Callback">{{ __('Callback') }}</option>
                    <option value="Follow up">{{ __('Follow up') }}</option>
                    <option value="Not Interested">{{ __('Not Interested') }}</option>
                  </select>
                </td>

                <!-- Country -->
                <td class="px-5 py-3.5">
                  <div class="font-medium text-ink-gray-8 dark:text-ink-gray-2">
                    {{ (task.country && task.country !== 'Not Available') ? task.country : __('Not Available') }}
                  </div>
                </td>

                <!-- Timezone -->
                <td class="px-5 py-3.5">
                  <div class="font-mono text-xs text-ink-gray-7 dark:text-ink-gray-3">
                    {{ formatTimezone(task.timezone) }}
                  </div>
                </td>

                <!-- Actions Column: Email and Call -->
                <td class="px-5 py-3.5 text-right whitespace-nowrap">
                  <div class="inline-flex items-center gap-1.5">
                    <Button
                      variant="subtle"
                      icon="lucide-mail"
                      :tooltip="__('Send Email')"
                      class="!size-7 p-1 text-ink-blue-3 hover:bg-surface-blue-2"
                      @click="openTaskEmail(task)"
                    />
                    <Button
                      variant="subtle"
                      icon="lucide-phone"
                      :tooltip="__('Log Call')"
                      class="!size-7 p-1 text-ink-green-3 hover:bg-surface-green-2"
                      @click="openTaskCall(task)"
                    />
                  </div>
                </td>
              </tr>

              <!-- Empty Row -->
              <tr v-if="!filteredTasks.length">
                <td :colspan="isAdmin ? 10 : 9" class="px-5 py-12 text-center text-ink-gray-5">
                  <div class="flex flex-col items-center justify-center gap-2">
                    <TaskIcon class="size-8 text-ink-gray-4" />
                    <p class="font-medium">{{ __('No tasks match your filter criteria.') }}</p>
                    <p class="text-xs text-ink-gray-4">{{ __('Assigned tasks from Daily Allocation appear here automatically.') }}</p>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- UPDATE SINGLE TASK MODAL -->
    <Dialog
      v-model="showEditModal"
      :options="{
        title: __('Update Task Progress'),
        size: 'lg',
      }"
    >
      <template #body-content>
        <div v-if="selectedTask" class="space-y-4 text-xs">
          <!-- Prospect Details Summary -->
          <div class="rounded bg-surface-gray-2 p-3 dark:bg-surface-gray-8">
            <div class="font-semibold text-ink-gray-9 dark:text-ink-white">{{ selectedTask.contact_name }}</div>
            <div class="text-ink-gray-5">
              {{ selectedTask.organization ? selectedTask.organization + ' • ' : '' }}
              {{ selectedTask.email }} • {{ selectedTask.mobile_no }}
            </div>
            <div class="mt-1 text-[11px] text-ink-gray-4">
              {{ __('Allocated for:') }} {{ selectedTask.allocation_date }} | {{ __('Assigned to:') }} {{ selectedTask.assigned_to_name }}
            </div>
          </div>

          <!-- Status Dropdown -->
          <div>
            <label class="mb-1 block font-medium text-ink-gray-7 dark:text-ink-gray-3">
              {{ __('Status *') }}
            </label>
            <select
              v-model="editForm.status"
              class="w-full rounded border border-outline-gray-2 bg-surface-white px-3 py-2 text-xs text-ink-gray-9 focus:border-outline-gray-4 focus:outline-none dark:border-outline-gray-7 dark:bg-surface-gray-9 dark:text-ink-white"
            >
              <option value="To Do">{{ __('To Do') }}</option>
              <option value="In Progress">{{ __('In Progress') }}</option>
              <option value="Pending">{{ __('Pending') }}</option>
              <option value="Callback">{{ __('Callback') }}</option>
              <option value="Follow up">{{ __('Follow up') }}</option>
              <option value="Not Interested">{{ __('Not Interested') }}</option>
            </select>
          </div>

          <!-- Follow-up Date -->
          <div>
            <label class="mb-1 block font-medium text-ink-gray-7 dark:text-ink-gray-3">
              {{ __('Follow-up Date (optional)') }}
            </label>
            <input
              v-model="editForm.follow_up_date"
              type="date"
              class="w-full rounded border border-outline-gray-2 bg-surface-white px-3 py-2 text-xs text-ink-gray-9 focus:border-outline-gray-4 focus:outline-none dark:border-outline-gray-7 dark:bg-surface-gray-9 dark:text-ink-white"
            />
          </div>

          <!-- Notes Textarea -->
          <div>
            <label class="mb-1 block font-medium text-ink-gray-7 dark:text-ink-gray-3">
              {{ __('Notes & Remarks') }}
            </label>
            <textarea
              v-model="editForm.notes"
              rows="4"
              :placeholder="__('Record notes from your discussion, call outcome, next steps...')"
              class="w-full rounded border border-outline-gray-2 bg-surface-white p-3 text-xs text-ink-gray-9 placeholder:text-ink-gray-4 focus:border-outline-gray-4 focus:outline-none dark:border-outline-gray-7 dark:bg-surface-gray-9 dark:text-ink-white"
            />
          </div>
        </div>
      </template>

      <template #actions>
        <Button
          variant="subtle"
          :label="__('Cancel')"
          @click="showEditModal = false"
        />
        <Button
          variant="solid"
          :loading="saving"
          :label="__('Save Progress')"
          @click="submitEdit"
        />
      </template>
    </Dialog>

    <!-- BULK EDIT MODAL -->
    <Dialog
      v-model:open="showBulkEditModal"
      :title="__('Bulk Edit Tasks')"
      size="md"
    >
      <template #default>
        <div class="space-y-4 text-xs">
          <p class="text-ink-gray-5">
            {{ __('Update workflow status, follow-up date, or remarks for {0} selected task(s).', [selectedTaskIds.length]) }}
          </p>

          <!-- Status Dropdown -->
          <div>
            <label class="mb-1 block font-medium text-ink-gray-7 dark:text-ink-gray-3">
              {{ __('Task Workflow Status') }}
            </label>
            <select
              v-model="bulkEditForm.status"
              class="w-full rounded border border-outline-gray-2 bg-surface-white px-3 py-2 text-xs text-ink-gray-9 focus:border-outline-gray-4 focus:outline-none dark:border-outline-gray-7 dark:bg-surface-gray-9 dark:text-ink-white"
            >
              <option value="">{{ __('Keep current status') }}</option>
              <option value="To Do">{{ __('To Do') }}</option>
              <option value="In Progress">{{ __('In Progress') }}</option>
              <option value="Pending">{{ __('Pending') }}</option>
              <option value="Callback">{{ __('Callback') }}</option>
              <option value="Follow up">{{ __('Follow up') }}</option>
              <option value="Not Interested">{{ __('Not Interested') }}</option>
            </select>
          </div>

          <!-- Follow-up Date -->
          <div>
            <label class="mb-1 block font-medium text-ink-gray-7 dark:text-ink-gray-3">
              {{ __('Follow-up Date') }}
            </label>
            <input
              v-model="bulkEditForm.follow_up_date"
              type="date"
              class="w-full rounded border border-outline-gray-2 bg-surface-white px-3 py-2 text-xs text-ink-gray-9 focus:border-outline-gray-4 focus:outline-none dark:border-outline-gray-7 dark:bg-surface-gray-9 dark:text-ink-white"
            />
          </div>

          <!-- Notes -->
          <div>
            <label class="mb-1 block font-medium text-ink-gray-7 dark:text-ink-gray-3">
              {{ __('Notes & Remarks') }}
            </label>
            <textarea
              v-model="bulkEditForm.notes"
              rows="3"
              :placeholder="__('Add notes to selected tasks...')"
              class="w-full rounded border border-outline-gray-2 bg-surface-white p-3 text-xs text-ink-gray-9 placeholder:text-ink-gray-4 focus:border-outline-gray-4 focus:outline-none dark:border-outline-gray-7 dark:bg-surface-gray-9 dark:text-ink-white"
            />
          </div>
        </div>
      </template>

      <template #actions>
        <div class="flex items-center justify-end gap-2">
          <Button
            variant="subtle"
            :label="__('Cancel')"
            @click="showBulkEditModal = false"
          />
          <Button
            variant="solid"
            :loading="bulkSaving"
            :label="__('Update {0} Tasks', [selectedTaskIds.length])"
            @click="submitBulkEdit"
          />
        </div>
      </template>
    </Dialog>

    <!-- ADMIN BULK ASSIGN MODAL -->
    <Dialog
      v-model:open="showAssignModal"
      :title="__('Assign Tasks')"
      size="md"
    >
      <template #default>
        <div class="space-y-4 text-xs">
          <p class="text-ink-gray-5">
            {{ __('Reassign {0} selected task(s) to a team member.', [selectedTaskIds.length]) }}
          </p>

          <div>
            <label class="mb-1 block font-medium text-ink-gray-7 dark:text-ink-gray-3">
              {{ __('Assign To *') }}
            </label>
            <select
              v-model="bulkAssignTargetUser"
              class="w-full rounded border border-outline-gray-2 bg-surface-white px-3 py-2 text-xs text-ink-gray-9 focus:border-outline-gray-4 focus:outline-none dark:border-outline-gray-7 dark:bg-surface-gray-9 dark:text-ink-white"
            >
              <option value="">{{ __('Select a user...') }}</option>
              <option
                v-for="u in assignableUsers"
                :key="u.name"
                :value="u.name"
              >
                {{ u.full_name }} ({{ u.email }})
              </option>
            </select>
          </div>
        </div>
      </template>

      <template #actions>
        <div class="flex items-center justify-end gap-2">
          <Button
            variant="subtle"
            :label="__('Cancel')"
            @click="showAssignModal = false"
          />
          <Button
            variant="solid"
            :loading="bulkAssigning"
            :disabled="!bulkAssignTargetUser"
            :label="__('Assign Tasks')"
            @click="submitBulkAssign"
          />
        </div>
      </template>
    </Dialog>

    <!-- BULK EMAIL MODAL -->
    <BulkEmailModal
      v-if="showBulkEmailModal"
      v-model="showBulkEmailModal"
      doctype="CRM Daily Allocation"
      :selectedValues="selectedTaskIds"
      @reload="onBulkEmailReload"
    />

    <!-- TASK EMAIL MODAL -->
    <Dialog
      v-model:open="showTaskEmailModal"
      :title="__('Send Email to {0}', [activeEmailTask?.contact_name || 'Prospect'])"
      size="lg"
    >
      <template #default>
        <div class="space-y-3 py-2 text-xs">
          <div>
            <label class="mb-1 block font-medium text-ink-gray-7 dark:text-ink-gray-3">{{ __('Recipient Email *') }}</label>
            <input
              v-model="taskEmailForm.recipient"
              type="email"
              placeholder="recipient@example.com"
              class="w-full rounded border border-outline-gray-2 bg-surface-white px-3 py-1.5 text-xs text-ink-gray-9 focus:border-outline-gray-4 focus:outline-none dark:border-outline-gray-7 dark:bg-surface-gray-9 dark:text-ink-white"
            />
          </div>
          <div>
            <label class="mb-1 block font-medium text-ink-gray-7 dark:text-ink-gray-3">{{ __('Subject *') }}</label>
            <input
              v-model="taskEmailForm.subject"
              type="text"
              placeholder="Email subject..."
              class="w-full rounded border border-outline-gray-2 bg-surface-white px-3 py-1.5 text-xs text-ink-gray-9 focus:border-outline-gray-4 focus:outline-none dark:border-outline-gray-7 dark:bg-surface-gray-9 dark:text-ink-white"
            />
          </div>
          <div class="grid grid-cols-2 gap-2">
            <div>
              <label class="mb-1 block font-medium text-ink-gray-7 dark:text-ink-gray-3">{{ __('CC (optional)') }}</label>
              <input
                v-model="taskEmailForm.cc"
                type="text"
                placeholder="cc@example.com"
                class="w-full rounded border border-outline-gray-2 bg-surface-white px-3 py-1.5 text-xs text-ink-gray-9 focus:border-outline-gray-4 focus:outline-none dark:border-outline-gray-7 dark:bg-surface-gray-9 dark:text-ink-white"
              />
            </div>
            <div>
              <label class="mb-1 block font-medium text-ink-gray-7 dark:text-ink-gray-3">{{ __('BCC (optional)') }}</label>
              <input
                v-model="taskEmailForm.bcc"
                type="text"
                placeholder="bcc@example.com"
                class="w-full rounded border border-outline-gray-2 bg-surface-white px-3 py-1.5 text-xs text-ink-gray-9 focus:border-outline-gray-4 focus:outline-none dark:border-outline-gray-7 dark:bg-surface-gray-9 dark:text-ink-white"
              />
            </div>
          </div>
          <div>
            <label class="mb-1 block font-medium text-ink-gray-7 dark:text-ink-gray-3">{{ __('Message *') }}</label>
            <textarea
              v-model="taskEmailForm.content"
              rows="6"
              placeholder="Write your email message here..."
              class="w-full rounded border border-outline-gray-2 bg-surface-white p-3 text-xs text-ink-gray-9 focus:border-outline-gray-4 focus:outline-none dark:border-outline-gray-7 dark:bg-surface-gray-9 dark:text-ink-white"
            />
          </div>
        </div>
      </template>
      <template #actions>
        <div class="flex items-center justify-end gap-2">
          <Button
            variant="subtle"
            :label="__('Cancel')"
            @click="showTaskEmailModal = false"
          />
          <Button
            variant="solid"
            :loading="taskEmailSending"
            :disabled="!taskEmailForm.recipient || !taskEmailForm.subject || !taskEmailForm.content"
            :label="__('Send Email')"
            @click="submitTaskEmail"
          />
        </div>
      </template>
    </Dialog>

    <!-- TASK CALL MODAL -->
    <Dialog
      v-model:open="showTaskCallModal"
      :title="__('Log Call with {0}', [activeCallTask?.contact_name || 'Prospect'])"
      size="md"
    >
      <template #default>
        <div class="space-y-3 py-2 text-xs">
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="mb-1 block font-medium text-ink-gray-7 dark:text-ink-gray-3">{{ __('Call Type') }}</label>
              <select
                v-model="taskCallForm.type"
                class="w-full rounded border border-outline-gray-2 bg-surface-white px-3 py-1.5 text-xs text-ink-gray-9 focus:border-outline-gray-4 focus:outline-none dark:border-outline-gray-7 dark:bg-surface-gray-9 dark:text-ink-white"
              >
                <option value="Outgoing">{{ __('Outgoing') }}</option>
                <option value="Incoming">{{ __('Incoming') }}</option>
              </select>
            </div>
            <div>
              <label class="mb-1 block font-medium text-ink-gray-7 dark:text-ink-gray-3">{{ __('Status') }}</label>
              <select
                v-model="taskCallForm.status"
                class="w-full rounded border border-outline-gray-2 bg-surface-white px-3 py-1.5 text-xs text-ink-gray-9 focus:border-outline-gray-4 focus:outline-none dark:border-outline-gray-7 dark:bg-surface-gray-9 dark:text-ink-white"
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
              <label class="mb-1 block font-medium text-ink-gray-7 dark:text-ink-gray-3">{{ __('Phone Number *') }}</label>
              <input
                v-model="taskCallForm.phone"
                type="text"
                placeholder="+1 234 567 8900"
                class="w-full rounded border border-outline-gray-2 bg-surface-white px-3 py-1.5 text-xs text-ink-gray-9 focus:border-outline-gray-4 focus:outline-none dark:border-outline-gray-7 dark:bg-surface-gray-9 dark:text-ink-white"
              />
            </div>
            <div>
              <label class="mb-1 block font-medium text-ink-gray-7 dark:text-ink-gray-3">{{ __('Duration (seconds or mm:ss)') }}</label>
              <input
                v-model="taskCallForm.duration"
                type="text"
                placeholder="150 or 02:30"
                class="w-full rounded border border-outline-gray-2 bg-surface-white px-3 py-1.5 text-xs text-ink-gray-9 focus:border-outline-gray-4 focus:outline-none dark:border-outline-gray-7 dark:bg-surface-gray-9 dark:text-ink-white"
              />
            </div>
          </div>
          <div>
            <label class="mb-1 block font-medium text-ink-gray-7 dark:text-ink-gray-3">{{ __('Notes & Remarks') }}</label>
            <textarea
              v-model="taskCallForm.note"
              rows="3"
              placeholder="Record call discussion, questions asked, next steps..."
              class="w-full rounded border border-outline-gray-2 bg-surface-white p-3 text-xs text-ink-gray-9 focus:border-outline-gray-4 focus:outline-none dark:border-outline-gray-7 dark:bg-surface-gray-9 dark:text-ink-white"
            />
          </div>
        </div>
      </template>
      <template #actions>
        <div class="flex items-center justify-end gap-2">
          <Button
            variant="subtle"
            :label="__('Cancel')"
            @click="showTaskCallModal = false"
          />
          <Button
            variant="solid"
            :loading="taskCallSaving"
            :disabled="!taskCallForm.phone"
            :label="__('Log Call')"
            @click="submitTaskCall"
          />
        </div>
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watchEffect, onMounted, onBeforeUnmount } from 'vue'
import { call, Button, Dialog, Badge, Dropdown, toast } from 'frappe-ui'
import { globalStore } from '@/stores/global'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import BulkEmailModal from '@/components/Modals/BulkEmailModal.vue'

const { $dialog, $socket } = globalStore()

const todayStr = new Date().toLocaleDateString('en-CA')
const loading = ref(false)
const isAdmin = ref(false)
const selectedUser = ref('all')
const dateFilterMode = ref('all')
const customDate = ref(todayStr)
const currentStatus = ref('To Do')
const searchQuery = ref('')

const tasks = ref([])
const assignableUsers = ref([])
const selectedTaskIds = ref([])
const headerCheckboxRef = ref(null)

// Single Edit Modal
const showEditModal = ref(false)
const saving = ref(false)
const selectedTask = ref(null)
const editForm = reactive({
  status: 'To Do',
  follow_up_date: '',
  notes: '',
})

// Bulk Modals
const showBulkEditModal = ref(false)
const bulkSaving = ref(false)
const bulkEditForm = reactive({
  status: '',
  follow_up_date: '',
  notes: '',
})

const showAssignModal = ref(false)
const bulkAssigning = ref(false)
const bulkAssignTargetUser = ref('')

const showBulkEmailModal = ref(false)

// Task Email & Call Modals
const showTaskEmailModal = ref(false)
const activeEmailTask = ref(null)
const taskEmailSending = ref(false)
const taskEmailForm = reactive({
  recipient: '',
  subject: '',
  cc: '',
  bcc: '',
  content: '',
})

const showTaskCallModal = ref(false)
const activeCallTask = ref(null)
const taskCallSaving = ref(false)
const taskCallForm = reactive({
  type: 'Outgoing',
  status: 'Completed',
  phone: '',
  duration: '02:30',
  note: '',
})

const statusPills = [
  { label: 'To Do', value: 'To Do', badgeClass: 'bg-surface-gray-2 text-ink-gray-7' },
  { label: 'In Progress', value: 'In Progress', badgeClass: 'bg-surface-blue-2 text-ink-blue-3' },
  { label: 'Pending', value: 'Pending', badgeClass: 'bg-surface-amber-2 text-ink-amber-3' },
  { label: 'Callback', value: 'Callback', badgeClass: 'bg-surface-purple-2 text-ink-purple-3' },
  { label: 'Follow up', value: 'Follow up', badgeClass: 'bg-surface-teal-2 text-ink-teal-3' },
  { label: 'Not Interested', value: 'Not Interested', badgeClass: 'bg-surface-gray-3 text-ink-gray-7' },
]

const myTaskStatuses = [
  'To Do',
  'In Progress',
  'Pending',
  'Callback',
  'Follow up',
  'Not Interested',
]

const TZ_FALLBACK_MAP = {
  'Asia/Kolkata': 'GMT+5:30 (IST)',
  'Asia/Singapore': 'GMT+8 (SGT)',
  'Asia/Kuala_Lumpur': 'GMT+8 (MYT)',
  'Europe/London': 'GMT+0 (GMT)',
  'America/New_York': 'GMT-5 (EST)',
  'America/Chicago': 'GMT-6 (CST)',
  'America/Los_Angeles': 'GMT-8 (PST)',
  'Australia/Sydney': 'GMT+11 (AEDT)',
  'Asia/Dubai': 'GMT+4 (GST)',
  'Asia/Tokyo': 'GMT+9 (JST)',
}

function formatTimezone(tz) {
  if (!tz || tz === 'Not Available') return __('Not Available')
  if (String(tz).startsWith('GMT')) return tz
  return TZ_FALLBACK_MAP[tz] || tz
}

// Three-Dot Bulk Actions
const bulkActionOptions = computed(() => {
  const actions = []

  // 1. Edit
  actions.push({
    label: __('Edit'),
    onClick: () => openBulkEditModal(),
  })

  // 2. Delete (Admin only)
  if (isAdmin.value) {
    actions.push({
      label: __('Delete'),
      onClick: () => confirmBulkDelete(),
    })
  }

  // 3. Assign To (Admin only)
  if (isAdmin.value) {
    actions.push({
      label: __('Assign To'),
      onClick: () => {
        bulkAssignTargetUser.value = ''
        showAssignModal.value = true
      },
    })

    // 4. Clear Assignment (Admin only)
    actions.push({
      label: __('Clear Assignment'),
      onClick: () => confirmClearAssignment(),
    })
  }

  // 5. Convert to Deal
  actions.push({
    label: __('Convert to Deal'),
    onClick: () => confirmConvertToDeal(),
  })

  // 6. Bulk Email
  actions.push({
    label: __('Bulk Email'),
    onClick: () => {
      showBulkEmailModal.value = true
    },
  })

  // 7. Change Status (with submenu containing the 6 My Task Statuses)
  actions.push({
    label: __('Change Status'),
    submenu: myTaskStatuses.map((st) => ({
      label: __(st),
      onClick: () => applyTaskStatus(st),
    })),
  })

  return actions
})

function openBulkEditModal() {
  bulkEditForm.status = ''
  bulkEditForm.follow_up_date = ''
  bulkEditForm.notes = ''
  showBulkEditModal.value = true
}

async function submitBulkEdit() {
  bulkSaving.value = true
  try {
    const res = await call('crm.api.daily_allocation.bulk_update_tasks', {
      tasks: selectedTaskIds.value,
      status: bulkEditForm.status || null,
      notes: bulkEditForm.notes ? bulkEditForm.notes : null,
      follow_up_date: bulkEditForm.follow_up_date || null,
    })
    toast.success(res.message || __('Tasks updated successfully.'))
    showBulkEditModal.value = false
    selectedTaskIds.value = []
    await fetchTasks()
  } catch (err) {
    toast.error(err.message || __('Failed to update tasks.'))
  } finally {
    bulkSaving.value = false
  }
}

function confirmBulkDelete() {
  $dialog({
    title: __('Delete Tasks'),
    message: __('Are you sure you want to delete {0} selected task(s)?', [selectedTaskIds.value.length]),
    variant: 'solid',
    theme: 'red',
    actions: [
      {
        label: __('Delete'),
        theme: 'red',
        variant: 'solid',
        onClick: async ({ close }) => {
          try {
            const res = await call('crm.api.daily_allocation.bulk_delete_tasks', {
              tasks: selectedTaskIds.value,
            })
            toast.success(res.message || __('Tasks deleted successfully.'))
            selectedTaskIds.value = []
            await fetchTasks()
            close()
          } catch (err) {
            toast.error(err.message || __('Failed to delete tasks.'))
          }
        },
      },
    ],
  })
}

async function submitBulkAssign() {
  if (!bulkAssignTargetUser.value) return
  bulkAssigning.value = true
  try {
    const res = await call('crm.api.daily_allocation.bulk_reassign_tasks', {
      tasks: selectedTaskIds.value,
      new_user: bulkAssignTargetUser.value,
    })
    toast.success(res.message || __('Tasks reassigned successfully.'))
    showAssignModal.value = false
    selectedTaskIds.value = []
    await fetchTasks()
  } catch (err) {
    toast.error(err.message || __('Failed to reassign tasks.'))
  } finally {
    bulkAssigning.value = false
  }
}

function confirmClearAssignment() {
  $dialog({
    title: __('Clear Assignment'),
    message: __('Are you sure you want to clear assignment for {0} selected task(s)?', [selectedTaskIds.value.length]),
    variant: 'solid',
    theme: 'red',
    actions: [
      {
        label: __('Clear Assignment'),
        theme: 'red',
        variant: 'solid',
        onClick: async ({ close }) => {
          try {
            const res = await call('crm.api.daily_allocation.bulk_clear_task_assignments', {
              tasks: selectedTaskIds.value,
            })
            toast.success(res.message || __('Assignments cleared successfully.'))
            selectedTaskIds.value = []
            await fetchTasks()
            close()
          } catch (err) {
            toast.error(err.message || __('Failed to clear assignments.'))
          }
        },
      },
    ],
  })
}

function confirmConvertToDeal() {
  $dialog({
    title: __('Convert to Deal'),
    message: __('Are you sure you want to convert {0} selected prospect(s) to deal(s)?', [selectedTaskIds.value.length]),
    variant: 'solid',
    theme: 'blue',
    actions: [
      {
        label: __('Convert'),
        variant: 'solid',
        onClick: async ({ close }) => {
          try {
            const res = await call('crm.api.daily_allocation.bulk_convert_to_deal', {
              doctype: 'CRM Daily Allocation',
              names: selectedTaskIds.value,
            })
            if (res.converted > 0) {
              toast.success(__('Successfully converted {0} record(s) to deal(s).', [res.converted]))
            }
            if (res.errors && res.errors.length) {
              toast.warning(res.errors[0])
            }
            selectedTaskIds.value = []
            await fetchTasks()
            close()
          } catch (err) {
            toast.error(err.message || __('Failed to convert to deal.'))
          }
        },
      },
    ],
  })
}

async function applyProspectStatus(statusName) {
  try {
    const res = await call('crm.api.daily_allocation.change_prospect_status', {
      doctype: 'CRM Daily Allocation',
      names: selectedTaskIds.value,
      status: statusName,
    })
    if (res.updated > 0) {
      toast.success(__('Updated CRM Lead status to {0} for {1} prospect(s)', [statusName, res.updated]))
    }
    if (res.skipped > 0) {
      toast.warning(__('Skipped {0} record(s) without linked CRM Lead', [res.skipped]))
    }
    await fetchTasks()
  } catch (err) {
    toast.error(err.message || __('Failed to update status.'))
  }
}

async function applyTaskStatus(statusName) {
  try {
    const res = await call('crm.api.daily_allocation.bulk_update_tasks', {
      tasks: selectedTaskIds.value,
      status: statusName,
    })
    toast.success(res.message || __('Updated {0} task(s) to {1}.', [selectedTaskIds.value.length, statusName]))
    selectedTaskIds.value = []
    await fetchTasks()
  } catch (err) {
    toast.error(err.message || __('Failed to update status.'))
  }
}

function openTaskEmail(task) {
  activeEmailTask.value = task
  taskEmailForm.recipient = task.email || ''
  taskEmailForm.subject = `Follow-up: ${task.contact_name}`
  taskEmailForm.content = `Hi ${task.contact_name},\n\nI am following up regarding our discussion.`
  taskEmailForm.cc = ''
  taskEmailForm.bcc = ''
  showTaskEmailModal.value = true
}

async function submitTaskEmail() {
  if (!activeEmailTask.value) return
  taskEmailSending.value = true
  try {
    await call('crm.api.daily_allocation.send_task_email', {
      task_name: activeEmailTask.value.name,
      recipient: taskEmailForm.recipient,
      subject: taskEmailForm.subject,
      content: taskEmailForm.content,
      cc: taskEmailForm.cc || null,
      bcc: taskEmailForm.bcc || null,
    })
    toast.success(__('Email sent successfully'))
    showTaskEmailModal.value = false
    if (activeEmailTask.value.status === 'To Do') {
      activeEmailTask.value.status = 'In Progress'
    }
    await fetchTasks()
  } catch (err) {
    toast.error(err.message || __('Failed to send email'))
  } finally {
    taskEmailSending.value = false
  }
}

function openTaskCall(task) {
  activeCallTask.value = task
  taskCallForm.type = 'Outgoing'
  taskCallForm.status = 'Completed'
  taskCallForm.phone = task.mobile_no || ''
  taskCallForm.duration = '02:30'
  taskCallForm.note = ''
  showTaskCallModal.value = true
}

async function submitTaskCall() {
  if (!activeCallTask.value) return
  taskCallSaving.value = true
  try {
    let durSec = 0
    if (String(taskCallForm.duration).includes(':')) {
      const [m, s] = String(taskCallForm.duration).split(':').map((n) => parseInt(n) || 0)
      durSec = m * 60 + s
    } else {
      durSec = parseInt(taskCallForm.duration) || 0
    }

    await call('crm.api.daily_allocation.log_task_call', {
      task_name: activeCallTask.value.name,
      call_type: taskCallForm.type,
      phone: taskCallForm.phone,
      duration: durSec,
      status: taskCallForm.status,
      note: taskCallForm.note || null,
    })
    toast.success(__('Call logged successfully'))
    showTaskCallModal.value = false
    if (taskCallForm.status === 'Completed' && activeCallTask.value.status === 'To Do') {
      activeCallTask.value.status = 'In Progress'
    }
    await fetchTasks()
  } catch (err) {
    toast.error(err.message || __('Failed to log call'))
  } finally {
    taskCallSaving.value = false
  }
}

function onBulkEmailReload() {
  selectedTaskIds.value = []
  fetchTasks()
}

function handleDateModeChange() {
  if (dateFilterMode.value === 'today') {
    customDate.value = todayStr
  }
  fetchTasks()
}

async function fetchTasks() {
  loading.value = true
  try {
    // Determine admin status
    const summary = await call('crm.api.daily_allocation.get_daily_allocation_summary', {
      date: todayStr,
    })
    isAdmin.value = summary.is_admin

    if (isAdmin.value && !assignableUsers.value.length) {
      assignableUsers.value = await call('crm.api.daily_allocation.get_assignable_users')
    }

    const params = {}
    if (dateFilterMode.value === 'today') {
      params.date = todayStr
    } else if (dateFilterMode.value === 'custom' && customDate.value) {
      params.date = customDate.value
    }

    if (isAdmin.value && selectedUser.value !== 'all') {
      params.user = selectedUser.value
    }

    tasks.value = await call('crm.api.daily_allocation.get_allocated_tasks', params)
  } catch (error) {
    console.error('Error fetching tasks in MyTask:', error)
  } finally {
    loading.value = false
  }
}

function getCountForStatus(statusVal) {
  if (!tasks.value) return 0
  return tasks.value.filter((t) => t.status === statusVal).length
}

const filteredTasks = computed(() => {
  let list = tasks.value || []
  list = list.filter((t) => t.status === currentStatus.value)

  if (searchQuery.value.trim()) {
    const q = searchQuery.value.trim().toLowerCase()
    list = list.filter((t) =>
      (t.contact_name || '').toLowerCase().includes(q) ||
      (t.organization || '').toLowerCase().includes(q) ||
      (t.email || '').toLowerCase().includes(q) ||
      (t.mobile_no || '').toLowerCase().includes(q) ||
      (t.country || '').toLowerCase().includes(q) ||
      (t.timezone || '').toLowerCase().includes(q) ||
      (t.notes || '').toLowerCase().includes(q)
    )
  }
  return list
})

// Checkbox selection computed & indeterminate state
const isAllSelected = computed(() => {
  if (!filteredTasks.value.length) return false
  return filteredTasks.value.every((t) => selectedTaskIds.value.includes(t.name))
})

const isIndeterminate = computed(() => {
  if (!filteredTasks.value.length) return false
  const selectedCount = filteredTasks.value.filter((t) => selectedTaskIds.value.includes(t.name)).length
  return selectedCount > 0 && selectedCount < filteredTasks.value.length
})

watchEffect(() => {
  if (headerCheckboxRef.value) {
    headerCheckboxRef.value.indeterminate = isIndeterminate.value
  }
})

function toggleSelectAll(event) {
  const checked = event.target.checked
  const currentVisibleIds = filteredTasks.value.map((t) => t.name)
  if (checked) {
    const newSet = new Set(selectedTaskIds.value)
    currentVisibleIds.forEach((id) => newSet.add(id))
    selectedTaskIds.value = Array.from(newSet)
  } else {
    selectedTaskIds.value = selectedTaskIds.value.filter((id) => !currentVisibleIds.includes(id))
  }
}

function getStatusBadgeClass(status) {
  switch (status) {
    case 'To Do':
      return 'bg-surface-gray-1 text-ink-gray-7 border-outline-gray-3'
    case 'In Progress':
      return 'bg-surface-blue-1 text-ink-blue-3 border-outline-blue-2'
    case 'Pending':
      return 'bg-surface-amber-1 text-ink-amber-3 border-outline-amber-2'
    case 'Callback':
      return 'bg-surface-purple-1 text-ink-purple-3 border-outline-purple-2'
    case 'Follow up':
      return 'bg-surface-teal-1 text-ink-teal-3 border-outline-teal-2'
    case 'Not Interested':
      return 'bg-surface-gray-2 text-ink-gray-6 border-outline-gray-3'
    default:
      return 'bg-surface-gray-1 text-ink-gray-7 border-outline-gray-2'
  }
}

async function handleStatusChange(task, newStatus) {
  const previousStatus = task.status
  task.status = newStatus
  try {
    await call('crm.api.daily_allocation.update_task_status', {
      task_name: task.name,
      status: newStatus,
    })
  } catch (error) {
    console.error('Error updating status:', error)
    task.status = previousStatus
  }
}

function openEditModal(task) {
  selectedTask.value = task
  editForm.status = task.status || 'To Do'
  editForm.follow_up_date = task.follow_up_date || ''
  editForm.notes = task.notes || ''
  showEditModal.value = true
}

async function submitEdit() {
  if (!selectedTask.value) return
  saving.value = true
  try {
    await call('crm.api.daily_allocation.update_task_status', {
      task_name: selectedTask.value.name,
      status: editForm.status,
      notes: editForm.notes,
      follow_up_date: editForm.follow_up_date,
    })
    selectedTask.value.status = editForm.status
    selectedTask.value.notes = editForm.notes
    selectedTask.value.follow_up_date = editForm.follow_up_date
    showEditModal.value = false
  } catch (error) {
    console.error('Save failed:', error)
  } finally {
    saving.value = false
  }
}

function onTasksRealtimeUpdate() {
  fetchTasks()
}

onMounted(() => {
  fetchTasks()
  if ($socket) {
    $socket.on('crm_tasks_updated', onTasksRealtimeUpdate)
  }
})

onBeforeUnmount(() => {
  if ($socket) {
    $socket.off('crm_tasks_updated', onTasksRealtimeUpdate)
  }
})
</script>
