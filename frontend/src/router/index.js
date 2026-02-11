import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/LoginView.vue'),
    meta: { public: true },
  },
  {
    path: '/setup',
    name: 'setup',
    component: () => import('../views/SetupView.vue'),
    meta: { public: true },
  },
  {
    path: '/',
    name: 'dashboard',
    component: () => import('../views/DashboardView.vue'),
  },
  {
    path: '/sites',
    name: 'sites',
    component: () => import('../views/SitesView.vue'),
  },
  {
    path: '/crawler/:siteId',
    name: 'crawler',
    component: () => import('../views/CrawlerView.vue'),
    props: true,
  },
  {
    path: '/pages/:siteId',
    name: 'pages',
    component: () => import('../views/PagesView.vue'),
    props: true,
  },
  {
    path: '/rules/:siteId',
    name: 'rules',
    component: () => import('../views/RulesView.vue'),
    props: true,
  },
  {
    path: '/security',
    name: 'security',
    component: () => import('../views/SecurityView.vue'),
  },
  {
    path: '/analytics',
    name: 'analytics',
    component: () => import('../views/AnalyticsView.vue'),
  },
  {
    path: '/shield',
    name: 'shield',
    component: () => import('../views/ShieldView.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  if (to.meta.public) return true

  const auth = useAuthStore()

  if (!auth.authenticated) {
    const isValid = await auth.checkAuth()
    if (!isValid) {
      return { name: 'login' }
    }
  }

  return true
})

export default router
