<script setup>
import { ref, reactive, onMounted } from 'vue'
import axios from 'axios'

// Define API URLs from environment variables
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api'

// Normalize API URL to ensure it ends with /api
const NORMALIZED_API_URL = API_URL.endsWith('/api') 
  ? API_URL 
  : `${API_URL}/api`

// State for test results
const tests = reactive({
  api: { status: 'pending', result: null, error: null },
  health: { status: 'pending', result: null, error: null },
  stats: { status: 'pending', result: null, error: null },
  filters: { status: 'pending', result: null, error: null },
  videos: { status: 'pending', result: null, error: null },
  audio: { status: 'pending', result: null, error: null },
  transcripts: { status: 'pending', result: null, error: null }
})

// Create axios instance
const api = axios.create({
  baseURL: NORMALIZED_API_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
})

// Test API connection
const testAPIConnection = async () => {
  tests.api.status = 'running'
  
  try {
    const response = await api.get('/', { timeout: 10000 })
    tests.api.result = response.data
    tests.api.status = 'success'
  } catch (error) {
    tests.api.error = error.message
    tests.api.status = 'error'
  }
}

// Test health endpoint
const testHealthEndpoint = async () => {
  tests.health.status = 'running'
  
  try {
    const response = await api.get('/health', { timeout: 10000 })
    tests.health.result = response.data
    tests.health.status = 'success'
  } catch (error) {
    tests.health.error = error.message
    tests.health.status = 'error'
  }
}

// Test stats endpoint
const testStatsEndpoint = async () => {
  tests.stats.status = 'running'
  
  try {
    const response = await api.get('/stats', { timeout: 10000 })
    tests.stats.result = response.data
    tests.stats.status = 'success'
  } catch (error) {
    tests.stats.error = error.message
    tests.stats.status = 'error'
  }
}

// Test filters endpoint
const testFiltersEndpoint = async () => {
  tests.filters.status = 'running'
  
  try {
    const response = await api.get('/filters', { timeout: 10000 })
    tests.filters.result = response.data
    tests.filters.status = 'success'
  } catch (error) {
    tests.filters.error = error.message
    tests.filters.status = 'error'
  }
}

// Test videos endpoint
const testVideosEndpoint = async () => {
  tests.videos.status = 'running'
  
  try {
    const response = await api.get('/videos', { timeout: 10000 })
    tests.videos.result = response.data
    tests.videos.status = 'success'
  } catch (error) {
    tests.videos.error = error.message
    tests.videos.status = 'error'
  }
}

// Test audio endpoint
const testAudioEndpoint = async () => {
  tests.audio.status = 'running'
  
  try {
    const response = await api.get('/audio', { timeout: 10000 })
    tests.audio.result = response.data
    
    if (Array.isArray(response.data)) {
      console.log(`Got ${response.data.length} audio items from API`)
      
      if (response.data.length > 0) {
        console.log('First audio item:', response.data[0])
      } else {
        console.warn('Audio array is empty')
      }
    } else {
      console.error('API returned non-array response for audio:', response.data)
    }
    
    tests.audio.status = 'success'
  } catch (error) {
    tests.audio.error = error.message
    tests.audio.status = 'error'
    console.error('Audio endpoint error:', error)
  }
}

// Test transcripts endpoint
const testTranscriptsEndpoint = async () => {
  tests.transcripts.status = 'running'
  
  try {
    const response = await api.get('/transcripts', { timeout: 10000 })
    tests.transcripts.result = response.data
    
    if (Array.isArray(response.data)) {
      console.log(`Got ${response.data.length} transcript items from API`)
      
      if (response.data.length > 0) {
        console.log('First transcript item:', response.data[0])
      } else {
        console.warn('Transcripts array is empty')
      }
    } else {
      console.error('API returned non-array response for transcripts:', response.data)
    }
    
    tests.transcripts.status = 'success'
  } catch (error) {
    tests.transcripts.error = error.message
    tests.transcripts.status = 'error'
    console.error('Transcripts endpoint error:', error)
  }
}

// Run all tests
const runAllTests = async () => {
  // Reset all test results
  Object.keys(tests).forEach(key => {
    tests[key].status = 'pending'
    tests[key].result = null
    tests[key].error = null
  })
  
  // Run all tests in parallel
  await Promise.all([
    testAPIConnection(),
    testHealthEndpoint(),
    testStatsEndpoint(),
    testFiltersEndpoint(),
    testVideosEndpoint(),
    testAudioEndpoint(),
    testTranscriptsEndpoint()
  ])
}

