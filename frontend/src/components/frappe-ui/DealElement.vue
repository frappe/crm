<template>
    <div class="flex gap-2 chip-data">
      <!-- Iterate over deals array and generate HTML for each deal_element -->
      <div
        v-for="(deal, index) in deals"
        :key="index"
        class="chip rounded-full bg-slate-800 py-0.5 px-2.5 border border-transparent text-sm text-white transition-all shadow-sm"
      >
        {{ deal.deal_elements }}
      </div>
    </div>
  </template>
  
  <script>
  export default {
    props: {
      deals: {
        type: Array,
        required: true,
      },
    },
  };
  </script>
