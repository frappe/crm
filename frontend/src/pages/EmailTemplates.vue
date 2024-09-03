<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs v-model="viewControls" routeName="Email Templates" />
    </template>
    <template #right-header>
      <CustomActions
        v-if="emailTemplatesListView?.customListActions"
        :actions="emailTemplatesListView.customListActions"
      />
      <Button
        variant="solid"
        :label="__('Create')"
        @click="() => showEmailTemplate()"
      >
        <template #prefix><FeatherIcon name="plus" class="h-4" /></template>
      </Button>
    </template>
  </LayoutHeader>
  <ViewControls
    ref="viewControls"
    v-model="emailTemplates"
    v-model:loadMore="loadMore"
    v-model:resizeColumn="triggerResize"
    v-model:updatedPageCount="updatedPageCount"
    doctype="Email Template"
  />
  <EmailTemplatesListView
    ref="emailTemplatesListView"
    v-if="emailTemplates.data && rows.length"
    v-model="emailTemplates.data.page_length_count"
    v-model:list="emailTemplates"
    :rows="rows"
    :columns="emailTemplates.data.columns"
    :options="{
      showTooltip: false,
      resizeColumn: true,
      rowCount: emailTemplates.data.row_count,
      totalCount: emailTemplates.data.total_count,
    }"
    @loadMore="() => loadMore++"
    @columnWidthUpdated="() => triggerResize++"
    @updatePageCount="(count) => (updatedPageCount = count)"
    @showEmailTemplate="showEmailTemplate"
    @applyFilter="(data) => viewControls.applyFilter(data)"
    @applyLikeFilter="(data) => viewControls.applyLikeFilter(data)"
    @likeDoc="(data) => viewControls.likeDoc(data)"
  />
  <div
    v-else-if="emailTemplates.data"
    class="flex h-full items-center justify-center"
  >
    <div
      class="flex flex-col items-center gap-3 text-xl font-medium text-gray-500"
    >
      <Email2Icon class="h-10 w-10" />
      <span>{{ __('No {0} Found', [__('Email Templates')]) }}</span>
      <Button :label="__('Create')" @click="() => showEmailTemplate()">
        <template #prefix><FeatherIcon name="plus" class="h-4" /></template>
      </Button>
    </div>
  </div>
  <EmailTemplateModal
    v-model="showEmailTemplateModal"
    v-model:reloadEmailTemplates="emailTemplates"
    :emailTemplate="emailTemplate"
  />
</template>

<script setup>
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import CustomActions from '@/components/CustomActions.vue'
import Email2Icon from '@/components/Icons/Email2Icon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewControls from '@/components/ViewControls.vue'
import EmailTemplatesListView from '@/components/ListViews/EmailTemplatesListView.vue'
import EmailTemplateModal from '@/components/Modals/EmailTemplateModal.vue'
import { dateFormat, dateTooltipFormat, timeAgo } from '@/utils'
import { computed, ref } from 'vue'

const emailTemplatesListView = ref(null)

// emailTemplates data is loaded in the ViewControls component
const emailTemplates = ref({})
const loadMore = ref(1)
const triggerResize = ref(1)
const updatedPageCount = ref(20)
const viewControls = ref(null)

const rows = computed(() => {
  if (
    !emailTemplates.value?.data?.data ||
    !['list', 'group_by'].includes(emailTemplates.value.data.view_type)
  )
    return []
  return emailTemplates.value?.data.data.map((emailTemplate) => {
    let _rows = {}
    emailTemplates.value?.data.rows.forEach((row) => {
      _rows[row] = emailTemplate[row]

      if (['modified', 'creation'].includes(row)) {
        _rows[row] = {
          label: dateFormat(emailTemplate[row], dateTooltipFormat),
          timeAgo: timeAgo(emailTemplate[row]),
        }
      }
    })
    return _rows
  })
})

const showEmailTemplateModal = ref(false)

const emailTemplate = ref({})

function showEmailTemplate(name) {
  if (!name) {
    emailTemplate.value = {
      subject: '',
      response: '',
      response_html: '',
      name: '',
      enabled: 1,
      use_html: 0,
      owner: '',
      reference_doctype: 'CRM Deal',
    }
  } else {
    let et = rows.value?.find((row) => row.name === name)
    emailTemplate.value = {
      subject: et.subject,
      response: et.response,
      response_html: et.response_html,
      name: et.name,
      enabled: et.enabled,
      use_html: et.use_html,
      owner: et.owner,
      reference_doctype: et.reference_doctype,
    }
  }
  showEmailTemplateModal.value = true
}
</script>
