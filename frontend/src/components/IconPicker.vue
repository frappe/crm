<template>
  <Popover transition="default">
    <template #target="{ togglePopover, isOpen }">
      <slot v-bind="{ isOpen, togglePopover }">
        <span class="text-base"> {{ modelValue || '' }} </span>
      </slot>
    </template>
    <template #body>
      <div class="my-3 max-w-max transform bg-white px-4 sm:px-0">
        <div
          class="relative max-h-96 overflow-y-auto rounded-lg pb-3 shadow-2xl ring-1 ring-black ring-opacity-5"
        >
          <div class="flex gap-2 px-3 pb-1 pt-3">
            <div class="flex-1">
              <FormControl
                type="text"
                placeholder="Search by keyword"
                v-model="search"
                :debounce="300"
              />
            </div>
            <Button @click="setRandom">Random</Button>
          </div>
          <div class="w-96"></div>
          <div class="px-3" v-for="(emojis, group) in emojiGroups" :key="group">
            <div class="sticky top-0 bg-white pb-2 pt-3 text-sm text-gray-700">
              {{ group }}
            </div>
            <div class="grid w-96 grid-cols-12 place-items-center">
              <button
                class="h-8 w-8 rounded-md p-1 text-2xl hover:bg-gray-100 focus:outline-none focus:ring focus:ring-blue-200"
                v-for="_emoji in emojis"
                :key="_emoji.description"
                @click="emoji = _emoji.emoji"
                :title="_emoji.description"
              >
                {{ _emoji.emoji }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </template>
  </Popover>
</template>
<script setup>
import { gemoji } from 'gemoji'
import { Popover } from 'frappe-ui'
import { ref, computed } from 'vue'

const search = ref('')
const emoji = defineModel()

const emojiGroups = computed(() => {
  let groups = {}
  for (let _emoji of gemoji) {
    if (search.value) {
      let keywords = [_emoji.description, ..._emoji.names, ..._emoji.tags]
        .join(' ')
        .toLowerCase()
      if (!keywords.includes(search.value.toLowerCase())) {
        continue
      }
    }

    let group = groups[_emoji.category]
    if (!group) {
      groups[_emoji.category] = []
      group = groups[_emoji.category]
    }
    group.push(_emoji)
  }
  if (!Object.keys(groups).length) {
    groups['No results'] = []
  }
  return groups
})

function setRandom() {
  let total = gemoji.length
  let index = randomInt(0, total - 1)
  emoji.value = gemoji[index].emoji
}

function randomInt(min, max) {
  return Math.floor(Math.random() * (max - min + 1) + min)
}

defineExpose({ setRandom })
</script>
