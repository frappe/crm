<!-- frappe-ui's Dropdown on a computer; on a phone the same options in a bottom sheet. -->
<template>
  <template v-if="isPhone">
    <span class="contents" @click.stop="open = true">
      <slot :open="open" />
    </span>
    <BottomSheet v-model:open="open" :title="submenu?.label || title">
      <div class="flex flex-col px-2 pb-8">
        <button
          v-if="submenu"
          type="button"
          class="flex items-center gap-3 rounded-4 px-3 py-2.5 text-start text-p-base text-ink-gray-6 hover:bg-surface-gray-2"
          @click="submenu = null"
        >
          <span class="lucide-chevron-left size-4" aria-hidden="true" />
          {{ __('Back') }}
        </button>
        <section
          v-for="(group, i) in shownGroups"
          :key="i"
          class="flex flex-col"
          :class="{ 'mt-1 border-t border-outline-gray-1 pt-1': i > 0 }"
        >
          <h3
            v-if="group.group && !group.hideLabel"
            class="px-3 pb-1 pt-2 text-sm text-ink-gray-5"
          >
            {{ group.group }}
          </h3>
          <button
            v-for="option in group.options"
            :key="option.label"
            type="button"
            class="flex items-center gap-3 rounded-4 px-3 py-2.5 text-start text-p-base hover:bg-surface-gray-2 disabled:opacity-50"
            :class="
              option.theme === 'red' ? 'text-ink-red-4' : 'text-ink-gray-8'
            "
            :disabled="option.disabled"
            @click="pick(option, $event)"
          >
            <span
              v-if="
                typeof option.icon === 'string' &&
                option.icon.startsWith('lucide-')
              "
              :class="option.icon"
              class="size-4 shrink-0"
              aria-hidden="true"
            />
            <Icon v-else-if="option.icon" :icon="option.icon" class="size-4" />
            <span class="flex min-w-0 flex-1 flex-col gap-0.5">
              <span class="truncate">{{ option.label }}</span>
              <span
                v-if="option.description"
                class="truncate text-sm text-ink-gray-5"
              >
                {{ option.description }}
              </span>
            </span>
            <span
              v-if="option.submenu"
              class="lucide-chevron-right size-4 shrink-0 text-ink-gray-4"
              aria-hidden="true"
            />
            <span
              v-else-if="option.selected"
              class="lucide-check size-4 shrink-0 text-ink-gray-7"
              aria-hidden="true"
            />
          </button>
        </section>
      </div>
    </BottomSheet>
  </template>
  <Dropdown
    v-else
    v-bind="$attrs"
    :options="options"
    @update:open="emit('update:open', $event)"
  >
    <template v-for="(_, name) in $slots" #[name]="slotProps">
      <slot :name="name" v-bind="slotProps || {}" />
    </template>
  </Dropdown>
</template>

<script setup>
import Icon from '@/components/Icon.vue'
import { isPhone, useBackClose } from '@/composables/phone'
import { BottomSheet, Dropdown } from 'frappe-ui'
import { computed, ref, watch } from 'vue'

defineOptions({ inheritAttrs: false })

const props = defineProps({
  options: { type: Array, default: () => [] },
  /** The sheet's title on a phone. */
  title: { type: String, default: '' },
})

const emit = defineEmits(['update:open'])

const open = ref(false)
const submenu = ref(null)

useBackClose(
  () => isPhone.value && open.value,
  () => (open.value = false),
)

watch(open, (isOpen) => {
  if (!isOpen) submenu.value = null
  emit('update:open', isOpen)
})

const shownGroups = computed(() =>
  toGroups(submenu.value ? submenu.value.submenu : props.options),
)

function toGroups(options) {
  const isShown = (option) =>
    option && (!option.condition || option.condition())
  const groups = options.some((option) => option?.group !== undefined)
    ? options.filter(Boolean)
    : [{ group: '', options }]
  return groups
    .map((group) => ({
      ...group,
      options: (group.options || []).filter(isShown),
    }))
    .filter((group) => group.options.length)
}

// An action that calls preventDefault keeps the sheet open, as in the Dropdown (a two-step delete).
function pick(option, event) {
  if (option.submenu) return void (submenu.value = option)
  if (option.switch) option.onClick?.(!option.switchValue)
  else option.onClick?.(event)
  if (!event.defaultPrevented) open.value = false
}
</script>
