<template>
  <Teleport to="#header-area">
    <header class="flex justify-between items-center px-5 py-3">
      <div class="flex items-center gap-2">
        <slot name="left-header" />
      </div>
      <div class="flex items-center gap-2">
        <slot name="right-header" class="flex items-center gap-2" />
        <slot name="call-area"></slot>
      </div>
    </header>
  </Teleport>
</template>
