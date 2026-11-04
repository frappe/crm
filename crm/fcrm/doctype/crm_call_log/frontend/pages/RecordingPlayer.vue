<!-- A call recording player from frappe-ui parts. The length comes from the
call, so nothing moves when the audio loads. -->
<template>
	<div class="flex h-9 items-center gap-2 rounded-4 bg-surface-gray-2 pl-1 pr-3">
		<Button
			variant="ghost"
			:icon="playing ? 'lucide-pause' : 'lucide-play'"
			:tooltip="failed ? __('Recording not available') : playing ? __('Pause') : __('Play recording')"
			:aria-label="playing ? __('Pause') : __('Play recording')"
			:disabled="failed"
			@click="toggle"
		/>
		<Slider
			v-model="position"
			:aria-label="__('Seek recording')"
			class="min-w-0 flex-1"
			:max="length"
			:step="1"
			:disabled="failed"
			@value-commit="seek"
		/>
		<span class="w-[5.5rem] shrink-0 text-right text-p-sm tabular-nums text-ink-gray-6">
			{{ clock(position[0]) }} / {{ clock(length) }}
		</span>
		<audio
			ref="audio"
			:src="src"
			preload="none"
			@timeupdate="tick"
			@loadedmetadata="measured = Math.round(audio.duration) || 0"
			@ended="playing = false"
			@error="onError"
		/>
	</div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { Button, Slider } from 'frappe-ui'
import { __ } from 'frappe/i18n'
import { clock } from './callFormat.js'

const props = defineProps({
	src: { type: String, required: true },
	duration: { type: Number, default: 0 },
})

const audio = ref(null)
const playing = ref(false)
const failed = ref(false)
const position = ref([0])
// A call with no length of its own (a voicemail) takes it from the audio once that loads.
const measured = ref(0)
const length = computed(() => Math.max(1, Math.round(props.duration) || measured.value))

function toggle() {
	if (playing.value) audio.value.pause()
	else audio.value.play().catch(onError)
	playing.value = !playing.value
}
function tick() {
	position.value = [Math.round(audio.value.currentTime)]
}
function seek([t]) {
	if (audio.value) audio.value.currentTime = t
}
function onError() {
	playing.value = false
	failed.value = true
}
</script>
