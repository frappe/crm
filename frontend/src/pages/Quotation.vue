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
  <div v-if="quotations.doc" ref="parentRef" class="flex h-full bg-gray-200 justify-center p-9">
    <div class="bg-white w-full h-full max-w-[210mm] max-h-[297mm] aspect-[210/297] shadow-xl"
         v-html="quotations.doc.name"
    >
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
import {computed, h, ref, onMounted} from 'vue'
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
const quotations = createDocumentResource({
  doctype: 'Quotation',
  name: props.quotationId,
  cache: ['quotation', props.quotationId],
  fields: ['*'],
  auto: false, // Add this since you're manually fetching
  onSuccess: () => {
    errorTitle.value = ''
    errorMessage.value = ''
  },
  onError: (err) => {
    if (err.messages?.[0]) {
      errorTitle.value = __('Not permitted')
      errorMessage.value = __(err.messages[0]) // Fixed: removed ?. since you already checked above
    } else {
      router.push({name: 'Quotations'})
    }
  },
})

const fcrmSettings = createResource({
  url: 'frappe.client.get',
  params: {doctype: 'FCRM Settings', name: 'FCRM Settings'},
  cache: ['fcrmSettings'],
  auto: false, // Add this since you're manually fetching
  onSuccess: (data) => {
    console.log({data})
    quotations.print_format = data.quotation_print_format
  },
});

const printView = createResource({
  url: 'frappe.www.printview.get_html_and_style',
  auto: false, // Don't auto-fetch
  onSuccess: (data) => {
    console.log('Print view data:', data)
    // Handle the print view response
  },
})

onMounted(async () => {
  try {
    // Wait for both APIs to complete
    await Promise.all([
      quotations.get(),
      fcrmSettings.fetch()
    ])

    // Now fetch printView with the correct params
    printView.update({
      params: {
        doc: quotations.doc,
        print_format: quotations.print_format,
      }
    })

    await printView.fetch()

  } catch (error) {
    console.error('API call failed:', error)
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


</script>
