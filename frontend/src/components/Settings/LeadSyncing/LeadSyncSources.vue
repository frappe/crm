<template>
    <pre>{{ JSON.stringify(sources, null, 2) }}</pre>
</template>
<script setup>
import { inject } from 'vue';

const sources = inject('sources')
</script>