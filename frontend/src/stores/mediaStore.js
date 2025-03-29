import { defineStore } from 'pinia'
import axios from 'axios'

// Define the API base URL with a fallback
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api'

// Also handle the case where the trailing /api might be missing
const NORMALIZED_API_URL = API_BASE_URL.endsWith('/api') 
  ? API_BASE_URL 
  : `${API_BASE_URL}/api`

console.log('Using API URL:', NORMALIZED_API_URL)

// Create an axios instance with common configuration
const api = axios.create({
  baseURL: NORMALIZED_API_URL,
  timeout: 15000, // Increased timeout for slow connections
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
})

// Add request interceptor for debugging
api.interceptors.request.use(
  config => {
    console.log('API Request:', config.method.toUpperCase(), config.url)
    
    // Add a timestamp to prevent caching issues
    if (config.method.toLowerCase() === 'get') {
      config.params = { 
        ...config.params, 
        _t: new Date().getTime() 
      }
    }
    
    return config
  },
  error => {
    console.error('API Request Error:', error)
    return Promise.reject(error)
  }
)

// Add a response interceptor for error handling
api.interceptors.response.use(
  response => {
    console.log('API Response:', response.status, response.config.url)
    return response
  },
  error => {
    // More detailed error logging
    if (error.response) {
      // The request was made and the server responded with a status code
      // that falls out of the range of 2xx
      console.error('API Error Response:', {
        status: error.response.status,
        statusText: error.response.statusText,
        url: error.config?.url,
        data: error.response.data
      })
    } else if (error.request) {
      // The request was made but no response was received
      console.error('API No Response:', {
        url: error.config?.url,
        message: 'No response received from server'
      })
    } else {
      // Something happened in setting up the request that triggered an Error
      console.error('API Request Setup Error:', {
        message: error.message,
        url: error.config?.url
      })
    }
    
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
        console.log('Fetching videos from API')
        
        // First, try to fetch filter options
        try {
          const filtersResponse = await api.get('/filters', { timeout: 10000 })
          if (filtersResponse.data && filtersResponse.data.years && filtersResponse.data.categories) {
            this.years = filtersResponse.data.years
            this.categories = filtersResponse.data.categories
            console.log('Loaded filter options from API:', this.years, this.categories)
          }
        } catch (filterError) {
          console.warn('Failed to load filter options:', filterError)
          // We'll continue and try to extract filters from video data
        }
        
        // Now fetch videos from API
        const response = await api.get('/videos', { timeout: 15000 })
        
        // Process response
        if (response.data && Array.isArray(response.data)) {
          this.videos = response.data
          console.log(`Loaded ${this.videos.length} videos`)
          
          // Update filter options if they weren't already loaded
          if (this.years.length === 0) {
            this.years = [...new Set(this.videos.map(video => video.year))]
            this.categories = [...new Set(this.videos.map(video => video.category))]
          }
        } else {
          throw new Error('Invalid API response format')
        }
      } catch (error) {
        console.error('Error fetching videos:', error)
        this.error = 'Failed to load videos from the server'
        
        // Use mock data as fallback
        this.videos = this.getMockVideos()
        console.log('Using mock data as fallback')
        
        // Also set filter options from mock data
        this.years = [...new Set(this.videos.map(video => video.year))]
        this.categories = [...new Set(this.videos.map(video => video.category))]
      } finally {
        this.loading = false
      }
    },
    
    // Fetch audio from API
    async fetchAudio() {
      this.loading = true
      this.error = null
      
      try {
        console.log('Fetching audio from API')
        
        // First, try to fetch filter options if we don't have them yet
        if (this.years.length === 0 || this.categories.length === 0) {
          try {
            const filtersResponse = await api.get('/filters', { timeout: 10000 })
            if (filtersResponse.data && filtersResponse.data.years && filtersResponse.data.categories) {
              this.years = filtersResponse.data.years
              this.categories = filtersResponse.data.categories
              console.log('Loaded filter options from API:', this.years, this.categories)
            }
          } catch (filterError) {
            console.warn('Failed to load filter options:', filterError)
          }
        }
        
        // Now fetch audio from API
        const response = await api.get('/audio', { timeout: 15000 })
        
        // Process response
        if (response.data && Array.isArray(response.data)) {
          console.log('Raw audio response data:', response.data)
          this.audio = response.data
          console.log(`Loaded ${this.audio.length} audio files`)
          
          if (this.audio.length > 0) {
            console.log('First audio item sample:', this.audio[0])
          } else {
            console.warn('Audio array is empty')
          }
          
          // Update filter options if they weren't already loaded
          if (this.years.length === 0) {
            this.years = [...new Set([
              ...this.audio.map(item => item.year),
              ...this.videos.map(item => item.year)
            ])]
            this.categories = [...new Set([
              ...this.audio.map(item => item.category),
              ...this.videos.map(item => item.category)
            ])]
          }
        } else {
          console.error('Invalid API response format for audio:', response.data)
          throw new Error('Invalid API response format')
        }
      } catch (error) {
        console.error('Error fetching audio:', error)
        this.error = 'Failed to load audio from the server'
        
        // Use mock data as fallback
        this.audio = this.getMockAudio()
        console.log('Using mock data as fallback')
      } finally {
        this.loading = false
      }
    },
    
    // Fetch transcripts from API
    async fetchTranscripts() {
      this.loading = true
      this.error = null
      
      try {
        console.log('Fetching transcripts from API')
        
        // First, try to fetch filter options if we don't have them yet
        if (this.years.length === 0 || this.categories.length === 0) {
          try {
            const filtersResponse = await api.get('/filters', { timeout: 10000 })
            if (filtersResponse.data && filtersResponse.data.years && filtersResponse.data.categories) {
              this.years = filtersResponse.data.years
              this.categories = filtersResponse.data.categories
              console.log('Loaded filter options from API:', this.years, this.categories)
            }
          } catch (filterError) {
            console.warn('Failed to load filter options:', filterError)
          }
        }
        
        // Now fetch transcripts from API
        const response = await api.get('/transcripts', { timeout: 15000 })
        
        // Process response
        if (response.data && Array.isArray(response.data)) {
          console.log('Raw transcripts response data:', response.data)
          this.transcripts = response.data
          console.log(`Loaded ${this.transcripts.length} transcripts`)
          
          if (this.transcripts.length > 0) {
            console.log('First transcript item sample:', this.transcripts[0])
          } else {
            console.warn('Transcripts array is empty')
          }
          
          // Update filter options if they weren't already loaded
          if (this.years.length === 0) {
            this.years = [...new Set([
              ...this.transcripts.map(item => item.year),
              ...this.videos.map(item => item.year),
              ...this.audio.map(item => item.year)
            ])]
            this.categories = [...new Set([
              ...this.transcripts.map(item => item.category),
              ...this.videos.map(item => item.category),
              ...this.audio.map(item => item.category)
            ])]
          }
        } else {
          console.error('Invalid API response format for transcripts:', response.data)
          throw new Error('Invalid API response format')
        }
      } catch (error) {
        console.error('Error fetching transcripts:', error)
        this.error = 'Failed to load transcripts from the server'
        
        // Use mock data as fallback
        this.transcripts = this.getMockTranscripts()
        console.log('Using mock data as fallback')
      } finally {
        this.loading = false
      }
    },
    
    // Get a single item by ID and type
    async getItemById(type, id) {
      this.loading = true
      this.error = null
      
      try {
        console.log(`Fetching ${type} item with ID: ${id}`)
        
        // Try to fetch from API
        try {
          const response = await api.get(`/${type}/${id}`, { timeout: 15000 })
          
          if (response.data) {
            console.log(`Loaded ${type} item:`, response.data)
            return response.data
          } else {
            throw new Error(`No ${type} item found with ID: ${id}`)
          }
        } catch (apiError) {
          console.warn(`API failed when fetching ${type}/${id}:`, apiError)
          
          // If API fails, look for the item in store
          let item = null;
          
          if (type === 'videos') {
            // Try exact match first
            item = this.videos.find(v => v.id === id)
            // If not found, try with parseInt if id is a string
            if (!item && typeof id === 'string') {
              item = this.videos.find(v => v.id === parseInt(id))
            }
          } else if (type === 'audio') {
            item = this.audio.find(a => a.id === id)
            if (!item && typeof id === 'string') {
              item = this.audio.find(a => a.id === parseInt(id))
            }
          } else if (type === 'transcripts') {
            item = this.transcripts.find(t => t.id === id)
            if (!item && typeof id === 'string') {
              item = this.transcripts.find(t => t.id === parseInt(id))
            }
          }
          
          if (item) {
            console.log(`Found ${type} item in store:`, item)
            return item
          } else {
            console.error(`Item not found in store for ${type}/${id}`)
            throw new Error(`Item not found: ${type}/${id}`)
          }
        }
      } catch (error) {
        this.error = error.message || `Failed to fetch ${type} item`
        console.error(`Error fetching ${type} item:`, error)
        return null
      } finally {
        this.loading = false
      }
    },
    
    // Get transcripts related to a video
    async getTranscriptsForVideo(videoId) {
      if (!videoId) {
        console.warn('No video ID provided to getTranscriptsForVideo')
        return []
      }
      
      try {
        console.log(`Fetching transcripts for video ID: ${videoId}`)
        const response = await api.get(`/videos/${videoId}/transcripts`, { timeout: 15000 })
        
        if (response.data && Array.isArray(response.data)) {
          console.log(`Found ${response.data.length} transcripts for video ID ${videoId}:`, response.data)
          return response.data
        } else {
          console.warn(`No transcripts found for video ID ${videoId}`)
          return []
        }
      } catch (error) {
        console.error(`Error fetching transcripts for video ID ${videoId}:`, error)
        return []
      }
    },
    
    // Get audio related to a video using session_id or related_audio_id
    async getRelatedAudio(video) {
      if (!video || !video.id) {
        console.warn('Invalid video provided to getRelatedAudio')
        return null
      }
      
      console.log(`Finding related audio for video: "${video.title}"`)
      
      // Strategy 0: Check if the video already has a direct audio URL
      if (video.related_audio_url) {
        console.log(`Video already has direct related_audio_url: ${video.related_audio_url}`)
        // Create a minimal audio object if we only have the URL
        return {
          id: video.related_audio_id || 'unknown',
          title: `Audio for ${video.title}`,
          url: video.related_audio_url
        }
      }
      
      // Strategy 1: Check if the video has a related_audio_id field
      if (video.related_audio_id) {
        try {
          console.log(`Video has related_audio_id: ${video.related_audio_id}`)
          const audioItem = await this.getItemById('audio', video.related_audio_id)
          if (audioItem) {
            console.log(`Found related audio via related_audio_id: ${audioItem.title}`)
            return audioItem
          }
        } catch (err) {
          console.warn(`Couldn't fetch audio ${video.related_audio_id} referenced by video`, err)
        }
      }
      
      // Strategy 2: Check if the video has a session_id and find audio with the same session_id
      if (video.session_id) {
        console.log(`Looking for audio with session_id: ${video.session_id}`)
        const matchingAudio = this.audio.find(audio => 
          audio.session_id === video.session_id
        )
        
        if (matchingAudio) {
          console.log(`Found related audio via session_id: ${matchingAudio.title}`)
          return matchingAudio
        }
      }
      
      // Strategy 3: Try to find a transcript that's related to this video
      try {
        const relatedTranscripts = await this.getTranscriptsForVideo(video.id)
        
        // Check if any transcript references an audio file
        for (const transcript of relatedTranscripts) {
          if (transcript.related_audio_id) {
            // Try to get the audio file
            try {
              const audioItem = await this.getItemById('audio', transcript.related_audio_id)
              if (audioItem) {
                console.log(`Found related audio via transcript: ${audioItem.title}`)
                return audioItem
              }
            } catch (err) {
              console.warn(`Couldn't fetch audio ${transcript.related_audio_id} referenced by transcript`)
            }
          }
        }
      } catch (err) {
        console.warn('Error fetching transcripts to find related audio:', err)
      }
      
      // Strategy 4: Fall back to title/metadata matching
      console.log('Falling back to title/metadata matching')
      return this.findRelatedAudioByMetadata(video)
    },
    
    // Get audio related to a video based on metadata matching (fallback method)
    async findRelatedAudioByMetadata(video) {
      if (!video) return null
      
      const videoTitle = video.title || ''
      const videoYear = video.year || ''
      const videoCategory = video.category || ''
      const videoDate = video.date || ''
      const videoId = video.id || ''
      const videoUrl = video.url || ''
      
      let matchingAudio = null
      
      console.log(`Finding related audio for video: "${videoTitle}" with ID: "${videoId}"`)
      console.log(`Video URL: ${videoUrl}`)
      
      // Extract session info from title
      let sessionInfo = {
        chamber: '',
        day: '',
        date: ''
      }
      
      try {
        // Extract chamber and session day
        if (videoTitle.includes('House Chambers')) {
          sessionInfo.chamber = 'House Chambers'
        } else if (videoTitle.includes('Senate Chambers')) {
          sessionInfo.chamber = 'Senate Chambers'
        }
        
        // Extract session day
        const dayMatch = videoTitle.match(/Session Day (\d+)/i)
        if (dayMatch && dayMatch[1]) {
          sessionInfo.day = dayMatch[1]
        }
        
        // Extract date from URL if available
        const dateMatch = videoUrl.match(/(\d{2}-\d{2}-\d{4})/i)
        if (dateMatch && dateMatch[1]) {
          sessionInfo.date = dateMatch[1]
        }
        
        console.log('Extracted session info:', sessionInfo)
      } catch (e) {
        console.warn('Error extracting session info from video:', e)
      }
      
      // Extract filename from URL for pattern matching
      let videoFilename = ''
      try {
        const urlParts = videoUrl.split('/')
        videoFilename = urlParts[urlParts.length - 1]
        console.log(`Video filename: ${videoFilename}`)
      } catch (e) {
        console.warn('Error extracting filename from URL:', e)
      }
      
      // Try multiple matching strategies in order of reliability
      
      // Strategy 1: Match on ID pattern (convert video ID to audio ID)
      if (videoId && this.audio.length > 0) {
        const audioIdPattern = videoId.replace('_video', '_audio')
        matchingAudio = this.audio.find(audio => 
          audio.id === audioIdPattern
        )
        
        if (matchingAudio) {
          console.log(`Found related audio via ID pattern matching: ${matchingAudio.title}`)
          return matchingAudio
        }
      }
      
      // Strategy 2: Match on filename pattern (replace file extension)
      if (videoFilename && this.audio.length > 0) {
        // Try different audio extensions (.mp3, .wav, etc.)
        const baseFilename = videoFilename.replace(/\.\w+$/, '')
        console.log(`Looking for audio with base filename: ${baseFilename}`)
        
        matchingAudio = this.audio.find(audio => {
          const audioUrl = audio.url || ''
          const audioUrlParts = audioUrl.split('/')
          const audioFilename = audioUrlParts[audioUrlParts.length - 1]
          return audioFilename.includes(baseFilename)
        })
        
        if (matchingAudio) {
          console.log(`Found related audio via filename pattern: ${matchingAudio.title}`)
          return matchingAudio
        }
      }
      
      // Strategy 3: Match on chamber, date and session day
      if ((sessionInfo.chamber || videoCategory) && (sessionInfo.date || videoDate) && this.audio.length > 0) {
        const chamber = sessionInfo.chamber || videoCategory
        const date = sessionInfo.date || videoDate
        
        console.log(`Looking for audio with chamber: ${chamber}, date: ${date}`)
        
        matchingAudio = this.audio.find(audio => {
          // Check if audio title or category contains the chamber
          const hasChamber = (audio.title && audio.title.includes(chamber)) || 
                             (audio.category && audio.category.includes(chamber))
          
          // Check if audio has matching date
          const hasDate = (audio.date && audio.date.includes(date)) || 
                         (audio.url && audio.url.includes(date))
          
          return hasChamber && hasDate
        })
        
        if (matchingAudio) {
          console.log(`Found related audio via chamber and date: ${matchingAudio.title}`)
          return matchingAudio
        }
      }
      
      // Strategy 4: Match on session day and year
      if (sessionInfo.day && videoYear && this.audio.length > 0) {
        console.log(`Looking for audio with session day: ${sessionInfo.day}, year: ${videoYear}`)
        
        matchingAudio = this.audio.find(audio => {
          const hasSessionDay = audio.title && audio.title.includes(`Session Day ${sessionInfo.day}`)
          const hasYear = audio.year === videoYear
          return hasSessionDay && hasYear
        })
        
        if (matchingAudio) {
          console.log(`Found related audio via session day and year: ${matchingAudio.title}`)
          return matchingAudio
        }
      }
      
      // Strategy 5: Last resort - try to match on any parts of the title
      if (videoTitle && this.audio.length > 0) {
        // Split the title into significant parts (excluding common words)
        const titleParts = videoTitle.split(' ').filter(part => 
          part.length > 3 && !['the', 'and', 'with'].includes(part.toLowerCase())
        )
        
        if (titleParts.length > 0) {
          console.log(`Looking for audio matching title parts: ${titleParts.join(', ')}`)
          
          // Find audio with the most matching title parts
          let bestMatch = null
          let bestMatchScore = 0
          
          this.audio.forEach(audio => {
            if (!audio.title) return
            
            let matchScore = 0
            titleParts.forEach(part => {
              if (audio.title.includes(part)) {
                matchScore++
              }
            })
            
            if (matchScore > bestMatchScore) {
              bestMatchScore = matchScore
              bestMatch = audio
            }
          })
          
          if (bestMatch && bestMatchScore >= Math.ceil(titleParts.length / 2)) {
            console.log(`Found related audio via title parts matching: ${bestMatch.title} (score: ${bestMatchScore}/${titleParts.length})`)
            return bestMatch
          }
        }
      }
      
      console.log('No related audio found for video')
      return null
    },
    
    // Get transcript related to a video using session_id or related_transcript_id
    async getRelatedTranscript(video) {
      if (!video || !video.id) {
        console.warn('Invalid video provided to getRelatedTranscript')
        return null
      }
      
      console.log(`Finding related transcript for video: "${video.title}"`)
      
      // Strategy 0: Check if the video already has a direct transcript URL
      if (video.related_transcript_url) {
        console.log(`Video already has direct related_transcript_url: ${video.related_transcript_url}`)
        // Create a minimal transcript object if we only have the URL
        return {
          id: video.related_transcript_id || 'unknown',
          title: `Transcript for ${video.title}`,
          url: video.related_transcript_url
        }
      }
      
      // Strategy 1: Check if the video has a related_transcript_id field
      if (video.related_transcript_id) {
        try {
          console.log(`Video has related_transcript_id: ${video.related_transcript_id}`)
          const transcriptItem = await this.getItemById('transcripts', video.related_transcript_id)
          if (transcriptItem) {
            console.log(`Found related transcript via related_transcript_id: ${transcriptItem.title}`)
            return transcriptItem
          }
        } catch (err) {
          console.warn(`Couldn't fetch transcript ${video.related_transcript_id} referenced by video`, err)
        }
      }
      
      // Strategy 2: Check if the video has a session_id and find transcript with the same session_id
      if (video.session_id) {
        console.log(`Looking for transcript with session_id: ${video.session_id}`)
        const matchingTranscript = this.transcripts.find(transcript => 
          transcript.session_id === video.session_id
        )
        
        if (matchingTranscript) {
          console.log(`Found related transcript via session_id: ${matchingTranscript.title}`)
          return matchingTranscript
        }
      }
      
      // Strategy 3: Try API endpoint for related transcripts
      try {
        const relatedTranscripts = await this.getTranscriptsForVideo(video.id)
        if (relatedTranscripts && relatedTranscripts.length > 0) {
          console.log(`Found related transcript via API: ${relatedTranscripts[0].title}`)
          return relatedTranscripts[0]
        }
      } catch (err) {
        console.warn('Error fetching transcripts for video:', err)
      }
      
      // Strategy 4: Fall back to title/metadata matching
      console.log('Falling back to title/metadata matching for transcript')
      return this.findRelatedTranscriptByMetadata(video)
    },
    
    // Get transcript related to a video based on metadata matching (fallback method)
    async findRelatedTranscriptByMetadata(video) {
      if (!video) return null
      
      const videoTitle = video.title || ''
      const videoYear = video.year || ''
      const videoCategory = video.category || ''
      const videoDate = video.date || ''
      const videoId = video.id || ''
      const videoUrl = video.url || ''
      
      let matchingTranscript = null
      
      console.log(`Finding related transcript for video: "${videoTitle}" with ID: "${videoId}"`)
      console.log(`Video URL: ${videoUrl}`)
      
      // Extract session info from title
      let sessionInfo = {
        chamber: '',
        day: '',
        date: ''
      }
      
      try {
        // Extract chamber and session day
        if (videoTitle.includes('House Chambers')) {
          sessionInfo.chamber = 'House Chambers'
        } else if (videoTitle.includes('Senate Chambers')) {
          sessionInfo.chamber = 'Senate Chambers'
        }
        
        // Extract session day
        const dayMatch = videoTitle.match(/Session Day (\d+)/i)
        if (dayMatch && dayMatch[1]) {
          sessionInfo.day = dayMatch[1]
        }
        
        // Extract date from URL if available
        const dateMatch = videoUrl.match(/(\d{2}-\d{2}-\d{4})/i)
        if (dateMatch && dateMatch[1]) {
          sessionInfo.date = dateMatch[1]
        }
        
        console.log('Extracted session info:', sessionInfo)
      } catch (e) {
        console.warn('Error extracting session info from video:', e)
      }
      
      // Extract filename from URL for pattern matching
      let videoFilename = ''
      try {
        const urlParts = videoUrl.split('/')
        videoFilename = urlParts[urlParts.length - 1]
        console.log(`Video filename: ${videoFilename}`)
      } catch (e) {
        console.warn('Error extracting filename from URL:', e)
      }
      
      // Try multiple matching strategies in order of reliability
      
      // Strategy 1: Match on ID pattern (convert video ID to transcript ID)
      if (videoId && this.transcripts.length > 0) {
        const transcriptIdPattern = videoId.replace('_video', '_transcript')
        matchingTranscript = this.transcripts.find(transcript => 
          transcript.id === transcriptIdPattern
        )
        
        if (matchingTranscript) {
          console.log(`Found related transcript via ID pattern matching: ${matchingTranscript.title}`)
          return matchingTranscript
        }
      }
      
      // Strategy 2: Match on filename pattern (replace file extension)
      if (videoFilename && this.transcripts.length > 0) {
        // Try different transcript extensions (.pdf, .txt, etc.)
        const baseFilename = videoFilename.replace(/\.\w+$/, '')
        console.log(`Looking for transcript with base filename: ${baseFilename}`)
        
        matchingTranscript = this.transcripts.find(transcript => {
          const transcriptUrl = transcript.url || ''
          const transcriptUrlParts = transcriptUrl.split('/')
          const transcriptFilename = transcriptUrlParts[transcriptUrlParts.length - 1]
          return transcriptFilename.includes(baseFilename)
        })
        
        if (matchingTranscript) {
          console.log(`Found related transcript via filename pattern: ${matchingTranscript.title}`)
          return matchingTranscript
        }
      }
      
      // Strategy 3: Match on chamber, date and session day
      if ((sessionInfo.chamber || videoCategory) && (sessionInfo.date || videoDate) && this.transcripts.length > 0) {
        const chamber = sessionInfo.chamber || videoCategory
        const date = sessionInfo.date || videoDate
        
        console.log(`Looking for transcript with chamber: ${chamber}, date: ${date}`)
        
        matchingTranscript = this.transcripts.find(transcript => {
          // Check if transcript title or category contains the chamber
          const hasChamber = (transcript.title && transcript.title.includes(chamber)) || 
                             (transcript.category && transcript.category.includes(chamber))
          
          // Check if transcript has matching date
          const hasDate = (transcript.date && transcript.date.includes(date)) || 
                         (transcript.url && transcript.url.includes(date))
          
          return hasChamber && hasDate
        })
        
        if (matchingTranscript) {
          console.log(`Found related transcript via chamber and date: ${matchingTranscript.title}`)
          return matchingTranscript
        }
      }
      
      // Strategy 4: Match on session day and year
      if (sessionInfo.day && videoYear && this.transcripts.length > 0) {
        console.log(`Looking for transcript with session day: ${sessionInfo.day}, year: ${videoYear}`)
        
        matchingTranscript = this.transcripts.find(transcript => {
          const hasSessionDay = transcript.title && transcript.title.includes(`Session Day ${sessionInfo.day}`)
          const hasYear = transcript.year === videoYear
          return hasSessionDay && hasYear
        })
        
        if (matchingTranscript) {
          console.log(`Found related transcript via session day and year: ${matchingTranscript.title}`)
          return matchingTranscript
        }
      }
      
      // Strategy 5: Last resort - try to match on any parts of the title
      if (videoTitle && this.transcripts.length > 0) {
        // Split the title into significant parts (excluding common words)
        const titleParts = videoTitle.split(' ').filter(part => 
          part.length > 3 && !['the', 'and', 'with'].includes(part.toLowerCase())
        )
        
        if (titleParts.length > 0) {
          console.log(`Looking for transcript matching title parts: ${titleParts.join(', ')}`)
          
          // Find transcript with the most matching title parts
          let bestMatch = null
          let bestMatchScore = 0
          
          this.transcripts.forEach(transcript => {
            if (!transcript.title) return
            
            let matchScore = 0
            titleParts.forEach(part => {
              if (transcript.title.includes(part)) {
                matchScore++
              }
            })
            
            if (matchScore > bestMatchScore) {
              bestMatchScore = matchScore
              bestMatch = transcript
            }
          })
          
          if (bestMatch && bestMatchScore >= Math.ceil(titleParts.length / 2)) {
            console.log(`Found related transcript via title parts matching: ${bestMatch.title} (score: ${bestMatchScore}/${titleParts.length})`)
            return bestMatch
          }
        }
      }
      
      console.log('No related transcript found for video')
      return null
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