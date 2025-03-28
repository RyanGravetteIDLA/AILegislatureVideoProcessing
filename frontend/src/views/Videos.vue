<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useMediaStore } from '../stores/mediaStore'

const route = useRoute()
const mediaStore = useMediaStore()

// Local state
const selectedVideo = ref(null)
const isDetailView = ref(false)

// Local video data for fallback
const mockVideos = [
  {
    id: 101,
    title: "Test Video 1",
    description: "This is a test video",
    date: "2025-03-27",
    category: "Test Category",
    year: "2025",
    duration: "01:30:00",
    url: "https://example.com/test1.mp4"
  },
  {
    id: 102,
    title: "Test Video 2",
    description: "This is another test video",
    date: "2025-03-28",
    category: "Test Category",
    year: "2025",
    duration: "00:45:00",
    url: "https://example.com/test2.mp4"
  }
]

// Get videos from store with fallback to mock data
const videos = computed(() => {
  // Check if store has videos
  if (mediaStore.videos.length > 0) {
    console.log('Using filtered videos from store:', mediaStore.filteredVideos.length)
    return mediaStore.filteredVideos
  }
  
  // If empty or undefined, use mock data
  console.log('Using mock video data')
  return mockVideos
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
  console.log('Videos component mounted')
  
  try {
    // Fetch videos if not already loaded
    if (mediaStore.videos.length === 0) {
      console.log('Fetching videos from store')
      await mediaStore.fetchVideos()
      console.log('Videos fetched:', mediaStore.videos.length)
    } else {
      console.log('Using existing videos:', mediaStore.videos.length)
    }
    
    // Apply default filters
    applyFilters()
    
    // Check if a specific video ID was requested
    const videoId = route.query.id
    if (videoId) {
      const video = mediaStore.videos.find(v => v.id === parseInt(videoId))
      if (video) {
        selectedVideo.value = video
        isDetailView.value = true
      }
    }
  } catch (error) {
    console.error('Error in Videos component:', error)
  }
})

// Handle video selection
const selectVideo = (video) => {
  selectedVideo.value = video
  isDetailView.value = true
}

// Close detail view
const closeDetailView = () => {
  selectedVideo.value = null
  isDetailView.value = false
}
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold mb-4">Video Library</h1>
    
    <!-- Status Debug -->
    <div class="card p-4 mb-4 bg-yellow-50 border border-yellow-200">
      <p>Videos count: {{ mediaStore.videos.length }}</p>
      <p>Loading state: {{ mediaStore.loading }}</p>
      <p>Filtered videos: {{ videos.length }}</p>
      <button @click="mediaStore.fetchVideos" class="btn btn-primary mt-2">
        Reload Videos
      </button>
    </div>
    
    <!-- Simple Filter -->
    <div class="card p-4 mb-4">
      <input 
        v-model="searchQuery" 
        placeholder="Search videos..." 
        class="input mb-2 w-full"
      />
      <div class="flex space-x-2">
        <button @click="applyFilters" class="btn btn-primary">Search</button>
        <button @click="resetFilters" class="btn btn-secondary">Reset</button>
      </div>
    </div>
    
    <!-- Loading state -->
    <div v-if="mediaStore.loading" class="text-center py-8">
      <p>Loading videos...</p>
    </div>
    
    <!-- Empty state -->
    <div v-else-if="videos.length === 0" class="card p-8 text-center">
      <p>No videos found.</p>
    </div>
    
    <!-- Videos list -->
    <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <div 
        v-for="video in videos" 
        :key="video.id"
        class="card p-4 cursor-pointer"
        @click="selectVideo(video)"
      >
        <h3 class="text-lg font-medium mb-2">{{ video.title }}</h3>
        <p class="text-sm text-gray-500">{{ video.description }}</p>
        <div class="mt-2 flex justify-between">
          <span>{{ video.date }}</span>
          <span>{{ video.category }}</span>
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

.border-yellow-200 {
  border-color: #fef08a;
}

.border {
  border-width: 1px;
}
</style>