<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs" />
    </template>
    <template #right-header>
      <Button variant="solid" label="Create" @click="showEmailTemplateModal = true">
        <template #prefix><FeatherIcon name="plus" class="h-4" /></template>
      </Button>
    </template>
  </LayoutHeader>
  <ViewControls
    v-model="emailTemplates"
    v-model:loadMore="loadMore"
    doctype="Email Template"
  />
  <EmailTemplatesListView
    v-if="emailTemplates.data && rows.length"
    v-model="emailTemplates.data.page_length_count"
    :rows="rows"
    :columns="emailTemplates.data.columns"
    :options="{
      rowCount: emailTemplates.data.row_count,
      totalCount: emailTemplates.data.total_count,
    }"
    @loadMore="() => loadMore++"
    @showEmailTemplate="showEmailTemplate"
    @reload="() => emailTemplates.reload()"
  />
  <div
    v-else-if="emailTemplates.data"
    class="flex h-full items-center justify-center"
  >
    <div
      class="flex flex-col items-center gap-3 text-xl font-medium text-gray-500"
    >
      <EmailIcon class="h-10 w-10" />
      <span>No Email Templates Found</span>
    </div>
  </div>
  <EmailTemplateModal
    v-model="showEmailTemplateModal"
    v-model:reloadEmailTemplates="emailTemplates"
    :emailTemplate="emailTemplate"
  />
</template>

<script setup>
import EmailIcon from '@/components/Icons/EmailIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewControls from '@/components/ViewControls.vue'
import EmailTemplatesListView from '@/components/ListViews/EmailTemplatesListView.vue'
import EmailTemplateModal from '@/components/Modals/EmailTemplateModal.vue'
import { dateFormat, dateTooltipFormat, timeAgo } from '@/utils'
import { Breadcrumbs } from 'frappe-ui'
import { computed, ref } from 'vue'

const breadcrumbs = [
  { label: 'Email Templates', route: { name: 'Email Templates' } },
]

// emailTemplates data is loaded in the ViewControls component
const emailTemplates = ref({})
const loadMore = ref(1)

const rows = computed(() => {
  if (!emailTemplates.value?.data?.data) return []
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

const emailTemplate = ref({
    subject: '',
    response: '',
    name: '',
    enabled: 1,
    owner: '',
    reference_doctype: 'CRM Deal',
})

function showEmailTemplate(name) {
  let et = rows.value?.find((row) => row.name === name)
  emailTemplate.value = {
    subject: et.subject,
    response: et.response,
    name: et.name,
    enabled: et.enabled,
    owner: et.owner,
    reference_doctype: et.reference_doctype,
  }
  showEmailTemplateModal.value = true
}
</script>
