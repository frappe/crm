<template>
  <div class="flex h-full flex-col gap-8 p-8 text-ink-gray-9">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <h2 class="flex gap-2 text-xl font-semibold leading-none h-5">
        {{ __('Agents') }}
      </h2>
      <div class="flex item-center space-x-2">
        <FormControl
          v-model="search"
          :placeholder="'Search'"
          type="text"
          :debounce="300"
        >
          <template #prefix>
            <LucideSearch class="h-4 w-4 text-ink-gray-4" />
          </template>
        </FormControl>
      </div>
    </div>

    <!-- loading state -->
    <div v-if="agents.loading" class="flex mt-28 justify-between w-full h-full">
      <Button
        :loading="agents.loading"
        variant="ghost"
        class="w-full"
        size="2xl"
      />
    </div>
    <!-- Empty State -->
    <div
      v-if="!agents.loading && !agents.data?.length"
      class="flex mt-28 justify-between w-full h-full"
    >
      <p class="text-sm text-gray-500 w-full flex justify-center">
        {{ __('No agents found') }}
      </p>
    </div>
    <!-- Agents List -->
    <ul
      v-if="!agents.loading && Boolean(agents.data?.length)"
      class="divide-y overflow-auto"
    >
      <li
        class="flex items-center justify-between p-2"
        v-for="agent in agents.data"
        :key="agent.name"
      >
        <div class="flex items-center">
          <Avatar :image="agent.image" :label="agent.agent_name" size="xl" />
          <div class="ml-3">
            <div class="text-base text-ink-gray-9">
              {{ agent.agent_name }}
            </div>
            <div class="mt-1 text-base text-ink-gray-7">
              {{ agent.name }}
            </div>
          </div>
        </div>
      </li>
      <!-- Load More Button -->
      <div class="flex justify-center">
        <Button
          v-if="!agents.loading && agents.hasNextPage"
          class="mt-3.5 p-2"
          @click="() => agents.next()"
          :loading="agents.loading"
          :label="__('Load More')"
          icon-left="refresh-cw"
        />
      </div>
    </ul>
  </div>
</template>

<script setup>
import { Avatar, createListResource, FormControl } from 'frappe-ui'
import { ref, watch } from 'vue'

const agents = createListResource({
  doctype: 'CRM Agent',
  cache: 'CRM Agents',
  fields: ['name', 'image', 'agent_name'],
  filters: { is_active: ['=', 1] },
  auto: true,
  start: 0,
  pageLength: 20,
  orderBy: 'creation desc',
})

const search = ref('')
watch(search, (newValue) => {
  agents.filters = {
    is_active: ['=', 1],
    agent_name: ['like', `%${newValue}%`],
  }
  if (!newValue) {
    agents.filters = {
      is_active: ['=', 1],
    }
    agents.start = 0
    agents.pageLength = 10
  }
  agents.reload()
})
</script>