// Run tests on mount
onMounted(() => {
  runAllTests()
})
</script>

<template>
  <div class="diagnostic-page">
    <h1 class="page-title">API Diagnostic</h1>
    <p class="page-description">This page tests the connection to the API and verifies all endpoints are working correctly.</p>
    
    <div class="api-info">
      <h2>API Information</h2>
      <p>API URL: <code>{{ NORMALIZED_API_URL }}</code></p>
      <button @click="runAllTests" class="run-tests-button">Run All Tests</button>
    </div>
    
    <div class="test-results">
      <!-- API Connection -->
      <div class="test-card">
        <div class="test-header">
          <h3>Base API Connection</h3>
          <span :class="`status-badge ${tests.api.status}`">{{ tests.api.status }}</span>
        </div>
        <div v-if="tests.api.status === 'running'" class="test-loading">Running test...</div>
        <div v-else-if="tests.api.status === 'error'" class="test-error">
          <p>Error: {{ tests.api.error }}</p>
        </div>
        <div v-else-if="tests.api.status === 'success'" class="test-success">
          <p>API connection successful!</p>
          <pre class="json-preview">{{ JSON.stringify(tests.api.result, null, 2) }}</pre>
        </div>
      </div>
      
      <!-- Health Endpoint -->
      <div class="test-card">
        <div class="test-header">
          <h3>Health Endpoint</h3>
          <span :class="`status-badge ${tests.health.status}`">{{ tests.health.status }}</span>
        </div>
        <div v-if="tests.health.status === 'running'" class="test-loading">Running test...</div>
        <div v-else-if="tests.health.status === 'error'" class="test-error">
          <p>Error: {{ tests.health.error }}</p>
        </div>
        <div v-else-if="tests.health.status === 'success'" class="test-success">
          <p>Health endpoint working!</p>
          <pre class="json-preview">{{ JSON.stringify(tests.health.result, null, 2) }}</pre>
        </div>
      </div>
      
      <!-- Stats Endpoint -->
      <div class="test-card">
        <div class="test-header">
          <h3>Stats Endpoint</h3>
          <span :class="`status-badge ${tests.stats.status}`">{{ tests.stats.status }}</span>
        </div>
        <div v-if="tests.stats.status === 'running'" class="test-loading">Running test...</div>
        <div v-else-if="tests.stats.status === 'error'" class="test-error">
          <p>Error: {{ tests.stats.error }}</p>
        </div>
        <div v-else-if="tests.stats.status === 'success'" class="test-success">
          <p>Stats endpoint working!</p>
          <pre class="json-preview">{{ JSON.stringify(tests.stats.result, null, 2) }}</pre>
        </div>
      </div>
      
      <!-- Filters Endpoint -->
      <div class="test-card">
        <div class="test-header">
          <h3>Filters Endpoint</h3>
          <span :class="`status-badge ${tests.filters.status}`">{{ tests.filters.status }}</span>
        </div>
        <div v-if="tests.filters.status === 'running'" class="test-loading">Running test...</div>
        <div v-else-if="tests.filters.status === 'error'" class="test-error">
          <p>Error: {{ tests.filters.error }}</p>
        </div>
        <div v-else-if="tests.filters.status === 'success'" class="test-success">
          <p>Filters endpoint working!</p>
          <pre class="json-preview">{{ JSON.stringify(tests.filters.result, null, 2) }}</pre>
        </div>
      </div>
      
      <!-- Videos Endpoint -->
      <div class="test-card">
        <div class="test-header">
          <h3>Videos Endpoint</h3>
          <span :class="`status-badge ${tests.videos.status}`">{{ tests.videos.status }}</span>
        </div>
        <div v-if="tests.videos.status === 'running'" class="test-loading">Running test...</div>
        <div v-else-if="tests.videos.status === 'error'" class="test-error">
          <p>Error: {{ tests.videos.error }}</p>
        </div>
        <div v-else-if="tests.videos.status === 'success'" class="test-success">
          <p>Videos endpoint working!</p>
          <p>Received {{ Array.isArray(tests.videos.result) ? tests.videos.result.length : 0 }} videos</p>
          <div v-if="Array.isArray(tests.videos.result) && tests.videos.result.length > 0">
            <p>First video sample:</p>
            <pre class="json-preview">{{ JSON.stringify(tests.videos.result[0], null, 2) }}</pre>
          </div>
        </div>
      </div>
      
      <!-- Audio Endpoint -->
      <div class="test-card">
        <div class="test-header">
          <h3>Audio Endpoint</h3>
          <span :class="`status-badge ${tests.audio.status}`">{{ tests.audio.status }}</span>
        </div>
        <div v-if="tests.audio.status === 'running'" class="test-loading">Running test...</div>
        <div v-else-if="tests.audio.status === 'error'" class="test-error">
          <p>Error: {{ tests.audio.error }}</p>
        </div>
        <div v-else-if="tests.audio.status === 'success'" class="test-success">
          <p>Audio endpoint working!</p>
          <p>Received {{ Array.isArray(tests.audio.result) ? tests.audio.result.length : 0 }} audio files</p>
          <div v-if="Array.isArray(tests.audio.result) && tests.audio.result.length > 0">
            <p>First audio sample:</p>
            <pre class="json-preview">{{ JSON.stringify(tests.audio.result[0], null, 2) }}</pre>
          </div>
        </div>
      </div>
      
      <!-- Transcripts Endpoint -->
      <div class="test-card">
        <div class="test-header">
          <h3>Transcripts Endpoint</h3>
          <span :class="`status-badge ${tests.transcripts.status}`">{{ tests.transcripts.status }}</span>
        </div>
        <div v-if="tests.transcripts.status === 'running'" class="test-loading">Running test...</div>
        <div v-else-if="tests.transcripts.status === 'error'" class="test-error">
          <p>Error: {{ tests.transcripts.error }}</p>
        </div>
        <div v-else-if="tests.transcripts.status === 'success'" class="test-success">
          <p>Transcripts endpoint working!</p>
          <p>Received {{ Array.isArray(tests.transcripts.result) ? tests.transcripts.result.length : 0 }} transcripts</p>
          <div v-if="Array.isArray(tests.transcripts.result) && tests.transcripts.result.length > 0">
            <p>First transcript sample:</p>
            <pre class="json-preview">{{ JSON.stringify(tests.transcripts.result[0], null, 2) }}</pre>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.diagnostic-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 1rem;
}

