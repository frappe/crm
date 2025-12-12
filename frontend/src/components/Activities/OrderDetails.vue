<template>
  <div class="flex flex-col gap-4 px-3 pb-3 sm:px-10 sm:pb-5">
    <div class="flex items-center justify-between">
      <div class="flex h-8 items-center text-xl font-semibold text-ink-gray-8">
        {{ __('Order Details') }}
      </div>
    </div>

    <div
      v-if="isLoading"
      class="flex flex-1 flex-col items-center justify-center gap-3 py-8 text-xl font-medium text-ink-gray-6"
    >
      <LoadingIndicator class="h-6 w-6" />
      <span>{{ __('Loading...') }}</span>
    </div>

    <div
      v-else-if="!orderHistory.data || orderHistory.data.length === 0"
      class="flex flex-1 flex-col items-center justify-center gap-3 py-8 text-xl font-medium text-ink-gray-6"
    >
      <DocumentIcon class="h-12 w-12 text-ink-gray-4" />
      <span>{{ __('No order history found') }}</span>
      <p v-if="fetching" class="text-sm text-ink-gray-5">
        {{ __('Fetching order history...') }}
      </p>
      <p v-else-if="hasFetched" class="text-sm text-ink-gray-5">
        {{ __('No orders found for this customer.') }}
      </p>
      <p v-else-if="!customerName" class="text-sm text-ink-gray-5">
        <span v-if="props.doctype === 'CRM Lead'">
          {{ __('Please set a lead name to fetch order history.') }}
        </span>
        <span v-else>
          {{ __('Please link a Lead to this Deal to fetch order history.') }}
        </span>
      </p>
    </div>

    <div v-else class="overflow-x-auto">
      <table class="w-full border-collapse">
        <thead>
          <tr class="border-b border-outline-gray-modals bg-surface-gray-1">
            <th class="px-4 py-3 text-left text-sm font-medium text-ink-gray-7">
              {{ __('Sales Order') }}
            </th>
            <th class="px-4 py-3 text-left text-sm font-medium text-ink-gray-7">
              {{ __('Order Date') }}
            </th>
            <th class="px-4 py-3 text-left text-sm font-medium text-ink-gray-7">
              {{ __('Item Name') }}
            </th>
            <th class="px-4 py-3 text-left text-sm font-medium text-ink-gray-7">
              {{ __('Qty') }}
            </th>
            <th class="px-4 py-3 text-left text-sm font-medium text-ink-gray-7">
              {{ __('Amount') }}
            </th>
            <th class="px-4 py-3 text-left text-sm font-medium text-ink-gray-7">
              {{ __('QA Status') }}
            </th>
            <th class="px-4 py-3 text-left text-sm font-medium text-ink-gray-7">
              {{ __('OPS Status') }}
            </th>
            <th class="px-4 py-3 text-left text-sm font-medium text-ink-gray-7">
              {{ __('Ingredient Status') }}
            </th>
            <th class="px-4 py-3 text-left text-sm font-medium text-ink-gray-7">
              {{ __('Production Status') }}
            </th>
            <th class="px-4 py-3 text-left text-sm font-medium text-ink-gray-7">
              {{ __('Aggregate Production Status') }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(order, index) in orderHistory.data"
            :key="index"
            class="border-b border-outline-gray-modals hover:bg-surface-gray-1"
          >
            <td class="px-4 py-3 text-sm">
              <a
                :href="`/app/sales-order/${order.sales_order}`"
                target="_blank"
                class="text-blue-600 hover:underline"
              >
                {{ order.sales_order }}
              </a>
            </td>
            <td class="px-4 py-3 text-sm text-ink-gray-8">
              {{ formatDate(order.order_date) }}
            </td>
            <td class="px-4 py-3 text-sm text-ink-gray-8">
              {{ order.item_name }}
            </td>
            <td class="px-4 py-3 text-sm text-ink-gray-8">
              {{ order.qty }}
            </td>
            <td class="px-4 py-3 text-sm font-medium text-ink-gray-8">
              {{ formatCurrency(order.amount) }}
            </td>
            <td class="px-4 py-3 text-sm">
              <span v-if="order.qa_status" class="status-badge-crm" :class="'status-badge-' + getStatusColor(order.qa_status)">
                {{ getStatusIcon(order.qa_status) }} {{ order.qa_status }}
              </span>
              <span v-else class="text-gray-400">-</span>
            </td>
            <td class="px-4 py-3 text-sm">
              <span v-if="order.ops_status" class="status-badge-crm" :class="'status-badge-' + getStatusColor(order.ops_status)">
                {{ getStatusIcon(order.ops_status) }} {{ order.ops_status }}
              </span>
              <span v-else class="text-gray-400">-</span>
            </td>
            <td class="px-4 py-3 text-sm">
              <span v-if="order.custom_ingredients_status" class="status-badge-crm" :class="'status-badge-' + getStatusColor(order.custom_ingredients_status)">
                {{ getStatusIcon(order.custom_ingredients_status) }} {{ order.custom_ingredients_status }}
              </span>
              <span v-else class="text-gray-400">-</span>
            </td>
            <td class="px-4 py-3 text-sm">
              <span v-if="order.pro_status" class="status-badge-crm" :class="'status-badge-' + getStatusColor(order.pro_status)">
                {{ getStatusIcon(order.pro_status) }} {{ order.pro_status }}
              </span>
              <span v-else class="text-gray-400">-</span>
            </td>
            <td class="px-4 py-3 text-sm">
              <span v-if="order.aggregate_production_status" class="status-badge-crm" :class="'status-badge-' + getStatusColor(order.aggregate_production_status)">
                {{ getStatusIcon(order.aggregate_production_status) }} {{ order.aggregate_production_status }}
              </span>
              <span v-else class="text-gray-400">-</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { createResource, call, toast } from 'frappe-ui'
import { ref, computed, onMounted, watch } from 'vue'
import LoadingIndicator from '@/components/Icons/LoadingIndicator.vue'
import DocumentIcon from '@/components/Icons/DocumentIcon.vue'

const props = defineProps({
  doctype: {
    type: String,
    required: true,
  },
  docname: {
    type: String,
    required: true,
  },
})

const fetching = ref(false)
const hasFetched = ref(false)
const customerName = ref(null)

const orderHistory = createResource({
  url: 'frappe.client.get',
  params: {
    doctype: props.doctype,
    name: props.docname,
  },
  transform: (data) => {
    return data.custom_order_history || []
  },
  auto: true,
})

// Computed property for loading state
const isLoading = computed(() => {
  return orderHistory.loading || fetching.value
})

// Truncate contact name if duplicated (e.g., "Tamala Fowler-Tamala Fowler" -> "Tamala Fowler")
function truncateContactName(name) {
  if (!name) return null
  if (name.includes('-')) {
    const parts = name.split('-')
    if (parts.length === 2 && parts[0].trim() === parts[1].trim()) {
      return parts[0].trim()
    }
  }
  return name
}

async function fetchOrderHistory() {
  if (fetching.value || hasFetched.value) {
    console.log('⏭️ Skipping fetch - already fetching or fetched:', { fetching: fetching.value, hasFetched: hasFetched.value })
    return
  }

  console.log('🚀 Starting fetchOrderHistory:', { doctype: props.doctype, docname: props.docname })

  try {
    fetching.value = true

    // Get the document to access customer/lead name
    const doc = await call('frappe.client.get', {
      doctype: props.doctype,
      name: props.docname,
    })

    console.log('📄 Document fetched:', { doctype: props.doctype, docname: props.docname, doc })

    let params = {}
    let method = ''
    let customer_name = null

    if (props.doctype === 'CRM Lead') {
      customer_name = truncateContactName(doc.lead_name)
      customerName.value = customer_name

      if (!customer_name) {
        console.warn('⚠️ No lead_name found on Lead document')
        toast.error('Please set a lead name to fetch order history')
        fetching.value = false
        hasFetched.value = true
        return
      }

      params = {
        lead_name: props.docname,
        customer_name: customer_name,
      }
      method = 'crm.api.order_history.fetch_lead_order_history'
    } else {
      // For Deal, get customer name from linked Lead's lead_name
      if (!doc.lead) {
        console.warn('⚠️ No Lead linked to Deal')
        toast.error('Please link a Lead to this Deal to fetch order history')
        fetching.value = false
        hasFetched.value = true
        return
      }

      const leadDoc = await call('frappe.client.get', {
        doctype: 'CRM Lead',
        name: doc.lead,
      })

      console.log('📄 Lead document fetched:', { leadName: doc.lead, leadDoc })

      customer_name = truncateContactName(leadDoc.lead_name)
      customerName.value = customer_name

      if (!customer_name) {
        console.warn('⚠️ No lead_name found on linked Lead document')
        toast.error('The linked Lead does not have a lead name')
        fetching.value = false
        hasFetched.value = true
        return
      }

      params = {
        deal_name: props.docname,
        customer_name: customer_name,
      }
      method = 'crm.api.order_history.fetch_deal_order_history'
    }

    console.log('📞 Calling API:', { method, params })

    const result = await call(method, params)

    console.log('✅ API response:', result)

    if (result && result.success) {
      toast.success(result.message || 'Order history fetched successfully')
      orderHistory.reload()
      hasFetched.value = true
    } else {
      toast.error(result?.message || 'Error fetching order history')
      hasFetched.value = true
    }
  } catch (err) {
    console.error('❌ Error fetching order history:', err)
    toast.error(err.messages?.[0] || err.message || 'Error fetching order history')
    hasFetched.value = true
  } finally {
    fetching.value = false
  }
}

// Watch for docname changes to refetch
watch(
  () => props.docname,
  (newDocname, oldDocname) => {
    if (newDocname && newDocname !== oldDocname) {
      console.log('🔄 Docname changed, resetting fetch state:', { old: oldDocname, new: newDocname })
      hasFetched.value = false
      customerName.value = null
      // Fetch will be triggered by onMounted or when orderHistory data becomes available
    }
  }
)

// Watch for orderHistory data to become available and trigger fetch
watch(
  () => orderHistory.data,
  (data) => {
    if (data !== undefined && !hasFetched.value && !fetching.value && props.docname) {
      console.log('📊 OrderHistory data available, triggering fetch:', { hasData: !!data, docname: props.docname })
      setTimeout(() => fetchOrderHistory(), 200)
    }
  },
  { immediate: true }
)

// Auto-fetch when component mounts
onMounted(() => {
  console.log('🎯 OrderDetails onMounted:', {
    doctype: props.doctype,
    docname: props.docname,
    hasOrderHistoryData: !!orderHistory.data,
    hasFetched: hasFetched.value,
    fetching: fetching.value,
  })

  // Add status badge styles - EXACT match to Helpdesk script
  if (!document.getElementById('crm-status-badge-styles')) {
    const styles = document.createElement('style')
    styles.id = 'crm-status-badge-styles'
    styles.textContent = `
      .status-badge-crm {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 12px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.3px;
        white-space: nowrap;
        border: 1px solid;
      }
      .status-badge-green {
        background: #ecfdf5;
        color: #059669;
        border-color: #a7f3d0;
      }
      .status-badge-blue {
        background: #eff6ff;
        color: #2563eb;
        border-color: #bfdbfe;
      }
      .status-badge-yellow {
        background: #fffbeb;
        color: #d97706;
        border-color: #fde68a;
      }
      .status-badge-red {
        background: #fef2f2;
        color: #dc2626;
        border-color: #fecaca;
      }
      .status-badge-gray {
        background: #f9fafb;
        color: #6b7280;
        border-color: #e5e7eb;
      }
    `
    document.head.appendChild(styles)
  }

  if (props.docname && !hasFetched.value && !fetching.value) {
    // Small delay to ensure orderHistory resource has loaded
    setTimeout(() => {
      if (orderHistory.data !== undefined) {
        fetchOrderHistory()
      }
    }, 300)
  }
})

function formatDate(date) {
  if (!date) return __('N/A')
  return new Date(date).toLocaleDateString()
}

function formatCurrency(amount) {
  if (!amount) return __('N/A')
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(amount)
}

function getDeliveryStatusTheme(status) {
  if (!status) return 'gray'
  const upperStatus = status.toUpperCase()
  if (['DELIVERED', 'COMPLETED'].includes(upperStatus)) {
    return 'green'
  }
  if (['PARTIALLY DELIVERED', 'IN TRANSIT'].includes(upperStatus)) {
    return 'blue'
  }
  if (['PENDING', 'NOT DELIVERED'].includes(upperStatus)) {
    return 'orange'
  }
  return 'gray'
}

// Status badge helper functions - EXACT match to Helpdesk script
function getStatusColor(status) {
  if (!status) return 'gray'
  const statusUpper = String(status).toUpperCase().trim()
  
  // Green - Complete/Approved
  if (['APPROVED', 'IN_STOCK', 'DONE', 'PASS'].includes(statusUpper)) {
    return 'green'
  }
  
  // Blue - Active/In Progress
  if (['WIP', 'IN PROGRESS', 'CONFIRMATION PENDING'].includes(statusUpper)) {
    return 'blue'
  }
  
  // Yellow - Warning/Review/Pending
  if (['NEW', 'AWAITING', 'REVIEW_REQUIRED', 'IN_STOCK_TENTATIVE', 
       'OPS REVIEW', 'EXPECTED', 'QA REWORK', 'ALTERNATE FABRIC', 
       'BLOCK REVIEW', 'NO RECIPE', 'NOT STARTED', 'NO_RECIPE'].includes(statusUpper)) {
    return 'yellow'
  }
  
  // Red - Error/Blocked/Not Available
  if (['NOT_AVAILABLE', 'NOT AVAILABLE', 'BLOCKED_FACTORY', 'BLOCKED_OPS', 
       'FAIL', 'CANCEL REQUEST', 'POST APPROVAL HOLD OR CHANGE REQUEST', 
       'PRE_APPROVAL_CUSTOMER HOLD'].includes(statusUpper)) {
    return 'red'
  }
  
  // Gray - Default
  return 'gray'
}

function getStatusIcon(status) {
  if (!status) return '📋'
  const statusUpper = String(status).toUpperCase().trim()
  
  const iconMap = {
    'APPROVED': '✅',
    'IN_STOCK': '✅',
    'DONE': '✅',
    'PASS': '✅',
    'WIP': '⚙️',
    'IN PROGRESS': '🔍',
    'NEW': '🆕',
    'AWAITING': '⏳',
    'REVIEW_REQUIRED': '⚠️',
    'OPS REVIEW': '👀',
    'NOT_AVAILABLE': '🔴',
    'NOT AVAILABLE': '🔴',
    'BLOCKED_FACTORY': '🚧',
    'BLOCKED_OPS': '⚠️',
    'FAIL': '❌',
    'EXPECTED': '📦',
    'NO RECIPE': '📝',
    'NO_RECIPE': '📝',
    'NOT STARTED': '🔵',
    'QA REWORK': '🔄'
  }
  
  return iconMap[statusUpper] || '📋'
}


</script>

