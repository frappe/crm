<template>
  <div class="flex h-full flex-col overflow-y-auto bg-surface-white dark:bg-surface-gray-9">
    <!-- Header -->
    <header class="flex flex-wrap items-center justify-between gap-3 border-b border-outline-gray-2 px-6 py-3.5 dark:border-outline-gray-7">
      <div class="flex items-center gap-3">
        <div class="flex size-8 items-center justify-center rounded bg-surface-gray-2 text-ink-gray-7 dark:bg-surface-gray-8 dark:text-ink-gray-3">
          <CalendarIcon class="size-4.5" />
        </div>
        <div>
          <h1 class="text-lg font-semibold text-ink-gray-9 dark:text-ink-white">
            {{ isAdmin ? __('Daily Allocation') : __('My Daily Allocation') }}
          </h1>
          <p class="text-xs text-ink-gray-5">
            {{ isAdmin ? __('Manage and inspect date-based prospect assignments across your team') : __('Your assigned prospects for today') }}
          </p>
        </div>
      </div>

      <div class="flex items-center gap-2">
        <!-- Date Filter (Admin can choose any date; standard user sees today) -->
        <div v-if="isAdmin" class="flex items-center gap-1.5 rounded border border-outline-gray-2 bg-surface-base px-2 py-1 text-sm dark:border-outline-gray-7">
          <span class="text-xs font-medium text-ink-gray-5">{{ __('Date:') }}</span>
          <input
            v-model="selectedDate"
            type="date"
            class="bg-transparent text-sm font-medium text-ink-gray-9 focus:outline-none dark:text-ink-white"
            @change="fetchData"
          />
          <button
            v-if="selectedDate !== todayStr"
            type="button"
            class="rounded px-1.5 py-0.5 text-xs font-medium text-ink-primary hover:bg-surface-gray-2 dark:hover:bg-surface-gray-8"
            @click="setToday"
          >
            {{ __('Today') }}
          </button>
        </div>
        <div v-else class="flex items-center gap-2 rounded bg-surface-gray-2 px-3 py-1.5 text-xs font-medium text-ink-gray-7 dark:bg-surface-gray-8 dark:text-ink-gray-3">
          <span>{{ __('Date: Today') }} ({{ todayStr }})</span>
        </div>

        <Button
          variant="subtle"
          iconLeft="lucide-rotate-cw"
          :loading="loading"
          @click="fetchData"
        />

        <!-- Allocate Button (Admin Only) -->
        <Button
          v-if="isAdmin"
          variant="solid"
          iconLeft="lucide-user-plus"
          :label="__('Allocate Prospects')"
          @click="openAllocateModal"
        />
      </div>
    </header>

    <!-- Main Content Area -->
    <div class="flex-1 space-y-6 p-6">
      <!-- 1. SUMMARY METRICS CARDS -->
      <div class="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
        <div v-if="isAdmin" class="rounded border border-outline-gray-2 bg-surface-base p-4 shadow-sm dark:border-outline-gray-7">
          <div class="text-xs font-medium uppercase tracking-wider text-ink-gray-5">{{ __('Active Users') }}</div>
          <div class="mt-2 text-2xl font-bold text-ink-gray-9 dark:text-ink-white">{{ summary.total_users || 0 }}</div>
          <div class="mt-1 text-xs text-ink-gray-4">{{ __('In sales team') }}</div>
        </div>

        <div class="rounded border border-outline-gray-2 bg-surface-base p-4 shadow-sm dark:border-outline-gray-7">
          <div class="text-xs font-medium uppercase tracking-wider text-ink-gray-5">
            {{ isAdmin ? __('Total Allocated') : __('Total Assigned') }}
          </div>
          <div class="mt-2 text-2xl font-bold text-ink-gray-9 dark:text-ink-white">{{ summary.total_tasks || 0 }}</div>
          <div class="mt-1 text-xs text-ink-gray-4">{{ __('For') }} {{ selectedDate }}</div>
        </div>

        <div class="rounded border border-outline-gray-2 bg-surface-base p-4 shadow-sm dark:border-outline-gray-7">
          <div class="text-xs font-medium uppercase tracking-wider text-ink-gray-5">{{ __('Completed') }}</div>
          <div class="mt-2 text-2xl font-bold text-ink-green-3">{{ summary.completed || 0 }}</div>
          <div class="mt-1 text-xs text-ink-gray-4">
            {{ summary.total_tasks ? Math.round(((summary.completed || 0) / summary.total_tasks) * 100) : 0 }}% {{ __('completion') }}
          </div>
        </div>

        <div class="rounded border border-outline-gray-2 bg-surface-base p-4 shadow-sm dark:border-outline-gray-7">
          <div class="text-xs font-medium uppercase tracking-wider text-ink-gray-5">{{ __('In Progress') }}</div>
          <div class="mt-2 text-2xl font-bold text-ink-blue-3">{{ summary.in_progress || 0 }}</div>
          <div class="mt-1 text-xs text-ink-gray-4">{{ __('Active calls & demos') }}</div>
        </div>

        <div class="rounded border border-outline-gray-2 bg-surface-base p-4 shadow-sm dark:border-outline-gray-7">
          <div class="text-xs font-medium uppercase tracking-wider text-ink-gray-5">{{ __('Pending') }}</div>
          <div class="mt-2 text-2xl font-bold text-ink-amber-3">{{ summary.pending || 0 }}</div>
          <div class="mt-1 text-xs text-ink-gray-4">{{ __('Awaiting outreach') }}</div>
        </div>
      </div>

      <!-- 2. ADMIN USER-WISE BREAKDOWN CARDS -->
      <div v-if="isAdmin" class="space-y-3">
        <div class="flex items-center justify-between">
          <h2 class="text-sm font-semibold uppercase tracking-wider text-ink-gray-6 dark:text-ink-gray-4">
            {{ __('Team Allocations') }} ({{ selectedDate }})
          </h2>
          <span class="text-xs text-ink-gray-5">{{ __('Click a user card to inspect their tasks') }}</span>
        </div>

        <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          <!-- All Users Option Card -->
          <div
            class="cursor-pointer rounded border p-4 transition-all hover:border-outline-gray-4 dark:hover:border-outline-gray-5"
            :class="[
              selectedUser === 'all'
                ? 'border-ink-gray-9 bg-surface-gray-2 shadow-sm dark:border-ink-white dark:bg-surface-gray-8'
                : 'border-outline-gray-2 bg-surface-base dark:border-outline-gray-7',
            ]"
            @click="selectedUser = 'all'; fetchTasks()"
          >
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2.5">
                <div class="flex size-9 items-center justify-center rounded-full bg-surface-gray-3 text-sm font-bold text-ink-gray-7 dark:bg-surface-gray-7 dark:text-ink-gray-2">
                  👥
                </div>
                <div>
                  <div class="font-semibold text-ink-gray-9 dark:text-ink-white">{{ __('All Users') }}</div>
                  <div class="text-xs text-ink-gray-5">{{ summary.total_users }} {{ __('team members') }}</div>
                </div>
              </div>
              <Badge variant="solid" size="md">
                {{ summary.total_tasks || 0 }}
              </Badge>
            </div>
            <div class="mt-3 flex items-center gap-2 text-xs text-ink-gray-6">
              <span class="text-ink-green-3 font-medium">{{ summary.completed || 0 }} {{ __('Done') }}</span>
              <span>•</span>
              <span class="text-ink-blue-3 font-medium">{{ summary.in_progress || 0 }} {{ __('In Progress') }}</span>
              <span>•</span>
              <span class="text-ink-amber-3 font-medium">{{ summary.pending || 0 }} {{ __('Pending') }}</span>
            </div>
          </div>

          <!-- Individual User Cards -->
          <div
            v-for="u in summary.users"
            :key="u.user"
            class="cursor-pointer rounded border p-4 transition-all hover:border-outline-gray-4 dark:hover:border-outline-gray-5"
            :class="[
              selectedUser === u.user
                ? 'border-ink-gray-9 bg-surface-gray-2 shadow-sm dark:border-ink-white dark:bg-surface-gray-8'
                : 'border-outline-gray-2 bg-surface-base dark:border-outline-gray-7',
            ]"
            @click="selectedUser = u.user; fetchTasks()"
          >
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2.5 truncate">
                <UserAvatar :user="u.user" size="md" />
                <div class="truncate">
                  <div class="truncate font-semibold text-ink-gray-9 dark:text-ink-white">
                    {{ u.full_name }}
                  </div>
                  <div class="truncate text-xs text-ink-gray-5">
                    {{ u.email }}
                  </div>
                </div>
              </div>
              <Badge variant="solid" size="md" :class="u.total ? 'bg-surface-gray-9 text-surface-white' : 'bg-surface-gray-3 text-ink-gray-6'">
                {{ u.total }}
              </Badge>
            </div>

            <!-- Task breakdown chips -->
            <div class="mt-3 flex items-center justify-between text-xs">
              <div class="flex items-center gap-1.5">
                <span class="font-medium text-ink-green-3">{{ u.completed }} {{ __('Done') }}</span>
                <span>•</span>
                <span class="font-medium text-ink-amber-3">{{ u.pending }} {{ __('Pending') }}</span>
              </div>
              <span class="text-ink-gray-4">
                {{ u.total ? Math.round((u.completed / u.total) * 100) : 0 }}%
              </span>
            </div>

            <!-- Progress bar -->
            <div class="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-surface-gray-3 dark:bg-surface-gray-7">
              <div
                class="h-full bg-surface-green-5 transition-all duration-300"
                :style="{ width: `${u.total ? (u.completed / u.total) * 100 : 0}%` }"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- 3. ALLOCATED TASKS TABLE -->
      <div class="rounded border border-outline-gray-2 bg-surface-base shadow-sm dark:border-outline-gray-7">
        <!-- Table Toolbar -->
        <div class="flex flex-wrap items-center justify-between gap-3 border-b border-outline-gray-2 px-5 py-3 dark:border-outline-gray-7">
          <div class="flex items-center gap-3">
            <h3 class="text-sm font-semibold text-ink-gray-9 dark:text-ink-white">
              {{ isAdmin ? __('Allocated Tasks') : __('Today\'s Tasks') }}
              <span v-if="isAdmin && selectedUser !== 'all'" class="text-ink-gray-5">
                ({{ getUserDisplayName(selectedUser) }})
              </span>
            </h3>
            <Badge variant="outline" size="sm">
              {{ filteredTasks.length }} {{ __('records') }}
            </Badge>
          </div>

          <div class="flex flex-wrap items-center gap-2">
            <!-- Status Tabs -->
            <div class="flex items-center gap-1 overflow-x-auto rounded bg-surface-gray-2 p-0.5 dark:bg-surface-gray-8">
              <button
                v-for="st in statusTabs"
                :key="st.value"
                type="button"
                class="rounded px-2.5 py-1 text-xs font-medium transition-colors"
                :class="[
                  statusFilter === st.value
                    ? 'bg-surface-white text-ink-gray-9 shadow-xs dark:bg-surface-gray-7 dark:text-ink-white font-semibold'
                    : 'text-ink-gray-6 hover:text-ink-gray-9 dark:hover:text-ink-white',
                ]"
                @click="statusFilter = st.value"
              >
                {{ st.label }}
              </button>
            </div>

            <!-- Search input -->
            <div class="relative w-48 sm:w-64">
              <input
                v-model="searchQuery"
                type="text"
                :placeholder="__('Search prospects...')"
                class="w-full rounded border border-outline-gray-2 bg-surface-white px-3 py-1.5 text-xs text-ink-gray-9 placeholder:text-ink-gray-4 focus:border-outline-gray-4 focus:outline-none dark:border-outline-gray-7 dark:bg-surface-gray-9 dark:text-ink-white"
              />
            </div>
          </div>
        </div>

        <!-- Table Content -->
        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs">
            <thead class="bg-surface-gray-1 text-ink-gray-5 border-b border-outline-gray-2 dark:bg-surface-gray-8 dark:border-outline-gray-7">
              <tr>
                <th class="px-5 py-3 font-medium uppercase tracking-wider">{{ __('Prospect / Contact') }}</th>
                <th class="px-5 py-3 font-medium uppercase tracking-wider">{{ __('Organization') }}</th>
                <th class="px-5 py-3 font-medium uppercase tracking-wider">{{ __('Contact Info') }}</th>
                <th v-if="isAdmin" class="px-5 py-3 font-medium uppercase tracking-wider">{{ __('Assigned To') }}</th>
                <th class="px-5 py-3 font-medium uppercase tracking-wider">{{ __('Status') }}</th>
                <th class="px-5 py-3 font-medium uppercase tracking-wider">{{ __('Notes / Follow-up') }}</th>
                <th class="px-5 py-3 text-right font-medium uppercase tracking-wider">{{ __('Actions') }}</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-outline-gray-2 dark:divide-outline-gray-7">
              <tr
                v-for="task in filteredTasks"
                :key="task.name"
                class="transition-colors hover:bg-surface-gray-1/60 dark:hover:bg-surface-gray-8/50"
              >
                <!-- Contact Name -->
                <td class="px-5 py-3.5">
                  <router-link
                    :to="`/contacts/${encodeURIComponent(task.contact)}`"
                    class="font-semibold text-ink-gray-9 hover:underline hover:text-ink-primary dark:text-ink-white"
                  >
                    {{ task.contact_name }}
                  </router-link>
                  <div class="text-[11px] text-ink-gray-4">{{ task.contact }}</div>
                </td>

                <!-- Organization -->
                <td class="px-5 py-3.5">
                  <div class="font-medium text-ink-gray-8 dark:text-ink-gray-2">
                    {{ task.organization || '-' }}
                  </div>
                </td>

                <!-- Contact Info -->
                <td class="px-5 py-3.5">
                  <div v-if="task.email" class="text-ink-gray-7 dark:text-ink-gray-3">
                    <a :href="`mailto:${task.email}`" class="hover:underline">{{ task.email }}</a>
                  </div>
                  <div v-if="task.mobile_no" class="text-[11px] text-ink-gray-5">
                    <a :href="`tel:${task.mobile_no}`" class="hover:underline">{{ task.mobile_no }}</a>
                  </div>
                  <div v-if="!task.email && !task.mobile_no" class="text-ink-gray-4">-</div>
                </td>

                <!-- Assigned To (Admin only) -->
                <td v-if="isAdmin" class="px-5 py-3.5">
                  <div class="flex items-center gap-2">
                    <UserAvatar :user="task.assigned_to" size="xs" />
                    <span class="font-medium text-ink-gray-8 dark:text-ink-gray-2">
                      {{ task.assigned_to_name }}
                    </span>
                  </div>
                </td>

                <!-- Status with interactive update -->
                <td class="px-5 py-3.5">
                  <select
                    :value="task.status"
                    class="rounded border border-outline-gray-2 bg-surface-white px-2 py-1 text-xs font-semibold focus:outline-none dark:border-outline-gray-7 dark:bg-surface-gray-9"
                    :class="getStatusBadgeClass(task.status)"
                    @change="handleStatusChange(task, $event.target.value)"
                  >
                    <option value="Pending">{{ __('Pending') }}</option>
                    <option value="In Progress">{{ __('In Progress') }}</option>
                    <option value="Completed">{{ __('Completed') }}</option>
                    <option value="Follow-up Required">{{ __('Follow-up Required') }}</option>
                    <option value="Not Interested">{{ __('Not Interested') }}</option>
                  </select>
                </td>

                <!-- Notes / Follow-up -->
                <td class="px-5 py-3.5">
                  <div class="max-w-xs truncate text-ink-gray-7 dark:text-ink-gray-3">
                    {{ task.notes || __('No notes yet') }}
                  </div>
                  <div v-if="task.follow_up_date" class="text-[11px] font-medium text-ink-primary">
                    {{ __('Follow-up:') }} {{ task.follow_up_date }}
                  </div>
                </td>

                <!-- Actions -->
                <td class="px-5 py-3.5 text-right">
                  <div class="flex items-center justify-end gap-1.5">
                    <Button
                      variant="subtle"
                      size="sm"
                      iconLeft="lucide-file-text"
                      :label="__('Notes')"
                      @click="openNotesModal(task)"
                    />
                    <Button
                      v-if="isAdmin"
                      variant="subtle"
                      size="sm"
                      iconLeft="lucide-user-check"
                      :label="__('Reassign')"
                      @click="openReassignModal(task)"
                    />
                    <Button
                      v-if="isAdmin"
                      variant="subtle"
                      size="sm"
                      iconLeft="lucide-trash-2"
                      class="text-ink-red-3 hover:bg-surface-red-1"
                      @click="handleDeleteAllocation(task)"
                    />
                  </div>
                </td>
              </tr>

              <!-- Empty State in Table -->
              <tr v-if="!filteredTasks.length">
                <td :colspan="isAdmin ? 7 : 6" class="px-5 py-12 text-center text-ink-gray-5">
                  <div class="flex flex-col items-center justify-center gap-2">
                    <CalendarIcon class="size-8 text-ink-gray-4" />
                    <p class="font-medium">
                      {{ isAdmin ? __('No allocated tasks found for this selection.') : __('No tasks allocated to you for today.') }}
                    </p>
                    <p v-if="isAdmin" class="text-xs text-ink-gray-4">
                      {{ __('Click "+ Allocate Prospects" above to assign prospects to team members.') }}
                    </p>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- ============================================================== -->
    <!-- MODAL 1: ALLOCATE PROSPECTS (ADMIN ONLY) -->
    <!-- ============================================================== -->
    <Dialog
      v-model="showAllocateModal"
      :options="{
        title: __('Allocate Prospects to Team Member'),
        size: '2xl',
      }"
    >
      <template #body-content>
        <div class="space-y-4 text-xs">
          <!-- Step 1 & 2: User & Date Selection -->
          <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label class="mb-1 block font-medium text-ink-gray-7 dark:text-ink-gray-3">
                {{ __('Assign To User *') }}
              </label>
              <select
                v-model="allocateForm.assigned_to"
                class="w-full rounded border border-outline-gray-2 bg-surface-white px-3 py-2 text-xs text-ink-gray-9 focus:border-outline-gray-4 focus:outline-none dark:border-outline-gray-7 dark:bg-surface-gray-9 dark:text-ink-white"
                @change="fetchAvailableContacts"
              >
                <option value="" disabled>{{ __('Select user...') }}</option>
                <option
                  v-for="u in assignableUsers"
                  :key="u.name"
                  :value="u.name"
                >
                  {{ u.full_name }} ({{ u.email }})
                </option>
              </select>
            </div>

            <div>
              <label class="mb-1 block font-medium text-ink-gray-7 dark:text-ink-gray-3">
                {{ __('Allocation Date *') }}
              </label>
              <input
                v-model="allocateForm.allocation_date"
                type="date"
                class="w-full rounded border border-outline-gray-2 bg-surface-white px-3 py-2 text-xs text-ink-gray-9 focus:border-outline-gray-4 focus:outline-none dark:border-outline-gray-7 dark:bg-surface-gray-9 dark:text-ink-white"
                @change="fetchAvailableContacts"
              />
            </div>
          </div>

          <!-- Step 3: Search and Select Contacts -->
          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <label class="font-medium text-ink-gray-7 dark:text-ink-gray-3">
                {{ __('Select Prospects / Contacts *') }}
                <span class="text-ink-gray-4 font-normal">({{ availableContacts.length }} {{ __('available') }})</span>
              </label>
              <div class="flex items-center gap-2">
                <button
                  type="button"
                  class="text-xs font-semibold text-ink-primary hover:underline"
                  @click="selectAllContacts"
                >
                  {{ isAllSelected ? __('Deselect All') : __('Select All') }}
                </button>
              </div>
            </div>

            <input
              v-model="contactSearch"
              type="text"
              :placeholder="__('Search by name, organization, email, or mobile...')"
              class="w-full rounded border border-outline-gray-2 bg-surface-white px-3 py-2 text-xs text-ink-gray-9 placeholder:text-ink-gray-4 focus:border-outline-gray-4 focus:outline-none dark:border-outline-gray-7 dark:bg-surface-gray-9 dark:text-ink-white"
              @input="fetchAvailableContacts"
            />

            <!-- Contacts list with checkboxes -->
            <div class="max-h-60 overflow-y-auto rounded border border-outline-gray-2 divide-y divide-outline-gray-2 dark:border-outline-gray-7 dark:divide-outline-gray-7">
              <label
                v-for="c in availableContacts"
                :key="c.name"
                class="flex cursor-pointer items-center justify-between p-2.5 transition-colors hover:bg-surface-gray-1 dark:hover:bg-surface-gray-8"
              >
                <div class="flex items-center gap-2.5">
                  <input
                    type="checkbox"
                    :value="c.name"
                    v-model="allocateForm.selectedContacts"
                    class="size-4 rounded border-outline-gray-3 text-ink-primary focus:ring-0"
                  />
                  <div>
                    <div class="font-semibold text-ink-gray-9 dark:text-ink-white">
                      {{ c.full_name }}
                    </div>
                    <div class="text-[11px] text-ink-gray-5">
                      {{ c.organization ? c.organization + ' • ' : '' }}{{ c.email || c.mobile_no || c.name }}
                    </div>
                  </div>
                </div>

                <div v-if="c.is_allocated">
                  <Badge variant="outline" size="sm" class="text-ink-amber-3">
                    {{ __('Allocated to') }} {{ c.allocated_to_name }}
                  </Badge>
                </div>
              </label>

              <div v-if="!availableContacts.length" class="p-6 text-center text-ink-gray-4">
                {{ __('No matching contacts found.') }}
              </div>
            </div>
          </div>

          <!-- Step 4: Preview Box -->
          <div
            v-if="allocateForm.selectedContacts.length && allocateForm.assigned_to"
            class="rounded bg-surface-gray-2 p-3 text-xs text-ink-gray-8 dark:bg-surface-gray-8 dark:text-ink-gray-2"
          >
            <div class="font-semibold text-ink-gray-9 dark:text-ink-white">
              {{ __('Allocation Preview') }}:
            </div>
            <p class="mt-1">
              Assigning <span class="font-bold text-ink-primary">{{ allocateForm.selectedContacts.length }}</span> prospect(s) to
              <span class="font-bold">{{ getUserDisplayName(allocateForm.assigned_to) }}</span> for
              <span class="font-bold">{{ allocateForm.allocation_date }}</span>.
            </p>
          </div>
        </div>
      </template>

      <template #actions>
        <Button
          variant="subtle"
          :label="__('Cancel')"
          @click="showAllocateModal = false"
        />
        <Button
          variant="solid"
          :loading="allocating"
          :disabled="!allocateForm.selectedContacts.length || !allocateForm.assigned_to"
          :label="__('Assign {0} Prospects').replace('{0}', allocateForm.selectedContacts.length)"
          @click="submitAllocation"
        />
      </template>
    </Dialog>

    <!-- ============================================================== -->
    <!-- MODAL 2: EDIT TASK NOTES & STATUS -->
    <!-- ============================================================== -->
    <Dialog
      v-model="showNotesModal"
      :options="{
        title: __('Update Task Notes & Status'),
        size: 'lg',
      }"
    >
      <template #body-content>
        <div v-if="taskToEdit" class="space-y-4 text-xs">
          <div class="rounded bg-surface-gray-2 p-3 dark:bg-surface-gray-8">
            <div class="font-semibold text-ink-gray-9 dark:text-ink-white">{{ taskToEdit.contact_name }}</div>
            <div class="text-ink-gray-5">{{ taskToEdit.organization }} • {{ taskToEdit.email }} • {{ taskToEdit.mobile_no }}</div>
          </div>

          <div>
            <label class="mb-1 block font-medium text-ink-gray-7 dark:text-ink-gray-3">{{ __('Status') }}</label>
            <select
              v-model="taskToEdit.status"
              class="w-full rounded border border-outline-gray-2 bg-surface-white px-3 py-2 text-xs text-ink-gray-9 focus:border-outline-gray-4 focus:outline-none dark:border-outline-gray-7 dark:bg-surface-gray-9 dark:text-ink-white"
            >
              <option value="Pending">{{ __('Pending') }}</option>
              <option value="In Progress">{{ __('In Progress') }}</option>
              <option value="Completed">{{ __('Completed') }}</option>
              <option value="Follow-up Required">{{ __('Follow-up Required') }}</option>
              <option value="Not Interested">{{ __('Not Interested') }}</option>
            </select>
          </div>

          <div>
            <label class="mb-1 block font-medium text-ink-gray-7 dark:text-ink-gray-3">{{ __('Follow-up Date') }}</label>
            <input
              v-model="taskToEdit.follow_up_date"
              type="date"
              class="w-full rounded border border-outline-gray-2 bg-surface-white px-3 py-2 text-xs text-ink-gray-9 focus:border-outline-gray-4 focus:outline-none dark:border-outline-gray-7 dark:bg-surface-gray-9 dark:text-ink-white"
            />
          </div>

          <div>
            <label class="mb-1 block font-medium text-ink-gray-7 dark:text-ink-gray-3">{{ __('Notes & Call Remarks') }}</label>
            <textarea
              v-model="taskToEdit.notes"
              rows="4"
              :placeholder="__('Enter notes from your call or meeting with this prospect...')"
              class="w-full rounded border border-outline-gray-2 bg-surface-white p-3 text-xs text-ink-gray-9 placeholder:text-ink-gray-4 focus:border-outline-gray-4 focus:outline-none dark:border-outline-gray-7 dark:bg-surface-gray-9 dark:text-ink-white"
            />
          </div>
        </div>
      </template>

      <template #actions>
        <Button
          variant="subtle"
          :label="__('Cancel')"
          @click="showNotesModal = false"
        />
        <Button
          variant="solid"
          :loading="savingNotes"
          :label="__('Save Changes')"
          @click="saveTaskNotes"
        />
      </template>
    </Dialog>

    <!-- ============================================================== -->
    <!-- MODAL 3: REASSIGN TASK (ADMIN ONLY) -->
    <!-- ============================================================== -->
    <Dialog
      v-model="showReassignModal"
      :options="{
        title: __('Reassign Task'),
        size: 'md',
      }"
    >
      <template #body-content>
        <div v-if="taskToReassign" class="space-y-4 text-xs">
          <p>
            {{ __('Reassign') }} <span class="font-bold">{{ taskToReassign.contact_name }}</span> {{ __('to another user or date:') }}
          </p>

          <div>
            <label class="mb-1 block font-medium text-ink-gray-7">{{ __('New Assignee') }}</label>
            <select
              v-model="reassignUser"
              class="w-full rounded border border-outline-gray-2 bg-surface-white px-3 py-2 text-xs text-ink-gray-9 focus:outline-none dark:border-outline-gray-7 dark:bg-surface-gray-9 dark:text-ink-white"
            >
              <option
                v-for="u in assignableUsers"
                :key="u.name"
                :value="u.name"
              >
                {{ u.full_name }} ({{ u.email }})
              </option>
            </select>
          </div>

          <div>
            <label class="mb-1 block font-medium text-ink-gray-7">{{ __('New Date (optional)') }}</label>
            <input
              v-model="reassignDate"
              type="date"
              class="w-full rounded border border-outline-gray-2 bg-surface-white px-3 py-2 text-xs text-ink-gray-9 focus:outline-none dark:border-outline-gray-7 dark:bg-surface-gray-9 dark:text-ink-white"
            />
          </div>
        </div>
      </template>

      <template #actions>
        <Button
          variant="subtle"
          :label="__('Cancel')"
          @click="showReassignModal = false"
        />
        <Button
          variant="solid"
          :loading="reassigning"
          :label="__('Confirm Reassign')"
          @click="submitReassign"
        />
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { call, Button, Dialog, Badge } from 'frappe-ui'
import CalendarIcon from '@/components/Icons/CalendarIcon.vue'
import UserAvatar from '@/components/UserAvatar.vue'

