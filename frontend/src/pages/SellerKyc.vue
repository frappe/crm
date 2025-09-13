<template>
    <LayoutHeader>
      <template #left-header>
        <ViewBreadcrumbs v-model="viewControls" routeName="Seller KYC" />
      </template>
      <template #right-header>
        <CustomActions
          v-if="sellerKycsListView?.customListActions"
          :actions="sellerKycsListView.customListActions"
        />
        <!-- <Button variant="solid" :label="__('Create')" @click="createSellerKyc">
          <template #prefix><FeatherIcon name="plus" class="h-4" /></template>
        </Button> -->
      </template>
    </LayoutHeader>
    <ViewControls
      ref="viewControls"
      v-model="sellerKycs"
      v-model:loadMore="loadMore"
      v-model:resizeColumn="triggerResize"
      v-model:updatedPageCount="updatedPageCount"
      doctype="Asroy Seller Profile KYC"
    />
    <SellerKycsListView
      ref="sellerKycsListView"
      v-if="sellerKycs.data && rows.length"
      v-model="sellerKycs.data.page_length_count"
      v-model:list="sellerKycs"
      :rows="rows"
      :columns="sellerKycs.data.columns"
      :options="{
        showTooltip: false,
        resizeColumn: true,
        rowCount: sellerKycs.data.row_count,
        totalCount: sellerKycs.data.total_count,
      }"
      @showSellerKyc="showSellerKyc"
      @loadMore="() => loadMore++"
      @columnWidthUpdated="() => triggerResize++"
      @updatePageCount="(count) => (updatedPageCount = count)"
      @applyFilter="(data) => viewControls.applyFilter(data)"
      @applyLikeFilter="(data) => viewControls.applyLikeFilter(data)"
      @likeDoc="(data) => viewControls.likeDoc(data)"
    />
    <div
      v-else-if="sellerKycs.data"
      class="flex h-full items-center justify-center"
    >
      <div
        class="flex flex-col items-center gap-3 text-xl font-medium text-ink-gray-4"
      >
        <PhoneIcon class="h-10 w-10" />
        <span>{{ __('No {0} Found', [__('Logs')]) }}</span>
      </div>
    </div>
  </template>
  
  <script setup>
  import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
  import CustomActions from '@/components/CustomActions.vue'
  import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
  import LayoutHeader from '@/components/LayoutHeader.vue'
  import ViewControls from '@/components/ViewControls.vue'
  import SellerKycsListView from '@/components/ListViews/SellerKycListView.vue'
  import { getKycDetail } from '@/utils/kyc'
  import { computed, ref } from 'vue'
  
  const sellerKycsListView = ref(null)
  const sellerKycs = ref({})
  const loadMore = ref(1)
  const triggerResize = ref(1)
  const updatedPageCount = ref(20)
  const viewControls = ref(null)
  
  const rows = computed(() => {
    if (
      !sellerKycs.value?.data?.data ||
      !['list', 'group_by'].includes(sellerKycs.value.data.view_type)
    )
      return []
    return sellerKycs.value?.data.data.map((sellerKyc) => {
      let _rows = {}
      sellerKycs.value?.data.rows.forEach((row) => {
        _rows[row] = getKycDetail(row, sellerKyc, sellerKycs.value?.data.columns)
      })
      return _rows
    })
  }) 
  </script>
  