<template>
  <div class="mt-6 space-y-5 px-3 pb-6 sm:px-0">

    <!-- ── DEAL PROGRESS (prominent hero) ─────────────────────────────────── -->
    <div class="rounded-xl border border-outline-gray-2 bg-surface-white p-5 shadow-sm dark:bg-surface-gray-1">
      <div class="mb-4 flex items-end justify-between gap-3">
        <div>
          <h3 class="text-base font-semibold text-ink-gray-9">{{ __('Deal Progress') }}</h3>
          <p class="mt-0.5 text-xs text-ink-gray-5">
            {{ __('{0} of {1} stages complete', [doneCount, stages.length]) }}
          </p>
        </div>
        <span class="text-2xl font-bold leading-none text-ink-gray-9">{{ progressPct }}%</span>
      </div>

      <!-- Overall progress bar -->
      <div class="mb-6 h-2 w-full overflow-hidden rounded-full bg-surface-gray-3">
        <div
          class="h-full rounded-full bg-green-500 transition-all duration-500 dark:bg-green-400"
          :style="{ width: progressPct + '%' }"
        />
      </div>

      <!-- Loading skeleton when lifecycle prop not yet available -->
      <div v-if="!props.lifecycle" class="flex gap-2">
        <div v-for="n in 6" :key="n" class="h-16 flex-1 animate-pulse rounded-lg bg-surface-gray-2" />
      </div>

      <!-- Stepper: vertical timeline on mobile, horizontal on lg -->
      <ol v-else class="flex flex-col gap-6 lg:flex-row lg:gap-0">
        <li
          v-for="(st, i) in stages"
          :key="st.key"
          class="relative flex flex-1 items-start gap-3 lg:flex-col lg:items-center lg:gap-0 lg:text-center"
        >
          <!-- Connector to the previous node -->
          <span
            v-if="i > 0"
            class="absolute left-4 top-[-24px] h-6 w-0.5 lg:left-auto lg:right-1/2 lg:top-4 lg:h-0.5 lg:w-full"
            :class="stages[i - 1].state === 'done' ? 'bg-green-500 dark:bg-green-400' : 'bg-surface-gray-3'"
          />

          <!-- Node circle -->
          <div
            class="relative z-10 flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full border text-xs font-semibold"
            :class="nodeClass(st.state)"
          >
            <svg
              v-if="st.state === 'done'"
              class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor"
              stroke-width="3" stroke-linecap="round" stroke-linejoin="round"
            >
              <polyline points="20 6 9 17 4 12" />
            </svg>
            <svg
              v-else-if="st.state === 'blocked'"
              class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor"
              stroke-width="3" stroke-linecap="round" stroke-linejoin="round"
            >
              <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
            </svg>
            <span v-else>{{ i + 1 }}</span>
          </div>

          <!-- Label + reference + status pill -->
          <div class="min-w-0 lg:mt-2 lg:w-full lg:px-1">
            <p class="text-xs font-semibold text-ink-gray-8">{{ __(st.label) }}</p>
            <p class="truncate text-xs text-ink-gray-5" :title="st.ref || ''">{{ st.ref || '—' }}</p>
            <span
              class="mt-1 inline-flex items-center gap-1 rounded-full bg-surface-gray-2 px-2 py-0.5 dark:bg-surface-gray-3"
            >
              <span :class="statusDot(st.status)" class="h-1.5 w-1.5 flex-shrink-0 rounded-full" />
              <span class="text-xs font-medium" :class="statusText(st.status)">{{ __(st.statusLabel) }}</span>
            </span>
          </div>
        </li>
      </ol>

      <!-- Signatory detail: edit unsigned signatories, resend/regenerate links -->
      <div
        v-if="contractExists && facilitySignatories.length"
        class="mt-6 border-t border-outline-gray-2 pt-4"
      >
        <p class="mb-2 text-xs font-medium uppercase tracking-wide text-ink-gray-4">
          {{ __('Facility Signatories') }}
        </p>
        <div class="space-y-2">
          <div
            v-for="s in facilitySignatories"
            :key="s.role"
            class="rounded-lg border border-outline-gray-2 bg-surface-gray-1 p-3 dark:bg-surface-gray-2"
          >
            <!-- Display row -->
            <div v-if="editingRole !== s.role" class="flex flex-wrap items-center gap-x-3 gap-y-1">
              <span :class="statusDot(s.status)" class="h-2 w-2 flex-shrink-0 rounded-full" />
              <div class="min-w-0">
                <p class="truncate text-sm font-medium text-ink-gray-8">{{ s.name || __(s.role) }}</p>
                <p class="truncate text-xs text-ink-gray-5">
                  {{ __(s.role) }}<template v-if="s.email"> · {{ s.email }}</template>
                </p>
              </div>
              <span class="ml-auto text-xs font-medium" :class="statusText(s.status)">{{ __(s.status) }}</span>

              <!-- Actions for signatories who have not yet signed -->
              <div
                v-if="canEdit(s.status)"
                class="flex w-full items-center gap-4 pt-1 sm:w-auto sm:basis-full sm:justify-end sm:pt-1"
              >
                <button
                  type="button"
                  class="text-xs underline text-ink-gray-6 hover:text-ink-gray-8 disabled:opacity-40 disabled:no-underline"
                  :disabled="!canGenerate || resendingKey === rowKey(s)"
                  :title="canGenerate ? __('Edit this signatory') : __('Sales Manager role required')"
                  @click="startEdit(s)"
                >
                  {{ __('Edit') }}
                </button>
                <button
                  v-if="isPendingStatus(s.status)"
                  type="button"
                  class="text-xs underline text-ink-gray-6 hover:text-ink-gray-8 disabled:opacity-40 disabled:no-underline"
                  :disabled="!canGenerate || resendingKey === rowKey(s)"
                  :title="canGenerate ? __('Regenerate and re-send the signing link') : __('Sales Manager role required')"
                  @click="doResend(s.role, s.row_name)"
                >
                  {{ resendingKey === rowKey(s) ? __('Sending…') : __('Resend link') }}
                </button>
              </div>
            </div>

            <!-- Inline edit form — free-text name + email for every signatory -->
            <div v-else class="space-y-2">
              <div class="grid grid-cols-1 gap-2 sm:grid-cols-2">
                <input
                  v-model="editName"
                  type="text"
                  :placeholder="__('Full legal name')"
                  class="w-full rounded-lg border border-outline-gray-2 bg-surface-white px-3 py-2 text-sm text-ink-gray-9 placeholder-ink-gray-4 focus:outline-none focus:ring-2 focus:ring-outline-gray-3 dark:bg-surface-gray-1"
                />
                <input
                  v-model="editEmail"
                  type="email"
                  :placeholder="__('signatory@hospital.org')"
                  class="w-full rounded-lg border border-outline-gray-2 bg-surface-white px-3 py-2 text-sm text-ink-gray-9 placeholder-ink-gray-4 focus:outline-none focus:ring-2 focus:ring-outline-gray-3 dark:bg-surface-gray-1"
                />
              </div>
              <p
                v-if="isSignedStatus(s.status)"
                class="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-700 dark:border-amber-800 dark:bg-amber-900/20 dark:text-amber-400"
              >
                {{ __('This signatory has already signed. Saving will invalidate their signature and send a fresh link so they sign again.') }}
              </p>
              <p v-else class="text-xs text-ink-gray-4">
                {{ __('Changing the email invalidates the old link and re-sends a fresh one to the new address.') }}
              </p>
              <div class="flex items-center justify-end gap-2">
                <Button variant="subtle" @click="cancelEdit">{{ __('Cancel') }}</Button>
                <Button
                  variant="solid"
                  :loading="savingEdit"
                  :disabled="!editName.trim() || !editEmail.trim()"
                  @click="saveEdit(s.role)"
                >
                  {{ __('Save') }}
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ── EXEC NOTES ────────────────────────────────────────────────────── -->
    <div class="rounded-lg border border-outline-gray-2 bg-surface-white p-4 dark:bg-surface-gray-1">
      <label
        class="mb-1 block text-xs font-medium uppercase tracking-wide text-ink-gray-4"
        for="exec-notes"
      >
        {{ __('Exec Notes') }}
      </label>
      <textarea
        id="exec-notes"
        v-model="execNotes"
        rows="4"
        :placeholder="__('Record your review notes here...')"
        class="w-full rounded-md border border-outline-gray-2 bg-surface-white p-2 text-sm text-ink-gray-9 placeholder-ink-gray-4 focus:outline-none focus:ring-2 focus:ring-outline-blue-4 dark:bg-surface-gray-1"
        @blur="saveNotes"
      />
    </div>

    <!-- ── GENERATE CONTRACT FORM ─────────────────────────────────────────── -->
    <div class="flex items-center justify-between border-b border-outline-gray-2 pb-3">
      <h3 class="text-base font-semibold text-ink-gray-9">
        {{ __('Send Contract for Signing') }}
      </h3>
    </div>

    <!-- Success banner -->
    <div
      v-if="successMsg"
      class="flex items-start gap-2 rounded-lg border border-green-200 bg-green-50 px-4 py-3 dark:border-green-800 dark:bg-green-900/20"
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        class="mt-0.5 h-4 w-4 flex-shrink-0 text-green-600 dark:text-green-400"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <polyline points="20 6 9 17 4 12"/>
      </svg>
      <p class="text-sm text-green-800 dark:text-green-300">{{ successMsg }}</p>
    </div>

    <!-- Error banner -->
    <div
      v-if="errorMsg"
      class="flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 dark:border-red-800 dark:bg-red-900/20"
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        class="mt-0.5 h-4 w-4 flex-shrink-0 text-red-600 dark:text-red-400"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <circle cx="12" cy="12" r="10"/>
        <line x1="15" y1="9" x2="9" y2="15"/>
        <line x1="9" y1="9" x2="15" y2="15"/>
      </svg>
      <p class="text-sm text-red-800 dark:text-red-300">{{ errorMsg }}</p>
    </div>

    <!-- Permission notice — visible-but-informative, never hidden -->
    <div
      v-if="!canGenerate"
      class="rounded-lg border border-amber-200 bg-amber-50 px-4 py-2.5 dark:border-amber-800 dark:bg-amber-900/20"
    >
      <p class="text-xs text-amber-700 dark:text-amber-400">
        {{ __('Sales Manager role required to generate contracts.') }}
      </p>
    </div>

    <!-- Nomination form -->
    <div class="rounded-lg border border-outline-gray-2 bg-surface-white p-4 dark:bg-surface-gray-1">
      <p class="mb-4 text-xs font-medium uppercase tracking-wide text-ink-gray-4">
        {{ __('Nominate Facility Signatory & Witness') }}
      </p>

      <!-- Facility Signatory -->
      <div class="mb-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div>
          <label class="mb-1 block text-xs font-medium text-ink-gray-6">
            {{ __('Facility Signatory Name') }}<span class="text-red-500">*</span>
          </label>
          <input
            v-model="facilitySignatoryName"
            type="text"
            :placeholder="__('Full legal name')"
            :disabled="formLocked"
            class="w-full rounded-lg border border-outline-gray-2 bg-surface-white px-3 py-2 text-sm text-ink-gray-9 placeholder-ink-gray-4 focus:outline-none focus:ring-2 focus:ring-outline-blue-4 dark:bg-surface-gray-2 disabled:cursor-not-allowed disabled:opacity-50"
          />
        </div>
        <div>
          <label class="mb-1 block text-xs font-medium text-ink-gray-6">
            {{ __('Facility Signatory Email') }}<span class="text-red-500">*</span>
          </label>
          <input
            v-model="facilitySignatoryEmail"
            type="email"
            :placeholder="__('signatory@hospital.org')"
            :disabled="formLocked"
            class="w-full rounded-lg border border-outline-gray-2 bg-surface-white px-3 py-2 text-sm text-ink-gray-9 placeholder-ink-gray-4 focus:outline-none focus:ring-2 focus:ring-outline-blue-4 dark:bg-surface-gray-2 disabled:cursor-not-allowed disabled:opacity-50"
          />
        </div>
      </div>

      <!-- Facility Witness -->
      <div class="mb-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div>
          <label class="mb-1 block text-xs font-medium text-ink-gray-6">
            {{ __('Facility Witness Name') }}<span class="text-red-500">*</span>
          </label>
          <input
            v-model="facilityWitnessName"
            type="text"
            :placeholder="__('Full legal name')"
            :disabled="formLocked"
            class="w-full rounded-lg border border-outline-gray-2 bg-surface-white px-3 py-2 text-sm text-ink-gray-9 placeholder-ink-gray-4 focus:outline-none focus:ring-2 focus:ring-outline-blue-4 dark:bg-surface-gray-2 disabled:cursor-not-allowed disabled:opacity-50"
          />
        </div>
        <div>
          <label class="mb-1 block text-xs font-medium text-ink-gray-6">
            {{ __('Facility Witness Email') }}<span class="text-red-500">*</span>
          </label>
          <input
            v-model="facilityWitnessEmail"
            type="email"
            :placeholder="__('witness@hospital.org')"
            :disabled="formLocked"
            class="w-full rounded-lg border border-outline-gray-2 bg-surface-white px-3 py-2 text-sm text-ink-gray-9 placeholder-ink-gray-4 focus:outline-none focus:ring-2 focus:ring-outline-blue-4 dark:bg-surface-gray-2 disabled:cursor-not-allowed disabled:opacity-50"
          />
        </div>
      </div>

      <!-- Co-signatories — Network Signatory(ies) + Tiberbu Signatory.
           Pre-generate: read-only preview resolved from the network / Opt-In config.
           Post-generate: editable per-contract — correct an unsigned row, or add a
           configured co-signatory that is missing from the contract (legacy /
           reconfigured). Each signs via the same OTP + pad once invited. -->
      <div class="mb-6">
        <div class="mb-2 flex items-center justify-between">
          <label class="block text-xs font-medium text-ink-gray-6">
            {{ __('Network & Tiberbu Co-Signatories') }}
          </label>
          <span v-if="coSignersLoading" class="text-xs text-ink-gray-4">{{ __('Loading…') }}</span>
        </div>

        <!-- Post-generate: editable rows (on-contract rows + configured-but-missing) -->
        <div v-if="contractExists" class="space-y-2">
          <div
            v-for="item in coSignatoryItems"
            :key="item.key"
            class="rounded-lg border border-outline-gray-2 bg-surface-gray-1 p-3 dark:bg-surface-gray-2"
          >
            <!-- Display row -->
            <div v-if="coEditKey !== item.key" class="flex flex-wrap items-center gap-x-3 gap-y-1">
              <span class="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full bg-surface-gray-3 text-xs font-semibold text-ink-gray-7 dark:bg-surface-gray-4">
                {{ initials(item.name || item.email) }}
              </span>
              <div class="min-w-0">
                <p class="truncate text-sm font-medium text-ink-gray-8">{{ item.name || __(item.role) }}</p>
                <p class="truncate text-xs text-ink-gray-5">
                  {{ __(item.role) }}<template v-if="item.email"> · {{ item.email }}</template>
                </p>
              </div>
              <span
                v-if="item.onContract"
                class="ml-auto text-xs font-medium"
                :class="statusText(item.status)"
              >{{ __(item.status) }}</span>
              <span
                v-else
                class="ml-auto rounded-full bg-surface-gray-3 px-2 py-0.5 text-xs font-medium text-ink-gray-6 dark:bg-surface-gray-4"
              >{{ __('Not on contract') }}</span>

              <!-- Actions: Edit an unsigned on-contract row, or Add a missing one -->
              <div
                v-if="!item.onContract || canEdit(item.status)"
                class="flex w-full items-center gap-4 pt-1 sm:w-auto sm:basis-full sm:justify-end sm:pt-1"
              >
                <button
                  type="button"
                  class="text-xs underline text-ink-gray-6 hover:text-ink-gray-8 disabled:opacity-40 disabled:no-underline"
                  :disabled="!canGenerate || savingCo || resendingKey === rowKey(item)"
                  :title="canGenerate
                    ? (item.onContract ? __('Edit this co-signatory') : __('Add this co-signatory to the contract'))
                    : __('Sales Manager role required')"
                  @click="startCoEdit(item)"
                >
                  {{ item.onContract ? __('Edit') : __('Add to contract') }}
                </button>
                <button
                  v-if="item.onContract && isPendingStatus(item.status)"
                  type="button"
                  class="text-xs underline text-ink-gray-6 hover:text-ink-gray-8 disabled:opacity-40 disabled:no-underline"
                  :disabled="!canGenerate || resendingKey === rowKey(item)"
                  :title="canGenerate ? __('Regenerate and re-send the signing link') : __('Sales Manager role required')"
                  @click="doResend(item.role, item.row_name)"
                >
                  {{ resendingKey === rowKey(item) ? __('Sending…') : __('Resend link') }}
                </button>
              </div>
            </div>

            <!-- Inline edit / add form — free-text name + email for every co-signatory -->
            <div v-else class="space-y-2">
              <label class="block text-xs font-medium text-ink-gray-6">
                {{ isTiberbuRole(item.role) ? __('Tiberbu Signatory') : __('Network Signatory') }}
              </label>
              <div class="grid grid-cols-1 gap-2 sm:grid-cols-2">
                <input
                  v-model="coEditName"
                  type="text"
                  :placeholder="__('Full legal name')"
                  class="w-full rounded-lg border border-outline-gray-2 bg-surface-white px-3 py-2 text-sm text-ink-gray-9 placeholder-ink-gray-4 focus:outline-none focus:ring-2 focus:ring-outline-gray-3 dark:bg-surface-gray-1"
                />
                <input
                  v-model="coEditEmail"
                  type="email"
                  :placeholder="isTiberbuRole(item.role) ? __('signatory@tiberbu.com') : __('signatory@network.org')"
                  class="w-full rounded-lg border border-outline-gray-2 bg-surface-white px-3 py-2 text-sm text-ink-gray-9 placeholder-ink-gray-4 focus:outline-none focus:ring-2 focus:ring-outline-gray-3 dark:bg-surface-gray-1"
                />
              </div>
              <p
                v-if="!coEditIsAdd && isSignedStatus(item.status)"
                class="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-700 dark:border-amber-800 dark:bg-amber-900/20 dark:text-amber-400"
              >
                {{ __('This co-signatory has already signed. Saving will invalidate their signature and send a fresh link so they sign again.') }}
              </p>
              <p v-else class="text-xs text-ink-gray-4">
                <template v-if="isTiberbuRole(item.role)">
                  {{ coEditIsAdd
                      ? __('Adds a Tiberbu co-signatory to this contract only. Opt-In Settings is not changed.')
                      : __('Changing the email invalidates the old link and re-sends a fresh one. This contract only — Opt-In Settings is not changed.') }}
                </template>
                <template v-else>
                  {{ __('Saves this signatory to the network configuration (used by future contracts) and updates them on this contract. Changing the email re-sends a fresh signing link.') }}
                </template>
              </p>
              <div class="flex items-center justify-end gap-2">
                <Button variant="subtle" @click="cancelCoEdit">{{ __('Cancel') }}</Button>
                <Button
                  variant="solid"
                  :loading="savingCo"
                  :disabled="!coEditName.trim() || !coEditEmail.trim()"
                  @click="saveCoEdit"
                >
                  {{ coEditIsAdd ? __('Add to contract') : __('Save') }}
                </Button>
              </div>
            </div>
          </div>
          <!-- Add a co-signatory from scratch. Network → written back to the network
               config; Tiberbu → this contract only (never the Opt-In singleton). -->
          <div
            v-if="coEditKey === ADD_KEY"
            class="space-y-2 rounded-lg border border-outline-gray-2 bg-surface-gray-1 p-3 dark:bg-surface-gray-2"
          >
            <label class="block text-xs font-medium text-ink-gray-6">
              {{ isTiberbuRole(coEditRole) ? __('Add Tiberbu Signatory') : __('Add Network Signatory') }}
            </label>

            <!-- Free-text name + email for both roles -->
            <div class="grid grid-cols-1 gap-2 sm:grid-cols-2">
              <input
                v-model="coEditName"
                type="text"
                :placeholder="__('Full legal name')"
                class="w-full rounded-lg border border-outline-gray-2 bg-surface-white px-3 py-2 text-sm text-ink-gray-9 placeholder-ink-gray-4 focus:outline-none focus:ring-2 focus:ring-outline-gray-3 dark:bg-surface-gray-1"
              />
              <input
                v-model="coEditEmail"
                type="email"
                :placeholder="isTiberbuRole(coEditRole) ? __('signatory@tiberbu.com') : __('signatory@network.org')"
                class="w-full rounded-lg border border-outline-gray-2 bg-surface-white px-3 py-2 text-sm text-ink-gray-9 placeholder-ink-gray-4 focus:outline-none focus:ring-2 focus:ring-outline-gray-3 dark:bg-surface-gray-1"
              />
            </div>

            <p class="text-xs text-ink-gray-4">
              {{ isTiberbuRole(coEditRole)
                  ? __('Adds a Tiberbu co-signatory to this contract only. Opt-In Settings is not changed.')
                  : __('Saves this signatory to the network configuration (used by future contracts) and adds them to this contract.') }}
            </p>
            <div class="flex items-center justify-end gap-2">
              <Button variant="subtle" @click="cancelCoEdit">{{ __('Cancel') }}</Button>
              <Button
                variant="solid"
                :loading="savingCo"
                :disabled="!coEditName.trim() || !coEditEmail.trim()"
                @click="saveCoEdit"
              >
                {{ __('Add to contract') }}
              </Button>
            </div>
          </div>

          <!-- Add actions (hidden while an edit/add form is open) -->
          <div v-else-if="!coEditKey" class="flex flex-wrap items-center gap-4 pt-1">
            <button
              type="button"
              class="text-xs font-medium underline text-ink-gray-6 hover:text-ink-gray-8 disabled:opacity-40 disabled:no-underline"
              :disabled="!canGenerate || !networkSlug"
              :title="!canGenerate
                ? __('Sales Manager role required')
                : (!networkSlug
                    ? __('No opt-in network is linked to this deal, so a network signatory cannot be saved.')
                    : __('Add a network signatory (saved to the network configuration)'))"
              @click="startAddNetwork"
            >
              + {{ __('Add Network Signatory') }}
            </button>
            <button
              v-if="!tiberbuOnContract"
              type="button"
              class="text-xs font-medium underline text-ink-gray-6 hover:text-ink-gray-8 disabled:opacity-40 disabled:no-underline"
              :disabled="!canGenerate"
              :title="canGenerate ? __('Add the Tiberbu signatory to this contract') : __('Sales Manager role required')"
              @click="startAddTiberbu"
            >
              + {{ __('Add Tiberbu Signatory') }}
            </button>
          </div>

          <p v-if="coSignatoryItems.length" class="text-xs text-ink-gray-4">
            {{ __('Co-signatories are invited automatically once the facility signatory and witness have both signed.') }}
          </p>
          <p v-else class="text-xs text-ink-gray-4">
            {{ __('No co-signatories yet. Add a Network or Tiberbu signatory so the contract can be co-signed.') }}
          </p>
        </div>

        <!-- Pre-generate: read-only preview resolved from configuration -->
        <div v-else-if="!contractExists && coSigners.length" class="space-y-2">
          <div
            v-for="(cs, i) in coSigners"
            :key="`${cs.signer_role}:${cs.email}:${i}`"
            class="flex items-center gap-3 rounded-lg border border-outline-gray-2 bg-surface-gray-1 px-3 py-2 dark:bg-surface-gray-2"
          >
            <span class="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full bg-surface-gray-3 text-xs font-semibold text-ink-gray-7 dark:bg-surface-gray-4">
              {{ initials(cs.full_name || cs.email) }}
            </span>
            <div class="min-w-0">
              <p class="truncate text-sm font-medium text-ink-gray-8">{{ cs.full_name || cs.email }}</p>
              <p class="truncate text-xs text-ink-gray-5">
                {{ __(cs.signer_role) }}<template v-if="cs.email"> · {{ cs.email }}</template>
              </p>
            </div>
          </div>
          <p class="text-xs text-ink-gray-4">
            {{ __('These co-signatories are seeded onto the contract at generation and invited automatically once the facility signatory and witness have both signed.') }}
          </p>
        </div>

        <!-- Pre-generate, nothing configured — co-signatories are added on the
             contract itself once it is generated (see the Add controls above). -->
        <div
          v-else-if="!coSignersLoading"
          class="rounded-lg border border-amber-200 bg-amber-50 px-4 py-2.5 dark:border-amber-800 dark:bg-amber-900/20"
        >
          <p class="text-xs text-amber-700 dark:text-amber-400">
            {{ __('No Network or Tiberbu co-signatories are configured for this network. You can add them on the contract once it is generated.') }}
          </p>
        </div>
      </div>

      <!-- Action row -->
      <div class="flex flex-wrap items-center justify-end gap-3">
        <span v-if="contractExists && !successMsg" class="text-xs text-ink-gray-5">
          {{ __('Contract already generated — see Deal Progress above.') }}
        </span>
        <Button
          v-if="contractExists"
          variant="subtle"
          :loading="downloadLoading"
          @click="doDownloadPdf"
        >
          <template #prefix>
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-3.5 w-3.5"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="7 10 12 15 17 10"/>
              <line x1="12" y1="15" x2="12" y2="3"/>
            </svg>
          </template>
          {{ __('Download PDF') }}
        </Button>
        <Button
          variant="solid"
          :disabled="generateDisabled"
          :loading="isGenerating"
          @click="doGenerate"
        >
          {{ __('Generate Contract') }}
        </Button>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { createResource, toast, Button } from 'frappe-ui'