.page-title {
  font-size: 1.5rem;
  font-weight: bold;
  margin-bottom: 0.5rem;
}

.page-description {
  margin-bottom: 1.5rem;
  color: #6b7280;
}

.api-info {
  background-color: #f9fafb;
  padding: 1rem;
  border-radius: 0.5rem;
  margin-bottom: 1.5rem;
  border: 1px solid #e5e7eb;
}

.api-info h2 {
  font-size: 1.25rem;
  margin-bottom: 0.5rem;
}

.api-info code {
  background-color: #f3f4f6;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  font-family: monospace;
}

.run-tests-button {
  margin-top: 0.75rem;
  padding: 0.5rem 1rem;
  background-color: #486581;
  color: white;
  border: none;
  border-radius: 0.375rem;
  font-weight: 500;
  cursor: pointer;
}

.run-tests-button:hover {
  background-color: #334e68;
}

.test-results {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 1rem;
}

.test-card {
  background-color: white;
  border-radius: 0.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  padding: 1rem;
  border: 1px solid #e5e7eb;
}

.test-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid #e5e7eb;
}

.test-header h3 {
  font-size: 1rem;
  font-weight: 600;
  margin: 0;
}

.status-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.status-badge.pending {
  background-color: #e5e7eb;
  color: #374151;
}

.status-badge.running {
  background-color: #dbeafe;
  color: #1e40af;
}

.status-badge.success {
  background-color: #d1fae5;
  color: #065f46;
}

.status-badge.error {
  background-color: #fee2e2;
  color: #b91c1c;
}

.test-loading {
  color: #6b7280;
  font-style: italic;
}

.test-error {
  color: #b91c1c;
}

.test-success {
  color: #065f46;
}

.json-preview {
  margin-top: 0.75rem;
  padding: 0.75rem;
  background-color: #f9fafb;
  border-radius: 0.375rem;
  font-family: monospace;
  font-size: 0.75rem;
  overflow-x: auto;
  max-height: 150px;
  overflow-y: auto;
  border: 1px solid #e5e7eb;
  white-space: pre-wrap;
}
</style>