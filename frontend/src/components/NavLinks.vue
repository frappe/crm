<template>
  <NavLink
    v-for="link in links"
    :key="link.name"
    :class="$attrs.class"
    v-bind="{ link, active, inactive }"
  >
    <slot :link="link">
      {{ link.name }}
    </slot>
  </NavLink>
</template>
<script setup>
import NavLink from './NavLink.vue'

const props = defineProps(['links', 'active', 'inactive'])
</script>
