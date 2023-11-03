<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs" />
    </template>
    <template #right-header>
      <Button
        variant="solid"
        label="Create"
        @click="showOrganizationModal = true"
      >
        <template #prefix><FeatherIcon name="plus" class="h-4" /></template>
        Create organization
      </Button>
    </template>
  </LayoutHeader>
  <div class="flex h-full overflow-hidden">
    <div class="flex shrink-0 flex-col overflow-y-auto border-r">
      <router-link
        :to="{
          name: 'Organization',
          params: { organizationId: organization.name },
        }"
        v-for="(organization, i) in organizations.data"
        :key="i"
        :class="[
          currentOrganization?.name === organization.name
            ? 'bg-gray-50 hover:bg-gray-100'
            : 'hover:bg-gray-50',
        ]"
      >
        <div class="flex w-[352px] items-center gap-3 border-b px-5 py-4">
          <Avatar
            :image="organization.organization_logo"
            :label="organization.name"
            size="xl"
          />
          <div class="flex flex-col items-start gap-1">
            <span class="text-base font-medium text-gray-900">
              {{ organization.name }}
            </span>
            <span class="text-sm text-gray-700">{{
              website(organization.website)
            }}</span>
          </div>
        </div>
      </router-link>
    </div>
    <router-view
      v-if="currentOrganization"
      :organization="currentOrganization"
    />
    <div
      v-else
      class="grid h-full flex-1 place-items-center text-xl font-medium text-gray-500"
    >
      <div class="flex flex-col items-center justify-center space-y-2">
        <OrganizationsIcon class="h-10 w-10" />
        <div>No organization selected</div>
      </div>
    </div>
  </div>
  <!-- <OrganizationModal
      v-model="showOrganizationModal"
      v-model:reloadOrganizations="organizations"
      :organization="{}"
    /> -->
</template>
<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
// import OrganizationModal from '@/components/OrganizationModal.vue'
import OrganizationsIcon from '@/components/Icons/OrganizationsIcon.vue'
import { FeatherIcon, Breadcrumbs, Avatar } from 'frappe-ui'
import { organizationsStore } from '@/stores/organizations.js'
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
const { organizations } = organizationsStore()
const route = useRoute()
const showOrganizationModal = ref(false)
const currentOrganization = computed(() => {
  return organizations.data.find(
    (organization) => organization.name === route.params.organizationId
  )
})
const breadcrumbs = computed(() => {
  let items = [{ label: 'Organizations', route: { name: 'Organizations' } }]
  if (!currentOrganization.value) return items
  items.push({
    label: currentOrganization.value.name,
    route: {
      name: 'Organization',
      params: { organizationId: currentOrganization.value.name },
    },
  })
  return items
})
onMounted(() => {
  const el = document.querySelector('.router-link-active')
  if (el)
    setTimeout(() => {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' })
    })
})
function website(url) {
  return url.replace(/^(?:https?:\/\/)?(?:www\.)?/i, '')
}
</script>