import { usersStore } from '@/stores/users'
import { sessionStore } from '@/stores/session'

// ---------------------------------------------------------------------------
// Props / Emits
// ---------------------------------------------------------------------------
const props = defineProps({
  dealId:   { type: String, required: true },
  oisDoc:   { type: Object, default: null },
  lifecycle: { type: Object, default: null },
})

const emit = defineEmits(['lifecycle-reload'])

// ---------------------------------------------------------------------------
// Stores — mirrors AppSidebar.vue lines 444-445 exactly
// ---------------------------------------------------------------------------
const { user: sessionUser } = sessionStore()
const { isManager } = usersStore()

// ---------------------------------------------------------------------------
// Lifecycle alias (null-safe)
// ---------------------------------------------------------------------------
const lc = computed(() => props.lifecycle ?? {})

const contractExists = computed(() => !!lc.value.contract?.name)

// ---------------------------------------------------------------------------
// Deal doc — for exec_notes pre-fill only
// ---------------------------------------------------------------------------
const dealDocResource = createResource({
  url: 'frappe.client.get',
  makeParams: () => ({ doctype: 'CRM Deal', name: props.dealId }),
  auto: true,
})
const dealDoc = computed(() => dealDocResource.data ?? null)

// ---------------------------------------------------------------------------
// Co-signatories — Network Signatories (per network) + Tiberbu Signatory,
// auto-resolved from configuration. Displayed read-only; not nominated here.
// ---------------------------------------------------------------------------
const coSignersResource = createResource({ url: 'crm.api.contracts.get_network_signatories' })
const coSignersLoading  = ref(true)

