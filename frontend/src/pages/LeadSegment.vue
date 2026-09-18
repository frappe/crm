<template>
  <LayoutHeader v-if="segment.data">
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs" />
    </template>
    <template #right-header>
      <Button
        :label="__('Add Leads')"
        iconLeft="plus"
        @click="showAddLeadsModal = true"
      />
      <Dropdown
        :options="[
          { label: __('Edit'), icon: 'edit-2', onClick: editSegment },
          { label: __('Delete'), icon: 'trash-2', onClick: deleteSegment },
        ]"
      >
        <Button icon="lucide-more-horizontal" variant="ghost" />
      </Dropdown>
    </template>
  </LayoutHeader>
  <div v-if="segment.data" class="flex flex-col overflow-hidden h-full">
    <div class="flex items-center gap-3 border-b px-5 py-4">
      <div class="flex-1 truncate">
        <div class="truncate text-lg-medium text-ink-gray-9">
          {{ segment.data.segment_name }}
        </div>
        <!-- description is passed through sanitizeHTML() (DOMPurify) before rendering -->
        <!-- eslint-disable vue/no-v-html -->
        <div
          v-if="segment.data.description"
          class="prose-f prose-sm text-p-sm mt-1 max-w-none truncate text-ink-gray-6"
          v-html="sanitizeHTML(segment.data.description)"
        />
        <!-- eslint-enable vue/no-v-html -->
      </div>
      <Tooltip
        v-if="segment.data.assigned_to"
        :text="getUser(segment.data.assigned_to).full_name"
      >
        <div class="flex items-center gap-2">
          <UserAvatar :user="segment.data.assigned_to" size="sm" />
          <div class="text-base text-ink-gray-8">
            {{ getUser(segment.data.assigned_to).full_name }}
          </div>
        </div>
      </Tooltip>
      <Badge
        :label="__('{0} leads', [segmentLeads.data?.total_count || 0])"
        variant="subtle"
      />
    </div>
    <SegmentLeadsListView
      v-if="rows.length"
      v-model="pageLength"
      :rows="rows"
      :columns="segmentLeads.data?.columns || []"
      :options="{
        rowCount: segmentLeads.data?.row_count,
        totalCount: segmentLeads.data?.total_count,
      }"
      @loadMore="loadMore"
      @updatePageCount="(count) => (pageLength = count)"
      @removeLeads="removeSelectedLeads"
    />
    <EmptyState
      v-else-if="segmentLeads.data"
      name="Leads"
      :title="__('No leads in this segment')"
      :description="__('Add leads to this segment to see them here.')"
      :icon="LeadsIcon"
    />
  </div>
  <AddLeadsToSegmentModal
    v-if="showAddLeadsModal"
    v-model="showAddLeadsModal"
    :segment="props.segmentId"
    @reload="segmentLeads.reload()"
  />
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import LeadsIcon from '@/components/Icons/LeadsIcon.vue'
import EmptyState from '@/components/ListViews/EmptyState.vue'
import SegmentLeadsListView from '@/components/ListViews/SegmentLeadsListView.vue'
import AddLeadsToSegmentModal from '@/components/Modals/AddLeadsToSegmentModal.vue'
import { useDoctypeModal } from '@/composables/doctypeModal'
import { timestampCell } from '@/composables/useTimelinePreferences'
import { globalStore } from '@/stores/global'
import { statusesStore } from '@/stores/statuses'
import { usersStore } from '@/stores/users'
import { sanitizeHTML } from '@/utils'
import {
  Badge,
  Breadcrumbs,
  Dropdown,
  Tooltip,
  call,
  createResource,
  toast,
} from 'frappe-ui'
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  segmentId: { type: String, required: true },
})

const { getUser } = usersStore()
const { getLeadStatus } = statusesStore()
const { showModal } = useDoctypeModal()
const { $dialog } = globalStore()
const router = useRouter()

const showAddLeadsModal = ref(false)
const pageLength = ref(20)

// get_value, not get: the header only needs these three fields, and fetching the whole
// doc would drag the entire `leads` child table along with it.
const segment = createResource({
  url: 'frappe.client.get_value',
  params: {
    doctype: 'CRM Lead Segment',
    filters: { name: props.segmentId },
    fieldname: ['segment_name', 'description', 'assigned_to'],
  },
  auto: true,
})

const segmentLeads = createResource({
  url: 'crm.fcrm.doctype.crm_lead_segment.crm_lead_segment.get_segment_leads',
  makeParams: () => ({
    segment: props.segmentId,
    page_length: pageLength.value,
  }),
  auto: true,
})

const breadcrumbs = computed(() => [
  { label: __('Lead Segments'), route: { name: 'Lead Segments' } },
  { label: segment.data?.segment_name || props.segmentId },
])

const rows = computed(() => {
  const data = segmentLeads.data?.data
  if (!data) return []

  return data.map((lead) => ({
    ...lead,
    lead_name: {
      label: lead.lead_name,
      image: lead.image,
      image_label: lead.first_name,
    },
    status: {
      label: lead.status,
      color: getLeadStatus(lead.status)?.color,
    },
    _assign: JSON.parse(lead._assign || '[]').map((user) => ({
      name: user,
      image: getUser(user).user_image,
      label: getUser(user).full_name,
    })),
    modified: timestampCell(lead.modified),
  }))
})

function loadMore() {
  pageLength.value += 20
  segmentLeads.reload()
}

function editSegment() {
  showModal({
    name: props.segmentId,
    doctype: 'CRM Lead Segment',
    title: 'Lead Segment',
    callbacks: { afterUpdate: () => segment.reload() },
  })
}

function deleteSegment() {
  $dialog({
    title: __('Delete Segment'),
    message: __(
      'Are you sure you want to delete this segment? The leads in it are not deleted.',
    ),
    variant: 'solid',
    theme: 'red',
    actions: [
      {
        label: __('Delete'),
        variant: 'solid',
        theme: 'red',
        onClick: async (close) => {
          await call('frappe.client.delete', {
            doctype: 'CRM Lead Segment',
            name: props.segmentId,
          })
          close()
          router.push({ name: 'Lead Segments' })
        },
      },
    ],
  })
}

function removeSelectedLeads(selections, unselectAll) {
  $dialog({
    title: __('Remove from Segment'),
    message: __('Remove {0} lead(s) from this segment?', [selections.size]),
    variant: 'solid',
    theme: 'red',
    actions: [
      {
        label: __('Remove'),
        variant: 'solid',
        theme: 'red',
        onClick: async (close) => {
          const { removed } = await call(
            'crm.fcrm.doctype.crm_lead_segment.crm_lead_segment.remove_leads',
            {
              segment: props.segmentId,
              leads: JSON.stringify(Array.from(selections)),
            },
          )
          toast.success(__('{0} lead(s) removed', [removed]))
          unselectAll?.()
          segmentLeads.reload()
          close()
        },
      },
    ],
  })
}
</script>
