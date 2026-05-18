// Web Audio ringtone/ringback generator.
// Plays a warbling two-frequency tone (classic phone-ring sound) in a
// 2s-on / 4s-off cadence — the standard US/EU PSTN ring pattern.
//
// Mobile autoplay handling: AudioContext can't start a tone without a prior
// user gesture. We unlock it on the first click/touch anywhere on the page,
// so incoming-call rings work even when the user hasn't interacted recently.

let ctx = null
let masterGain = null
let activeOscillators = []
let cadenceTimer = null
let unlockListenerAdded = false
let vibrateInterval = null

function getContext() {
  if (!ctx) {
    const AC = window.AudioContext || window.webkitAudioContext
    if (!AC) return null
    ctx = new AC()
    masterGain = ctx.createGain()
    masterGain.gain.value = 0
    masterGain.connect(ctx.destination)
  }
  return ctx
}

function ensureUnlocked() {
  if (unlockListenerAdded) return
  unlockListenerAdded = true
  const unlock = () => {
    const c = getContext()
    if (c && c.state === 'suspended') c.resume().catch(() => {})
  }
  // Unlock on the next user interaction.
  ['click', 'touchstart', 'keydown'].forEach((ev) => {
    window.addEventListener(ev, unlock, { passive: true, once: true })
  })
}

// Call this once at app start so the audio context is primed by the time
// an incoming call arrives.
export function prime() {
  ensureUnlocked()
}

function playRing() {
  const c = getContext()
  if (!c) return
  if (c.state === 'suspended') c.resume().catch(() => {})

  const now = c.currentTime
  // Volume envelope: quick fade in, hold, fade out — avoids harsh clicks.
  masterGain.gain.cancelScheduledValues(now)
  masterGain.gain.setValueAtTime(0.0001, now)
  masterGain.gain.exponentialRampToValueAtTime(0.25, now + 0.05)
  masterGain.gain.setValueAtTime(0.25, now + 1.9)
  masterGain.gain.exponentialRampToValueAtTime(0.0001, now + 2.0)

  // Two simultaneous sine tones at 440 + 480 Hz, slightly detuned by an LFO
  // for the warble that makes it sound like a real phone.
  const lfo = c.createOscillator()
  lfo.frequency.value = 20
  const lfoGain = c.createGain()
  lfoGain.gain.value = 3
  lfo.connect(lfoGain)

  const o1 = c.createOscillator()
  o1.type = 'sine'
  o1.frequency.value = 440
  lfoGain.connect(o1.frequency)
  o1.connect(masterGain)

  const o2 = c.createOscillator()
  o2.type = 'sine'
  o2.frequency.value = 480
  lfoGain.connect(o2.frequency)
  o2.connect(masterGain)

  lfo.start(now)
  o1.start(now)
  o2.start(now)
  const stopAt = now + 2.05
  lfo.stop(stopAt)
  o1.stop(stopAt)
  o2.stop(stopAt)

  activeOscillators = [lfo, o1, o2]
}

// Optional custom ringtone file. Drop an MP3 at
// `frontend/public/sounds/ringtone.mp3` and it will be used in place of the
// synthesized tone. Falls back silently if the file isn't present.
const CUSTOM_RINGTONE_URL = '/assets/crm/frontend/sounds/ringtone.mp3'
let customAudio = null

function tryCustomAudio() {
  if (!customAudio) {
    customAudio = new Audio(CUSTOM_RINGTONE_URL)
    customAudio.loop = true
    customAudio.preload = 'auto'
  }
  return customAudio.play()
    .then(() => true)
    .catch(() => false)
}

export function startRinging() {
  stop()
  ensureUnlocked()

  // Try the custom MP3 first; if it isn't there (404) or autoplay is blocked,
  // fall back to the synthesized tone.
  tryCustomAudio().then((ok) => {
    if (ok) return
    const cycle = () => {
      playRing()
      cadenceTimer = setTimeout(cycle, 6000)
    }
    cycle()
  })

  // Phone-style vibration on mobile if available.
  if (typeof navigator !== 'undefined' && typeof navigator.vibrate === 'function') {
    // pattern: vibrate 1s, pause 1s, repeat
    try { navigator.vibrate([1000, 1000, 1000, 1000, 1000]) } catch (_) {}
    vibrateInterval = setInterval(() => {
      try { navigator.vibrate([1000, 1000, 1000, 1000, 1000]) } catch (_) {}
    }, 5000)
  }
}

export function stop() {
  if (customAudio) {
    try {
      customAudio.pause()
      customAudio.currentTime = 0
    } catch (_) {}
  }
  if (cadenceTimer) {
    clearTimeout(cadenceTimer)
    cadenceTimer = null
  }
  if (vibrateInterval) {
    clearInterval(vibrateInterval)
    vibrateInterval = null
    try { navigator.vibrate(0) } catch (_) {}
  }
  if (masterGain && ctx) {
    try {
      const now = ctx.currentTime
      masterGain.gain.cancelScheduledValues(now)
      masterGain.gain.setValueAtTime(masterGain.gain.value, now)
      masterGain.gain.exponentialRampToValueAtTime(0.0001, now + 0.02)
    } catch (_) {}
  }
  activeOscillators.forEach((o) => {
    try { o.stop() } catch (_) {}
    try { o.disconnect() } catch (_) {}
  })
  activeOscillators = []
}