const coSigners = computed(() => coSignersResource.data?.signers ?? [])
const networkSlug = computed(() => coSignersResource.data?.network_slug ?? '')

// The top "Signatories" block owns only the facility parties; the Network /
// Tiberbu counterparties are edited in their own block below (coSignatoryItems).
const facilitySignatories = computed(() =>
  (lc.value.signatories ?? []).filter((s) => !isCoRole(s.role))
)

onMounted(async () => {
  try {
    await coSignersResource.submit({ deal: props.dealId })
  } catch {
    // non-fatal — the empty-state notice covers a failed/empty resolve
  } finally {
    coSignersLoading.value = false
  }
})

function initials(nameOrEmail) {
  const s = (nameOrEmail ?? '').trim()
  if (!s) return '?'
  const parts = s.split(/[\s@.]+/).filter(Boolean)
  const first = parts[0]?.[0] ?? ''
  const second = parts.length > 1 ? (parts[1]?.[0] ?? '') : ''
  return (first + second).toUpperCase() || '?'
}

// ---------------------------------------------------------------------------
// OIS raw_json (parsed from prop — no fetch, parent owns the resource)
// ---------------------------------------------------------------------------
const oisRawJson = computed(() => {
  const raw = props.oisDoc?.raw_json
  if (!raw) return {}
  try { return JSON.parse(raw) } catch { return {} }
})

