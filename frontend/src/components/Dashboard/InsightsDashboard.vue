<template>
  <div class="flex flex-col h-full overflow-hidden">
    <LayoutHeader>
      <template #left-header>
        <ViewBreadcrumbs routeName="Dashboard" />
      </template>
      <template #right-header>
        <Button
          v-if="actions.length"
          :label="actions[0].label"
          :href="actions[0].href"
          @click="actions[0].onClick?.()"
        />
        <Dropdown v-if="actions.length > 1" :options="moreActions" align="end">
          <Button icon="lucide-more-horizontal" />
        </Dropdown>
      </template>
    </LayoutHeader>

    <div class="flex-1 min-h-0">
      <ErrorMessage v-if="error" class="p-5" :message="error" />
      <Island
        v-else
        name="insights.dashboard"
        :dashboard="dashboard"
        @actions="actions = $event"
        @error="error = $event.message"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import Island from '@framework/ui/island/Island.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import { Button, Dropdown, ErrorMessage } from 'frappe-ui'
import { computed, ref } from 'vue'

type Action = { label: string } & (
  | { onClick: () => void; href?: never }
  | { href: string; onClick?: never }
)

defineProps<{ dashboard: string }>()

const error = ref('')
const actions = ref<Action[]>([])

// A menu option's `route` is a router destination, so an `href` action, which
// leaves CRM, opens its own tab.
const moreActions = computed(() =>
  actions.value.slice(1).map((action) => ({
    label: action.label,
    onClick: () =>
      action.href
        ? window.open(action.href, '_blank', 'noopener')
        : action.onClick?.(),
  })),
)
</script>
