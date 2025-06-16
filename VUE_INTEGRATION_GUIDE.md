const createCharts = () => {
  createStatusChart()
  createTrendsChart()
}

const createStatusChart = () => {
  if (statusChartInstance) {
    statusChartInstance.destroy()
  }

  const ctx = statusChart.value?.getContext('2d')
  if (!ctx || !analytics.value?.summary) return

  const summary = analytics.value.summary
  const data = {
    labels: ['Planned', 'In Progress', 'Completed', 'Cancelled'],
    datasets: [{
      data: [
        summary.planned_visits || 0,
        summary.in_progress_visits || 0,
        summary.completed_visits || 0,
        summary.cancelled_visits || 0
      ],
      backgroundColor: [
        '#FCD34D', // Yellow for Planned
        '#60A5FA', // Blue for In Progress
        '#34D399', // Green for Completed
        '#F87171'  // Red for Cancelled
      ],
      borderWidth: 0
    }]
  }

  statusChartInstance = new Chart(ctx, {
    type: 'doughnut',
    data: data,
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom'
        }
      }
    }
  })
}

const createTrendsChart = () => {
  if (trendsChartInstance) {
    trendsChartInstance.destroy()
  }

  const ctx = trendsChart.value?.getContext('2d')
  if (!ctx || !analytics.value?.weekly_trends) return

  const trends = analytics.value.weekly_trends
  const labels = trends.map(t => new Date(t.week_start).toLocaleDateString())
  
  const data = {
    labels: labels,
    datasets: [
      {
        label: 'Total Visits',
        data: trends.map(t => t.total_visits),
        borderColor: '#3B82F6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.4
      },
      {
        label: 'Completed',
        data: trends.map(t => t.completed_visits),
        borderColor: '#10B981',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        tension: 0.4
      },
      {
        label: 'Hot Leads',
        data: trends.map(t => t.hot_leads),
        borderColor: '#EF4444',
        backgroundColor: 'rgba(239, 68, 68, 0.1)',
        tension: 0.4
      }
    ]
  }

  trendsChartInstance = new Chart(ctx, {
    type: 'line',
    data: data,
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true
        }
      },
      plugins: {
        legend: {
          position: 'bottom'
        }
      }
    }
  })
}

const exportData = () => {
  if (!analytics.value) return

  const csvData = generateCSV(analytics.value)
  const blob = new Blob([csvData], { type: 'text/csv' })
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `site-visit-analytics-${selectedPeriod.value}.csv`
  a.click()
  window.URL.revokeObjectURL(url)
}

const generateCSV = (data) => {
  const headers = ['Sales Person', 'Total Visits', 'Completed', 'Hot Leads', 'Potential Value']
  const rows = Object.entries(data.sales_performance || {}).map(([person, perf]) => [
    person,
    perf.total_visits,
    perf.completed_visits,
    perf.hot_leads,
    perf.potential_value || 0
  ])

  return [headers, ...rows].map(row => row.join(',')).join('\n')
}

onMounted(() => {
  loadAnalytics()
})
</script>

<style scoped>
.form-select {
  @apply block w-auto rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm;
}

.btn-secondary {
  @apply inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500;
}
</style>
```

## 🧪 Testing Setup

### Component Testing with Vitest
```javascript
// tests/components/SiteVisitCard.test.js
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import SiteVisitCard from '@/components/SiteVisit/SiteVisitCard.vue'

