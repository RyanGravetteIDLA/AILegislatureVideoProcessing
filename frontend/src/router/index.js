import { createRouter, createWebHistory } from 'vue-router'

// Import views
import Home from '../views/Home.vue'

const routes = [
  {
    path: '/',
    name: 'home',
    component: Home,
    meta: { title: 'Dashboard' }
  },
  {
    path: '/videos',
    name: 'videos',
    component: () => import('../views/Videos.vue'),
    meta: { title: 'Media Library' }
  },
  {
    path: '/audio',
    redirect: '/videos',
    meta: { title: 'Media Library' }
  },
  {
    path: '/transcripts',
    redirect: '/videos',
    meta: { title: 'Media Library' }
  },
  {
    path: '/sitemap',
    name: 'sitemap',
    component: () => import('../views/Sitemap.vue'),
    meta: { title: 'Sitemap' }
  },
  {
    path: '/admin',
    name: 'admin',
    component: () => import('../views/Admin.vue'),
    meta: { title: 'Admin Dashboard', requiresAuth: true }
  },
  {
    path: '/diagnostic',
    name: 'diagnostic',
    component: () => import('../views/Diagnostic.vue'),
    meta: { title: 'API Diagnostic' }
  },
  // Add a catch-all route for 404
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: Home,
    meta: { title: 'Page Not Found' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  }
})

// Navigation guards
router.beforeEach((to, from, next) => {
  // Set document title
  document.title = `${to.meta.title || 'Home'} | Idaho Legislature Media`
  
  // Add analytics tracking here if needed
  console.log(`Route changed: ${from.path} → ${to.path}`)
  
  // Handle auth-required routes (to be implemented)
  if (to.meta.requiresAuth) {
    // For now, just allow access
    // This would check authentication status in a real app
    next()
  } else {
    next()
  }
})

// Handle errors during navigation
router.onError((error) => {
  console.error('Navigation error:', error)
  
  // Log the error but don't attempt to reload
  // This prevents potential infinite reload loops
})

export default router