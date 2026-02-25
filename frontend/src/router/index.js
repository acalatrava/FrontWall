import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  {
    path: '/',
    redirect: '/dashboard',
  },
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
    path: '/forgot-password',
    name: 'forgot-password',
    component: () => import('../views/ForgotPasswordView.vue'),
    meta: { public: true },
  },
  {
    path: '/reset-password',
    name: 'reset-password',
    component: () => import('../views/ResetPasswordView.vue'),
    meta: { public: true },
  },
  {
    path: '/accept-invite',
    name: 'accept-invite',
    component: () => import('../views/AcceptInviteView.vue'),
    meta: { public: true },
  },
  {
    path: '/dashboard',
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
  {
    path: '/profile',
    name: 'profile',
    component: () => import('../views/ProfileView.vue'),
  },
  {
    path: '/users',
    name: 'users',
    component: () => import('../views/UsersView.vue'),
    meta: { adminOnly: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to) {
    if (to.hash) return { el: to.hash, behavior: 'smooth' }
    return { top: 0 }
  },
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

  if (to.meta.adminOnly && !auth.isAdmin) {
    return { name: 'dashboard' }
  }

  return true
})

export default router
