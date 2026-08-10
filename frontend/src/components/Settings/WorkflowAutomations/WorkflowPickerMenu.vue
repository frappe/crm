<template>
  <Popover v-model:open="open" :side="side" align="start" bare>
    <template #trigger="{ open: isOpen }">
      <slot :open="isOpen" />
    </template>
    <template #default>
      <div class="flex items-stretch gap-2">
        <div v-if="hint && hinted" class="workflow-picker-hint">
          <div class="workflow-picker-hint-icon">
            <component :is="hinted.icon" class="size-6 text-ink-gray-5" />
          </div>
          <div class="text-base-medium text-ink-gray-8">
            {{ hinted.label }}
          </div>
          <div class="mt-1 text-p-sm text-ink-gray-5">
            {{ hinted.description }}
          </div>
        </div>
        <div class="workflow-picker">
          <input
            ref="search"
            v-model="query"
            class="workflow-picker-search"
            :placeholder="placeholder"
            :aria-label="placeholder"
            @keydown.down.prevent="moveHint(1)"
            @keydown.up.prevent="moveHint(-1)"
            @keydown.enter.prevent="hinted && pick(hinted)"
          />
          <div class="workflow-picker-list">
            <template v-for="group in matches" :key="group.label">
              <div class="workflow-picker-group">{{ group.label }}</div>
              <button
                v-for="option in group.options"
                :key="option.value"
                class="workflow-picker-option"
                :class="{
                  'workflow-picker-option-active': hinted === option,
                }"
                @click="pick(option)"
                @mouseenter="hintedValue = option.value"
                @focus="hintedValue = option.value"
              >
                <component
                  :is="option.icon"
                  class="size-4 shrink-0 text-ink-gray-6"
                />
                <span class="truncate">{{ option.label }}</span>
              </button>
            </template>
            <div v-if="!flattened.length" class="workflow-picker-empty">
              {{ __('Nothing matches that search.') }}
            </div>
          </div>
        </div>
      </div>
    </template>
  </Popover>
</template>

<script setup>
import { Popover } from 'frappe-ui'
import { computed, nextTick, ref, watch } from 'vue'

const props = defineProps({
  groups: { type: Array, default: () => [] },
  placeholder: { type: String, default: '' },
  side: { type: String, default: 'bottom' },
  hint: { type: Boolean, default: false },
})

const emit = defineEmits(['select'])

const open = ref(false)
const query = ref('')
const search = ref(null)
const hintedValue = ref('')

const matches = computed(() =>
  props.groups
    .map((group) => ({ ...group, options: group.options.filter(isMatch) }))
    .filter((group) => group.options.length),
)

const flattened = computed(() =>
  matches.value.flatMap((group) => group.options),
)

const hinted = computed(
  () =>
    flattened.value.find((option) => option.value === hintedValue.value) ||
    flattened.value[0] ||
    null,
)

watch(open, focusSearch)

function isMatch(option) {
  const term = query.value.trim().toLowerCase()
  return !term || String(option.label).toLowerCase().includes(term)
}

async function focusSearch(isOpen) {
  if (!isOpen) return
  query.value = ''
  hintedValue.value = ''
  await nextTick()
  search.value?.focus()
}

/** Arrow keys walk the flattened list so the hint panel keeps up with the keyboard. */
function moveHint(step) {
  const options = flattened.value
  if (!options.length) return
  const next = options.indexOf(hinted.value) + step
  hintedValue.value = options[(next + options.length) % options.length].value
}

function pick(option) {
  open.value = false
  emit('select', option)
}
</script>

<style scoped>
.workflow-picker {
  display: flex;
  width: 260px;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid var(--outline-gray-2);
  border-radius: 10px;
  background: var(--surface-modal);
  box-shadow: 0 8px 24px rgb(0 0 0 / 14%);
}

.workflow-picker-search {
  border: 0;
  border-bottom: 1px solid var(--outline-gray-2);
  background: transparent;
  padding: 10px 12px;
  font-size: 13px;
  color: var(--ink-gray-8);
}

.workflow-picker-search:focus {
  outline: none;
  box-shadow: none;
}

.workflow-picker-list {
  max-height: 288px;
  overflow-y: auto;
  padding: 4px;
}

.workflow-picker-group {
  padding: 8px 8px 4px;
  font-size: 11px;
  font-weight: 500;
  color: var(--ink-gray-5);
}

.workflow-picker-option {
  display: flex;
  width: 100%;
  align-items: center;
  gap: 10px;
  border-radius: 6px;
  padding: 7px 8px;
  font-size: 13px;
  color: var(--ink-gray-8);
  text-align: left;
}

.workflow-picker-option-active {
  background: var(--surface-gray-2);
}

.workflow-picker-empty {
  padding: 12px 8px;
  font-size: 13px;
  color: var(--ink-gray-5);
}

.workflow-picker-hint {
  width: 220px;
  align-self: flex-start;
  border: 1px solid var(--outline-gray-2);
  border-radius: 10px;
  background: var(--surface-modal);
  padding: 16px;
  box-shadow: 0 8px 24px rgb(0 0 0 / 14%);
}

.workflow-picker-hint-icon {
  display: flex;
  height: 40px;
  width: 40px;
  align-items: center;
  justify-content: center;
  margin-bottom: 12px;
  border-radius: 8px;
  background: var(--surface-gray-2);
}
</style>
