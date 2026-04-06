<template>
  <div class="flex gap-3">
    <div
      class="flex-1 rounded-lg border cursor-pointer"
      :class="
        theme == 'light'
          ? 'border-outline-gray-5'
          : 'border-outline-gray-modals'
      "
      @click="theme = 'light'"
    >
      <div class="pl-5 pt-3.5 bg-surface-gray-2 rounded-t-[10.5px]">
        <div class="bg-white rounded-tl-sm">
          <div class="flex gap-[3px] py-[3px] px-1 border-b border-gray-100">
            <div class="size-1.5 bg-[#FF5F57] rounded-full"></div>
            <div class="size-1.5 bg-[#FEBC2D] rounded-full"></div>
            <div class="size-1.5 bg-[#28C840] rounded-full"></div>
          </div>
          <div class="flex items-start justify-between gap-2 p-2.5 pr-0 pb-1">
            <div
              class="flex items-center flex-1 gap-1 text-xs text-ink-gray-5 font-semibold"
            >
              <img
                v-if="typeof logo == 'string'"
                :src="logo"
                class="size-5 object-cover"
              />
              <component :is="logo" v-else class="size-5 shrink-0 rounded" />
              <div>{{ __(name) }}</div>
            </div>
            <div class="flex flex-col flex-1 gap-[5px]">
              <div class="bg-gray-100 w-full h-1.5"></div>
              <div class="bg-gray-100 w-full h-1.5"></div>
              <div class="bg-gray-100 w-full h-1.5"></div>
            </div>
          </div>
        </div>
      </div>
      <div class="flex items-center justify-between px-3 py-2 border-t">
        <div class="text-base text-ink-gray-7">
          {{ __('Light') }}
        </div>
        <div
          class="rounded-full size-3.5"
          :class="
            theme == 'light'
              ? 'border-4 border-outline-gray-5'
              : 'border  border-outline-gray-4'
          "
        />
      </div>
    </div>
    <div
      class="flex-1 rounded-lg border cursor-pointer"
      :class="
        theme == 'dark' ? 'border-outline-gray-5' : 'border-outline-gray-modals'
      "
      @click="theme = 'dark'"
    >
      <div class="pl-5 pt-3.5 bg-surface-gray-2 rounded-t-[10.5px]">
        <div class="bg-gray-900 rounded-tl-sm">
          <div class="flex gap-[3px] py-[3px] px-1 border-b border-gray-800">
            <div class="size-1.5 bg-[#FF5F57] rounded-full"></div>
            <div class="size-1.5 bg-[#FEBC2D] rounded-full"></div>
            <div class="size-1.5 bg-[#28C840] rounded-full"></div>
          </div>
          <div class="flex items-start justify-between gap-2 p-2.5 pr-0 pb-1">
            <div
              class="flex items-center flex-1 gap-1 text-xs text-ink-gray-5 font-semibold"
            >
              <img
                v-if="typeof logo == 'string'"
                :src="logo"
                class="size-5 object-cover"
              />
              <component :is="logo" v-else class="size-5 shrink-0 rounded" />
              <div>{{ __(name) }}</div>
            </div>
            <div class="flex flex-col flex-1 gap-[5px]">
              <div class="bg-gray-800 w-full h-1.5"></div>
              <div class="bg-gray-800 w-full h-1.5"></div>
              <div class="bg-gray-800 w-full h-1.5"></div>
            </div>
          </div>
        </div>
      </div>
      <div class="flex items-center justify-between px-3 py-2 border-t">
        <div class="text-base text-ink-gray-7">
          {{ __('Dark') }}
        </div>
        <div
          class="rounded-full size-3.5"
          :class="
            theme == 'dark'
              ? 'border-4 border-outline-gray-5'
              : 'border border-outline-gray-4'
          "
        />
      </div>
    </div>
    <div
      class="flex-1 rounded-lg border cursor-pointer"
      :class="
        theme == 'system'
          ? 'border-outline-gray-5'
          : 'border-outline-gray-modals'
      "
      @click="theme = 'system'"
    >
      <div class="flex">
        <div
          class="flex flex-1 pl-5 pt-3.5 bg-surface-gray-2 rounded-tl-[10.5px]"
        >
          <div class="bg-white rounded-tl-sm w-full">
            <div class="flex gap-[3px] py-[3px] px-1 border-b border-gray-100">
              <div class="size-1.5 bg-[#FF5F57] rounded-full"></div>
              <div class="size-1.5 bg-[#FEBC2D] rounded-full"></div>
              <div class="size-1.5 bg-[#28C840] rounded-full"></div>
            </div>
            <div class="flex items-start justify-between gap-2 p-2.5 pr-0 pb-1">
              <div
                class="flex items-center flex-1 gap-1 text-xs text-ink-gray-5 font-semibold"
              >
                <img
                  v-if="typeof logo == 'string'"
                  :src="logo"
                  class="size-5 object-cover"
                />
                <component :is="logo" v-else class="size-5 shrink-0 rounded" />
                <div>{{ __(name) }}</div>
              </div>
            </div>
          </div>
        </div>
        <div
          class="flex flex-1 pl-5 pt-3.5 bg-surface-gray-3 rounded-tr-[10.5px]"
        >
          <div class="bg-gray-900 rounded-tl-sm w-full">
            <div class="flex gap-[3px] py-[3px] px-1 border-b border-gray-800">
              <div class="size-1.5 bg-[#FF5F57] rounded-full"></div>
              <div class="size-1.5 bg-[#FEBC2D] rounded-full"></div>
              <div class="size-1.5 bg-[#28C840] rounded-full"></div>
            </div>
            <div class="flex items-start justify-between gap-2 p-2.5 pb-3 pr-0">
              <div
                class="flex items-center flex-1 gap-1 text-xs text-ink-gray-5 font-semibold"
              >
                <img
                  v-if="typeof logo == 'string'"
                  :src="logo"
                  class="size-5 object-cover"
                />
                <component :is="logo" v-else class="size-5 shrink-0 rounded" />
                <div>{{ __(name) }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="flex items-center justify-between px-3 py-2 border-t">
        <div class="text-base text-ink-gray-7">
          {{ __('System') }}
        </div>
        <div
          class="rounded-full size-3.5"
          :class="
            theme == 'system'
              ? 'border-4 border-outline-gray-5'
              : 'border border-outline-gray-4'
          "
        ></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useTheme } from 'frappe-ui'
import { computed } from 'vue'

defineProps({
  logo: { type: [String, Object], default: '' },
  name: { type: String, default: '' },
})

const { currentTheme, setTheme } = useTheme()

const theme = computed({
  get() {
    if (currentTheme.value === 'light') return 'light'
    if (currentTheme.value === 'dark') return 'dark'
    return 'system'
  },
  set(value) {
    setTheme(value)
  },
})
</script>
