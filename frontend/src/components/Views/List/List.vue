<template>
  <ListView
    :columns="columns"
    :rows="rows"
    :options="{ showTooltip: false, resizeColumn: true }"
    row-key="name"
  >
    <ListHeader class="sm:mx-5 mx-3">
      <ListHeaderItem
        v-for="column in columns"
        :key="column.key"
        :item="column"
        @columnWidthUpdated="updateColumns()"
      >
        <Button
          v-if="column.key == '_liked_by'"
          variant="ghosted"
          class="!h-4"
          :class="isLikeFilterApplied ? 'fill-red-500' : 'fill-white'"
          @click="applyLikeFilter"
        >
          <HeartIcon class="h-4 w-4" />
        </Button>
      </ListHeaderItem>
    </ListHeader>
    <ListRows
      :rows="rows"
      v-slot="{ idx, column, item, row }"
      :doctype="doctype"
    >
      <div v-if="column.key === '_assign'" class="flex items-center">
        <MultipleAvatar
          :avatars="getAvatars(item)"
          size="sm"
          @click="
            (event) =>
              applyRowItemFilter({
                event,
                idx,
                column,
                item,
                firstColumn: columns[0],
              })
          "
        />
      </div>
      <ListRowItem v-else :item="item" :align="column.align">
        <template #default="{ label }">
          <div
            v-if="['modified', 'creation'].includes(column.key)"
            class="truncate text-base"
            @click="
              (event) =>
                applyRowItemFilter({
                  event,
                  idx,
                  column,
                  item,
                  firstColumn: columns[0],
                })
            "
          >
            <Tooltip :text="formatDate(item)">
              <div>{{ timeAgo(item) }}</div>
            </Tooltip>
          </div>
          <div v-else-if="column.key === '_liked_by'">
            <Button
              v-if="column.key == '_liked_by'"
              variant="ghosted"
              :class="
                isLiked(item) ? 'fill-red-500 text-ink-red-3' : 'fill-white'
              "
              @click.stop.prevent="
                () =>
                  likeDoc({
                    name: row.name,
                    liked: isLiked(item),
                  })
              "
            >
              <HeartIcon class="h-4 w-4" />
            </Button>
          </div>
          <div v-else-if="column.type === 'Check'">
            <FormControl
              type="checkbox"
              :modelValue="item"
              :disabled="true"
              class="text-ink-gray-9"
            />
          </div>
          <div
            v-else
            class="truncate text-base"
            @click="
              (event) =>
                applyRowItemFilter({
                  event,
                  idx,
                  column,
                  item,
                  firstColumn: columns[0],
                })
            "
          >
            {{ label }}
          </div>
        </template>
      </ListRowItem>
    </ListRows>
    <!-- <ListSelectBanner>
      <template #actions="{ selections, unselectAll }">
        <Dropdown
          :options="listBulkActionsRef.bulkActions(selections, unselectAll)"
        >
          <Button icon="more-horizontal" variant="ghost" />
        </Dropdown>
      </template>
    </ListSelectBanner> -->
  </ListView>
  <!-- <ListFooter
    v-if="pageLengthCount"
    class="border-t sm:px-5 px-3 py-2"
    v-model="pageLengthCount"
    :options="{
      rowCount: options.rowCount,
      totalCount: options.totalCount,
    }"
    @loadMore="emit('loadMore')"
  /> -->
  <!-- <ListBulkActions ref="listBulkActionsRef" v-model="list" :doctype="doctype" /> -->
</template>

<script setup>
import HeartIcon from '@/components/Icons/HeartIcon.vue'
import MultipleAvatar from '@/components/MultipleAvatar.vue'
import { formatDate, timeAgo } from '@/utils'
import { usersStore } from '@/stores/users'
import { useControls } from './controls'
import { useList } from './list'
import { useLike } from './like'
import {
  ListView,
  ListHeader,
  ListHeaderItem,
  ListSelectBanner,
  ListRowItem,
  ListFooter,
  Dropdown,
  Tooltip,
  Button,
  FormControl,
} from 'frappe-ui'
import { inject } from 'vue'

const doctype = inject('doctype')

const { updateColumns, applyRowItemFilter } = useControls()
const { columns, rows } = useList()
const { isLikeFilterApplied, isLiked, applyLikeFilter, likeDoc } = useLike()
const { allUsers: users } = usersStore()

function getAvatars(item) {
  const assignees = JSON.parse(item) || []
  return assignees.map((assignee) => {
    const user = users.find((user) => user.name === assignee)
    return {
      name: assignee,
      label: user?.full_name || assignee,
      image: user?.user_image || '',
    }
  })
}
</script>
