<template>
  <span class="relative inline-flex shrink-0" :class="marginClasses">
    <Avatar
      :label="getUser(user).full_name"
      :image="getUser(user).user_image"
      v-bind="avatarAttrs"
    />
    <AvailabilityDot
      v-if="!hideStatus"
      :user="user"
      class="absolute bottom-0 right-0 ring-2 ring-[--surface-base]"
      :class="dotSize"
    />
  </span>
</template>
<script setup>
import AvailabilityDot from '@/components/AvailabilityDot.vue'
import { usersStore } from '@/stores/users'
import { Avatar } from 'frappe-ui'
import { computed, useAttrs } from 'vue'

defineOptions({ inheritAttrs: false })

defineProps({
  user: { type: String, default: null },
  hideStatus: { type: Boolean, default: false },
})

const { getUser } = usersStore()
const attrs = useAttrs()

// margins space the avatar from its neighbours, so they go on the wrapper the dot is pinned to
const isMargin = (c) => /^-?m[trblxy]?-/.test(c)
const classes = computed(() =>
  typeof attrs.class === 'string' ? attrs.class.split(/\s+/) : [],
)
const marginClasses = computed(() => classes.value.filter(isMargin))
const avatarAttrs = computed(() => ({
  ...attrs,
  class:
    typeof attrs.class === 'string'
      ? classes.value.filter((c) => !isMargin(c))
      : attrs.class,
}))

const dotSizes = {
  xs: '!size-1.5 !ring-1',
  sm: '!size-2',
  md: '!size-2',
  lg: '!size-2.5',
  xl: '!size-2.5',
  '2xl': '!size-3',
}
const dotSize = computed(() => dotSizes[attrs.size] || '!size-2')
</script>
