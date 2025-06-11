<template>
  <LayoutHeader v-if="quotations.doc">
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs">
        <template #prefix="{ item }">
          <Icon v-if="item.icon" :icon="item.icon" class="mr-2 h-4"/>
        </template>
      </Breadcrumbs>
    </template>
  </LayoutHeader>
  <div v-if="quotations.doc" ref="parentRef" class="flex h-full bg-gray-200 justify-center p-9 overflow-y-auto">
    <div class="bg-white w-full h-full max-w-[210mm] max-h-[297mm] aspect-[210/297] shadow-xl  mb-5">
      <!-- Shadow DOM container -->
      <div ref="shadowContainer" class="w-full h-full"></div>
    </div>
  </div>
  <ErrorPage
      v-else-if="errorTitle"
      :errorTitle="errorTitle"
      :errorMessage="errorMessage"
  />
</template>

<script setup>
import ErrorPage from '@/components/ErrorPage.vue'
import Icon from '@/components/Icon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import DealsIcon from '@/components/Icons/DealsIcon.vue'
import {getSettings} from '@/stores/settings'
import {getMeta} from '@/stores/meta'
import {getView} from '@/utils/view'
import {Breadcrumbs, createDocumentResource, createResource, usePageMeta} from 'frappe-ui'
import {computed, h, ref, onMounted, nextTick, watch} from 'vue'
import {useRoute, useRouter} from 'vue-router'

const props = defineProps({
  quotationId: {
    type: String,
    required: true,
  },
})

const {brand} = getSettings()
const {doctypeMeta} = getMeta('Quotation')

const route = useRoute()
const router = useRouter()

const errorTitle = ref('')
const errorMessage = ref('')
const shadowContainer = ref(null)
let shadowRoot = null

const quotations = createDocumentResource({
  doctype: 'Quotation',
  name: props.quotationId,
  cache: ['quotation', props.quotationId],
  fields: ['*'],
  auto: true,
  onSuccess: () => {
    errorTitle.value = ''
    errorMessage.value = ''
  },
  onError: (err) => {
    if (err.messages?.[0]) {
      errorTitle.value = __('Not permitted')
      errorMessage.value = __(err.messages[0])
    } else {
      router.push({name: 'Quotations'})
    }
  },
})

const fcrmSettings = createResource({
  url: 'frappe.client.get',
  params: {doctype: 'FCRM Settings', name: 'FCRM Settings'},
  cache: ['fcrmSettings'],
  auto: false,
  onSuccess: (data) => {
    console.log('FCRM Settings loaded:', data)
    // Trigger print view fetch if quotation is also ready
    if (quotations.doc) {
      fetchPrintView()
    }
  },
  onError: (err) => {
    console.error('Failed to load FCRM Settings:', err)
    // Use default print format if settings fail
    if (quotations.doc) {
      fetchPrintView()
    }
  }
})

const printSettings = createResource({
  url: 'frappe.client.get',
  params: {doctype: 'Print Settings', name: 'Print Settings'},
  cache: ['printSettings'],
  auto: false,
  onSuccess: (data) => {
    console.log('Print Settings loaded:', data)
    // You can access print settings like:
    // data.print_style - Default print style
    // data.repeat_header_footer - Whether to repeat headers/footers
    // data.allow_print_for_draft - Allow printing draft documents
  },
  onError: (err) => {
    console.error('Failed to load Print Settings:', err)
  }
});

const printView = createResource({
  url: 'frappe.www.printview.get_html_and_style',
  auto: false,
  onSuccess: (data) => {
    console.log('Print view data:', data)
    renderPrintViewInShadowDOM(data)
  },
  onError: (err) => {
    console.error('Print view failed:', err)
    errorTitle.value = 'Print View Error'
    errorMessage.value = 'Failed to load print view'
  }
})

// Function to create and manage Shadow DOM
const createShadowDOM = () => {
  if (shadowContainer.value && !shadowRoot) {
    try {
      shadowRoot = shadowContainer.value.attachShadow({ mode: 'open' })
      console.log('Shadow DOM created successfully')
    } catch (error) {
      console.error('Failed to create Shadow DOM:', error)
      // Fallback to regular DOM if Shadow DOM is not supported
      shadowRoot = shadowContainer.value
    }
  }
}

