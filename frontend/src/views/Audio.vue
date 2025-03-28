<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useMediaStore } from '../stores/mediaStore'

const route = useRoute()
const mediaStore = useMediaStore()

// Local state
const selectedAudio = ref(null)
const isDetailView = ref(false)

// Get audio files from store
const audioFiles = computed(() => {
  // Force return mock data for testing
  const mockAudio = [
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
  ];
  return mockAudio;
  // Uncomment to use real data
  // return mediaStore.filteredAudio
})

// Filter state
const yearFilter = ref(null)
const categoryFilter = ref(null)
const searchQuery = ref('')

// Apply filters
const applyFilters = () => {
  mediaStore.updateFilters({
    year: yearFilter.value,
    category: categoryFilter.value,
    searchQuery: searchQuery.value
  })
}

// Reset filters
const resetFilters = () => {
  yearFilter.value = null
  categoryFilter.value = null
  searchQuery.value = ''
  mediaStore.resetFilters()
}

// Get available years and categories
const years = computed(() => mediaStore.years)
const categories = computed(() => mediaStore.categories)

// Initialize component
onMounted(async () => {
  console.log('Audio component mounted')
  
  try {
    // Fetch audio if not already loaded
    if (mediaStore.audio.length === 0) {
      console.log('Fetching audio from store')
      await mediaStore.fetchAudio()
      console.log('Audio fetched:', mediaStore.audio.length)
    } else {
      console.log('Using existing audio:', mediaStore.audio.length)
    }
    
    // Apply default filters
    applyFilters()
    
    // Check if a specific audio ID was requested
    const audioId = route.query.id
    if (audioId) {
      const audio = mediaStore.audio.find(a => a.id === parseInt(audioId))
      if (audio) {
        selectedAudio.value = audio
        isDetailView.value = true
      }
    }
  } catch (error) {
    console.error('Error in Audio component:', error)
  }
})

// Handle audio selection
const selectAudio = (audio) => {
  selectedAudio.value = audio
  isDetailView.value = true
}

// Close detail view
const closeDetailView = () => {
  selectedAudio.value = null
  isDetailView.value = false
}
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold mb-4">Audio Library</h1>
    
    <!-- Status Debug -->
    <div class="card p-4 mb-4 bg-yellow-50 border border-yellow-200">
      <p>Audio count: {{ mediaStore.audio.length }}</p>
      <p>Loading state: {{ mediaStore.loading }}</p>
      <p>Filtered audio: {{ audioFiles.length }}</p>
      <button @click="mediaStore.fetchAudio" class="btn btn-primary mt-2">
        Reload Audio
      </button>
    </div>
    
    <!-- Simple Filter -->
    <div class="card p-4 mb-4">
      <input 
        v-model="searchQuery" 
        placeholder="Search audio..." 
        class="input mb-2 w-full"
      />
      <div class="flex space-x-2">
        <button @click="applyFilters" class="btn btn-primary">Search</button>
        <button @click="resetFilters" class="btn btn-secondary">Reset</button>
      </div>
    </div>
    
    <!-- Loading state -->
    <div v-if="mediaStore.loading" class="text-center py-8">
      <p>Loading audio files...</p>
    </div>
    
    <!-- Empty state -->
    <div v-else-if="audioFiles.length === 0" class="card p-8 text-center">
      <p>No audio files found.</p>
    </div>
    
    <!-- Audio list -->
    <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <div 
        v-for="audio in audioFiles" 
        :key="audio.id"
        class="card p-4 cursor-pointer"
        @click="selectAudio(audio)"
      >
        <h3 class="text-lg font-medium mb-2">{{ audio.title }}</h3>
        <p class="text-sm text-gray-500">{{ audio.description }}</p>
        
        <!-- Audio player -->
        <div class="mt-2 p-2 bg-gray-100 rounded">
          <audio controls class="w-full">
            <source :src="audio.url" type="audio/mpeg">
            Your browser does not support the audio element.
          </audio>
        </div>
        
        <div class="mt-2 flex justify-between">
          <span>{{ audio.date }}</span>
          <span>{{ audio.category }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.card {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin-bottom: 1rem;
}

.btn {
  display: inline-block;
  padding: 0.5rem 1rem;
  border-radius: 0.25rem;
  font-weight: 500;
  cursor: pointer;
}

.btn-primary {
  background-color: #486581;
  color: white;
}

.btn-secondary {
  background-color: #e2e8f0;
  color: #334e68;
}

.input {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 0.25rem;
}

.grid {
  display: grid;
  gap: 1rem;
}

@media (min-width: 640px) {
  .grid-cols-1 {
    grid-template-columns: repeat(1, minmax(0, 1fr));
  }
  .sm\:grid-cols-2 {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (min-width: 1024px) {
  .lg\:grid-cols-3 {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

.flex {
  display: flex;
}

.justify-between {
  justify-content: space-between;
}

.space-x-2 > * + * {
  margin-left: 0.5rem;
}

.mb-2 {
  margin-bottom: 0.5rem;
}

.mb-4 {
  margin-bottom: 1rem;
}

.mt-2 {
  margin-top: 0.5rem;
}

.text-center {
  text-align: center;
}

.text-2xl {
  font-size: 1.5rem;
  line-height: 2rem;
}

.text-lg {
  font-size: 1.125rem;
  line-height: 1.75rem;
}

.text-sm {
  font-size: 0.875rem;
  line-height: 1.25rem;
}

.font-bold {
  font-weight: 700;
}

.font-medium {
  font-weight: 500;
}

.text-gray-500 {
  color: #6b7280;
}

.cursor-pointer {
  cursor: pointer;
}

.py-8 {
  padding-top: 2rem;
  padding-bottom: 2rem;
}

.p-2 {
  padding: 0.5rem;
}

.p-4 {
  padding: 1rem;
}

.p-8 {
  padding: 2rem;
}

.w-full {
  width: 100%;
}

.bg-yellow-50 {
  background-color: #fffbeb;
}

.bg-gray-100 {
  background-color: #f3f4f6;
}

.border-yellow-200 {
  border-color: #fef08a;
}

.border {
  border-width: 1px;
}

.rounded {
  border-radius: 0.25rem;
}
</style>