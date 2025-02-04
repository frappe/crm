<template>
  <header class="flex h-14 items-center justify-between border-b bg-white px-4">
    <div class="flex items-center gap-3">
      <slot name="left"></slot>
    </div>
    <div class="flex-1 text-center">
      <h1 class="text-base font-medium text-gray-900">
        <slot name="title"></slot>
      </h1>
    </div>
    <div class="flex items-center gap-3">
      <slot name="right"></slot>
    </div>
  </header>
</template> 