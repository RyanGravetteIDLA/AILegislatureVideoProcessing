<script setup>
import { ref, onMounted } from 'vue'
import { useMediaStore } from '../stores/mediaStore'

// Get the media store
const mediaStore = useMediaStore()

// Local state
const audio = ref([])
const loading = ref(true)
const error = ref(null)

// Load audio on component mount
onMounted(async () => {
  try {
    // Show loading state
    loading.value = true
    error.value = null
    
    // Fetch audio data from the store
    await mediaStore.fetchAudio()
    
    if (mediaStore.audio && mediaStore.audio.length > 0) {
      console.log(`Loaded ${mediaStore.audio.length} audio files from store:`, mediaStore.audio[0])
      audio.value = mediaStore.audio
    } else {
      console.warn('No audio data found in store, using mock data')
      // Use mock data as fallback only if store is empty
      audio.value = [
        {
          id: 201,
          title: "Test Audio 1",
          description: "This is a test audio file",
          date: "2025-03-27",
          category: "Test Category",
          year: "2025",
          duration: "01:30:00",
          url: "https://example.com/test1.mp3"
        },
        {
          id: 202,
          title: "Test Audio 2",
          description: "This is another test audio file",
          date: "2025-03-28",
          category: "Test Category",
          year: "2025",
          duration: "00:45:00",
          url: "https://example.com/test2.mp3"
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
  <div class="audio-page">
    <h1 class="page-title">Audio Library</h1>
    
    <!-- Loading state -->
    <div v-if="loading" class="status-message">
      <p>Loading audio files...</p>
    </div>
    
    <!-- Error state -->
    <div v-else-if="error" class="status-message error">
      <p>{{ error }}</p>
      <button @click="mediaStore.fetchAudio">Retry</button>
    </div>
    
    <!-- Empty state -->
    <div v-else-if="audio.length === 0" class="status-message">
      <p>No audio files found.</p>
    </div>
    
    <!-- Audio listing -->
    <div v-else class="audio-list">
      <div v-for="audioItem in audio" :key="audioItem.id" class="audio-card">
        <h3>{{ audioItem.title }}</h3>
        <p>{{ audioItem.description }}</p>
        
        <!-- Audio player -->
        <div class="audio-player">
          <audio controls class="w-full">
            <source :src="audioItem.url" type="audio/mpeg">
            Your browser does not support the audio element.
          </audio>
        </div>
        
        <div class="audio-meta">
          <span>{{ audioItem.category }}</span>
          <span>{{ audioItem.year }}</span>
          <span v-if="audioItem.date">{{ audioItem.date }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.audio-page {
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

.audio-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1rem;
  margin-top: 1rem;
}

.audio-card {
  background-color: white;
  border-radius: 0.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  padding: 1rem;
}

.audio-card h3 {
  margin-top: 0;
  font-size: 1.125rem;
  margin-bottom: 0.5rem;
}

.audio-meta {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.5rem;
  font-size: 0.875rem;
  color: #6b7280;
}

.audio-player {
  margin: 1rem 0;
  padding: 0.5rem;
  background-color: #f3f4f6;
  border-radius: 0.25rem;
}

.w-full {
  width: 100%;
}
</style>