// ---------------------------------------------------------------------------
// Exec Notes
// ---------------------------------------------------------------------------
const execNotes      = ref('')
const execNotesReady = ref(false)

watch(
  () => dealDoc.value?.exec_notes,
  (notes) => {
    if (!execNotesReady.value && notes !== undefined) {
      execNotes.value      = notes ?? ''
      execNotesReady.value = true
    }
  },
  { immediate: true }
)

const saveNotesResource = createResource({ url: 'frappe.client.set_value' })

async function saveNotes() {
  try {
    await saveNotesResource.submit({
      doctype: 'CRM Deal',
      name: props.dealId,
      fieldname: 'exec_notes',
      value: execNotes.value,
    })
  } catch {
    // best-effort; non-fatal
  }
}

// ---------------------------------------------------------------------------
// Form state
// ---------------------------------------------------------------------------
const facilitySignatoryName  = ref('')
const facilitySignatoryEmail = ref('')
const facilityWitnessName    = ref('')
const facilityWitnessEmail   = ref('')

// Pre-fill signatory + witness fields from oisDoc prop
// Priority: explicit fields > raw_json contact > empty
watch(
  () => props.oisDoc,
  (doc) => {
    if (!doc) return
    const explicitName  = (doc.facility_signatory_name  ?? '').trim()
    const explicitEmail = (doc.facility_signatory_email ?? '').trim()
    const rawContact    = oisRawJson.value?.contact

    if (!facilitySignatoryName.value) {
      facilitySignatoryName.value = explicitName
        || [rawContact?.first_name, rawContact?.last_name].filter(Boolean).join(' ')
    }
    if (!facilitySignatoryEmail.value) {
      facilitySignatoryEmail.value = explicitEmail || (rawContact?.email ?? '')
    }

    // Witness captured during opt-in submission — pre-fill so the exec doesn't
    // have to re-key it (still editable before generating).
    if (!facilityWitnessName.value) {
      facilityWitnessName.value = (doc.facility_witness_name ?? '').trim()
    }
    if (!facilityWitnessEmail.value) {
      facilityWitnessEmail.value = (doc.facility_witness_email ?? '').trim()
    }
  },
  { immediate: true }
)

