<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useMediaStore } from '../stores/mediaStore'

// Import media icons
import videoIcon from '../assets/icons/video.png'
import audioIcon from '../assets/icons/audio.png'
import transcriptIcon from '../assets/icons/transcript.png'

// Get the media store
const mediaStore = useMediaStore()

// Local state
const rawVideos = ref([])
const loading = ref(true)
const error = ref(null)
const selectedVideo = ref(null)
const debugPanelVisible = ref(false)

// Debug function to show video details
const showVideoDetails = (video) => {
  selectedVideo.value = video
  debugPanelVisible.value = true
}

// Close debug panel
const closeDebugPanel = () => {
  debugPanelVisible.value = false
}

// No longer need manual URL construction since we'll use the direct URLs from the API

// Filter state
const selectedYear = ref('')
const selectedCategory = ref('')

// Pagination state
const currentPage = ref(1)
const itemsPerPage = ref(10) // Number of items to show per page

// Function to extract session day number from description
const extractSessionDay = (description) => {
  if (!description) return 0
  
  // Try to find "Session Day X" or "Day X" pattern
  const match = description.match(/(?:Session Day|Day)\s+(\d+)/i)
  if (match && match[1]) {
    return parseInt(match[1], 10)
  }
  
  return 0 // Default to day 0 if no match found
}

// Computed list of available years
const availableYears = computed(() => {
  const years = [...new Set(rawVideos.value.map(video => video.year))]
  return years.sort((a, b) => b.localeCompare(a)) // Sort years in descending order
})

// Computed list of available categories
const availableCategories = computed(() => {
  const categories = [...new Set(rawVideos.value.map(video => video.category))]
  return categories.sort() // Sort categories alphabetically
})

// Filter and sort all videos
const filteredSortedVideos = computed(() => {
  // First filter the videos based on selected year and category
  const filtered = rawVideos.value.filter(video => {
    // Apply year filter if selected
    if (selectedYear.value && video.year !== selectedYear.value) {
      return false
    }
    
    // Apply category filter if selected
    if (selectedCategory.value && video.category !== selectedCategory.value) {
      return false
    }
    
    return true
  })

  // Then sort the filtered videos
  return [...filtered].sort((a, b) => {
    // First sort by year (newest first)
    if (a.year !== b.year) {
      return b.year.localeCompare(a.year)
    }
    
    // Then sort by category
    if (a.category !== b.category) {
      return a.category.localeCompare(b.category)
    }
    
    // Then sort by session day (extracted from description)
    const dayA = extractSessionDay(a.description)
    const dayB = extractSessionDay(b.description)
    
    if (dayA !== dayB) {
      return dayA - dayB // Ascending order (day 1, 2, 3...)
    }
    
    // Finally sort by date if available
    if (a.date && b.date) {
      return a.date.localeCompare(b.date)
    }
    
    return 0
  })
})

// Total number of pages based on filtered results
const totalPages = computed(() => {
  return Math.ceil(filteredSortedVideos.value.length / itemsPerPage.value) || 1
})

// Get paginated videos for current page
const videos = computed(() => {
  const startIndex = (currentPage.value - 1) * itemsPerPage.value
  const endIndex = startIndex + itemsPerPage.value
  return filteredSortedVideos.value.slice(startIndex, endIndex)
})

// Reset all filters
const resetFilters = () => {
  selectedYear.value = ''
  selectedCategory.value = ''
  currentPage.value = 1 // Reset to first page when filters change
}

// Pagination navigation
const goToPage = (page) => {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page
  }
}

// When filters change, reset to page 1
watch([selectedYear, selectedCategory], () => {
  currentPage.value = 1
})

