<template>
  <div class="w-full max-w-6xl mx-auto p-3 sm:p-6">
    <Transition name="fade">
      <div v-if="fcrmSettings.loading" class="mb-4 text-center">
        <div class="inline-flex items-center gap-2 px-3 py-2 bg-blue-50 text-blue-700 rounded-lg text-sm">
          <div class="animate-spin w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full"></div>
          Loading pipeline settings...
        </div>
      </div>
    </Transition>
    <Transition name="fade" appear>
      <div class="bg-white rounded-lg border shadow-sm">
        <!-- Mobile View: Single Horizontal Line -->
        <div class="block sm:hidden">
          <!-- Compact Header with Summary -->
          <div class="flex items-center justify-between p-3 border-b border-gray-100">
            <div class="flex items-center gap-2">
              <TrendingUp class="w-4 h-4 text-blue-600" />
              <span class="text-sm font-bold">SPANCO</span>
            </div>
            <div class="flex items-center gap-3 text-xs">
              <div class="text-center">
                <div class="text-gray-500">Total</div>
                <div class="font-bold text-emerald-600">
                  <CountUp :end-val="totalPipelineValue" :format="true" :prefix="'$'" />
                </div>
              </div>
              <div class="text-center">
                <div class="text-gray-500">Rate</div>
                <div class="font-bold text-green-600">
                  <CountUp :end-val="parseFloat(overallConversionRate)" :decimals="1" :suffix="'%'" />
                </div>
              </div>
            </div>
          </div>

          <!-- Single Line Stages -->
          <div class="p-2">
            <div class="flex w-full h-12 rounded-lg overflow-hidden shadow-sm border">
              <TransitionGroup name="mobile-stage">
                <div
                  v-for="(stage, index) in spancoData"
                  :key="stage.stage"
                  :class="[stage.color, 'mobile-stage-segment']"
                  :style="{ width: `${Math.max(stage.percent * 0.85, 10)}%` }"
                  @click="gotoView(stage.view)"
                  @touchstart="toggleStageDetails(stage.stage)"
                >
                  <div class="flex items-center justify-center h-full px-1 text-white">
                    <div class="text-center">
                      <div class="text-xs font-bold">{{ stage.stage }}</div>
                      <div class="text-xs opacity-90 leading-tight">
                        <CountUp :end-val="stage.number" :format="true" />
                      </div>
                    </div>
                  </div>

                  <!-- Separator -->
                  <div
                    v-if="index < spancoData.length - 1"
                    class="absolute right-0 top-1 bottom-1 w-px bg-white/30"
                  ></div>
                </div>
              </TransitionGroup>
            </div>

            <!-- Stage Details Row -->
            <div class="mt-2 grid grid-cols-6 gap-1 text-xs">
              <div
                v-for="(stage, index) in spancoData"
                :key="`detail-${stage.stage}`"
                class="text-center"
              >
                <div class="font-medium text-gray-700 truncate">{{ stage.fullName }}</div>
                <div class="text-gray-500">{{ stage.percent }}%</div>
                <div class="font-semibold text-gray-800">{{ formatCurrency(stage.valuation) }}</div>
              </div>
            </div>
          </div>

          <!-- Expandable Details Overlay -->
          <Transition name="expand-overlay">
            <div v-if="expandedStages.length > 0" class="absolute inset-0 bg-black/90 z-50 p-4 rounded-lg">
              <div v-for="stage in expandedStages" :key="`expanded-${stage}`" class="text-white">
                <div class="flex justify-between items-center mb-4">
                  <h3 class="text-lg font-bold">{{ getStageData(stage).fullName }}</h3>
                  <button @click="toggleStageDetails(stage)" class="text-white/60 hover:text-white">
                    ✕
                  </button>
                </div>

                <div class="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <div class="text-white/70">Active Deals</div>
                    <div class="text-xl font-bold">
                      <CountUp :end-val="getStageData(stage).number" />
                    </div>
                  </div>
                  <div>
                    <div class="text-white/70">Total Value</div>
                    <div class="text-xl font-bold">{{ formatCurrency(getStageData(stage).valuation) }}</div>
                  </div>
                  <div>
                    <div class="text-white/70">Conversion Rate</div>
                    <div class="text-xl font-bold">{{ getStageData(stage).percent }}%</div>
                  </div>
                  <div>
                    <div class="text-white/70">Avg Deal Size</div>
                    <div class="text-xl font-bold">
                      {{ formatCurrency(Math.round(getStageData(stage).valuation / getStageData(stage).number)) }}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </Transition>
        </div>

        <!-- Desktop Header -->
        <div class="hidden sm:block p-4 sm:p-6 pb-3 sm:pb-4">
          <h2 class="text-lg sm:text-xl font-bold flex items-center gap-2">
            <TrendingUp class="w-4 h-4 sm:w-5 sm:h-5" />
            SPANCO Sales Pipeline
          </h2>
        </div>

        <!-- Desktop Content -->
        <div class="hidden sm:block px-4 sm:px-6 pb-4 sm:pb-6">
          <div class="w-full">
            <!-- Desktop/Tablet View: Original Horizontal Bar (Preserved) -->
            <div class="flex w-full h-20 sm:h-24 rounded-lg overflow-hidden shadow-lg border">
              <TransitionGroup name="spanco-stage">
                <div
                  v-for="(stage, index) in spancoData"
                  :key="stage.stage"
                  :class="[stage.color, stage.textColor, 'flex flex-col justify-center items-center relative stage-block']"
                  :style="{
                    width: `${Math.max(stage.percent * 0.8, 12)}%`,
                    minWidth: index === spancoData.length - 1 ? '100px' : '80px'
                  }"
                  @click="gotoView(stage.view)"
                >
                  <!-- Stage Letter with Animation -->
                  <Transition name="bounce" appear>
                    <div class="text-sm sm:text-lg font-bold mb-1">{{ stage.stage }}</div>
                  </Transition>

                  <!-- Stage Name -->
                  <div class="text-xs font-medium mb-1 text-center leading-tight hidden sm:block">{{ stage.fullName }}</div>

                  <!-- Metrics with Counter Animation -->
                  <div class="text-xs text-center leading-tight">
                    <div class="font-semibold text-xs sm:text-sm">
                      <CountUp :end-val="stage.number" :format="true" />
                    </div>
                    <div class="opacity-90 text-xs">
                      {{ stage.percent }}%<span class="hidden sm:inline"> • {{ formatCurrency(stage.valuation) }}</span>
                    </div>
                  </div>

                  <!-- Separator Line -->
                  <div
                    v-if="index < spancoData.length - 1"
                    class="absolute right-0 top-2 bottom-2 w-px bg-white/30"
                  ></div>
                </div>
              </TransitionGroup>
            </div>

            <!-- Desktop Summary Information (Preserved) -->
            <Transition name="slide-up" appear>
              <div class="mt-4 bg-gray-50 rounded-lg p-3">
                <div class="flex justify-between items-center text-sm text-gray-600">
                  <div class="flex items-center gap-4 lg:gap-6">
                    <div>
                      <span class="font-medium">Total Pipeline:</span>
                      <CountUp :end-val="totalPipelineValue" :format="true" :prefix="'$'" />
                    </div>
                    <div>
                      <span class="font-medium">Conversion Rate:</span>
                      <CountUp :end-val="parseFloat(overallConversionRate)" :decimals="1" :suffix="'%'" />
                    </div>
                    <div>
                      <span class="font-medium">Total Suspects:</span>
                      <CountUp :end-val="spancoData[0].number" :format="true" />
                    </div>
                  </div>
                  <div class="text-xs text-gray-500 hidden lg:block">S-P-A-N-C-O Pipeline</div>
                </div>
              </div>
            </Transition>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted, defineComponent, watch, nextTick } from 'vue'
