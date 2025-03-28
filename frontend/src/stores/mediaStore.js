import { defineStore } from 'pinia'
import axios from 'axios'

// Define the API base URL 
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api'

// Create an axios instance with common configuration
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
})

// Add a response interceptor for error handling
api.interceptors.response.use(
  response => response,
  error => {
    console.error('API Error:', error.response || error.message)
    return Promise.reject(error)
  }
)

export const useMediaStore = defineStore('media', {
  state: () => ({
    // Collection of media items by type
    videos: [],
    audio: [],
    transcripts: [],
    
    // Current selected item
    currentItem: null,
    
    // UI state
    loading: false,
    error: null,
    
    // Filter state
    filters: {
      year: null,
      category: null,
      searchQuery: '',
    },
    
    // Available filter options
    years: [],
    categories: [],
  }),
  
  getters: {
    // Helper function to filter items based on common filter criteria
    filterItems: (state) => (items) => {
      return items.filter(item => {
        // Filter by year
        if (state.filters.year && item.year !== state.filters.year) {
          return false
        }
        
        // Filter by category
        if (state.filters.category && item.category !== state.filters.category) {
          return false
        }
        
        // Filter by search query
        if (state.filters.searchQuery) {
          const query = state.filters.searchQuery.toLowerCase()
          return item.title.toLowerCase().includes(query) || 
                 (item.description && item.description.toLowerCase().includes(query))
        }
        
        return true
      })
    },
    
    // Get filtered videos based on current filters
    filteredVideos: (state, getters) => {
      return getters.filterItems(state.videos)
    },
    
    // Get filtered audio based on current filters
    filteredAudio: (state, getters) => {
      return getters.filterItems(state.audio)
    },
    
    // Get filtered transcripts based on current filters
    filteredTranscripts: (state, getters) => {
      return getters.filterItems(state.transcripts)
    }
  },
  
  actions: {
    // Mock data for fallback when API is unavailable
    getMockVideos() {
      return [
        {
          id: 1,
          title: 'House Chambers - January 7, 2025',
          description: 'Legislative Session Day 1',
          year: '2025',
          category: 'House Chambers',
          date: '2025-01-07',
          duration: '01:25:30',
          thumbnail: 'https://via.placeholder.com/300x180',
          url: 'https://example.com/video1.mp4'
        },
        {
          id: 2,
          title: 'House Chambers - January 8, 2025',
          description: 'Legislative Session Day 2',
          year: '2025',
          category: 'House Chambers',
          date: '2025-01-08',
          duration: '01:15:20',
          thumbnail: 'https://via.placeholder.com/300x180',
          url: 'https://example.com/video2.mp4'
        },
        {
          id: 3,
          title: 'Senate Chambers - January 7, 2025',
          description: 'Legislative Session Day 1',
          year: '2025',
          category: 'Senate Chambers',
          date: '2025-01-07',
          duration: '01:45:10',
          thumbnail: 'https://via.placeholder.com/300x180',
          url: 'https://example.com/video3.mp4'
        }
      ]
    },
    
    getMockAudio() {
      return [
        {
          id: 1,
          title: 'House Chambers - January 7, 2025 (Audio)',
          description: 'Legislative Session Day 1',
          year: '2025',
          category: 'House Chambers',
          date: '2025-01-07',
          duration: '01:25:30',
          url: 'https://example.com/audio1.mp3'
        },
        {
          id: 2,
          title: 'House Chambers - January 8, 2025 (Audio)',
          description: 'Legislative Session Day 2',
          year: '2025',
          category: 'House Chambers',
          date: '2025-01-08',
          duration: '01:15:20',
          url: 'https://example.com/audio2.mp3'
        }
      ]
    },
    
    getMockTranscripts() {
      return [
        {
          id: 1,
          title: 'House Chambers - January 7, 2025 (Transcript)',
          description: 'Legislative Session Day 1',
          year: '2025',
          category: 'House Chambers',
          date: '2025-01-07',
          url: 'https://example.com/transcript1.pdf'
        },
        {
          id: 2,
          title: 'House Chambers - January 8, 2025 (Transcript)',
          description: 'Legislative Session Day 2',
          year: '2025',
          category: 'House Chambers',
          date: '2025-01-08',
          url: 'https://example.com/transcript2.pdf'
        }
      ]
    },
    
    // Fetch videos from API
    async fetchVideos() {
      this.loading = true
      this.error = null
      
      try {
        console.log('fetchVideos: Starting API request')
        // Try to fetch from API
        try {
          const response = await api.get('/videos')
          this.videos = response.data
          console.log('fetchVideos: API success')
        } catch (apiError) {
          console.warn('API not available, using mock data', apiError)
          // If API fails, use mock data
          console.log('fetchVideos: Using mock data')
          this.videos = this.getMockVideos()
        }
        
        console.log('fetchVideos: Videos loaded', this.videos.length)
        
        // Extract years and categories for filters
        this.years = [...new Set(this.videos.map(video => video.year))]
        this.categories = [...new Set(this.videos.map(video => video.category))]
      } catch (error) {
        this.error = error.message || 'Failed to fetch videos'
        console.error('Error fetching videos:', error)
      } finally {
        this.loading = false
      }
    },
    
    // Fetch audio from API
    async fetchAudio() {
      this.loading = true
      this.error = null
      
      try {
        // Try to fetch from API
        try {
          const response = await api.get('/audio')
          this.audio = response.data
        } catch (apiError) {
          console.warn('API not available, using mock data', apiError)
          // If API fails, use mock data
          this.audio = this.getMockAudio()
        }
      } catch (error) {
        this.error = error.message || 'Failed to fetch audio'
        console.error('Error fetching audio:', error)
      } finally {
        this.loading = false
      }
    },
    
    // Fetch transcripts from API
    async fetchTranscripts() {
      this.loading = true
      this.error = null
      
      try {
        // Try to fetch from API
        try {
          const response = await api.get('/transcripts')
          this.transcripts = response.data
        } catch (apiError) {
          console.warn('API not available, using mock data', apiError)
          // If API fails, use mock data
          this.transcripts = this.getMockTranscripts()
        }
      } catch (error) {
        this.error = error.message || 'Failed to fetch transcripts'
        console.error('Error fetching transcripts:', error)
      } finally {
        this.loading = false
      }
    },
    
    // Get a single item by ID and type
    async getItemById(type, id) {
      this.loading = true
      this.error = null
      
      try {
        // Try to fetch from API
        try {
          const response = await api.get(`/${type}/${id}`)
          return response.data
        } catch (apiError) {
          console.warn('API not available, finding in store', apiError)
          // If API fails, look for the item in store
          if (type === 'videos') {
            return this.videos.find(item => item.id === parseInt(id)) || null
          } else if (type === 'audio') {
            return this.audio.find(item => item.id === parseInt(id)) || null
          } else if (type === 'transcripts') {
            return this.transcripts.find(item => item.id === parseInt(id)) || null
          }
          return null
        }
      } catch (error) {
        this.error = error.message || `Failed to fetch ${type} item`
        console.error(`Error fetching ${type} item:`, error)
        return null
      } finally {
        this.loading = false
      }
    },
    
    // Set the current item
    setCurrentItem(item) {
      this.currentItem = item
    },
    
    // Update filters
    updateFilters(newFilters) {
      this.filters = { ...this.filters, ...newFilters }
    },
    
    // Reset filters
    resetFilters() {
      this.filters = {
        year: null,
        category: null,
        searchQuery: '',
      }
    }
  }
})