// Helpers
const todayStr = new Date().toLocaleDateString('en-CA')
const selectedDate = ref(todayStr)
const loading = ref(false)
const isAdmin = ref(false)
const selectedUser = ref('all')
const statusFilter = ref('all')
const searchQuery = ref('')

const summary = reactive({
  is_admin: false,
  total_users: 0,
  total_tasks: 0,
  completed: 0,
  pending: 0,
  in_progress: 0,
  not_interested: 0,
  follow_up: 0,
  users: [],
})

const tasks = ref([])
const assignableUsers = ref([])
const availableContacts = ref([])
const contactSearch = ref('')

// Modals state
const showAllocateModal = ref(false)
const allocating = ref(false)
const allocateForm = reactive({
  assigned_to: '',
  allocation_date: todayStr,
  selectedContacts: [],
})

const showNotesModal = ref(false)
const savingNotes = ref(false)
const taskToEdit = ref(null)

const showReassignModal = ref(false)
const reassigning = ref(false)
const taskToReassign = ref(null)
const reassignUser = ref('')
const reassignDate = ref('')

const statusTabs = [
  { label: 'All', value: 'all' },
  { label: 'Pending', value: 'Pending' },
  { label: 'In Progress', value: 'In Progress' },
  { label: 'Completed', value: 'Completed' },
  { label: 'Follow-up', value: 'Follow-up Required' },
  { label: 'Not Interested', value: 'Not Interested' },
]