import { TrendingUp } from 'lucide-vue-next'
import { Transition, TransitionGroup } from 'vue'
import {createResource} from "frappe-ui";
import { useRouter } from 'vue-router'


const router = useRouter()
// Expanded stages for mobile view
const expandedStages = ref([])


const toggleStageDetails = (stage) => {
  if (expandedStages.value.includes(stage)) {
    expandedStages.value = []
  } else {
    expandedStages.value = [stage]
  }
}

const getStageData = (stageKey) => {
  return spancoData.value.find(stage => stage.stage === stageKey)
}

const viewResources = ref(new Map())

function getOrCreateViewResource(viewId) {
  if (!viewId) return null
  
  if (!viewResources.value.has(viewId)) {
    const resource = createResource({
      url: 'frappe.client.get',
      params: { doctype: 'CRM View Settings', name: viewId },
      cache: ['fcrmView', viewId],
      auto: true,
      onError: (err) => {
        console.error(`Failed to load view ${viewId}:`, err)
      }
    })
    viewResources.value.set(viewId, resource)
  }
  
  return viewResources.value.get(viewId)
}

function parseView(viewId) {
  const resource = getOrCreateViewResource(viewId)
  if (!resource?.data) return null
  
  const view = resource.data
  if (!view || !view.route_name) {
    console.warn(`View ${viewId} not found or invalid`)
    return null
  }
  
  return {
    label: view.label,
    to: {
      name: view.route_name,
      params: { viewType: view.type || 'list' },
      query: { view: view.name },
    },
  }
}


