<template>
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      width="20"
      height="20"
      fill="none"
      :stroke="isRecording ? 'white' : 'black'"
      stroke-width="2"
      stroke-linecap="round"
      stroke-linejoin="round"
      class="transition-colors duration-200"
    >
      <!-- Chat bubble -->
      <path d="M21 15a2 2 0 0 0 2-2V5a2 2 0 0 0-2-2H3a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h4v4l4-4h10z" />
      <!-- Two circles -->
      <circle cx="9" cy="10" r="2" />
      <circle cx="15" cy="10" r="2" />
    </svg>
  </template>
  
  <script setup>
  defineProps({
    isRecording: {
      type: Boolean,
      default: false
    }
  })
  </script>
  