// ---------------------------------------------------------------------------
// Permission check — mirrors AppSidebar.vue / existing ContractingPanel
// ---------------------------------------------------------------------------
const canGenerate = computed(() => isManager(sessionUser.value))

// ---------------------------------------------------------------------------
// Form locking + validation
// ---------------------------------------------------------------------------
const isGenerating = ref(false)

// Locked: no permission, OR contract exists, OR currently generating
const formLocked = computed(
  () => !canGenerate.value || contractExists.value || isGenerating.value
)

const formValid = computed(() =>
  facilitySignatoryName.value.trim()  !== '' &&
  facilitySignatoryEmail.value.trim() !== '' &&
  facilityWitnessName.value.trim()    !== '' &&
  facilityWitnessEmail.value.trim()   !== ''
)

// Disabled: locked, form incomplete, or no quote yet
const generateDisabled = computed(
  () => formLocked.value || !formValid.value || !lc.value.quotation
)

// ---------------------------------------------------------------------------
// Banners
// ---------------------------------------------------------------------------
const successMsg = ref(null)
const errorMsg   = ref(null)

// ---------------------------------------------------------------------------
// Generate contract
// ---------------------------------------------------------------------------
const generateResource = createResource({ url: 'crm.api.contracts.generate' })

async function doGenerate() {
  if (generateDisabled.value) return
  isGenerating.value = true
  successMsg.value   = null
  errorMsg.value     = null
  try {
    await generateResource.submit({
      deal:                     props.dealId,
      quote:                    lc.value.quotation?.name ?? '',
      facility_signatory_name:  facilitySignatoryName.value.trim(),
      facility_signatory_email: facilitySignatoryEmail.value.trim(),
      facility_witness_name:    facilityWitnessName.value.trim(),
      facility_witness_email:   facilityWitnessEmail.value.trim(),
    })
    successMsg.value = __(
      'Contract sent — signing invitation emailed to {0}',
      [facilitySignatoryEmail.value.trim()]
    )
    toast.success(successMsg.value)
    emit('lifecycle-reload')
  } catch (err) {
    const msg = err?.messages?.[0] ?? err?.message ?? __('Contract generation failed.')
    errorMsg.value = msg
    toast.error(msg)
  } finally {
    isGenerating.value = false
  }
}

