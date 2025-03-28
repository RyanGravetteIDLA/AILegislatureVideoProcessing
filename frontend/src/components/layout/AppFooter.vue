<script setup>
// Get current year for copyright
const currentYear = new Date().getFullYear()
</script>

<template>
  <footer class="bg-primary-800 dark:bg-primary-900 mt-auto text-white" role="contentinfo">
    <div class="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
      <div class="flex flex-col md:flex-row justify-between items-center">
        <!-- Logo and copyright -->
        <div class="mb-4 md:mb-0">
          <div class="flex items-center">
            <span class="text-lg font-semibold text-white dark:text-gray-100">Legislative Media</span>
          </div>
          <p class="text-sm text-gray-200 dark:text-gray-300 mt-1">
            &copy; {{ currentYear }} Idaho Legislature Media Processor
          </p>
        </div>
        
        <!-- Links -->
        <nav aria-label="Footer navigation" class="flex space-x-6">
          <router-link to="/" class="text-gray-200 hover:text-white dark:text-gray-300 dark:hover:text-white focus:outline-2 focus:outline-offset-2 focus:outline-primary-300">
            Home
          </router-link>
          <router-link to="/videos" class="text-gray-200 hover:text-white dark:text-gray-300 dark:hover:text-white focus:outline-2 focus:outline-offset-2 focus:outline-primary-300">
            Videos
          </router-link>
          <router-link to="/audio" class="text-gray-200 hover:text-white dark:text-gray-300 dark:hover:text-white focus:outline-2 focus:outline-offset-2 focus:outline-primary-300">
            Audio
          </router-link>
          <router-link to="/transcripts" class="text-gray-200 hover:text-white dark:text-gray-300 dark:hover:text-white focus:outline-2 focus:outline-offset-2 focus:outline-primary-300">
            Transcripts
          </router-link>
          <router-link to="/sitemap" class="text-gray-200 hover:text-white dark:text-gray-300 dark:hover:text-white focus:outline-2 focus:outline-offset-2 focus:outline-primary-300">
            Sitemap
          </router-link>
        </nav>
      </div>
    </div>
  </footer>
</template>