// Find related audio and transcripts for a video
const findRelatedMedia = async (video) => {
  console.log('Finding related media for video:', video)
  console.log('Available audio items:', mediaStore.audio.length)
  console.log('Available transcript items:', mediaStore.transcripts.length)
  
  if (!video || !video.id) {
    console.warn('Video missing ID or invalid:', video)
    return { audio: null, transcript: null }
  }
  
  // Use the new relationship methods to find related media
  let [relatedAudio, relatedTranscript] = await Promise.all([
    mediaStore.getRelatedAudio(video),
    mediaStore.getRelatedTranscript(video)
  ])
  
  console.log('Found related media:', {
    audio: relatedAudio ? relatedAudio.title : 'None',
    transcript: relatedTranscript ? relatedTranscript.title : 'None'
  })
  
  return {
    audio: relatedAudio || null,
    transcript: relatedTranscript || null
  }
}

// Enhance videos with related media
const enhanceVideosWithRelatedMedia = async (videos) => {
  const enhancedVideos = []
  
  // Process videos sequentially to avoid too many simultaneous API calls
  for (const video of videos) {
    try {
      const related = await findRelatedMedia(video)
      enhancedVideos.push({
        ...video,
        relatedAudio: related.audio,
        relatedTranscript: related.transcript,
        // Add direct URL references for faster access
        related_audio_url: related.audio ? related.audio.url : null,
        related_transcript_url: related.transcript ? related.transcript.url : null
      })
    } catch (error) {
      console.error(`Error enhancing video with ID ${video.id}:`, error)
      enhancedVideos.push({
        ...video,
        relatedAudio: null,
        relatedTranscript: null,
        related_audio_url: null,
        related_transcript_url: null
      })
    }
  }
  
  return enhancedVideos
}