// ---------------------------------------------------------------------------
// Resend / regenerate signing invitation
// ---------------------------------------------------------------------------
const resendResource = createResource({ url: 'crm.api.contracts.resend_invitation' })
// Tracked by a per-row key (row_name when present, else role) so resending on one
// Network Signatory doesn't spin the button on its sibling row sharing the role.
const resendingKey   = ref('')

function rowKey(row) {
  return row?.row_name || row?.role || ''
}

async function doResend(role, rowName) {
  if (!canGenerate.value || resendingKey.value) return
  resendingKey.value = rowName || role
  try {
    const res = await resendResource.submit({
      contract: lc.value.contract?.name ?? '',
      role,
      row_name: rowName ?? '',
    })
    toast.success(__('Signing link re-sent to {0}', [res?.email ?? role]))
    emit('lifecycle-reload')
  } catch (err) {
    const msg = err?.messages?.[0] ?? err?.message ?? __('Could not resend the signing link.')
    toast.error(msg)
  } finally {
    resendingKey.value = ''
  }
}

// ---------------------------------------------------------------------------
// Edit an unsigned signatory
// ---------------------------------------------------------------------------
const updateSignatoryResource = createResource({ url: 'crm.api.contracts.update_signatory' })
const editingRole = ref('')
const editRowName = ref('')
const editName    = ref('')
const editEmail   = ref('')
const savingEdit  = ref(false)

// Every signatory row is editable — Pending, Declined, or Signed. Editing a
// Signed row invalidates its signature server-side (update_signatory clears the
// signature + resets to Pending) so the person re-signs the current terms.
function canEdit(_status) {
  return true
}

// True for an already-signed row — used to warn that editing will invalidate
// the captured signature and require the party to sign again.
function isSignedStatus(status) {
  return (status ?? '').toLowerCase() === 'signed'
}

// Resending a signing link only makes sense for a Pending (invited) row;
// resend_invitation throws for any other status.
function isPendingStatus(status) {
  return (status ?? '').toLowerCase() === 'pending'
}

// Distinguishes the two counterparty roles for labels, helper text, and the
// per-role save routing. Every signatory — including Tiberbu — is captured as
// free-text name + email so the signing flow is identical across the board.
function isTiberbuRole(role) {
  return (role ?? '').toLowerCase() === 'tiberbu signatory'
}

function startEdit(s) {
  if (!canGenerate.value) return
  editingRole.value = s.role
  editRowName.value = s.row_name ?? ''
  editName.value    = s.name ?? ''
  editEmail.value   = s.email ?? ''
}

function cancelEdit() {
  editingRole.value = ''
  editRowName.value = ''
  editName.value    = ''
  editEmail.value   = ''
}

async function saveEdit(role) {
  if (!editName.value.trim() || !editEmail.value.trim() || savingEdit.value) return
  savingEdit.value = true
  try {
    const email = editEmail.value.trim()
    const name = editName.value.trim()
    const res = await updateSignatoryResource.submit({
      contract: lc.value.contract?.name ?? '',
      role,
      name,
      email,
      row_name: editRowName.value ?? '',
    })
    toast.success(
      res?.resent
        ? __('Signatory updated — new signing link sent to {0}', [res.email])
        : __('Signatory updated.')
    )
    cancelEdit()
    emit('lifecycle-reload')
  } catch (err) {
    const msg = err?.messages?.[0] ?? err?.message ?? __('Could not update the signatory.')
    toast.error(msg)
  } finally {
    savingEdit.value = false
  }
}

// ---------------------------------------------------------------------------
// Network & Tiberbu co-signatories — editable per-contract (post-generate).
//
// The "Signatories" block above handles the facility parties. This surface owns
// the counterparties (Network Signatory, Tiberbu Signatory): it edits the rows
// already on the contract AND lets the exec add a configured co-signatory that
// is missing from the contract (e.g. legacy contracts generated before co-signing
// was wired, or where the network/Tiberbu config changed after generation).
//
// Persistence differs by role (per the confirmed design):
//   • Network Signatory — writes back to the network configuration (source of
//     truth, for future contracts) AND syncs onto this contract.
//   • Tiberbu Signatory — per-contract only; never overwrites the Opt-In Settings
//     singleton (shared across all networks).
// ---------------------------------------------------------------------------
const addSignatoryResource = createResource({ url: 'crm.api.contracts.add_signatory' })
const saveNetworkSignerResource = createResource({ url: 'crm.api.contracts.save_network_signer' })