// CountUp component for animated number transitions
const CountUp = defineComponent({
  props: {
    endVal: { type: Number, required: true },
    duration: { type: Number, default: 1500 },
    decimals: { type: Number, default: 0 },
    format: { type: Boolean, default: false },
    prefix: { type: String, default: '' },
    suffix: { type: String, default: '' }
  },
  setup(props) {
    const current = ref(0)
    const isAnimating = ref(false)
    const animationId = ref(null)

    const startAnimation = () => {
      // Prevent multiple animations
      if (isAnimating.value) return
      
      // Cancel any existing animation
      if (animationId.value) {
        cancelAnimationFrame(animationId.value)
      }
      
      isAnimating.value = true
      const startTime = performance.now()
      const startValue = current.value
      const targetValue = props.endVal

      const animate = (currentTime) => {
        if (!isAnimating.value) return // Safety check
        
        const elapsed = currentTime - startTime
        const progress = Math.min(elapsed / props.duration, 1)
        
        // Smooth easing function
        const easeProgress = 1 - Math.pow(1 - progress, 3)
        
        current.value = Math.round(startValue + (targetValue - startValue) * easeProgress)

        if (progress < 1) {
          animationId.value = requestAnimationFrame(animate)
        } else {
          isAnimating.value = false
          current.value = targetValue
        }
      }

      animationId.value = requestAnimationFrame(animate)
    }

    // Watch for prop changes and restart animation
    watch(() => props.endVal, (newVal, oldVal) => {
      if (newVal !== oldVal && newVal > 0) {
        // Small delay to prevent conflicts with multiple components
        setTimeout(startAnimation, Math.random() * 100)
      }
    }, { immediate: false })

    onMounted(() => {
      // Multiple fallback strategies for production
      const strategies = [
        // Strategy 1: Immediate start
        () => {
          if (props.endVal > 0) {
            setTimeout(startAnimation, 50)
          }
        },
        
        // Strategy 2: Wait for next tick
        () => {
          nextTick(() => {
            if (props.endVal > 0) {
              startAnimation()
            }
          })
        },
        
        // Strategy 3: Wait for idle callback
        () => {
          if (window.requestIdleCallback) {
            window.requestIdleCallback(() => {
              if (props.endVal > 0) {
                startAnimation()
              }
            })
          }
        },
        
        // Strategy 4: Fallback with delay
        () => {
          setTimeout(() => {
            if (current.value === 0 && props.endVal > 0) {
              current.value = props.endVal // Direct assignment as fallback
            }
          }, 2000)
        }
      ]

      // Execute all strategies
      strategies.forEach((strategy, index) => {
        setTimeout(strategy, index * 100)
      })
    })

    onUnmounted(() => {
      isAnimating.value = false
      if (animationId.value) {
        cancelAnimationFrame(animationId.value)
      }
    })

    const formattedValue = computed(() => {
      let value = current.value

      if (props.format && value >= 1000) {
        return props.prefix + (value >= 1000000
          ? (value / 1000000).toFixed(1) + 'M'
          : (value / 1000).toFixed(0) + 'K') + props.suffix
      }

      return props.prefix + value.toFixed(props.decimals) + props.suffix
    })

    return { formattedValue }
  },
  template: `<span>{{ formattedValue }}</span>`
})

