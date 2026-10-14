<template>
  <div class="flex min-h-0 flex-1 flex-col px-3 sm:px-5">
    <!-- CRM's lists have a grey header bar; frappe-ui's list exposes data-slot hooks to style it -->
    <GroupByTable
      class="[&_[data-slot=list-header-border]]:hidden [&_[data-slot=list-header]]:mb-2 [&_[data-slot=list-header]]:rounded-4 [&_[data-slot=list-header]]:bg-surface-gray-2"
      :doctype="doctype"
      :groupBy="settings"
      :rows="groups.rows.value"
      :totals="groups.totals.value"
      :loading="groups.loading.value"
      @update:groupBy="(settings) => emit('update:settings', settings)"
    >
      <template #cell="{ row, column, value, total }">
        <div
          class="flex items-center gap-2 truncate text-base"
          :class="[
            column.align === 'right' ? 'tabular-nums' : '',
            total ? 'font-medium text-ink-gray-9' : 'text-ink-gray-8',
          ]"
        >
          <UserAvatar
            v-if="column.options === 'User' && row[column.key]"
            :user="row[column.key]"
            size="sm"
          />
          <IndicatorIcon
            v-else-if="statusColor(column, row[column.key])"
            :class="statusColor(column, row[column.key])"
          />
          <span class="truncate">{{
            cellText(row, column, value, total)
          }}</span>
        </div>
      </template>
    </GroupByTable>
  </div>
  <ListFooter
    v-if="groups.rowCount.value"
    v-model="groups.pageLength.value"
    class="border-t px-3 py-2 sm:px-5"
  >
    <!-- groups are counted up to a cap, so the total can be a floor -->
    <template #right>
      <div class="flex items-center">
        <template v-if="groups.hasNextPage.value">
          <Button :label="__('Load More')" @click="groups.loadMore" />
          <div class="mx-3 h-[80%] border-l" />
        </template>
        <div class="text-base text-ink-gray-5">
          {{ __('{0} of {1}', [groups.rowCount.value, totalLabel]) }}
        </div>
      </div>
    </template>
  </ListFooter>
</template>

<script setup lang="ts">
import UserAvatar from '@/components/UserAvatar.vue'
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import { statusesStore } from '@/stores/statuses'
import { usersStore } from '@/stores/users'
import { formatCurrency } from '@/utils/numberFormat.js'
import { GroupByTable, useGroupByData } from '@framework/ui/components/GroupBy'
import type {
  GroupByColumn,
  GroupBySettings,
} from '@framework/ui/components/GroupBy'
import { Button } from 'frappe-ui'
import { ListFooter } from 'frappe-ui/experimental'
import { computed } from 'vue'

const props = defineProps<{
  doctype: string
  settings: GroupBySettings
  // the list's current filters, with @me already resolved
  filters: Record<string, unknown>
}>()

// a column resize changes the grouping's saved widths, so the view saves it
const emit = defineEmits<{ 'update:settings': [settings: GroupBySettings] }>()

const { getUser } = usersStore()
const { getDealStatus, getLeadStatus } = statusesStore()

// lead and deal statuses carry a colour; show it the way the list does
function statusColor(column: GroupByColumn, value: unknown): string {
  if (column.key !== 'status' || !value) return ''
  if (props.doctype === 'CRM Deal') return getDealStatus(String(value))?.color
  if (props.doctype === 'CRM Lead') return getLeadStatus(String(value))?.color
  return ''
}

const groups = useGroupByData(
  () => props.doctype,
  () => props.settings,
  () => props.filters,
)

const totalLabel = computed(() =>
  groups.totalCapped.value
    ? `${groups.totalCount.value}+`
    : String(groups.totalCount.value),
)

// as desk's report view: a currency read from another field shows only when grouped by it
function currencyOf(
  row: Record<string, unknown>,
  column: GroupByColumn,
  total?: boolean,
): string | null {
  if (!column.options) return window.sysdefaults?.currency || 'USD'
  if (total || !props.settings.fields.includes(column.options)) return null
  return row[column.options] ? String(row[column.options]) : null
}

// CRM knows user names and currencies; the shared table falls back to raw values
function cellText(
  row: Record<string, unknown>,
  column: GroupByColumn,
  value: string,
  total?: boolean,
): string {
  const raw = row[column.key]
  if (column.options === 'User' && raw) {
    return getUser(String(raw)).full_name || value
  }
  if (column.fieldtype === 'Currency' && typeof raw === 'number') {
    const currency = currencyOf(row, column, total)
    if (currency) return formatCurrency(raw, '', currency)
  }
  return value
}
</script>