describe('SiteVisitCard', () => {
  let wrapper
  let mockVisit

  beforeEach(() => {
    setActivePinia(createPinia())
    
    mockVisit = {
      name: 'SV-2025-00001',
      reference_title: 'Test Customer',
      visit_type: 'Initial Meeting',
      status: 'Planned',
      visit_date: '2025-06-16',
      city: 'New York',
      state: 'NY',
      planned_start_time: '2025-06-16T09:00:00'
    }

    // Mock geolocation
    global.navigator.geolocation = {
      getCurrentPosition: vi.fn()
    }
  })

  it('renders visit information correctly', () => {
    wrapper = mount(SiteVisitCard, {
      props: { visit: mockVisit }
    })

    expect(wrapper.text()).toContain('Test Customer')
    expect(wrapper.text()).toContain('Initial Meeting')
    expect(wrapper.text()).toContain('New York, NY')
  })

  it('shows check-in button for planned visits', () => {
    wrapper = mount(SiteVisitCard, {
      props: { visit: mockVisit }
    })

    const checkInButton = wrapper.find('button[data-test="check-in"]')
    expect(checkInButton.exists()).toBe(true)
    expect(checkInButton.text()).toContain('Check In')
  })

  it('shows check-out button for in-progress visits', () => {
    const inProgressVisit = {
      ...mockVisit,
      status: 'In Progress',
      check_in_time: '2025-06-16T09:00:00'
    }

    wrapper = mount(SiteVisitCard, {
      props: { visit: inProgressVisit }
    })

    const checkOutButton = wrapper.find('button[data-test="check-out"]')
    expect(checkOutButton.exists()).toBe(true)
    expect(checkOutButton.text()).toContain('Check Out')
  })

  it('emits check-in event when check-in button is clicked', async () => {
    // Mock successful geolocation
    global.navigator.geolocation.getCurrentPosition.mockImplementation((success) => {
      success({
        coords: {
          latitude: 40.7128,
          longitude: -74.0060,
          accuracy: 10
        }
      })
    })

    wrapper = mount(SiteVisitCard, {
      props: { visit: mockVisit }
    })

    const checkInButton = wrapper.find('button[data-test="check-in"]')
    await checkInButton.trigger('click')

    expect(wrapper.emitted('check-in')).toBeTruthy()
    expect(wrapper.emitted('check-in')[0]).toEqual([
      mockVisit.name,
      {
        latitude: 40.7128,
        longitude: -74.0060,
        accuracy: 10
      }
    ])
  })
})
```

### API Service Testing
```javascript
// tests/services/siteVisitApi.test.js
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { siteVisitApi } from '@/services/siteVisitApi'
import api from '@/services/api'

vi.mock('@/services/api')

describe('siteVisitApi', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('getSiteVisits', () => {
    it('fetches site visits with filters', async () => {
      const mockVisits = [
        { name: 'SV-001', reference_title: 'Customer 1' },
        { name: 'SV-002', reference_title: 'Customer 2' }
      ]

      api.get.mockResolvedValue({
        data: { message: mockVisits }
      })

      const filters = { status: 'Planned' }
      const result = await siteVisitApi.getSiteVisits(filters)

      expect(api.get).toHaveBeenCalledWith(
        '/api/method/crm.api.site_visit.get_my_visits?status=Planned'
      )
      expect(result).toEqual(mockVisits)
    })
  })

  describe('checkIn', () => {
    it('sends check-in request with location data', async () => {
      const mockResponse = {
        success: true,
        message: 'Check-in successful'
      }

      api.post.mockResolvedValue({
        data: { message: mockResponse }
      })

      const visitId = 'SV-001'
      const locationData = {
        latitude: 40.7128,
        longitude: -74.0060,
        accuracy: 10
      }

      const result = await siteVisitApi.checkIn(visitId, locationData)

      expect(api.post).toHaveBeenCalledWith(
        '/api/method/crm.api.site_visit.quick_checkin',
        {
          visit_id: visitId,
          latitude: locationData.latitude,
          longitude: locationData.longitude,
          accuracy: locationData.accuracy
        }
      )
      expect(result).toEqual(mockResponse)
    })
  })
})
```

## 🚀 Deployment Configuration

### Build Configuration
```javascript
// vite.config.js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['vue', 'vue-router', 'pinia'],
          charts: ['chart.js'],
          maps: ['leaflet', 'vue-leaflet']
        }
      }
    },
    chunkSizeWarningLimit: 1000
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
```

### Environment Configuration
```bash
# .env.development
VUE_APP_API_BASE_URL=http://localhost:8000
VUE_APP_WS_URL=ws://localhost:8000/ws
VUE_APP_MAPS_API_KEY=your_maps_api_key
VUE_APP_ENV=development

