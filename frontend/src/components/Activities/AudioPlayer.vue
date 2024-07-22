<template>
  <div class="w-full text-sm text-gray-600">
    <div class="flex items-center gap-2">
      <Button variant="ghost" @click="playPause">
        <template #icon>
          <PlayIcon v-if="isPaused" class="size-4 text-gray-600" />
          <PauseIcon v-else class="size-4 text-gray-600" />
        </template>
      </Button>
      <div class="flex gap-2 items-center justify-between flex-1">
        <input
          class="w-full slider !h-[0.5] bg-gray-200 [&::-webkit-slider-thumb]:shadow [&::-webkit-slider-thumb:hover]:outline [&::-webkit-slider-thumb:hover]:outline-[0.5px]"
          :style="{
            background: `linear-gradient(to right, #171717 ${progress}%, #ededed ${progress}%)`,
          }"
          type="range"
          id="track"
          min="0"
          :max="duration"
          :value="currentTime"
          step="0.01"
          @input="(e) => (audio.currentTime = e.target.value)"
        />
        <div class="shrink-0">
          {{ formatTime(currentTime) }} / {{ formatTime(duration) }}
        </div>
      </div>
      <div class="flex items-center gap-1">
        <div class="flex group gap-2 items-center">
          <input
            class="slider opacity-0 group-hover:opacity-100 w-0 group-hover:w-20 !h-[0.5] [&::-webkit-slider-thumb]:shadow [&::-webkit-slider-thumb:hover]:outline [&::-webkit-slider-thumb:hover]:outline-[0.5px]"
            :style="{
              background: `linear-gradient(to right, #171717 ${volumnProgress}%, #ededed ${volumnProgress}%)`,
            }"
            type="range"
            id="volume"
            min="0"
            max="1"
            :value="currentVolumn"
            step="0.01"
            @input="(e) => updateVolumnProgress(e.target.value)"
          />
          <Button variant="ghost">
            <template #icon>
              <MuteIcon
                v-if="volumnProgress == 0"
                class="size-4"
                @click="updateVolumnProgress('1')"
              />
              <VolumnLowIcon
                v-else-if="volumnProgress <= 40"
                class="size-4"
                @click="updateVolumnProgress('0')"
              />
              <VolumnHighIcon
                v-else-if="volumnProgress > 20"
                class="size-4"
                @click="updateVolumnProgress('0')"
              />
            </template>
          </Button>
        </div>
        <Dropdown :options="options">
          <Button variant="ghost" @click="showPlaybackSpeed = false">
            <template #icon>
              <FeatherIcon class="size-4" name="more-horizontal" />
            </template>
          </Button>
        </Dropdown>
      </div>
    </div>

    <audio
      ref="audio"
      :src="src"
      crossorigin="anonymous"
      @loadedmetadata="setupDuration"
      @timeupdate="updateCurrentTime"
      @ended="isPaused = true"
    ></audio>
  </div>
</template>

<script setup>
import PlayIcon from '@/components/Icons/PlayIcon.vue'
import PauseIcon from '@/components/Icons/PauseIcon.vue'
import VolumnLowIcon from '@/components/Icons/VolumnLowIcon.vue'
import VolumnHighIcon from '@/components/Icons/VolumnHighIcon.vue'
import MuteIcon from '@/components/Icons/MuteIcon.vue'
import PlaybackSpeedIcon from '@/components/Icons/PlaybackSpeedIcon.vue'
import PlaybackSpeedOption from '@/components/Activities/PlaybackSpeedOption.vue'
import Dropdown from '@/components/frappe-ui/Dropdown.vue'
import { computed, h, ref } from 'vue'

const props = defineProps({
  src: String,
})

const audio = ref(null)
const isPaused = ref(true)

const duration = ref(0)
const currentTime = ref(0)
const progress = computed(() => (currentTime.value / duration.value) * 100)
const currentVolumn = ref(1)
const volumnProgress = ref(100)

function setupDuration() {
  duration.value = audio.value.duration
}

function updateCurrentTime() {
  currentTime.value = audio.value.currentTime
}

function playPause() {
  if (audio.value.paused) {
    audio.value.play()
    isPaused.value = false
  } else {
    audio.value.pause()
    isPaused.value = true
  }
}

function formatTime(time) {
  if (isNaN(time)) return '00:00'
  const minutes = Math.floor(time / 60)
  const seconds = Math.floor(time % 60)
  return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
}

function updateVolumnProgress(value) {
  audio.value.volume = value
  currentVolumn.value = value
  volumnProgress.value = value * 100
}

const showPlaybackSpeed = ref(false)
const currentPlaybackSpeed = ref(1)

const options = computed(() => {
  let playbackSpeeds = [0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2]

  let playbackSpeedOptions = playbackSpeeds.map((speed) => {
    let label = `${speed}x`
    if (speed === 1) {
      label = __('Normal')
    }
    return {
      component: () =>
        h(PlaybackSpeedOption, {
          label,
          active: speed === currentPlaybackSpeed.value,
          onClick: () => {
            audio.value.playbackRate = speed
            showPlaybackSpeed.value = false
            currentPlaybackSpeed.value = speed
          },
        }),
    }
  })
  let _options = [
    {
      icon: 'download',
      label: __('Download'),
      onClick: () => {
        const a = document.createElement('a')
        a.href = props.src
        a.download = props.src.split('/').pop()
        a.click()
      },
    },
    {
      icon: () => h(PlaybackSpeedIcon, { class: 'size-4' }),
      label: __('Playback speed'),
      onClick: (e) => {
        e.preventDefault()
        e.stopPropagation()
        showPlaybackSpeed.value = true
      },
    },
  ]

  return showPlaybackSpeed.value ? playbackSpeedOptions : _options
})
</script>

<style scoped>
.slider {
  --trackHeight: 2px;
  --thumbRadius: 14px;
  -webkit-appearance: none;
  appearance: none;
  background: transparent;
  padding: 0;
  margin: 0;
  border-radius: 100px;
  cursor: pointer;
}

.slider::-webkit-slider-runnable-track {
  appearance: none;
  height: var(--trackHeight);
  border-radius: 100px;
}

.slider:focus-visible {
  outline: none;
}

.slider::-webkit-slider-thumb {
  width: var(--thumbRadius);
  height: var(--thumbRadius);
  margin-top: calc((var(--trackHeight) - var(--thumbRadius)) / 2);
  background: #fff;
  border-radius: 100px;
  pointer-events: all;
  appearance: none;
  z-index: 1;
}

.slider::-webkit-slider-thumb {
  width: var(--thumbRadius);
  height: var(--thumbRadius);
  margin-top: calc((var(--trackHeight) - var(--thumbRadius)) / 2);
  background: #fff;
  border-radius: 100px;
  pointer-events: all;
  appearance: none;
  z-index: 1;
}
</style>
