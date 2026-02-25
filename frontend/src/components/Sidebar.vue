<template>
  <aside
    class="fixed md:static inset-y-0 left-0 z-50 w-64 bg-gray-900 border-r border-gray-800 flex flex-col transition-transform duration-200 ease-in-out"
    :class="mobileOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'"
  >
    <div class="p-5 border-b border-gray-800">
      <div class="flex items-center gap-3">
        <svg class="w-8 h-8 text-blue-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
          <path d="m9 12 2 2 4-4" stroke="#22c55e"/>
        </svg>
        <span class="text-lg font-bold text-white">FrontWall</span>
      </div>
    </div>

    <nav class="flex-1 p-4 space-y-1 overflow-y-auto">
      <router-link
        v-for="item in visibleNav"
        :key="item.to"
        :to="item.to"
        @click="$emit('close')"
        class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors"
        :class="isActive(item.to) ? 'bg-blue-600/20 text-blue-400' : 'text-gray-400 hover:bg-gray-800 hover:text-gray-200'"
      >
        <component :is="item.icon" class="w-5 h-5 flex-shrink-0" />
        {{ t(item.labelKey) }}
      </router-link>
    </nav>

    <div class="p-4 border-t border-gray-800 space-y-2">
      <div class="px-3 py-1">
        <select
          :value="currentLocale"
          @change="switchLocale($event.target.value)"
          class="w-full px-2.5 py-1.5 bg-gray-800 border border-gray-700 rounded-lg text-xs text-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option v-for="loc in locales" :key="loc" :value="loc">{{ localeLabels[loc] }}</option>
        </select>
      </div>

      <router-link to="/profile" class="block px-3 py-2 rounded-lg hover:bg-gray-800 transition-colors cursor-pointer" @click="$emit('close')">
        <div class="flex items-center justify-between">
          <div class="text-sm font-medium text-white truncate">{{ auth.user?.email }}</div>
          <svg class="w-3.5 h-3.5 text-gray-500 flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 01-2.83 2.83l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z"/></svg>
        </div>
        <div class="flex items-center gap-1.5 mt-0.5">
          <span class="text-xs px-1.5 py-0.5 rounded-full"
                :class="auth.user?.role === 'admin' ? 'bg-purple-500/10 text-purple-400' : 'bg-blue-500/10 text-blue-400'">
            {{ auth.user?.role }}
          </span>
          <span v-if="auth.user?.has_passkey" class="text-[10px] text-emerald-400">
            <svg class="w-3 h-3 inline" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0110 0v4"/></svg>
          </span>
        </div>
      </router-link>
      <button
        @click="handleLogout"
        class="flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-sm text-gray-400 hover:bg-gray-800 hover:text-gray-200 transition-colors"
      >
        <LogoutIcon class="w-5 h-5 flex-shrink-0" />
        {{ t('nav.logout') }}
      </button>
    </div>
  </aside>
</template>

<script setup>
import { h, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '../stores/auth'
import { setLocale } from '../i18n'

defineProps({ mobileOpen: { type: Boolean, default: false } })
defineEmits(['close'])

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const { t, locale: currentLocale } = useI18n()
const locales = ['en', 'es']
const localeLabels = { en: 'English', es: 'Español' }

function switchLocale(loc) {
  setLocale(loc)
}

const isActive = (path) => route.path === path || route.path.startsWith(path + '/')

function makeIcon(pathD) {
  return {
    render() {
      return h('svg', { viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '2', 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, [
        ...(Array.isArray(pathD) ? pathD : [pathD]).map(d => h('path', { d }))
      ])
    }
  }
}

const DashboardIcon = makeIcon(['M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z', 'M9 22V12h6v10'])
const SitesIcon = makeIcon(['M12 2L2 7l10 5 10-5-10-5z', 'M2 17l10 5 10-5', 'M2 12l10 5 10-5'])
const ShieldIcon = makeIcon('M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z')
const SecurityIcon = makeIcon(['M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z', 'M12 8v4', 'M12 16h.01'])
const AnalyticsIcon = makeIcon(['M18 20V10', 'M12 20V4', 'M6 20v-6'])
const UsersIcon = makeIcon(['M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2', 'M9 7a4 4 0 100 8 4 4 0 000-8z', 'M23 21v-2a4 4 0 00-3-3.87', 'M16 3.13a4 4 0 010 7.75'])
const LogoutIcon = makeIcon(['M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4', 'M16 17l5-5-5-5', 'M21 12H9'])

const allNav = [
  { to: '/dashboard', labelKey: 'nav.dashboard', icon: DashboardIcon, adminOnly: false },
  { to: '/sites', labelKey: 'nav.sites', icon: SitesIcon, adminOnly: false },
  { to: '/security', labelKey: 'nav.security', icon: SecurityIcon, adminOnly: false },
  { to: '/analytics', labelKey: 'nav.analytics', icon: AnalyticsIcon, adminOnly: false },
  { to: '/shield', labelKey: 'nav.shield', icon: ShieldIcon, adminOnly: false },
  { to: '/users', labelKey: 'nav.users', icon: UsersIcon, adminOnly: true },
]

const visibleNav = computed(() =>
  allNav.filter(item => !item.adminOnly || auth.isAdmin)
)

async function handleLogout() {
  await auth.logout()
  router.push('/login')
}
</script>