// Function to render print view content in Shadow DOM
const renderPrintViewInShadowDOM = (data) => {
  console.log('Attempting to render print view in Shadow DOM:', {
    hasShadowRoot: !!shadowRoot,
    hasData: !!data,
    hasHtml: !!data?.html,
    hasStyle: !!data?.style
  })

  if (!shadowRoot) {
    console.warn('Shadow DOM not available, creating it now')
    createShadowDOM()
  }

  if (!shadowRoot || !data) {
    console.warn('Shadow DOM or print view data not available')
    return
  }

  try {
    // Clear existing content
    shadowRoot.innerHTML = ''

    // Create style element for print view styles
    if (data.style) {
      const styleElement = document.createElement('style')
      styleElement.textContent = data.style
      shadowRoot.appendChild(styleElement)
      console.log('Applied print view styles to Shadow DOM')
    }

    // Create container div for the HTML content with proper margins
    const contentContainer = document.createElement('div')
    contentContainer.className = 'print-format'
    contentContainer.style.cssText = `
      width: 100%;
      height: 100%;
      overflow: auto;
      box-sizing: border-box;
    `

    // Set the HTML content
    if (data.html) {
      contentContainer.innerHTML = data.html
      console.log('Applied print view HTML to Shadow DOM')
    }

    // Append content to shadow root
    shadowRoot.appendChild(contentContainer)

    console.log('Print view rendered in Shadow DOM successfully')
  } catch (error) {
    console.error('Error rendering print view in Shadow DOM:', error)

    // Fallback: render in regular DOM
    if (shadowContainer.value) {
      shadowContainer.value.innerHTML = `
        <style>${data.style || ''}</style>
        <div class="print-format" style="width: 100%; height: 100%; overflow: auto;">${data.html || ''}</div>
      `
      console.log('Fallback: Rendered in regular DOM')
    }
  }
}

// Watch for changes in print view data
watch(() => printView.data, (newData) => {
  if (newData && shadowRoot) {
    renderPrintViewInShadowDOM(newData)
  }
})

// Function to fetch print view once all dependencies are ready
const fetchPrintView = async () => {
  if (!quotations.doc || !fcrmSettings.data) {
    console.log('Dependencies not ready yet:', {
      hasQuotation: !!quotations.doc,
      hasSettings: !!fcrmSettings.data
    })
    return
  }

  try {
    const printFormat = fcrmSettings.data.quotation_print_format || 'Standard'

    printView.update({
      params: {
        doc: JSON.stringify(quotations.doc),
        print_format: printFormat,
      }
    })

    await printView.fetch()
    console.log('Print view fetched successfully')
  } catch (error) {
    console.error('Failed to fetch print view:', error)
  }
}

// Watch for quotations data changes
watch(() => quotations.doc, (newDoc) => {
  if (newDoc && shadowRoot) {
    fetchPrintView()
  }
})

// Watch for settings data changes
watch(() => fcrmSettings.data, (newData) => {
  if (newData && quotations.doc) {
    fetchPrintView()
  }
})

onMounted(async () => {
  try {
    // Wait for DOM to be ready
    await nextTick()

    // Create Shadow DOM
    createShadowDOM()

    // Start fetching settings immediately
    fcrmSettings.fetch()
    printSettings.fetch()

    // If quotation is not loaded, reload it
    if (!quotations.doc) {
      quotations.reload()
    } else {
      // If quotation is already loaded, try to fetch print view
      fetchPrintView()
    }

  } catch (error) {
    console.error('Initialization failed:', error)
  }
});

const breadcrumbs = computed(() => {
  let items = [{label: __('Quotations'), route: {name: 'Quotations'}}]

  if (route.query.view || route.query.viewType) {
    let view = getView(
        route.query.view,
        route.query.viewType,
        'Quotation',
    )
    if (view) {
      items.push({
        label: __(view.label),
        icon: view.icon,
        route: {
          name: 'Quotations',
          params: {viewType: route.query.viewType},
          query: {view: route.query.view},
        },
      })
    }
  }

  items.push({
    label: title.value,
    route: {
      name: 'Quotation',
      params: {quotationId: props.quotationId},
    },
  })
  return items
})

const title = computed(() => {
  let t = doctypeMeta['Quotation']?.title_field || 'name'
  return quotations.doc?.[t] || props.quotationId
})

usePageMeta(() => {
  return {
    title: title.value,
    icon: brand.favicon,
  }
})

const tabIndex = ref(0)
const tabs = [
  {
    label: 'Deals',
    icon: h(DealsIcon, {class: 'h-4 w-4'}),
  }
]

// Utility function to print the shadow DOM content
const handlePrint = () => {
  if (!printView.data) {
    console.warn('No print view data available')
    return
  }

  const printWindow = window.open('', '_blank')
  const printContent = `
    <!DOCTYPE html>
    <html>
      <head>
        <title>Print Quotation - ${title.value}</title>
        <style>
          ${printView.data.style || ''}
          @media print {
            body { margin: 0; }
            * { -webkit-print-color-adjust: exact; }
          }
        </style>
      </head>
      <body>
        ${printView.data.html || ''}
      </body>
    </html>
  `

  printWindow.document.write(printContent)
  printWindow.document.close()

  // Wait for content to load before printing
  printWindow.onload = () => {
    printWindow.print()
    printWindow.close()
  }
}

// Expose print function for external use
defineExpose({
  handlePrint
})
</script>