import { getBilling } from '@frappe/cloud-sdk/api'
import { computed, ref, watch } from 'vue'
import {
  cloudSettingsOpen,
  isCloudSettingsAvailable,
} from '@/composables/cloudSettings'

const CACHE_MS = 6 * 60 * 60 * 1000
const DISMISS_MS = 24 * 60 * 60 * 1000
const CACHE_KEY = 'crm-trial-card'
const DISMISS_KEY = 'crm-trial-card-dismissed-at'

function readCache() {
  try {
    return JSON.parse(localStorage.getItem(CACHE_KEY) ?? 'null')
  } catch {
    return null
  }
}

const isFresh = (cached) => cached && Date.now() - cached.fetchedAt < CACHE_MS

async function loadTrial() {
  const { trial } = await getBilling()
  const cached = { trial: trial ?? null, fetchedAt: Date.now() }
  try {
    localStorage.setItem(CACHE_KEY, JSON.stringify(cached))
  } catch {
    // storage blocked, the next load fetches again
  }
  return cached.trial
}

// Overlapping callers share one request
let pending = null
function fetchTrial() {
  pending ??= loadTrial().finally(() => (pending = null))
  return pending
}

function isDismissed() {
  try {
    return (
      Date.now() - Number(localStorage.getItem(DISMISS_KEY) ?? 0) < DISMISS_MS
    )
  } catch {
    return false
  }
}

export function useTrialCard() {
  const enabled = isCloudSettingsAvailable()
  const cached = readCache()
  // A stale trial stays on screen if the refresh fails
  const trial = ref(cached?.trial ?? null)
  const dismissed = ref(isDismissed())

  const refresh = () =>
    fetchTrial()
      .then((value) => (trial.value = value))
      .catch(() => {})

  if (enabled && !isFresh(cached)) refresh()

  // Choosing a plan in the billing dialog ends the trial
  watch(cloudSettingsOpen, (open, wasOpen) => {
    if (wasOpen && !open && enabled) refresh()
  })

  function dismiss() {
    try {
      localStorage.setItem(DISMISS_KEY, String(Date.now()))
    } catch {
      // storage blocked, the card stays hidden until the next load
    }
    dismissed.value = true
  }

  // An ended trial cannot be dismissed
  const visibleTrial = computed(() => {
    if (!enabled || !trial.value) return null
    if (dismissed.value && trial.value.state !== 'Ended') return null
    return trial.value
  })

  return { trial: visibleTrial, dismiss }
}