function setToday() {
  selectedDate.value = todayStr
  fetchData()
}

async function fetchData() {
  loading.value = true
  try {
    const res = await call('crm.api.daily_allocation.get_daily_allocation_summary', {
      date: selectedDate.value,
    })
    Object.assign(summary, res)
    isAdmin.value = res.is_admin

    if (isAdmin.value && !assignableUsers.value.length) {
      assignableUsers.value = await call('crm.api.daily_allocation.get_assignable_users')
    }

    await fetchTasks()
  } catch (error) {
    console.error('Error fetching allocation summary:', error)
  } finally {
    loading.value = false
  }
}

async function fetchTasks() {
  try {
    const params = {
      date: selectedDate.value,
    }
    if (isAdmin.value && selectedUser.value !== 'all') {
      params.user = selectedUser.value
    }
    tasks.value = await call('crm.api.daily_allocation.get_allocated_tasks', params)
  } catch (error) {
    console.error('Error fetching allocated tasks:', error)
  }
}

const filteredTasks = computed(() => {
  let list = tasks.value || []
  if (statusFilter.value !== 'all') {
    list = list.filter((t) => t.status === statusFilter.value)
  }
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.trim().toLowerCase()
    list = list.filter((t) =>
      (t.contact_name || '').toLowerCase().includes(q) ||
      (t.organization || '').toLowerCase().includes(q) ||
      (t.email || '').toLowerCase().includes(q) ||
      (t.mobile_no || '').toLowerCase().includes(q) ||
      (t.notes || '').toLowerCase().includes(q)
    )
  }
  return list
})

