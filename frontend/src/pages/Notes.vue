<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="[{ label: list.title }]" />
    </template>
    <template #right-header>
      <Button variant="solid" label="Create">
        <template #prefix><FeatherIcon name="plus" class="h-4" /></template>
      </Button>
    </template>
  </LayoutHeader>
  <div class="flex justify-between items-center px-5 pb-2.5 border-b">
    <div class="flex items-center gap-2">
      <TabButtons
        v-model="currentView"
        :buttons="[{ label: 'List' }, { label: 'Grid' }]"
        class="w-max"
      />
    </div>
    <div class="flex items-center gap-2">
      <Button label="Sort">
        <template #prefix><SortIcon class="h-4" /></template>
      </Button>
      <Button label="Filter">
        <template #prefix><FilterIcon class="h-4" /></template>
      </Button>
      <Button icon="more-horizontal" />
    </div>
  </div>
  <ListView :list="list" :columns="columns" :rows="rows" row-key="name" />
</template>

<script setup>
import ListView from '@/components/ListView.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import Breadcrumbs from '@/components/Breadcrumbs.vue'
import SortIcon from '@/components/Icons/SortIcon.vue'
import FilterIcon from '@/components/Icons/FilterIcon.vue'
import { usersStore } from '@/stores/users'
import { FeatherIcon, Button, createListResource, TabButtons } from 'frappe-ui'
import { computed, ref } from 'vue'

const { getUser } = usersStore()

const currentView = ref('List')

const list = {
  title: 'Notes',
  plural_label: 'Notes',
  singular_label: 'Note',
}

const notes = createListResource({
  type: 'list',
  doctype: 'CRM Note',
  fields: ['name', 'title', 'content', 'owner', 'modified'],
  filters: {},
  orderBy: 'modified desc',
  pageLength: 20,
  auto: true,
})

const columns = [
  {
    label: 'Title',
    key: 'title',
    type: 'data',
    size: 'w-48',
  },
  {
    label: 'Content',
    key: 'content',
    type: 'html',
    size: 'w-96',
  },
  {
    label: 'Created by',
    key: 'owner',
    type: 'avatar',
    size: 'w-36',
  },
  {
    label: 'Last modified',
    key: 'modified',
    type: 'pretty_date',
    size: 'w-28',
  },
]

const rows = computed(() => {
  return notes.data?.map((note) => {
    return {
      name: note.name,
      title: note.title,
      content: note.content,
      owner: note.owner && getUser(note.owner),
      modified: note.modified,
    }
  })
})
</script>
