<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import mainLogo from '../../assets/main.png'

const router = useRouter()
const mobileMenuOpen = ref(false)

// Toggle mobile menu
const toggleMobileMenu = () => {
  mobileMenuOpen.value = !mobileMenuOpen.value
}

// Close mobile menu
const closeMobileMenu = () => {
  mobileMenuOpen.value = false
}

// Navigation items
const navItems = [
  { name: 'Home', path: '/', icon: 'home' },
  { name: 'Media', path: '/videos', icon: 'video' },
  { name: 'Sitemap', path: '/sitemap', icon: 'map' },
  { name: 'Admin', path: '/admin', icon: 'settings' },
  { name: 'Diagnostic', path: '/diagnostic', icon: 'tools' }
]

// Active route
const isActive = (path) => {
  return router.currentRoute.value.path === path
}
</script>

<template>
  <header class="bg-primary-900 dark:bg-primary-900 shadow-sm text-white" role="banner">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between h-16">
        <!-- Logo and Desktop Navigation -->
        <div class="flex">
          <div class="flex-shrink-0 flex items-center">
            <router-link to="/" class="flex items-center">
              <div class="logo-container">
                <img :src="mainLogo" alt="Legislative Video Reviews with AI" class="app-logo" />
              </div>
            </router-link>
          </div>
          
          <!-- Desktop Navigation -->
          <nav class="hidden sm:ml-8 sm:flex sm:space-x-4" role="navigation" aria-label="Main navigation">
            <router-link
              v-for="item in navItems"
              :key="item.name"
              :to="item.path"
              :class="[
                isActive(item.path)
                  ? 'border-white text-white font-semibold bg-primary-700 px-4 py-2 rounded-md'
                  : 'border-transparent text-white hover:bg-primary-700 hover:text-white hover:scale-105 px-4 py-2 rounded-md transition-transform',
                'inline-flex items-center text-base font-semibold'
              ]"
            >
              {{ item.name }}
            </router-link>
          </nav>
        </div>
        
        <!-- Right side actions -->
        <div class="flex items-center">
          <!-- Theme toggle (placeholder) -->
          <button class="p-2 rounded-md text-white hover:text-gray-200 dark:text-gray-200 dark:hover:text-white">
            <span class="sr-only">Toggle theme</span>
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
              <path d="M10 2a8 8 0 100 16 8 8 0 000-16zm0 14a6 6 0 110-12 6 6 0 010 12z" />
              <path fill-rule="evenodd" d="M10 14a4 4 0 100-8 4 4 0 000 8zm0-2a2 2 0 100-4 2 2 0 000 4z" clip-rule="evenodd" />
            </svg>
          </button>
          
          <!-- Mobile menu button -->
          <div class="sm:hidden ml-4 flex items-center">
            <button 
              @click="toggleMobileMenu"
              class="inline-flex items-center justify-center p-2 rounded-md text-white hover:text-gray-200 dark:text-gray-200 dark:hover:text-white"
              aria-expanded="mobileMenuOpen"
              aria-controls="mobile-menu"
            >
              <span class="sr-only">{{ mobileMenuOpen ? 'Close main menu' : 'Open main menu' }}</span>
              <svg 
                v-if="!mobileMenuOpen" 
                xmlns="http://www.w3.org/2000/svg" 
                class="h-6 w-6" 
                fill="none" 
                viewBox="0 0 24 24" 
                stroke="currentColor"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
              </svg>
              <svg 
                v-else 
                xmlns="http://www.w3.org/2000/svg" 
                class="h-6 w-6" 
                fill="none" 
                viewBox="0 0 24 24" 
                stroke="currentColor"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Mobile menu -->
    <div v-if="mobileMenuOpen" class="sm:hidden" id="mobile-menu" role="navigation" aria-label="Mobile navigation">
      <div class="pt-2 pb-3 space-y-1">
        <router-link
          v-for="item in navItems"
          :key="item.name"
          :to="item.path"
          @click="closeMobileMenu"
          :class="[
            isActive(item.path)
              ? 'bg-primary-700 border-white text-white dark:bg-primary-800'
              : 'border-transparent text-white hover:bg-primary-700 hover:border-white hover:text-white dark:hover:bg-primary-800',
            'block pl-3 pr-4 py-2 border-l-4 text-base font-semibold'
          ]"
        >
          {{ item.name }}
        </router-link>
      </div>
    </div>
  </header>
</template>

<style scoped>
.logo-container {
  height: 40px;
  overflow: hidden;
  display: flex;
  align-items: center;
}

.app-logo {
  height: 40px;
  width: auto;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.25));
  transition: transform 0.3s ease;
}

.app-logo:hover {
  transform: scale(1.05);
}

@media (max-width: 640px) {
  .logo-container {
    height: 32px;
  }
  
  .app-logo {
    height: 32px;
  }
}
</style>