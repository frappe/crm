<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs" />
    </template>
    <template #right-header>
      <CustomActions
        v-if="dealsListView?.customListActions"
        :actions="dealsListView.customListActions"
      />
      <Button
        variant="solid"
        :label="__('Create')"
        @click="showDealModal = true"
      >
        <template #prefix><FeatherIcon name="plus" class="h-4" /></template>
      </Button>
    </template>
  </LayoutHeader>
  <ViewControls
    ref="viewControls"
    v-model="deals"
    v-model:loadMore="loadMore"
    v-model:resizeColumn="triggerResize"
    v-model:updatedPageCount="updatedPageCount"
    doctype="CRM Deal"
  />
  <DealsListView
    ref="dealsListView"
    v-if="deals.data && rows.length"
    v-model="deals.data.page_length_count"
    v-model:list="deals"
    :rows="rows"
    :columns="deals.data.columns"
    :options="{
      showTooltip: false,
      resizeColumn: true,
      rowCount: deals.data.row_count,
      totalCount: deals.data.total_count,
    }"
    @loadMore="() => loadMore++"
    @columnWidthUpdated="() => triggerResize++"
    @updatePageCount="(count) => (updatedPageCount = count)"
    @applyFilter="(data) => viewControls.applyFilter(data)"
  />
  <div v-else-if="deals.data" class="flex h-full items-center justify-center">
    <div
      class="flex flex-col items-center gap-3 text-xl font-medium text-gray-500"
    >
      <DealsIcon class="h-10 w-10" />
      <span>{{ __('No Deals Found') }}</span>
      <Button :label="__('Create')" @click="showDealModal = true">
        <template #prefix><FeatherIcon name="plus" class="h-4" /></template>
      </Button>
    </div>
  </div>
  <DealModal v-model="showDealModal" />
</template>

<script setup>
import CustomActions from '@/components/CustomActions.vue'
import DealsIcon from '@/components/Icons/DealsIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import DealsListView from '@/components/ListViews/DealsListView.vue'
import DealModal from '@/components/Modals/DealModal.vue'
import ViewControls from '@/components/ViewControls.vue'
import { usersStore } from '@/stores/users'
import { organizationsStore } from '@/stores/organizations'
import { statusesStore } from '@/stores/statuses'
import {
  dateFormat,
  dateTooltipFormat,
  timeAgo,
  formatNumberIntoCurrency,
  formatTime,
} from '@/utils'
import { Breadcrumbs } from 'frappe-ui'
import { ref, computed } from 'vue'

const breadcrumbs = [{ label: __('Deals'), route: { name: 'Deals' } }]

const { getUser } = usersStore()
const { getOrganization } = organizationsStore()
const { getDealStatus } = statusesStore()

const dealsListView = ref(null)
const showDealModal = ref(false)

// deals data is loaded in the ViewControls component
const deals = ref({})
const loadMore = ref(1)
const triggerResize = ref(1)
const updatedPageCount = ref(20)
const viewControls = ref(null)

// Rows
const rows = computed(() => {
  if (!deals.value?.data?.data) return []
  return deals.value.data.data.map((deal) => {
    let _rows = {}
    deals.value.data.rows.forEach((row) => {
      _rows[row] = deal[row]

      let org = getOrganization(deal.organization)

      if (row == 'organization') {
        _rows[row] = {
          label: deal.organization,
          logo: org?.organization_logo,
        }
      } else if (row == 'annual_revenue') {
        _rows[row] = formatNumberIntoCurrency(org?.annual_revenue)
      } else if (row == 'status') {
        _rows[row] = {
          label: deal.status,
          color: getDealStatus(deal.status)?.iconColorClass,
        }
      } else if (row == 'sla_status') {
        let value = deal.sla_status
        let tooltipText = value
        let color =
          deal.sla_status == 'Failed'
            ? 'red'
            : deal.sla_status == 'Fulfilled'
            ? 'green'
            : 'orange'
        if (value == 'First Response Due') {
          value = __(timeAgo(deal.response_by))
          tooltipText = dateFormat(deal.response_by, dateTooltipFormat)
          if (new Date(deal.response_by) < new Date()) {
            color = 'red'
          }
        }
        _rows[row] = {
          label: tooltipText,
          value: value,
          color: color,
        }
      } else if (row == 'deal_owner') {
        _rows[row] = {
          label: deal.deal_owner && getUser(deal.deal_owner).full_name,
          ...(deal.deal_owner && getUser(deal.deal_owner)),
        }
      } else if (row == '_assign') {
        let assignees = JSON.parse(deal._assign) || []
        if (!assignees.length && deal.deal_owner) {
          assignees = [deal.deal_owner]
        }
        _rows[row] = assignees.map((user) => ({
          name: user,
          image: getUser(user).user_image,
          label: getUser(user).full_name,
        }))
      } else if (['modified', 'creation'].includes(row)) {
        _rows[row] = {
          label: dateFormat(deal[row], dateTooltipFormat),
          timeAgo: __(timeAgo(deal[row])),
        }
      } else if (
        ['first_response_time', 'first_responded_on', 'response_by'].includes(
          row
        )
      ) {
        let field = row == 'response_by' ? 'response_by' : 'first_responded_on'
        _rows[row] = {
          label: deal[field] ? dateFormat(deal[field], dateTooltipFormat) : '',
          timeAgo: deal[row]
            ? row == 'first_response_time'
              ? formatTime(deal[row])
              : __(timeAgo(deal[row]))
            : '',
        }
      }
    })
    return _rows
  })
})
</script>