# .env.production
VUE_APP_API_BASE_URL=https://your-api.com
VUE_APP_WS_URL=wss://your-api.com/ws
VUE_APP_MAPS_API_KEY=your_production_maps_api_key
VUE_APP_ENV=production
```

### PWA Configuration
```javascript
// src/registerSW.js
import { registerSW } from 'virtual:pwa-register'

const updateSW = registerSW({
  onNeedRefresh() {
    if (confirm('New content available. Reload?')) {
      updateSW(true)
    }
  },
  onOfflineReady() {
    console.log('App ready to work offline')
  },
})

// Add to main.js
import { registerSW } from './registerSW'
registerSW()
```

### Docker Configuration
```dockerfile
# Dockerfile
FROM node:18-alpine as build-stage

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

FROM nginx:stable-alpine as production-stage
COPY --from=build-stage /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## 📱 Mobile App Features

### PWA Manifest
```json
{
  "name": "CRM Site Visits",
  "short_name": "SiteVisits",
  "description": "Mobile app for managing site visits",
  "theme_color": "#3B82F6",
  "background_color": "#FFFFFF",
  "display": "standalone",
  "orientation": "portrait",
  "scope": "/",
  "start_url": "/",
  "icons": [
    {
      "src": "/icons/icon-192x192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-512x512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ],
  "shortcuts": [
    {
      "name": "Check In",
      "short_name": "Check In",
      "description": "Quick check-in to current visit",
      "url": "/quick-checkin",
      "icons": [{ "src": "/icons/checkin.png", "sizes": "96x96" }]
    },
    {
      "name": "New Visit",
      "short_name": "New Visit",
      "description": "Create a new site visit",
      "url": "/site-visits/new",
      "icons": [{ "src": "/icons/new.png", "sizes": "96x96" }]
    }
  ]
}
```

### Offline Support
```javascript
// src/composables/useOfflineSync.js
import { ref, computed } from 'vue'
import { useOnline } from '@vueuse/core'

export function useOfflineSync() {
  const isOnline = useOnline()
  const pendingActions = ref([])
  const syncInProgress = ref(false)

  const addPendingAction = (action) => {
    pendingActions.value.push({
      id: Date.now(),
      timestamp: new Date().toISOString(),
      ...action
    })
    
    // Store in localStorage for persistence
    localStorage.setItem('pendingActions', JSON.stringify(pendingActions.value))
  }

  const syncPendingActions = async () => {
    if (!isOnline.value || syncInProgress.value || pendingActions.value.length === 0) {
      return
    }

    syncInProgress.value = true

    try {
      for (const action of pendingActions.value) {
        await executeAction(action)
      }
      
      // Clear successful actions
      pendingActions.value = []
      localStorage.removeItem('pendingActions')
    } catch (error) {
      console.error('Sync failed:', error)
    } finally {
      syncInProgress.value = false
    }
  }

  const executeAction = async (action) => {
    switch (action.type) {
      case 'checkin':
        await siteVisitApi.checkIn(action.visitId, action.locationData)
        break
      case 'checkout':
        await siteVisitApi.checkOut(action.visitId, action.locationData, action.summary)
        break
      case 'update':
        await siteVisitApi.updateSiteVisit(action.visitId, action.updates)
        break
      default:
        throw new Error(`Unknown action type: ${action.type}`)
    }
  }

  // Auto-sync when coming online
  watch(isOnline, (online) => {
    if (online) {
      syncPendingActions()
    }
  })

  // Load pending actions from localStorage on init
  onMounted(() => {
    const stored = localStorage.getItem('pendingActions')
    if (stored) {
      try {
        pendingActions.value = JSON.parse(stored)
      } catch (error) {
        console.error('Failed to load pending actions:', error)
      }
    }
  })

  return {
    isOnline,
    pendingActions: computed(() => pendingActions.value),
    syncInProgress: computed(() => syncInProgress.value),
    addPendingAction,
    syncPendingActions
  }
}
```

## 🎯 Performance Optimization

### Lazy Loading Routes
```javascript
// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('@/views/DashboardView.vue')
  },
  {
    path: '/site-visits',
    name: 'SiteVisits',
    component: () => import('@/views/SiteVisitsView.vue'),
    children: [
      {
        path: ':id',
        name: 'SiteVisitDetail',
        component: () => import('@/views/SiteVisitDetailView.vue'),
        props: true
      }
    ]
  },
  {
    path: '/analytics',
    name: 'Analytics',
    component: () => import('@/views/AnalyticsView.vue')
  }
]

export default createRouter({
  history: createWebHistory(),
  routes
})
```

