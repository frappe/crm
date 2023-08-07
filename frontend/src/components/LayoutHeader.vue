<template>
  <header class="flex justify-between items-center px-5 py-3">
    <div class="flex items-center gap-2">
      <slot name="left-header" />
    </div>
    <div class="flex items-center gap-2">
      <slot name="right-header" class="flex items-center gap-2" />
    </div>
  </header>
  <div
    v-if="$slots['left-subheader'] || $slots['right-subheader']"
    id="sub-header"
    class="flex justify-between items-center px-5 pb-2.5 border-b"
  >
    <div class="flex items-center gap-2">
      <slot name="left-subheader" />
    </div>
    <div class="flex items-center gap-2">
      <slot name="right-subheader" />
    </div>
  </div>
</template>