const isNavigating = ref(false)

const fcrmSettings = createResource({
  url: 'frappe.client.get',
  params: {doctype: 'FCRM Settings', name: 'FCRM Settings'},
  cache: ['fcrmSettings'],
  auto: true, // Auto-fetch on component mount
  onSuccess: (data) => {
    console.log('FCRM Settings loaded:', data)
    // Settings are now available, spancoData will reactively update
  },
  onError: (err) => {
    console.error('Failed to load FCRM Settings:', err)
    // Could show user notification here
  }
})

const isSettingsLoaded = computed(() => {
  return fcrmSettings.data && !fcrmSettings.loading
})

const gotoView = async (view) => {
  if (!view) {
    // Settings not loaded yet or view not configured
    if (fcrmSettings.loading) {
      console.warn('FCRM Settings still loading, please wait...')
      return
    } else {
      console.warn('View not configured in FCRM Settings')
      return  
    }
  }
  
  if (isNavigating.value) return // Prevent double-clicks
  
  try {
    isNavigating.value = true
    await router.push(view?.to)
  } catch (error) {
    console.error('Navigation failed:', error)
  } finally {
    isNavigating.value = false
  }
}

const suspectView = computed(() => parseView(fcrmSettings.data?.suspects || null))
const prospectView = computed(() => parseView(fcrmSettings.data?.prospects || null))
const analysisView = computed(() => parseView(fcrmSettings.data?.analysis || null))
const negotiationView = computed(() => parseView(fcrmSettings.data?.negotiation || null))
const closureView = computed(() => parseView(fcrmSettings.data?.closed || null))
const orderView = computed(() => parseView(fcrmSettings.data?.order || null))

// SPANCO data with preserved desktop colors
const spancoData = computed(() => [
  {
    stage: "S",
    fullName: "Suspects",
    number: 1250,
    percent: 100,
    valuation: 2500000,
    color: "bg-gradient-to-br from-blue-600 to-blue-700 sm:bg-blue-600/95",
    textColor: "text-white",
    view: suspectView.value
  },
  {
    stage: "P",
    fullName: "Prospects", 
    number: 875,
    percent: 70,
    valuation: 1750000,
    color: "bg-gradient-to-br from-indigo-600 to-indigo-700 sm:bg-indigo-600/95",
    textColor: "text-white",
    view: prospectView.value
  },
  {
    stage: "A",
    fullName: "Analysis",
    number: 525,
    percent: 42, 
    valuation: 1050000,
    color: "bg-gradient-to-br from-violet-600 to-violet-700 sm:bg-violet-600/95",
    textColor: "text-white",
    view: analysisView.value
  },
  {
    stage: "N",
    fullName: "Negotiation",
    number: 315,
    percent: 25,
    valuation: 630000,
    color: "bg-gradient-to-br from-amber-600 to-amber-700 sm:bg-amber-600/95", 
    textColor: "text-white",
    view: negotiationView.value
  },
  {
    stage: "C",
    fullName: "Closure",
    number: 188,
    percent: 15,
    valuation: 376000,
    color: "bg-gradient-to-br from-emerald-600 to-emerald-700 sm:bg-emerald-600/95",
    textColor: "text-white",
    view: closureView.value
  },
  {
    stage: "O", 
    fullName: "Order",
    number: 125,
    percent: 10,
    valuation: 250000,
    color: "bg-gradient-to-br from-teal-600 to-teal-700 sm:bg-teal-600/95",
    textColor: "text-white",
    view: orderView.value
  },
])

