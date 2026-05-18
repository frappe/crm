// Simple Web Audio API ringtone/ringback generator.
// Plays the standard 440Hz+480Hz cadence (2s on / 4s off) used by US/EU PSTN.
// No audio assets needed; works on iOS Safari and Android Chrome.

let ctx = null
let activeNodes = null
let cadenceTimer = null

function ensureContext() {
  if (!ctx) {
    const AC = window.AudioContext || window.webkitAudioContext
    ctx = new AC()
  }
  if (ctx.state === 'suspended') ctx.resume()
  return ctx
}

function playTone() {
  const c = ensureContext()
  const now = c.currentTime
  const gain = c.createGain()
  gain.gain.value = 0.0001
  gain.gain.exponentialRampToValueAtTime(0.15, now + 0.02)
  gain.connect(c.destination)

  const o1 = c.createOscillator()
  o1.frequency.value = 440
  o1.connect(gain)
  const o2 = c.createOscillator()
  o2.frequency.value = 480
  o2.connect(gain)

  o1.start(now)
  o2.start(now)
  return { oscillators: [o1, o2], gain }
}

function stopTone(nodes) {
  if (!nodes) return
  const c = ctx
  if (!c) return
  const now = c.currentTime
  try {
    nodes.gain.gain.cancelScheduledValues(now)
    nodes.gain.gain.setValueAtTime(nodes.gain.gain.value, now)
    nodes.gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.02)
  } catch (_) {}
  nodes.oscillators.forEach((o) => {
    try { o.stop(now + 0.05) } catch (_) {}
  })
}

export function startRinging() {
  stop()
  const cycle = () => {
    activeNodes = playTone()
    cadenceTimer = setTimeout(() => {
      stopTone(activeNodes)
      activeNodes = null
      cadenceTimer = setTimeout(cycle, 4000)
    }, 2000)
  }
  cycle()
}

export function stop() {
  if (cadenceTimer) {
    clearTimeout(cadenceTimer)
    cadenceTimer = null
  }
  if (activeNodes) {
    stopTone(activeNodes)
    activeNodes = null
  }
}
