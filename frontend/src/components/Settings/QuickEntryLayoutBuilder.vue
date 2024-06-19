<template>
  <div
    class="border rounded-xl h-full inline-block w-full transform overflow-hidden bg-white text-left align-middle shadow-xl transition-all"
  >
    <div class="bg-white px-4 pb-6 pt-5 sm:px-6">
      <div class="mb-6 flex items-center justify-between">
        <div class="flex items-center space-x-2">
          <header>
            <h3 class="text-2xl font-semibold leading-6 text-gray-900">
              {{ __('Create Lead') }}
            </h3>
          </header>
        </div>
        <Button icon="x" disabled variant="ghost" />
      </div>
      <div>
        <div v-for="section in sections">
          <div>{{ section.label }}</div>
          <div v-for="field in section.fields">
            <div>{{ field.label }}</div>
          </div>
        </div>
      </div>
    </div>
    <!-- <div class="px-4 pb-7 pt-4 sm:px-6">Actions</div> -->
  </div>
</template>
<script setup>
const props = defineProps({
  sections: Object,
  doctype: String,
})
</script>