function getUserDisplayName(userEmail) {
  if (!userEmail) return ''
  const u = assignableUsers.value.find((x) => x.name === userEmail)
  return u ? u.full_name : userEmail
}

function getStatusBadgeClass(status) {
  switch (status) {
    case 'Completed':
      return 'bg-surface-green-1 text-ink-green-3 border-outline-green-2'
    case 'In Progress':
      return 'bg-surface-blue-1 text-ink-blue-3 border-outline-blue-2'
    case 'Pending':
      return 'bg-surface-amber-1 text-ink-amber-3 border-outline-amber-2'
    case 'Follow-up Required':
      return 'bg-surface-purple-1 text-ink-purple-3 border-outline-purple-2'
    case 'Not Interested':
      return 'bg-surface-gray-2 text-ink-gray-6 border-outline-gray-3'
    default:
      return 'bg-surface-gray-2 text-ink-gray-7 border-outline-gray-2'
  }
}

async function handleStatusChange(task, newStatus) {
  try {
    await call('crm.api.daily_allocation.update_task_status', {
      task_name: task.name,
      status: newStatus,
    })
    task.status = newStatus
    // Refresh summary counts
    const s = await call('crm.api.daily_allocation.get_daily_allocation_summary', {
      date: selectedDate.value,
    })
    Object.assign(summary, s)
  } catch (error) {
    console.error('Failed to update status:', error)
  }
}

