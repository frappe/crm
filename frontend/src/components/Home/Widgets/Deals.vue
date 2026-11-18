<template>
  <LeadsAndDeals doctype="Deal" />
</template>
<script setup>
import LeadsAndDeals from '@/components/Home/Widgets/LeadsAndDeals.vue'

// Declared so Home's `config` does not fall through and show the doctype filter
defineProps({ config: { type: Object, default: null } })
</script>
