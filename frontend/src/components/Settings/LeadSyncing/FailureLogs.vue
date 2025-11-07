<template>
    Failure log list for source {{ props.source }} goes here...
</template>

<script setup>
const props = defineProps({
    source: {
        type: String,
        required: true
    }
})
</script>