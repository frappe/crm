<template>
  <aside class="border-l border-outline-gray-2" aria-hidden="true" inert>
    <SetupScene :step="scene" :fx="FX" class="h-full w-full" />
  </aside>
</template>

<script setup>
import SetupScene from '@/components/Setup/SetupScene.vue'
import { computed } from 'vue'

const props = defineProps({
  step: { type: String, required: true },
  state: { type: Object, required: true },
})

const FX = ['shimmer', 'sheen', 'ripple', 'toast']

const SCENES = {
  connect_email: 'email',
  bring_leads: 'leads',
  invite_team: 'team',
}

const scene = computed(() => SCENES[props.step] || 'email')
</script>
