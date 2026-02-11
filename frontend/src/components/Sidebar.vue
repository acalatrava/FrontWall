<template>
  <aside class="w-64 bg-gray-900 border-r border-gray-800 flex flex-col">
    <div class="p-5 border-b border-gray-800">
      <div class="flex items-center gap-3">
        <svg class="w-8 h-8 text-blue-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
          <path d="m9 12 2 2 4-4" stroke="#22c55e"/>
        </svg>
        <span class="text-lg font-bold text-white">FrontWall</span>
      </div>
    </div>

    <nav class="flex-1 p-4 space-y-1">
      <router-link
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors"
        :class="isActive(item.to) ? 'bg-blue-600/20 text-blue-400' : 'text-gray-400 hover:bg-gray-800 hover:text-gray-200'"
      >
        <component :is="item.icon" class="w-5 h-5" />
        {{ item.label }}
      </router-link>
    </nav>

    <div class="p-4 border-t border-gray-800">
      <button
        @click="logout"
        class="flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-sm text-gray-400 hover:bg-gray-800 hover:text-gray-200 transition-colors"
      >
        <LogoutIcon class="w-5 h-5" />
        Logout
      </button>
    </div>
  </aside>
</template>

<script setup>
import { h } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

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
const LogoutIcon = makeIcon(['M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4', 'M16 17l5-5-5-5', 'M21 12H9'])

const navItems = [
  { to: '/', label: 'Dashboard', icon: DashboardIcon },
  { to: '/sites', label: 'Sites', icon: SitesIcon },
  { to: '/security', label: 'Security', icon: SecurityIcon },
  { to: '/analytics', label: 'Analytics', icon: AnalyticsIcon },
  { to: '/shield', label: 'Shield', icon: ShieldIcon },
]

async function logout() {
  await auth.logout()
  router.push('/login')
}
</script>
