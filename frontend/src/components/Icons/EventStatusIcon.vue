<template>
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="16"
    height="16"
    viewBox="0 0 16 16"
    fill="none"
    class="text-ink-gray-7"
    :aria-label="status"
  >
    <path
      v-if="status == 'Open'"
      fill="currentColor"
      fill-rule="evenodd"
      d="M8 13A5 5 0 1 0 8 3a5 5 0 0 0 0 10Zm0 2A7 7 0 1 0 8 1a7 7 0 0 0 0 14Z"
      clip-rule="evenodd"
    />
    <path
      v-else-if="status == 'Completed'"
      fill="currentColor"
      fill-rule="evenodd"
      d="M8 15A7 7 0 1 0 8 1a7 7 0 0 0 0 14Zm3.173-9.015a.5.5 0 0 0-.772-.636l-3.45 4.183L5.612 7.8a.5.5 0 1 0-.792.612l1.725 2.228a.5.5 0 0 0 .781.013l3.848-4.667Z"
      clip-rule="evenodd"
    />
    <path
      v-else-if="status == 'Closed'"
      fill="currentColor"
      fill-rule="evenodd"
      d="M8 15A7 7 0 1 0 8 1a7 7 0 0 0 0 14Zm3.173-9.015a.5.5 0 0 0-.772-.636l-3.45 4.183L5.612 7.8a.5.5 0 1 0-.792.612l1.725 2.228a.5.5 0 0 0 .781.013l3.848-4.667Z"
      clip-rule="evenodd"
    />
    <path
      v-else-if="status == 'Cancelled'"
      fill="currentColor"
      fill-rule="evenodd"
      clip-rule="evenodd"
      d="M8 15C11.866 15 15 11.866 15 8C15 4.13401 11.866 1 8 1C4.13401 1 1 4.13401 1 8C1 11.866 4.13401 15 8 15ZM5.14645 5.14645C4.95118 5.34171 4.95118 5.65829 5.14645 5.85355L7.29289 8L5.14645 10.1464C4.95118 10.3417 4.95118 10.6583 5.14645 10.8536C5.34171 11.0488 5.65829 11.0488 5.85355 10.8536L8 8.70711L10.1464 10.8536C10.3417 11.0488 10.6583 11.0488 10.8536 10.8536C11.0488 10.6583 11.0488 10.3417 10.8536 10.1464L8.70711 8L10.8536 5.85355C11.0488 5.65829 11.0488 5.34171 10.8536 5.14645C10.6583 4.95118 10.3417 4.95118 10.1464 5.14645L8 7.29289L5.85355 5.14645C5.65829 4.95118 5.34171 4.95118 5.14645 5.14645Z"
    />
  </svg>
</template>
<script setup>
const props = defineProps({
  status: {
    type: String,
    required: true,
  },
})
</script>
