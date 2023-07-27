<template>
  <ListView :list="list_details"/>
</template>

<script setup>
import ListView from '../components/ListView.vue';

const list_details = {
  title: 'Inbox',
  plural_label: 'Emails',
  singular_label: 'Email',
}
</script>
