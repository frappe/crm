<template>
  <div>
    <Button
      class="flex justify-between w-full rounded text-base"
      variant="ghost"
      :label="label"
      @click="onClick"
    >
      <template v-if="active" #suffix>
        <FeatherIcon class="size-4" name="check" />
      </template>
    </Button>
  </div>
</template>
<script setup>
defineProps({
  label: { type: String, default: '' },
  active: { type: Boolean, default: false },
  onClick: { type: Function, default: () => {} },
})
</script>
