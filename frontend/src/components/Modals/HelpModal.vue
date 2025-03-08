<template>
  <div
    v-show="show"
    class="fixed z-20 w-80 h-[calc(100%_-_80px)] text-ink-gray-9 m-5 mt-[62px] p-3 flex gap-2 flex-col rounded-lg bg-surface-modal shadow-2xl"
    :class="[minimize ? 'right-0 top-[calc(100%_-_110px)]' : 'right-0']"
    @click.stop
  >
    <div class="flex justify-between">
      <div></div>
      <div>
        <Button @click="minimize = !minimize" variant="ghost">
          <MaximizeIcon v-if="minimize" class="h-3.5 w-3.5" />
          <MinimizeIcon v-else class="h-3.5 w-3.5" />
        </Button>
        <Button variant="ghost" @click="show = false">
          <FeatherIcon name="x" class="h-3.5" />
        </Button>
      </div>
    </div>
  </div>
</template>
<script setup>
import MinimizeIcon from '@/components/Icons/MinimizeIcon.vue'
import MaximizeIcon from '@/components/Icons/MaximizeIcon.vue'
import { ref } from 'vue'

const show = defineModel()
const minimize = ref(false)
</script>
