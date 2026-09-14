<template>
  <div
    v-if="showGroupedRows"
    ref="groupedScrollContainer"
    class="mx-3 mt-2 h-full overflow-y-auto sm:mx-5"
  >
    <div v-for="group in reactivieRows" :key="group.group">
      <ListGroupHeader :group="group">
        <div
          class="my-2 flex items-center gap-2 text-base-medium text-ink-gray-8"
        >
          <div>{{ __(group.label) }} -</div>
          <div class="flex items-center gap-1">
            <component :is="group.icon" v-if="group.icon" />
            <div v-if="group.group == ' '" class="text-ink-gray-4">
              {{ __('Empty') }}
            </div>
            <div v-else>{{ group.group }}</div>
          </div>
        </div>
      </ListGroupHeader>
      <ListGroupRows :group="group">
        <ListRow
          v-for="row in group.rows"
          :key="row.name"
          v-slot="{ idx, column, item }"
          :row="row"
        >
          <slot
            v-bind="{ idx, column, item, row, isVisited: isVisited(row._seen) }"
          />
        </ListRow>
      </ListGroupRows>
    </div>
  </div>
  <ListRows v-else ref="scrollContainer" class="mx-3 sm:mx-5">
    <ListRow
      v-for="row in reactivieRows"
      :key="row.name"
      v-slot="{ idx, column, item }"
      :row="row"
    >
      <slot
        v-bind="{ idx, column, item, row, isVisited: isVisited(row._seen) }"
      />
    </ListRow>
  </ListRows>
</template>

<script setup>
import { useStorage } from '@vueuse/core'
import { ListRows, ListRow, ListGroupHeader, ListGroupRows } from 'frappe-ui'
import { ref, computed, watch, onBeforeUnmount } from 'vue'
import { useVisitedRecords } from '@/composables/useVisitedRecords'

const props = defineProps({
  rows: { type: Array, required: true },
  doctype: { type: String, default: 'CRM Lead' },
})

const reactivieRows = ref(props.rows)

watch(
  () => props.rows,
  (val) => (reactivieRows.value = val),
)

let showGroupedRows = computed(() => {
  return props.rows.every(
    (row) => row.group && row.rows && Array.isArray(row.rows),
  )
})

const scrollPosition = useStorage(`scrollPosition${props.doctype}`, 0)
const scrollContainer = ref(null)
const groupedScrollContainer = ref(null)

const { isVisited } = useVisitedRecords(props.doctype)

const handleScroll = (e) => {
  scrollPosition.value = e.target.scrollTop
}

// Grouping can toggle at runtime (props.rows reshaping) without remounting
// this component, so track whichever container is currently in the DOM
// rather than only wiring the listener up once on mount.
let activeScrollEl = null

watch(
  [scrollContainer, groupedScrollContainer],
  () => {
    const el =
      scrollContainer.value?.$el || groupedScrollContainer.value || null
    if (el === activeScrollEl) return

    if (activeScrollEl) {
      activeScrollEl.removeEventListener('scroll', handleScroll)
    }
    activeScrollEl = el
    if (activeScrollEl) {
      activeScrollEl.addEventListener('scroll', handleScroll)
      activeScrollEl.scrollTop = scrollPosition.value
    }
  },
  { immediate: true, flush: 'post' },
)

onBeforeUnmount(() => {
  if (activeScrollEl) {
    activeScrollEl.removeEventListener('scroll', handleScroll)
  }
})
</script>
