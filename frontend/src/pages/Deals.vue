<template>
  <ListView :list="list_details"/>
</template>

<script setup>
import ListView from '../components/ListView.vue';

const list_details = {
  title: 'Deals',
  plural_label: 'Deals',
  singular_label: 'Deal',
}
</script>
