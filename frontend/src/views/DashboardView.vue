<template>
  <div>
    <h1 class="text-2xl font-bold text-white mb-6">Dashboard</h1>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
      <div class="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <div class="text-sm text-gray-400 mb-1">Total Sites</div>
        <div class="text-3xl font-bold text-white">{{ sites.length }}</div>
      </div>
      <div class="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <div class="text-sm text-gray-400 mb-1">Active Shields</div>
        <div class="flex items-center gap-2 mt-1">
          <span class="w-3 h-3 rounded-full" :class="activeCount > 0 ? 'bg-green-500' : 'bg-gray-600'"></span>
          <span class="text-xl font-bold" :class="activeCount > 0 ? 'text-green-400' : 'text-gray-500'">
            {{ activeCount }} / {{ sites.length }}
          </span>
        </div>
      </div>
      <div class="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <div class="text-sm text-gray-400 mb-1">Shield Ports</div>
        <div v-if="shieldStore.shields.length" class="flex flex-wrap gap-2 mt-1">
          <code v-for="s in shieldStore.shields" :key="s.site_id" class="px-2 py-0.5 bg-gray-800 rounded text-blue-400 text-sm">{{ s.port }}</code>
        </div>
        <div v-else class="text-xl font-bold text-gray-500 mt-1">None</div>
      </div>
    </div>

    <div class="bg-gray-900 border border-gray-800 rounded-xl">
      <div class="px-6 py-4 border-b border-gray-800">
        <h2 class="text-lg font-semibold text-white">Configured Sites</h2>
      </div>
      <div v-if="sites.length === 0" class="p-6 text-center text-gray-500">
        No sites configured yet.
        <router-link to="/sites" class="text-blue-400 hover:underline ml-1">Add a site</router-link>
      </div>
      <div v-else class="divide-y divide-gray-800">
        <div v-for="site in sites" :key="site.id" class="px-6 py-4 flex items-center justify-between">
          <div>
            <div class="font-medium text-white">{{ site.name }}</div>
            <div class="text-sm text-gray-400">{{ site.target_url }}</div>
          </div>
          <div class="flex items-center gap-3">
            <span
              class="px-2.5 py-1 rounded-full text-xs font-medium"
              :class="site.shield_active ? 'bg-green-500/10 text-green-400' : 'bg-gray-700/50 text-gray-400'"
            >
              {{ site.shield_active ? `Port ${site.shield_port}` : 'Unshielded' }}
            </span>
            <router-link
              :to="`/crawler/${site.id}`"
              class="text-sm text-blue-400 hover:text-blue-300"
            >
              Manage
            </router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useSitesStore } from '../stores/sites'
import { useShieldStore } from '../stores/shield'

const sitesStore = useSitesStore()
const shieldStore = useShieldStore()
const { sites } = storeToRefs(sitesStore)

const activeCount = computed(() => shieldStore.shields.filter(s => s.active).length)

onMounted(() => {
  sitesStore.fetchSites()
  shieldStore.fetchStatus()
})
</script>