const ADD_KEY = '__add__'         // sentinel: the standalone "add from scratch" form is open

const coEditKey     = ref('')     // unique key of the row being edited (role + email)
const coEditRole    = ref('')
const coEditRowName = ref('')     // child docname — targets the exact row when a role repeats
const coEditName    = ref('')
const coEditEmail   = ref('')
const coEditOrigEmail = ref('')   // network write-back: the config row to update (blank → append)
const coEditIsAdd   = ref(false)  // true → row is configured but not yet on the contract
const savingCo    = ref(false)

// Counterparty roles this surface owns — matches contracts.py _COUNTERPARTY_ROLES.
function isCoRole(role) {
  const r = (role ?? '').toLowerCase()
  return r === 'network signatory' || r === 'tiberbu signatory'
}

function coKey(role, email) {
  return `${(role ?? '').toLowerCase()}::${(email ?? '').trim().toLowerCase()}`
}

// Merge the contract's counterparty rows with the configured co-signatories that
// are not yet on the contract. `onContract` rows are edited via update_signatory;
// the rest are added via add_signatory. Deduped on email (Tiberbu is singular).
const coSignatoryItems = computed(() => {
  const rows = (lc.value.signatories ?? []).filter((s) => isCoRole(s.role))
  const onContractEmails = new Set(
    rows.map((r) => (r.email ?? '').trim().toLowerCase()).filter(Boolean)
  )
  // Tiberbu is singular per contract; its config email may have changed after
  // generation, so it is deduped by role (not email) — else a reconfigured
  // Tiberbu would offer a phantom "Add" the backend singular-guard rejects.
  const hasTiberbuOnContract = rows.some((r) => isTiberbuRole(r.role))
  const items = rows.map((r) => ({
    key: coKey(r.role, r.email),
    row_name: r.row_name,
    role: r.role,
    name: r.name,
    email: r.email,
    status: r.status,
    onContract: true,
  }))
  for (const cs of coSigners.value) {
    const email = (cs.email ?? '').trim().toLowerCase()
    const role = cs.signer_role || 'Network Signatory'
    // Skip config entries already represented by a contract row.
    if (isTiberbuRole(role)) {
      if (hasTiberbuOnContract) continue
    } else if (email && onContractEmails.has(email)) {
      continue
    }
    items.push({
      key: coKey(role, cs.email),
      row_name: null,
      role,
      name: cs.full_name || cs.email,
      email: cs.email,
      status: null,
      onContract: false,
    })
  }
  return items
})

// A Tiberbu Signatory is singular per contract — hide "Add Tiberbu" once present.
const tiberbuOnContract = computed(() =>
  coSignatoryItems.value.some((i) => isTiberbuRole(i.role) && i.onContract)
)

function startCoEdit(item) {
  if (!canGenerate.value) return
  coEditKey.value     = item.key
  coEditRole.value    = item.role
  coEditRowName.value = item.row_name ?? ''
  coEditName.value    = item.name ?? ''
  coEditEmail.value   = item.email ?? ''
  coEditOrigEmail.value = item.email ?? ''
  coEditIsAdd.value   = !item.onContract
}

// Open the standalone "add from scratch" form for a given counterparty role.
function startAddNetwork() {
  if (!canGenerate.value) return
  cancelCoEdit()
  coEditKey.value  = ADD_KEY
  coEditRole.value = 'Network Signatory'
  coEditIsAdd.value = true
}

function startAddTiberbu() {
  if (!canGenerate.value) return
  cancelCoEdit()
  coEditKey.value  = ADD_KEY
  coEditRole.value = 'Tiberbu Signatory'
  coEditIsAdd.value = true
}

function cancelCoEdit() {
  coEditKey.value     = ''
  coEditRole.value    = ''
  coEditRowName.value = ''
  coEditName.value    = ''
  coEditEmail.value   = ''
  coEditOrigEmail.value = ''
  coEditIsAdd.value   = false
}

async function saveCoEdit() {
  if (!coEditName.value.trim() || !coEditEmail.value.trim() || savingCo.value) return
  savingCo.value = true
  try {
    const role  = coEditRole.value
    const email = coEditEmail.value.trim()
    const name  = coEditName.value.trim()
    const contract = lc.value.contract?.name ?? ''

    if (isTiberbuRole(role)) {
      // Tiberbu stays per-contract — never overwrites the Opt-In Settings singleton.
      if (coEditIsAdd.value) {
        await addSignatoryResource.submit({ contract, role, name, email })
        toast.success(__('Tiberbu signatory added to the contract.'))
      } else {
        const res = await updateSignatoryResource.submit({
          contract, role, name, email, row_name: coEditRowName.value ?? '',
        })
        toast.success(
          res?.resent
            ? __('Tiberbu signatory updated — new signing link sent to {0}', [res.email])
            : __('Tiberbu signatory updated.')
        )
      }
    } else {
      // Network Signatory writes back to the network config (source of truth) and
      // syncs onto this contract in one call.
      if (!networkSlug.value) {
        throw new Error(__('No network is resolved for this deal, so the signer cannot be saved.'))
      }
      const res = await saveNetworkSignerResource.submit({
        network_slug: networkSlug.value,
        name,
        email,
        original_email: coEditOrigEmail.value ?? '',
        contract,
      })
      toast.success(
        res?.contract_synced === 'updated'
          ? __('Network signatory saved to the network and updated on this contract.')
          : __('Network signatory saved to the network and added to this contract.')
      )
      // Refresh the resolved config so the list reflects the write-back.
      await coSignersResource.submit({ deal: props.dealId })
    }

    cancelCoEdit()
    emit('lifecycle-reload')
  } catch (err) {
    const msg = err?.messages?.[0] ?? err?.message ?? __('Could not save the co-signatory.')
    toast.error(msg)
  } finally {
    savingCo.value = false
  }
}

// ---------------------------------------------------------------------------
// Download PDF
// ---------------------------------------------------------------------------
const downloadPdfResource = createResource({ url: 'crm.api.contracts.download_pdf' })
const downloadLoading     = ref(false)

