<script setup>
import { ref, onMounted } from 'vue'
import { useMediaStore } from '../stores/mediaStore'

// Get the media store
const mediaStore = useMediaStore()

// Local state
const transcripts = ref([])
const loading = ref(true)
const error = ref(null)

// Load transcripts on component mount
onMounted(async () => {
  try {
    // Show loading state
    loading.value = true
    error.value = null
    
    // Fetch transcript data from the store
    await mediaStore.fetchTranscripts()
    
    if (mediaStore.transcripts && mediaStore.transcripts.length > 0) {
      console.log(`Loaded ${mediaStore.transcripts.length} transcripts from store:`, mediaStore.transcripts[0])
      transcripts.value = mediaStore.transcripts
    } else {
      console.warn('No transcript data found in store, using mock data')
      // Use mock data as fallback only if store is empty
      transcripts.value = [
        {
          id: 301,
          title: "Test Transcript 1",
          description: "This is a test transcript file",
          date: "2025-03-27",
          category: "Test Category",
          year: "2025",
          url: "https://example.com/test1.pdf"
        },
        {
          id: 302,
          title: "Test Transcript 2",
          description: "This is another test transcript file",
          date: "2025-03-28",
          category: "Test Category",
          year: "2025",
          url: "https://example.com/test2.pdf"
        }
      ]
    }
  } catch (err) {
    console.error('Component error:', err)
    error.value = 'An unexpected error occurred'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="transcripts-page">
    <h1 class="page-title">Transcript Library</h1>
    
    <!-- Loading state -->
    <div v-if="loading" class="status-message">
      <p>Loading transcripts...</p>
    </div>
    
    <!-- Error state -->
    <div v-else-if="error" class="status-message error">
      <p>{{ error }}</p>
      <button @click="mediaStore.fetchTranscripts">Retry</button>
    </div>
    
    <!-- Empty state -->
    <div v-else-if="transcripts.length === 0" class="status-message">
      <p>No transcripts found.</p>
    </div>
    
    <!-- Transcript listing -->
    <div v-else class="transcript-list">
      <div v-for="transcript in transcripts" :key="transcript.id" class="transcript-card">
        <h3>{{ transcript.title }}</h3>
        <p>{{ transcript.description }}</p>
        <div class="transcript-meta">
          <span>{{ transcript.category }}</span>
          <span>{{ transcript.year }}</span>
          <span v-if="transcript.date">{{ transcript.date }}</span>
        </div>
        <div class="transcript-actions">
          <a :href="transcript.url" target="_blank" class="view-button">
            View Transcript
          </a>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.transcripts-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 1rem;
}

.page-title {
  font-size: 1.5rem;
  font-weight: bold;
  margin-bottom: 1rem;
}

.status-message {
  text-align: center;
  padding: 2rem;
  background-color: #f9f9f9;
  border-radius: 0.5rem;
  margin: 1rem 0;
}

.error {
  background-color: #fee2e2;
  color: #b91c1c;
}

.transcript-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1rem;
  margin-top: 1rem;
}

.transcript-card {
  background-color: white;
  border-radius: 0.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  padding: 1rem;
}

.transcript-card h3 {
  margin-top: 0;
  font-size: 1.125rem;
  margin-bottom: 0.5rem;
}

.transcript-meta {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.5rem;
  font-size: 0.875rem;
  color: #6b7280;
}

.transcript-actions {
  margin-top: 1rem;
}

.view-button {
  display: inline-block;
  width: 100%;
  padding: 0.5rem 1rem;
  background-color: #486581;
  color: white;
  text-align: center;
  border-radius: 0.25rem;
  font-weight: 500;
  cursor: pointer;
  text-decoration: none;
}

.view-button:hover {
  background-color: #334e68;
}
</style>