// Modal 1: Allocation
async function openAllocateModal() {
  allocateForm.assigned_to = ''
  allocateForm.allocation_date = selectedDate.value || todayStr
  allocateForm.selectedContacts = []
  contactSearch.value = ''
  showAllocateModal.value = true
  await fetchAvailableContacts()
}

async function fetchAvailableContacts() {
  try {
    availableContacts.value = await call('crm.api.daily_allocation.get_available_contacts', {
      search: contactSearch.value,
      allocation_date: allocateForm.allocation_date,
      assigned_to: allocateForm.assigned_to,
    })
  } catch (error) {
    console.error('Failed to fetch contacts:', error)
  }
}

const isAllSelected = computed(() => {
  return (
    availableContacts.value.length > 0 &&
    allocateForm.selectedContacts.length === availableContacts.value.length
  )
})

function selectAllContacts() {
  if (isAllSelected.value) {
    allocateForm.selectedContacts = []
  } else {
    allocateForm.selectedContacts = availableContacts.value.map((c) => c.name)
  }
}

async function submitAllocation() {
  allocating.value = true
  try {
    await call('crm.api.daily_allocation.allocate_prospects', {
      assigned_to: allocateForm.assigned_to,
      contacts: allocateForm.selectedContacts,
      allocation_date: allocateForm.allocation_date,
    })
    showAllocateModal.value = false
    await fetchData()
  } catch (error) {
    console.error('Allocation failed:', error)
  } finally {
    allocating.value = false
  }
}