const formatCurrency = (value) => {
  if (value >= 1000000) {
    return `$${(value / 1000000).toFixed(1)}M`
  }
  if (value >= 1000) {
    return `$${(value / 1000).toFixed(0)}K`
  }
  return `$${value}`
}

const formatNumber = (value) => {
  if (value >= 1000) {
    return `${(value / 1000).toFixed(1)}K`
  }
  return value.toString()
}

const totalPipelineValue = computed(() => {
  return spancoData.value.reduce((sum, stage) => sum + stage.valuation, 0)
})

const overallConversionRate = computed(() => {
  return ((spancoData.value[5].number / spancoData.value[0].number) * 100).toFixed(1)
})

// // Simulate data update for demonstration
// const updateData = () => {
//   setTimeout(() => {
//     spancoData.value = spancoData.value.map(stage => ({
//       ...stage,
//       number: Math.max(Math.round(stage.number * (0.95 + Math.random() * 0.1)), 10),
//       valuation: Math.max(Math.round(stage.valuation * (0.95 + Math.random() * 0.1)), 10000)
//     }))
//
//     const total = spancoData.value[0].number
//     spancoData.value = spancoData.value.map((stage, index) => ({
//       ...stage,
//       percent: index === 0 ? 100 : Math.round((stage.number / total) * 100)
//     }))
//
//     updateData()
//   }, 8000)
// }
//
onMounted(async () => {
  // Settings will auto-fetch, but we can add retry logic
  if (!fcrmSettings.data && !fcrmSettings.loading) {
    try {
      await fcrmSettings.fetch()
    } catch (error) {
      console.error('Failed to fetch FCRM Settings on mount:', error)
    }
  }
})
</script>

<style scoped>
/* Mobile stage segments */
.mobile-stage-segment {
  @apply relative cursor-pointer touch-manipulation;
  transition: all 0.2s ease;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.mobile-stage-segment:active {
  filter: brightness(1.1);
}

/* Desktop stage blocks - PRESERVED */
.stage-block {
  transition: all 0.8s cubic-bezier(0.16, 1, 0.3, 1);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.stage-block:hover {
  filter: brightness(1.1);
  transform: translateY(-2px);
}

/* Expand overlay transition */
.expand-overlay-enter-active, .expand-overlay-leave-active {
  transition: all 0.3s ease;
}

.expand-overlay-enter-from, .expand-overlay-leave-to {
  opacity: 0;
  transform: scale(0.95);
}

/* Mobile stage transitions */
.mobile-stage-move,
.mobile-stage-enter-active,
.mobile-stage-leave-active {
  transition: all 0.5s ease;
}

.mobile-stage-enter-from,
.mobile-stage-leave-to {
  opacity: 0;
  transform: translateY(10px);
}

/* Desktop SPANCO stage transitions - PRESERVED */
.spanco-stage-move,
.spanco-stage-enter-active,
.spanco-stage-leave-active {
  transition: all 0.6s ease;
}

.spanco-stage-enter-from,
.spanco-stage-leave-to {
  opacity: 0;
  transform: translateY(30px);
}

.spanco-stage-leave-active {
  position: absolute;
}

/* Fade transition - PRESERVED */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.5s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Slide up transition - PRESERVED */
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.5s ease-out;
}

.slide-up-enter-from,
.slide-up-leave-to {
  transform: translateY(20px);
  opacity: 0;
}

/* Bounce animation - PRESERVED */
.bounce-enter-active {
  animation: bounce-in 0.8s;
}

@keyframes bounce-in {
  0% {
    transform: scale(0);
  }
  50% {
    transform: scale(1.25);
  }
  100% {
    transform: scale(1);
  }
}

/* Mobile responsive optimizations */
@media (max-width: 320px) {
  .text-xs { font-size: 0.65rem; }
}
</style>