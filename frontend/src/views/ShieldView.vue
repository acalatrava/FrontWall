<template>
  <div>
    <h1 class="text-2xl font-bold text-white mb-6">Shield Deployment</h1>

    <div class="bg-gray-900 border border-gray-800 rounded-xl p-8 mb-6">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-4">
          <div
            class="w-16 h-16 rounded-full flex items-center justify-center"
            :class="shieldStore.active ? 'bg-green-500/20' : 'bg-gray-800'"
          >
            <svg class="w-8 h-8" :class="shieldStore.active ? 'text-green-400' : 'text-gray-600'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
              <path v-if="shieldStore.active" d="m9 12 2 2 4-4" stroke="currentColor"/>
            </svg>
          </div>
          <div>
            <h2 class="text-xl font-bold" :class="shieldStore.active ? 'text-green-400' : 'text-gray-400'">
              {{ shieldStore.active ? 'Shield Active' : 'Shield Inactive' }}
            </h2>
            <p class="text-sm text-gray-500 mt-1">
              {{ shieldStore.active
                ? `Serving cached content on port ${shieldStore.port}`
                : 'Deploy the shield to start serving protected content'
              }}
            </p>
          </div>
        </div>
        <div>
          <button
            v-if="shieldStore.active"
            @click="handleUndeploy"
            :disabled="shieldStore.loading"
            class="px-6 py-3 bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white font-medium rounded-lg transition-colors"
          >
            {{ shieldStore.loading ? 'Stopping...' : 'Undeploy Shield' }}
          </button>
        </div>
      </div>
    </div>

    <div v-if="!shieldStore.active" class="bg-gray-900 border border-gray-800 rounded-xl p-6">
      <h2 class="text-lg font-semibold text-white mb-4">Deploy Shield</h2>
      <p class="text-sm text-gray-400 mb-4">
        Select a site to deploy. The shield will serve its cached content on port {{ shieldStore.port }}.
      </p>

      <div v-if="sites.length === 0" class="text-center text-gray-500 py-4">
        No sites configured.
        <router-link to="/sites" class="text-blue-400 hover:underline">Add a site first.</router-link>
      </div>

      <div v-else class="space-y-3">
        <div
          v-for="site in sites"
          :key="site.id"
          class="flex items-center justify-between bg-gray-800/50 rounded-lg px-5 py-4 hover:bg-gray-800 transition-colors"
        >
          <div>
            <div class="font-medium text-white">{{ site.name }}</div>
            <div class="text-sm text-gray-400">{{ site.target_url }}</div>
          </div>
          <button
            @click="handleDeploy(site.id)"
            :disabled="shieldStore.loading"
            class="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white text-sm font-medium rounded-lg transition-colors"
          >
            Deploy
          </button>
        </div>
      </div>
    </div>

    <div v-if="shieldStore.active" class="bg-gray-900 border border-gray-800 rounded-xl p-6">
      <h2 class="text-lg font-semibold text-white mb-4">Connection Info</h2>
      <div class="space-y-3 text-sm">
        <div class="flex items-center gap-3">
          <span class="text-gray-400 w-32">Shield Port:</span>
          <code class="bg-gray-800 px-3 py-1 rounded text-blue-400">{{ shieldStore.port }}</code>
        </div>
        <div class="flex items-center gap-3">
          <span class="text-gray-400 w-32">Proxy Config:</span>
          <code class="bg-gray-800 px-3 py-1 rounded text-green-400 text-xs">
            proxy_pass http://webshield:{{ shieldStore.port }};
          </code>
        </div>
      </div>
    </div>

    <div v-if="deployError" class="mt-4 bg-red-500/10 border border-red-500/30 rounded-xl px-6 py-4 text-sm text-red-400">
      {{ deployError }}
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useSitesStore } from '../stores/sites'
import { useShieldStore } from '../stores/shield'

const sitesStore = useSitesStore()
const shieldStore = useShieldStore()
const { sites } = storeToRefs(sitesStore)
const deployError = ref('')

onMounted(() => {
  sitesStore.fetchSites()
  shieldStore.fetchStatus()
})

async function handleDeploy(siteId) {
  deployError.value = ''
  try {
    await shieldStore.deploy(siteId)
  } catch (e) {
    deployError.value = e.response?.data?.detail || 'Failed to deploy shield'
  }
}

async function handleUndeploy() {
  try {
    await shieldStore.undeploy()
  } catch (e) {
    deployError.value = e.response?.data?.detail || 'Failed to undeploy shield'
  }
}
</script>