async function doDownloadPdf() {
  if (!contractExists.value) return
  downloadLoading.value = true
  try {
    const result = await downloadPdfResource.submit({
      contract: lc.value.contract.name,
    })
    const b64 = result?.pdf_b64
    if (!b64) {
      toast.error(__('PDF generation failed.'))
      return
    }
    const bytes = atob(b64)
    const arr   = new Uint8Array(bytes.length)
    for (let i = 0; i < bytes.length; i++) arr[i] = bytes.charCodeAt(i)
    const blob = new Blob([arr], { type: 'application/pdf' })
    const url  = URL.createObjectURL(blob)
    const a    = document.createElement('a')
    a.href     = url
    a.download = `contract-${lc.value.contract.name ?? 'document'}.pdf`
    a.click()
    URL.revokeObjectURL(url)
  } catch (err) {
    const msg = err?.messages?.[0] ?? err?.message ?? __('PDF download failed.')
    toast.error(msg)
  } finally {
    downloadLoading.value = false
  }
}

// ---------------------------------------------------------------------------
// Lifecycle status derived from prop
// ---------------------------------------------------------------------------

const submissionStatus = computed(() => lc.value.submission?.status  ?? 'None')
const quotationStatus  = computed(() => lc.value.quotation?.status   ?? 'None')
const contractStatus   = computed(() =>
  lc.value.contract?.workflow_state ?? lc.value.contract?.status ?? 'None'
)
const approvalStatus   = computed(() => lc.value.onboarding?.approval_status ?? 'None')
const invoiceStatus    = computed(() => {
  const inv = lc.value.sales_invoice
  if (!inv) return 'None'
  const ds = inv.docstatus ?? 0
  if (ds === 0) return 'Draft'
  if (ds === 1) return 'Submitted'
  return 'Cancelled'
})

// Signatories roll up into a single lifecycle stage.
const signatoriesStatus = computed(() => {
  const list = lc.value.signatories ?? []
  if (!list.length) return 'None'
  const signed = list.filter((s) => (s.status ?? '').toLowerCase() === 'signed').length
  if (signed === list.length) return 'Signed'
  if (signed > 0) return 'Awaiting Signatures'
  return 'Pending'
})

const signatoriesSummary = computed(() => {
  const list = lc.value.signatories ?? []
  if (!list.length) return ''
  const signed = list.filter((s) => (s.status ?? '').toLowerCase() === 'signed').length
  return __('{0} of {1} signed', [signed, list.length])
})

// ---------------------------------------------------------------------------
// Stepper model — six ordered lifecycle stages
// ---------------------------------------------------------------------------
const stages = computed(() =>
  [
    { key: 'optin',       label: 'Opt-In',      ref: lc.value.submission?.ref,     status: submissionStatus.value },
    { key: 'quote',       label: 'Quote',       ref: lc.value.quotation?.name,     status: quotationStatus.value },
    { key: 'contract',    label: 'Contract',    ref: lc.value.contract?.name,      status: contractStatus.value },
    { key: 'signatories', label: 'Signatories', ref: signatoriesSummary.value,     status: signatoriesStatus.value },
    { key: 'approval',    label: 'Approval',    ref: lc.value.onboarding?.name,    status: approvalStatus.value },
    { key: 'invoice',     label: 'Invoice',     ref: lc.value.sales_invoice?.name, status: invoiceStatus.value },
  ].map((s) => ({ ...s, state: stageState(s.status), statusLabel: s.status }))
)

const doneCount   = computed(() => stages.value.filter((s) => s.state === 'done').length)
const progressPct = computed(() =>
  stages.value.length ? Math.round((doneCount.value / stages.value.length) * 100) : 0
)

// ---------------------------------------------------------------------------
// Status colour helpers — tokens only, never hex
// ---------------------------------------------------------------------------

const DONE_KEYS    = ['processed', 'accepted', 'signed', 'approved', 'submitted', 'fully executed', 'paid']
const BLOCKED_KEYS = ['failed', 'rejected', 'cancelled']

function isDone(status) {
  const s = (status ?? '').toLowerCase()
  return DONE_KEYS.some((k) => s.includes(k))
}
function isBlocked(status) {
  const s = (status ?? '').toLowerCase()
  return BLOCKED_KEYS.some((k) => s.includes(k))
}
function isIdle(status) {
  const s = (status ?? '').toLowerCase()
  return s === '' || s === 'none'
}

/**
 * Stage node state:
 *   done    = green (completed)
 *   blocked = red   (failed/rejected/cancelled)
 *   idle    = gray  (not started)
 *   active  = amber (in progress)
 */
function stageState(status) {
  if (isBlocked(status)) return 'blocked'
  if (isDone(status)) return 'done'
  if (isIdle(status)) return 'idle'
  return 'active'
}

function nodeClass(state) {
  return {
    done:    'border-green-500 bg-green-500 text-white dark:border-green-400 dark:bg-green-400',
    active:  'border-amber-400 bg-amber-50 text-amber-600 dark:border-amber-500 dark:bg-amber-900/20 dark:text-amber-400',
    blocked: 'border-red-400 bg-red-50 text-red-600 dark:border-red-500 dark:bg-red-900/20 dark:text-red-400',
    idle:    'border-outline-gray-2 bg-surface-gray-2 text-ink-gray-4',
  }[state] ?? 'border-outline-gray-2 bg-surface-gray-2 text-ink-gray-4'
}

/**
 * Green  = done/success  (Processed, Accepted, Signed, Approved, Submitted, Fully Executed)
 * Amber  = in-progress   (Pending, Processing, Awaiting, Draft, Sent)
 * Red    = failure/stop  (Failed, Rejected, Cancelled)
 * Gray   = absent/none
 */
function statusDot(status) {
  const state = stageState(status)
  return {
    done:    'bg-green-500 dark:bg-green-400',
    blocked: 'bg-red-500 dark:bg-red-400',
    idle:    'bg-surface-gray-4 dark:bg-surface-gray-5',
    active:  'bg-amber-500 dark:bg-amber-400',
  }[state]
}

function statusText(status) {
  const state = stageState(status)
  return {
    done:    'text-green-700 dark:text-green-400',
    blocked: 'text-red-600 dark:text-red-400',
    idle:    'text-ink-gray-4',
    active:  'text-amber-700 dark:text-amber-400',
  }[state]
}
</script>