// Modal 2: Edit Notes
function openNotesModal(task) {
  taskToEdit.value = { ...task }
  showNotesModal.value = true
}

async function saveTaskNotes() {
  if (!taskToEdit.value) return
  savingNotes.value = true
  try {
    await call('crm.api.daily_allocation.update_task_status', {
      task_name: taskToEdit.value.name,
      status: taskToEdit.value.status,
      notes: taskToEdit.value.notes,
      follow_up_date: taskToEdit.value.follow_up_date,
    })
    // Update local task
    const t = tasks.value.find((x) => x.name === taskToEdit.value.name)
    if (t) {
      t.status = taskToEdit.value.status
      t.notes = taskToEdit.value.notes
      t.follow_up_date = taskToEdit.value.follow_up_date
    }
    showNotesModal.value = false
    // Refresh summary
    const s = await call('crm.api.daily_allocation.get_daily_allocation_summary', {
      date: selectedDate.value,
    })
    Object.assign(summary, s)
  } catch (error) {
    console.error('Save notes failed:', error)
  } finally {
    savingNotes.value = false
  }
}

// Modal 3: Reassign
function openReassignModal(task) {
  taskToReassign.value = task
  reassignUser.value = task.assigned_to
  reassignDate.value = task.allocation_date
  showReassignModal.value = true
}

async function submitReassign() {
  if (!taskToReassign.value) return
  reassigning.value = true
  try {
    await call('crm.api.daily_allocation.reassign_task', {
      task_name: taskToReassign.value.name,
      new_user: reassignUser.value,
      new_date: reassignDate.value,
    })
    showReassignModal.value = false
    await fetchData()
  } catch (error) {
    console.error('Reassign failed:', error)
  } finally {
    reassigning.value = false
  }
}

async function handleDeleteAllocation(task) {
  if (!confirm(__('Are you sure you want to remove this allocation?'))) return
  try {
    await call('crm.api.daily_allocation.delete_allocation', {
      task_name: task.name,
    })
    await fetchData()
  } catch (error) {
    console.error('Delete failed:', error)
  }
}

onMounted(() => {
  fetchData()
})
</script>