// Load all media on component mount
onMounted(async () => {
  try {
    // Show loading state
    loading.value = true
    error.value = null
    
    // Load all media types
    try {
      console.log('Starting to fetch media data from API...')
      console.log('API URL:', import.meta.env.VITE_API_URL)

      // Fetch videos first
      console.log('Fetching videos...')
      await mediaStore.fetchVideos()
      console.log(`Successfully loaded ${mediaStore.videos.length} videos`)
      
      if (mediaStore.videos.length > 0) {
        console.log('Sample video data structure:', mediaStore.videos[0])
        
        // Check if videos already have direct path references from the database
        const videosWithDbAudioUrl = mediaStore.videos.filter(v => v.related_audio_url).length
        const videosWithDbTranscriptUrl = mediaStore.videos.filter(v => v.related_transcript_url).length
        
        if (videosWithDbAudioUrl > 0 || videosWithDbTranscriptUrl > 0) {
          console.log(`Videos with DB audio URL: ${videosWithDbAudioUrl}/${mediaStore.videos.length}`)
          console.log(`Videos with DB transcript URL: ${videosWithDbTranscriptUrl}/${mediaStore.videos.length}`)
          console.log('Example of direct URL from DB:', 
            mediaStore.videos.find(v => v.related_audio_url)?.related_audio_url || 'None found')
        } else {
          console.log('No videos have direct path references from the database.')
        }
      }
      
      // Fetch audio with separate try/catch to isolate errors
      try {
        console.log('Fetching audio...')
        await mediaStore.fetchAudio()
        console.log(`Successfully loaded ${mediaStore.audio.length} audio files`)
        
        if (mediaStore.audio.length > 0) {
          console.log('Sample audio data structure:', mediaStore.audio[0])
        } else {
          console.warn('No audio files loaded from API')
        }
      } catch (audioError) {
        console.error('Failed to load audio:', audioError)
      }
      
      // Fetch transcripts with separate try/catch to isolate errors
      try {
        console.log('Fetching transcripts...')
        await mediaStore.fetchTranscripts()
        console.log(`Successfully loaded ${mediaStore.transcripts.length} transcripts`)
        
        if (mediaStore.transcripts.length > 0) {
          console.log('Sample transcript data structure:', mediaStore.transcripts[0])
        } else {
          console.warn('No transcripts loaded from API')
        }
      } catch (transcriptError) {
        console.error('Failed to load transcripts:', transcriptError)
      }
      
      console.log('-------- MEDIA LOADING SUMMARY --------')
      console.log(`Total videos: ${mediaStore.videos.length}`)
      console.log(`Total audio files: ${mediaStore.audio.length}`)
      console.log(`Total transcripts: ${mediaStore.transcripts.length}`)
      
      // Enhance videos with related media (if audio and transcripts loaded)
      if (mediaStore.videos.length > 0) {
        console.log('Enhancing videos with related media...')
        
        // Show a loading message while enhancing videos
        loading.value = true
        
        // Use a subset of videos for faster processing during development
        // In production, use all videos
        const videosToProcess = mediaStore.videos.slice(0, 20) // Process first 20 videos
        
        try {
          rawVideos.value = await enhanceVideosWithRelatedMedia(videosToProcess)
          
          // Debug the first few enhanced videos
          if (rawVideos.value.length > 0) {
            const firstFewVideos = rawVideos.value.slice(0, 3)
            console.log('First few enhanced videos:', firstFewVideos)
            
            // Count how many videos have related media
            const videosWithAudio = rawVideos.value.filter(v => v.relatedAudio).length
            const videosWithTranscript = rawVideos.value.filter(v => v.relatedTranscript).length
            const videosWithAudioUrl = rawVideos.value.filter(v => v.related_audio_url).length
            const videosWithTranscriptUrl = rawVideos.value.filter(v => v.related_transcript_url).length
            
            console.log(`Videos with related audio: ${videosWithAudio}/${rawVideos.value.length}`)
            console.log(`Videos with related transcript: ${videosWithTranscript}/${rawVideos.value.length}`)
            console.log(`Videos with direct audio URL: ${videosWithAudioUrl}/${rawVideos.value.length}`)
            console.log(`Videos with direct transcript URL: ${videosWithTranscriptUrl}/${rawVideos.value.length}`)
          }
        } catch (enhanceError) {
          console.error('Error enhancing videos with related media:', enhanceError)
          // Fall back to non-enhanced videos
          rawVideos.value = mediaStore.videos.map(video => ({
            ...video,
            relatedAudio: null,
            relatedTranscript: null,
            related_audio_url: null,
            related_transcript_url: null
          }))
        } finally {
          loading.value = false
        }
      } else {
        console.warn('No videos to enhance with related media')
      }
    } catch (apiError) {
      console.error('API error:', apiError)
      error.value = 'Failed to load media from API'
      
      // Use mock data as fallback
      console.log('Using mock data as fallback')
      rawVideos.value = [
        {
          id: 1,
          title: 'Sample Video 1',
          description: 'Legislative Session Day 1',
          year: '2025',
          category: 'House Chambers',
          date: '2025-01-01',
          url: '#',
          relatedAudio: {
            id: 101,
            title: 'Sample Audio 1',
            url: '#'
          },
          relatedTranscript: {
            id: 201,
            title: 'Sample Transcript 1',
            url: '#'
          },
          related_audio_url: '#',
          related_transcript_url: '#'
        },
        {
          id: 2, 
          title: 'Sample Video 2',
          description: 'Legislative Session Day 2',
          year: '2025',
          category: 'House Chambers',
          date: '2025-01-02',
          url: '#',
          relatedAudio: {
            id: 102,
            title: 'Sample Audio 2',
            url: '#'
          },
          relatedTranscript: null,
          related_audio_url: '#',
          related_transcript_url: null
        },
        {
          id: 3, 
          title: 'Sample Video 3',
          description: 'Legislative Session Day 10',
          year: '2025',
          category: 'House Chambers',
          date: '2025-01-10',
          url: '#',
          relatedAudio: null,
          relatedTranscript: null,
          related_audio_url: null,
          related_transcript_url: null
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
  <div class="videos-page">
    <h1 class="page-title">Legislative Media</h1>
    <p class="page-description">Browse videos, audio recordings, and transcripts from Idaho legislative sessions</p>
    
    <!-- Loading state -->
    <div v-if="loading" class="status-message">
      <p>Loading media...</p>
    </div>
    
    <!-- Error state -->
    <div v-else-if="error" class="status-message error">
      <p>{{ error }}</p>
      <button @click="mediaStore.fetchVideos">Retry</button>
    </div>
    
    <!-- Filter controls -->
    <div v-else class="filter-controls">
      <div class="filter-row">
        <div class="filter-group">
          <label for="year-filter">Year:</label>
          <select id="year-filter" v-model="selectedYear" class="filter-select">
            <option value="">All Years</option>
            <option v-for="year in availableYears" :key="year" :value="year">{{ year }}</option>
          </select>
        </div>
        
        <div class="filter-group">
          <label for="category-filter">Chamber:</label>
          <select id="category-filter" v-model="selectedCategory" class="filter-select">
            <option value="">All Chambers</option>
            <option v-for="category in availableCategories" :key="category" :value="category">{{ category }}</option>
          </select>
        </div>
        
        <button @click="resetFilters" class="reset-button">
          Reset Filters
        </button>
      </div>
    </div>
    
    <!-- Empty state -->
    <div v-if="!loading && !error && videos.length === 0" class="status-message">
      <p>No videos found with the selected filters.</p>
    </div>
    
    <!-- Video listing -->
    <div v-if="!loading && !error && videos.length > 0" class="video-container">
      <table class="video-list-table">
        <thead>
          <tr>
            <th>Title</th>
            <th>Session Day</th>
            <th>Chambers</th>
            <th>Date</th>
            <th>Media</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="video in videos" :key="video.id" class="video-list-item">
            <td class="video-title">{{ video.title }}</td>
            <td class="video-session">{{ video.description }}</td>
            <td class="video-chamber">{{ video.category }}</td>
            <td class="video-date">{{ video.date }}</td>
            <td class="video-actions">
              <div class="media-links">
                <!-- Video link -->
                <a :href="video.url" class="media-link video-link" target="_blank" download>
                  <img :src="videoIcon" alt="Video" class="media-icon" /> Video
                </a>
                
                <!-- Audio link - use direct URL reference -->
                <a 
                  v-if="video.related_audio_url" 
                  :href="video.related_audio_url" 
                  class="media-link audio-link" 
                  target="_blank" 
                  download
                >
                  <img :src="audioIcon" alt="Audio" class="media-icon" /> Audio
                </a>
                <span v-else class="media-link disabled">
                  <img :src="audioIcon" alt="Audio" class="media-icon disabled-icon" /> No Audio
                </span>
                
                <!-- Transcript link - use direct URL reference -->
                <a 
                  v-if="video.related_transcript_url" 
                  :href="video.related_transcript_url" 
                  class="media-link transcript-link" 
                  target="_blank" 
                  download
                >
                  <img :src="transcriptIcon" alt="Transcript" class="media-icon" /> Transcript
                </a>
                <span v-else class="media-link disabled">
                  <img :src="transcriptIcon" alt="Transcript" class="media-icon disabled-icon" /> No Transcript
                </span>
                
                <!-- Debug button - always visible in this version -->
                <button 
                  @click.prevent="showVideoDetails(video)" 
                  class="media-link debug-button"
                >
                  Debug
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
      
      <!-- Pagination controls -->
      <div class="pagination-controls" v-if="totalPages > 1">
        <div class="pagination-info">
          Showing {{ (currentPage - 1) * itemsPerPage + 1 }} - 
          {{ Math.min(currentPage * itemsPerPage, filteredSortedVideos.length) }} 
          of {{ filteredSortedVideos.length }} videos
        </div>
        
        <div class="pagination-buttons">
          <button 
            @click="goToPage(1)" 
            class="pagination-button" 
            :disabled="currentPage === 1"
            :class="{ 'disabled': currentPage === 1 }"
          >
            &laquo;
          </button>
          
          <button 
            @click="goToPage(currentPage - 1)" 
            class="pagination-button"
            :disabled="currentPage === 1"
            :class="{ 'disabled': currentPage === 1 }"
          >
            &lsaquo;
          </button>
          
          <span class="pagination-current">{{ currentPage }} of {{ totalPages }}</span>
          
          <button 
            @click="goToPage(currentPage + 1)" 
            class="pagination-button"
            :disabled="currentPage === totalPages"
            :class="{ 'disabled': currentPage === totalPages }"
          >
            &rsaquo;
          </button>
          
          <button 
            @click="goToPage(totalPages)" 
            class="pagination-button"
            :disabled="currentPage === totalPages"
            :class="{ 'disabled': currentPage === totalPages }"
          >
            &raquo;
          </button>
        </div>
        
        <div class="items-per-page">
          <label for="items-per-page">Items per page:</label>
          <select 
            id="items-per-page" 
            v-model="itemsPerPage" 
            @change="currentPage = 1"
            class="items-select"
          >
            <option :value="10">10</option>
            <option :value="25">25</option>
            <option :value="50">50</option>
            <option :value="100">100</option>
          </select>
        </div>
      </div>

      <!-- Debug info about sorting (can be removed in production) -->
      <div class="debug-info" v-if="false">
        <p>Videos are sorted by:</p>
        <ol>
          <li>Year (newest first)</li>
          <li>Category (alphabetical)</li>
          <li>Session Day number (extracted from description)</li>
          <li>Date (if available)</li>
        </ol>
      </div>
      
      <!-- Debug Panel -->
      <div v-if="debugPanelVisible" class="debug-panel">
        <div class="debug-panel-header">
          <h3>Video Details</h3>
          <button @click="closeDebugPanel" class="close-button">&times;</button>
        </div>
        <div v-if="selectedVideo" class="debug-panel-content">
          <div class="debug-section">
            <h4>Basic Info</h4>
            <p><strong>ID:</strong> {{ selectedVideo.id }}</p>
            <p><strong>Title:</strong> {{ selectedVideo.title }}</p>
            <p><strong>URL:</strong> {{ selectedVideo.url }}</p>
            <p><strong>Session ID:</strong> {{ selectedVideo.session_id || 'Not set' }}</p>
          </div>
          
          <div class="debug-section">
            <h4>Audio References</h4>
            <p><strong>related_audio_id:</strong> {{ selectedVideo.related_audio_id || 'Not set' }}</p>
            <p><strong>related_audio_url:</strong> {{ selectedVideo.related_audio_url || 'Not set' }}</p>
            <div v-if="selectedVideo.relatedAudio">
              <p><strong>relatedAudio Object:</strong></p>
              <pre>{{ JSON.stringify(selectedVideo.relatedAudio, null, 2) }}</pre>
            </div>
            <p v-else><strong>relatedAudio Object:</strong> Not set</p>
          </div>
          
          <div class="debug-section">
            <h4>Transcript References</h4>
            <p><strong>related_transcript_id:</strong> {{ selectedVideo.related_transcript_id || 'Not set' }}</p>
            <p><strong>related_transcript_url:</strong> {{ selectedVideo.related_transcript_url || 'Not set' }}</p>
            <div v-if="selectedVideo.relatedTranscript">
              <p><strong>relatedTranscript Object:</strong></p>
              <pre>{{ JSON.stringify(selectedVideo.relatedTranscript, null, 2) }}</pre>
            </div>
            <p v-else><strong>relatedTranscript Object:</strong> Not set</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.videos-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 1rem;
}

.page-title {
  font-size: 1.75rem;
  font-weight: bold;
  margin-bottom: 0.5rem;
}

.page-description {
  font-size: 1rem;
  color: #6b7280;
  margin-bottom: 1.5rem;
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

.video-container {
  margin-top: 1rem;
  overflow-x: auto;
}

.video-list-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
  background-color: white;
  border-radius: 0.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.video-list-table th {
  text-align: left;
  padding: 0.75rem 1rem;
  font-weight: 600;
  font-size: 0.875rem;
  color: #374151;
  background-color: #f3f4f6;
  border-bottom: 1px solid #e5e7eb;
}

.video-list-table td {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #e5e7eb;
  font-size: 0.875rem;
}

.video-list-item:hover {
  background-color: #f9fafb;
}

.video-title {
  font-weight: 500;
}

.video-chamber, .video-date {
  color: #6b7280;
}

.video-actions {
  vertical-align: middle;
}

.media-links {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.media-link {
  display: inline-flex;
  align-items: center;
  padding: 0.5rem 0.75rem;
  border-radius: 0.25rem;
  font-size: 0.8rem;
  font-weight: 500;
  text-decoration: none;
  transition: all 0.2s ease;
  white-space: nowrap;
  margin-bottom: 0.5rem;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.media-link:hover:not(.disabled) {
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.15);
}

.video-link {
  background-color: #1e3a8a;
  color: white;
  border: 1px solid #1e3a8a;
}

.video-link:hover {
  background-color: #1e40af;
}

.audio-link {
  background-color: #047857;
  color: white;
  border: 1px solid #047857;
}

.audio-link:hover {
  background-color: #065f46;
}

.transcript-link {
  background-color: #9d174d;
  color: white;
  border: 1px solid #9d174d;
}

.transcript-link:hover {
  background-color: #831843;
}

.media-link.disabled {
  background-color: #f3f4f6;
  color: #9ca3af;
  cursor: not-allowed;
  border: 1px solid #e5e7eb;
  box-shadow: none;
}

.media-icon {
  width: 16px;
  height: 16px;
  margin-right: 0.5rem;
  vertical-align: middle;
  object-fit: contain;
}

.disabled-icon {
  opacity: 0.5;
  filter: grayscale(100%);
}

.debug-info {
  margin-top: 2rem;
  padding: 1rem;
  background-color: #f9f9f9;
  border-radius: 0.5rem;
  font-size: 0.875rem;
}

.debug-button {
  background-color: #7c3aed;
  color: white;
  border: 1px solid #6d28d9;
}

.debug-button:hover {
  background-color: #6d28d9;
}

.debug-panel {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background-color: white;
  border-radius: 0.5rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  width: 90%;
  max-width: 800px;
  max-height: 80vh;
  z-index: 100;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.debug-panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background-color: #f3f4f6;
  border-bottom: 1px solid #e5e7eb;
}

.debug-panel-header h3 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
}

.close-button {
  background: none;
  border: none;
  font-size: 1.5rem;
  line-height: 1;
  cursor: pointer;
  padding: 0.25rem;
  color: #6b7280;
}

.debug-panel-content {
  padding: 1rem;
  overflow-y: auto;
  flex-grow: 1;
}

.debug-section {
  margin-bottom: 1.5rem;
}

.debug-section h4 {
  margin-top: 0;
  margin-bottom: 0.5rem;
  font-size: 1rem;
  font-weight: 600;
  color: #374151;
}

.debug-section p {
  margin: 0.25rem 0;
  font-size: 0.875rem;
}

.debug-section pre {
  background-color: #f3f4f6;
  padding: 0.75rem;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-all;
  margin-top: 0.5rem;
}

/* Pagination styles */
.pagination-controls {
  margin-top: 1.5rem;
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem 1rem;
  background-color: #f9fafb;
  border-radius: 0.5rem;
  border: 1px solid #e5e7eb;
}

.pagination-info {
  font-size: 0.875rem;
  color: #6b7280;
}

.pagination-buttons {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.pagination-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  padding: 0;
  border: 1px solid #d1d5db;
  border-radius: 0.25rem;
  background-color: white;
  cursor: pointer;
  font-size: 0.875rem;
}

.pagination-button:hover:not(.disabled) {
  background-color: #f3f4f6;
}

.pagination-button.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.pagination-current {
  margin: 0 0.5rem;
  font-size: 0.875rem;
}

.items-per-page {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
}

.items-select {
  padding: 0.25rem 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 0.25rem;
  background-color: white;
  font-size: 0.75rem;
}

/* Filter styles */
.filter-controls {
  margin: 1rem 0;
  padding: 1rem;
  background-color: #f9fafb;
  border-radius: 0.5rem;
  border: 1px solid #e5e7eb;
}

.filter-row {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  align-items: center;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.filter-select {
  padding: 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  background-color: white;
  font-size: 0.875rem;
  min-width: 150px;
}

.reset-button {
  padding: 0.5rem 1rem;
  background-color: #e5e7eb;
  border: none;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  cursor: pointer;
  font-weight: 500;
  color: #374151;
}

.reset-button:hover {
  background-color: #d1d5db;
}
</style>