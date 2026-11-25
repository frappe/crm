<template>
  <div class="flex flex-col h-full overflow-hidden">
    <LayoutHeader>
      <template #left-header>
        <ViewBreadcrumbs routeName="Dashboard" />
        <Dropdown v-if="current && rows.length > 1" :options="switchOptions">
          <Button
            variant="ghost"
            :label="current.label || current.dashboard"
            iconRight="lucide-chevron-down"
          />
        </Dropdown>
      </template>
      <template #right-header>
        <Button
          v-if="actions.length"
          :label="actions[0].label"
          :href="actions[0].href"
          @click="actions[0].onClick?.()"
        />
        <Dropdown v-if="moreActions.length" :options="moreActions" align="end">
          <Button icon="lucide-more-horizontal" />
        </Dropdown>
      </template>
    </LayoutHeader>

    <div class="flex-1 min-h-0">
      <ErrorMessage v-if="error" class="p-5" :message="error" />
      <p
        v-else-if="dashboards.data && !current"
        class="p-5 text-p-base text-ink-gray-5"
      >
        {{ __('No dashboards to show. Ask an admin to add one.') }}
      </p>
      <Island
        v-else-if="current"
        :key="current.dashboard"
        name="insights.dashboard"
        :dashboard="current.dashboard"
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
import { globalStore } from '@/stores/global'
import { usersStore } from '@/stores/users'
import {
  Button,
  call,
  createResource,
  Dropdown,
  ErrorMessage,
  toast,
} from 'frappe-ui'
import { computed, ref, watch } from 'vue'

type Action = { label: string } & (
  | { onClick: () => void; href?: never }
  | { href: string; onClick?: never }
)

const { isAdmin } = usersStore()
const { $dialog } = globalStore()
const error = ref('')
const actions = ref<Action[]>([])
const isStandard = ref(false)
const picked = ref('')

const dashboards = createResource({
  url: 'crm.api.dashboard.get_insights_dashboards',
  auto: true,
  onSuccess: (data) => (picked.value = data.picked || ''),
})

const rows = computed(() => dashboards.data?.dashboards || [])

const current = computed(
  () =>
    rows.value.find((row) => row.dashboard === picked.value) ||
    rows.value.find((row) => row.is_default) ||
    rows.value[0],
)

const switchOptions = computed(() =>
  rows.value.map((row) => ({
    label: row.label || row.dashboard,
    onClick: () => pick(row.dashboard),
  })),
)

function pick(dashboard: string) {
  picked.value = dashboard
  call('crm.api.dashboard.pick_insights_dashboard', { dashboard }).catch(
    (err) => console.error('Could not save the picked dashboard', err),
  )
}

watch(
  () => current.value?.dashboard,
  async (dashboard) => {
    error.value = ''
    isStandard.value = false
    if (!dashboard || !isAdmin()) return
    const doc = await call('frappe.client.get_value', {
      doctype: 'Insights Dashboard v3',
      filters: dashboard,
      fieldname: 'is_standard',
    }).catch(() => null)
    isStandard.value = Boolean(doc?.is_standard)
  },
  { immediate: true },
)

const adminActions = computed(() => {
  if (!isAdmin() || !current.value) return []
  if (current.value.customized_from) {
    return [{ label: __('Reset to Default'), onClick: confirmReset }]
  }
  return isStandard.value
    ? [{ label: __('Customize'), onClick: customize }]
    : []
})

// A menu option's `route` is a router destination, so an `href` action, which
// leaves CRM, opens its own tab.
const moreActions = computed(() => [
  ...actions.value.slice(1).map((action) => ({
    label: action.label,
    onClick: () =>
      action.href
        ? window.open(action.href, '_blank', 'noopener')
        : action.onClick?.(),
  })),
  ...adminActions.value,
])

async function customize() {
  try {
    const copy = await call('crm.api.dashboard.customize_insights_dashboard', {
      dashboard: current.value.dashboard,
    })
    pick(copy.dashboard)
    await dashboards.reload()
    toast.success(__('Dashboard copied. Use Edit to change it.'))
  } catch (err) {
    toast.error(err.messages?.[0] || __('Could not customize the dashboard'))
  }
}

function confirmReset() {
  $dialog({
    title: __('Reset to Default'),
    message: __(
      'CRM will show the default dashboard again. Your customized copy stays in Insights.',
    ),
    actions: [
      {
        label: __('Reset'),
        variant: 'solid',
        onClick: ({ close }) => reset().then(close),
      },
    ],
  })
}

async function reset() {
  try {
    const shipped = await call('crm.api.dashboard.reset_insights_dashboard', {
      dashboard: current.value.dashboard,
    })
    pick(shipped)
    await dashboards.reload()
  } catch (err) {
    toast.error(err.messages?.[0] || __('Could not reset the dashboard'))
  }
}
</script>
