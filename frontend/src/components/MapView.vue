<template>
  <div class="map-container">
    <div ref="mapDiv" class="map"></div>
    <div class="controls">
      <button @click="zoomIn">Zoom In</button>
      <button @click="zoomOut">Zoom Out</button>
      <button @click="resetView">Reset View</button>
      <button @click="addMarker">Add Random Marker</button>
      <button @click="clearMarkers">Clear Markers</button>
    </div>
    <div class="info">
      <p>Lat: {{ currentCenter.lat.toFixed(4) }}, Lng: {{ currentCenter.lng.toFixed(4) }}</p>
      <p>Zoom: {{ currentZoom }}</p>
      <p>Markers: {{ markers.length }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, reactive } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

// Fix for default marker icon issue in webpack
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
})

// Component refs and state
const mapDiv = ref(null)
let map = null
const markers = ref([])
const currentCenter = reactive({ lat: 40.7128, lng: -74.0060 })
const currentZoom = ref(13)

// Default map configuration
const defaultCenter = [40.7128, -74.0060] // New York City
const defaultZoom = 13

// Initialize map
onMounted(() => {
  // Create map instance
  map = L.map(mapDiv.value, {
    center: defaultCenter,
    zoom: defaultZoom,
    zoomControl: true,
  })

  // Add OpenStreetMap tile layer
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 19,
  }).addTo(map)

  // Add some initial markers
  addInitialMarkers()

  // Set up event listeners
  map.on('moveend', updateCenter)
  map.on('zoomend', updateZoom)
})

// Cleanup on unmount
onUnmounted(() => {
  if (map) {
    map.remove()
  }
})

// Update current center position
const updateCenter = () => {
  const center = map.getCenter()
  currentCenter.lat = center.lat
  currentCenter.lng = center.lng
}

// Update current zoom level
const updateZoom = () => {
  currentZoom.value = map.getZoom()
}

// Add initial markers
const addInitialMarkers = () => {
  const locations = [
    { lat: 40.7580, lng: -73.9855, name: 'Times Square' },
    { lat: 40.7489, lng: -73.9680, name: 'Grand Central Terminal' },
    { lat: 40.6892, lng: -74.0445, name: 'Statue of Liberty' },
  ]

  locations.forEach(location => {
    const marker = L.marker([location.lat, location.lng])
      .addTo(map)
      .bindPopup(`<b>${location.name}</b><br>Lat: ${location.lat}<br>Lng: ${location.lng}`)
    
    markers.value.push(marker)
  })
}

// Control functions
const zoomIn = () => {
  map.zoomIn()
}

const zoomOut = () => {
  map.zoomOut()
}

const resetView = () => {
  map.setView(defaultCenter, defaultZoom)
}

const addMarker = () => {
  // Generate random coordinates around current center
  const center = map.getCenter()
  const lat = center.lat + (Math.random() - 0.5) * 0.1
  const lng = center.lng + (Math.random() - 0.5) * 0.1

  const marker = L.marker([lat, lng])
    .addTo(map)
    .bindPopup(`<b>Random Marker</b><br>Lat: ${lat.toFixed(4)}<br>Lng: ${lng.toFixed(4)}`)
    .openPopup()

  markers.value.push(marker)
}

const clearMarkers = () => {
  markers.value.forEach(marker => {
    map.removeLayer(marker)
  })
  markers.value = []
}
</script>

<style scoped>
.map-container {
  height: 100vh;
  width: 100%;
  position: relative;
  font-family: Arial, sans-serif;
}

.map {
  height: 100%;
  width: 100%;
}

.controls {
  position: absolute;
  top: 20px;
  right: 20px;
  z-index: 1000;
  background: white;
  padding: 15px;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
}

.controls button {
  display: block;
  width: 100%;
  padding: 8px 16px;
  margin-bottom: 8px;
  background: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.3s;
}

.controls button:last-child {
  margin-bottom: 0;
}

.controls button:hover {
  background: #45a049;
}

.info {
  position: absolute;
  bottom: 20px;
  left: 20px;
  z-index: 1000;
  background: white;
  padding: 15px;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
}

.info p {
  margin: 5px 0;
  font-size: 14px;
  color: #333;
}

/* Leaflet overrides for better appearance */
:deep(.leaflet-control-zoom) {
  border: none;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
}

:deep(.leaflet-control-zoom a) {
  background: white;
  color: #333;
}

:deep(.leaflet-control-zoom a:hover) {
  background: #f4f4f4;
}

/* Responsive design */
@media (max-width: 768px) {
  .controls {
    top: 10px;
    right: 10px;
    padding: 10px;
  }
  
  .controls button {
    padding: 6px 12px;
    font-size: 12px;
  }
  
  .info {
    bottom: 10px;
    left: 10px;
    padding: 10px;
  }
  
  .info p {
    font-size: 12px;
  }
}
</style>