<template>
  <router-link custom :to="link.route" v-slot="{ href, isActive, navigate }">
    <a
      :href="href"
      @click="navigate"
      :class="[isActive ? active : inactive, $attrs.class]"
    >
      <slot :link="link">
        {{ link.name }}
      </slot>
    </a>
  </router-link>
</template>
<script setup>
const props = defineProps(['link', 'active', 'inactive'])
</script>
