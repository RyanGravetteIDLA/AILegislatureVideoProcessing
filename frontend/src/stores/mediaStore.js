import { defineStore } from 'pinia'
import axios from 'axios'

// Define the API base URL with a fallback
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api'

// Also handle the case where the trailing /api might be missing
const NORMALIZED_API_URL = API_BASE_URL.endsWith('/api') 
  ? API_BASE_URL 
  : `${API_BASE_URL}/api`

// Define the file server URL with a fallback
const FILE_SERVER_URL = import.meta.env.VITE_FILE_SERVER_URL || 'http://localhost:5001'

console.log('Using API URL:', NORMALIZED_API_URL)
console.log('Using File Server URL:', FILE_SERVER_URL)

// Helper function to ensure URLs are complete
const ensureCompleteUrl = (url) => {
  if (!url) return url
  
  // If the URL is already absolute (starts with http:// or https://), return it as is
  if (url.startsWith('http://') || url.startsWith('https://')) {
    return url
  }
  
  // If the URL starts with /api/files/, prefix it with the file server URL
  if (url.startsWith('/api/files/')) {
    // Remove the /api prefix since the file server URL already includes it
    const path = url.replace(/^\/api/, '')
    return `${FILE_SERVER_URL}${path}`
  }
  
  // Return the URL as is in other cases
  return url
}

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
          // Process URLs to ensure they're complete and handle enhanced fields
          this.videos = response.data.map(video => {
            // Process the main video URL
            const processedVideo = {
              ...video,
              url: ensureCompleteUrl(video.url)
            }
            
            // Process related media URLs if they exist
            if (video.related_audio_url) {
              processedVideo.related_audio_url = ensureCompleteUrl(video.related_audio_url)
            }
            if (video.related_transcript_url) {
              processedVideo.related_transcript_url = ensureCompleteUrl(video.related_transcript_url)
            }
            if (video.related_video_url) {
              processedVideo.related_video_url = ensureCompleteUrl(video.related_video_url)
            }
            
            return processedVideo
          })
          console.log(`Loaded ${this.videos.length} videos with enhanced data`)
          
          // Log the first video for debugging
          if (this.videos.length > 0) {
            console.log('First video item sample:', this.videos[0])
          }
          
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
        
        // Set empty arrays
        this.videos = []
        console.log('API request failed, no videos loaded')
        
        // Set empty filter options
        this.years = []
        this.categories = []
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
          
          // Process URLs to ensure they're complete and handle enhanced fields
          this.audio = response.data.map(audio => {
            // Process the main audio URL
            const processedAudio = {
              ...audio,
              url: ensureCompleteUrl(audio.url)
            }
            
            // Process related media URLs if they exist
            if (audio.related_video_url) {
              processedAudio.related_video_url = ensureCompleteUrl(audio.related_video_url)
            }
            if (audio.related_transcript_url) {
              processedAudio.related_transcript_url = ensureCompleteUrl(audio.related_transcript_url)
            }
            
            return processedAudio
          })
          console.log(`Loaded ${this.audio.length} audio files with enhanced data`)
          
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
        
        // Set empty array
        this.audio = []
        console.log('API request failed, no audio loaded')
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
          
          // Process URLs to ensure they're complete and handle enhanced fields
          this.transcripts = response.data.map(transcript => {
            // Process the main transcript URL
            const processedTranscript = {
              ...transcript,
              url: ensureCompleteUrl(transcript.url)
            }
            
            // Process related media URLs if they exist
            if (transcript.related_video_url) {
              processedTranscript.related_video_url = ensureCompleteUrl(transcript.related_video_url)
            }
            if (transcript.related_audio_url) {
              processedTranscript.related_audio_url = ensureCompleteUrl(transcript.related_audio_url)
            }
            
            return processedTranscript
          })
          console.log(`Loaded ${this.transcripts.length} transcripts with enhanced data`)
          
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
        
        // Set empty array
        this.transcripts = []
        console.log('API request failed, no transcripts loaded')
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
            // Process URLs to ensure they're complete and handle enhanced fields
            const item = {
              ...response.data,
              url: ensureCompleteUrl(response.data.url)
            }
            
            // Process related media URLs if they exist
            if (response.data.related_video_url) {
              item.related_video_url = ensureCompleteUrl(response.data.related_video_url)
            }
            if (response.data.related_audio_url) {
              item.related_audio_url = ensureCompleteUrl(response.data.related_audio_url)
            }
            if (response.data.related_transcript_url) {
              item.related_transcript_url = ensureCompleteUrl(response.data.related_transcript_url)
            }
            
            console.log(`Loaded ${type} item with enhanced data:`, item)
            return item
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
    
    // Get related media (audio and transcript) for a video using the enhanced API endpoint
    async getVideoRelatedMedia(videoId) {
      if (!videoId) {
        console.warn('No video ID provided to getVideoRelatedMedia')
        return { audio: null, transcript: null }
      }
      
      try {
        // Determine if we're using the new API format or old API format
        const apiUrl = api.defaults.baseURL;
        const isNewApiFormat = apiUrl.includes('cloud-function-api') || apiUrl.includes('media_portal_api');
        
        // Adjust endpoint based on API format
        const endpoint = isNewApiFormat ? `/videos/${videoId}/related` : `/api/videos/${videoId}/related`;
        
        console.log(`Fetching related media for video ID: ${videoId} using endpoint: ${endpoint}`)
        const response = await api.get(endpoint, { timeout: 15000 })
        
        if (response.data) {
          const result = {
            audio: null,
            transcript: null
          }
          
          // Process the audio if available
          if (response.data.audio) {
            // Ensure the URL is complete
            result.audio = {
              ...response.data.audio,
              url: ensureCompleteUrl(response.data.audio.url || response.data.audio.gcs_path || '')
            }
          }
          
          // Process the transcript if available
          if (response.data.transcript) {
            // Ensure the URL is complete
            result.transcript = {
              ...response.data.transcript,
              url: ensureCompleteUrl(response.data.transcript.url || response.data.transcript.gcs_path || '')
            }
          }
          
          console.log('Found related media for video:', result)
          return result
        } else {
          console.warn(`No related media found for video ${videoId}`)
          return { audio: null, transcript: null }
        }
      } catch (error) {
        console.error(`Error fetching related media for video ${videoId}:`, error)
        
        // Fall back to the traditional method when API fails
        console.log('Falling back to traditional related media matching method')
        const audio = await this.getRelatedAudio({ id: videoId })
        const transcript = await this.getRelatedTranscript({ id: videoId })
        
        return {
          audio,
          transcript
        }
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
          // Process URLs to ensure they're complete
          const transcripts = response.data.map(transcript => ({
            ...transcript,
            url: ensureCompleteUrl(transcript.url)
          }))
          console.log(`Found ${transcripts.length} transcripts for video ID ${videoId}:`, transcripts)
          return transcripts
        } else {
          console.warn(`No transcripts found for video ID ${videoId}`)
          return []
        }
      } catch (error) {
        console.error(`Error fetching transcripts for video ID ${videoId}:`, error)
        return []
      }
    },
    
    // Get audio related to a video using enhanced fields
    async getRelatedAudio(video) {
      if (!video || !video.id) {
        console.warn('Invalid video provided to getRelatedAudio')
        return null
      }
      
      console.log(`Finding related audio for video: "${video.title}"`)
      
      // Strategy 0: Check if the video already has a direct audio URL with enhanced fields
      if (video.related_audio_url && video.related_audio_id) {
        console.log(`Video has complete related audio information: ID=${video.related_audio_id}, URL=${video.related_audio_url}`)
        // Try to get the complete audio object
        try {
          const audioItem = await this.getItemById('audio', video.related_audio_id)
          if (audioItem) {
            console.log(`Found complete related audio via related_audio_id: ${audioItem.title}`)
            return audioItem
          }
        } catch (err) {
          console.warn(`Couldn't fetch complete audio ${video.related_audio_id}, using minimal object instead`, err)
        }
        
        // Fallback to creating a minimal audio object if we can't fetch the complete one
        return {
          id: video.related_audio_id,
          title: `Audio for ${video.title}`,
          url: video.related_audio_url,
          year: video.year,
          category: video.category,
          session_id: video.session_id,
          session_name: video.session_name
        }
      }
      
      // Strategy 1: Check if the video has related_audio_id field (for backward compatibility)
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
    
    // Get transcript related to a video using enhanced fields
    async getRelatedTranscript(video) {
      if (!video || !video.id) {
        console.warn('Invalid video provided to getRelatedTranscript')
        return null
      }
      
      console.log(`Finding related transcript for video: "${video.title}"`)
      
      // Strategy 0: Check if the video already has direct transcript URL with enhanced fields
      if (video.related_transcript_url && video.related_transcript_id) {
        console.log(`Video has complete related transcript information: ID=${video.related_transcript_id}, URL=${video.related_transcript_url}`)
        // Try to get the complete transcript object
        try {
          const transcriptItem = await this.getItemById('transcripts', video.related_transcript_id)
          if (transcriptItem) {
            console.log(`Found complete related transcript via related_transcript_id: ${transcriptItem.title}`)
            return transcriptItem
          }
        } catch (err) {
          console.warn(`Couldn't fetch complete transcript ${video.related_transcript_id}, using minimal object instead`, err)
        }
        
        // Fallback to creating a minimal transcript object if we can't fetch the complete one
        return {
          id: video.related_transcript_id,
          title: `Transcript for ${video.title}`,
          url: video.related_transcript_url,
          year: video.year,
          category: video.category,
          session_id: video.session_id,
          session_name: video.session_name
        }
      }
      
      // Strategy 1: Check if the video has a related_transcript_id field (for backward compatibility)
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