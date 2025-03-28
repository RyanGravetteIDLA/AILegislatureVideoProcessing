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
    meta: { title: 'Video Library' }
  },
  {
    path: '/audio',
    name: 'audio',
    component: () => import('../views/Audio.vue'),
    meta: { title: 'Audio Library' }
  },
  {
    path: '/transcripts',
    name: 'transcripts',
    component: () => import('../views/Transcripts.vue'),
    meta: { title: 'Transcript Library' }
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
  
  // Handle auth-required routes (to be implemented)
  if (to.meta.requiresAuth) {
    // For now, just allow access
    // This would check authentication status in a real app
    next()
  } else {
    next()
  }
})

export default router