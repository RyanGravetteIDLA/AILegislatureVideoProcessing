<script setup>
import AppHeader from './AppHeader.vue'
import AppFooter from './AppFooter.vue'
</script>

<template>
  <div class="min-h-screen flex flex-col bg-gray-50 dark:bg-gray-900">
    <!-- Skip to content link for keyboard users -->
    <a href="#main-content" class="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-white focus:text-primary-700 focus:outline focus:outline-primary-400">
      Skip to main content
    </a>
    
    <AppHeader />
    
    <main id="main-content" class="flex-grow" role="main" aria-label="Main content">
      <div class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <!-- Page content -->
        <slot></slot>
      </div>
    </main>
    
    <AppFooter />
  </div>
</template>