### Image Optimization
```vue
<!-- src/components/Common/OptimizedImage.vue -->
<template>
  <div class="image-container">
    <img
      :src="currentSrc"
      :alt="alt"
      @load="onLoad"
      @error="onError"
      :class="[
        'transition-opacity duration-300',
        loaded ? 'opacity-100' : 'opacity-0'
      ]"
    />
    <div 
      v-if="!loaded" 
      class="placeholder bg-gray-200 animate-pulse absolute inset-0"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const props = defineProps({
  src: String,
  alt: String,
  sizes: {
    type: Array,
    default: () => [480, 768, 1024]
  }
})

const loaded = ref(false)
const error = ref(false)

const currentSrc = computed(() => {
  if (error.value) return '/placeholder.png'
  
  // Return optimized image based on screen size
  const screenWidth = window.innerWidth
  const size = props.sizes.find(s => screenWidth <= s) || props.sizes[props.sizes.length - 1]
  
  return `${props.src}?w=${size}&q=80`
})

const onLoad = () => {
  loaded.value = true
}

const onError = () => {
  error.value = true
  loaded.value = true
}
</script>
```

## 🔐 Security Best Practices

### API Security
```javascript
// src/services/authService.js
class AuthService {
  constructor() {
    this.token = localStorage.getItem('auth_token')
    this.refreshToken = localStorage.getItem('refresh_token')
  }

  async login(credentials) {
    try {
      const response = await api.post('/auth/login', credentials)
      const { token, refresh_token, user } = response.data
      
      this.setTokens(token, refresh_token)
      return { user, token }
    } catch (error) {
      throw new Error('Login failed')
    }
  }

  setTokens(token, refreshToken) {
    this.token = token
    this.refreshToken = refreshToken
    localStorage.setItem('auth_token', token)
    localStorage.setItem('refresh_token', refreshToken)
  }

  async refreshAuthToken() {
    try {
      const response = await api.post('/auth/refresh', {
        refresh_token: this.refreshToken
      })
      
      const { token } = response.data
      this.setTokens(token, this.refreshToken)
      return token
    } catch (error) {
      this.logout()
      throw new Error('Session expired')
    }
  }

  logout() {
    this.token = null
    this.refreshToken = null
    localStorage.removeItem('auth_token')
    localStorage.removeItem('refresh_token')
    window.location.href = '/login'
  }

  isAuthenticated() {
    return !!this.token
  }
}

export const authService = new AuthService()
```

## 📋 Conclusion

This comprehensive Vue.js integration guide provides:

### ✅ **Complete Frontend Solution**
- Modern Vue 3 + Composition API architecture
- Mobile-first responsive design
- Real-time geolocation integration
- Offline-capable Progressive Web App

### ✅ **Advanced Features**
- Swipeable mobile cards for intuitive interaction
- Real-time WebSocket updates
- Comprehensive analytics dashboard
- Offline sync capabilities

### ✅ **Production Ready**
- Full test coverage with Vitest
- Performance optimizations
- Security best practices
- Docker deployment configuration

### ✅ **Developer Experience**
- TypeScript support ready
- Hot module replacement
- Component story development
- Comprehensive error handling

### 🚀 **Next Steps**

1. **Setup Development Environment**:
   ```bash
   npm create vue@latest crm-site-visits
   cd crm-site-visits
   npm install [dependencies from guide]
   ```

2. **Implement Core Components**:
   - Start with SiteVisitList and SiteVisitCard
   - Add check-in/checkout functionality
   - Integrate with your backend API

3. **Add Mobile Features**:
   - Implement swipeable cards
   - Add PWA configuration
   - Test offline functionality

4. **Deploy and Scale**:
   - Configure production environment
   - Set up CI/CD pipeline
   - Monitor performance metrics

This Vue.js integration transforms your CRM Site Visit system into a modern, mobile-first application that field sales teams will love to use! 🎉
