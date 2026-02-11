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

    <div v-if="shieldStore.active" class="bg-gray-900 border border-gray-800 rounded-xl p-6 mb-6">
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

    <div v-if="shieldStore.active" class="bg-gray-900 border border-gray-800 rounded-xl p-6 mb-6">
      <div class="flex items-center justify-between mb-4">
        <div>
          <h2 class="text-lg font-semibold text-white">Learn Mode</h2>
          <p class="text-sm text-gray-400 mt-1">
            When enabled, the shield automatically learns from live traffic:
          </p>
          <ul class="text-xs text-gray-500 mt-2 space-y-1 list-disc list-inside">
            <li>POST requests are captured and forwarded to the origin, creating exception rules automatically</li>
            <li>Missing assets (404s) are fetched from the origin server, cached, and served transparently</li>
          </ul>
        </div>
        <label class="flex items-center cursor-pointer">
          <div class="relative">
            <input
              type="checkbox"
              :checked="shieldStore.learnMode"
              @change="handleToggleLearn"
              class="sr-only peer"
            />
            <div class="w-11 h-6 bg-gray-700 rounded-full peer-checked:bg-amber-500 transition-colors"></div>
            <div class="absolute left-0.5 top-0.5 w-5 h-5 bg-white rounded-full transition-transform peer-checked:translate-x-5"></div>
          </div>
          <span class="ml-3 text-sm font-medium" :class="shieldStore.learnMode ? 'text-amber-400' : 'text-gray-400'">
            {{ shieldStore.learnMode ? 'Active' : 'Off' }}
          </span>
        </label>
      </div>

      <div v-if="learnedPosts.length > 0">
        <h3 class="text-sm font-medium text-gray-300 mb-2">Learned POST Rules ({{ learnedPosts.length }})</h3>
        <div class="divide-y divide-gray-800 bg-gray-800/50 rounded-lg overflow-hidden">
          <div v-for="(post, idx) in learnedPosts" :key="idx" class="px-4 py-3">
            <div class="flex items-center justify-between">
              <code class="text-sm text-amber-400">{{ post.path }}</code>
              <span class="text-xs text-gray-500">{{ post.fields.length }} fields</span>
            </div>
            <div v-if="post.fields.length" class="mt-1 text-xs text-gray-500">
              {{ post.fields.join(', ') }}
            </div>
          </div>
        </div>
        <p class="text-xs text-gray-500 mt-2">These rules have been auto-created. Review them in the POST Rules section.</p>
      </div>

      <div v-if="learnedAssets.length > 0" class="mt-4">
        <h3 class="text-sm font-medium text-gray-300 mb-2">Learned Assets ({{ learnedAssets.length }})</h3>
        <div class="divide-y divide-gray-800 bg-gray-800/50 rounded-lg overflow-hidden max-h-60 overflow-y-auto">
          <div v-for="(asset, idx) in learnedAssets" :key="idx" class="px-4 py-2">
            <div class="flex items-center justify-between">
              <code class="text-sm text-cyan-400 truncate mr-4">{{ asset.path }}</code>
              <div class="flex items-center gap-3 shrink-0">
                <span class="text-xs text-gray-500">{{ asset.content_type }}</span>
                <span class="text-xs text-gray-600">{{ formatSize(asset.size) }}</span>
              </div>
            </div>
          </div>
        </div>
        <p class="text-xs text-gray-500 mt-2">These assets were fetched from the origin and cached automatically.</p>
      </div>

      <div v-if="!learnedPosts.length && !learnedAssets.length && shieldStore.learnMode" class="text-sm text-gray-500 bg-gray-800/50 rounded-lg p-4 text-center">
        Waiting for traffic... Browse the deployed site to capture missing assets and form submissions.
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
import api from '../api'

const sitesStore = useSitesStore()
const shieldStore = useShieldStore()
const { sites } = storeToRefs(sitesStore)
const deployError = ref('')
const learnedPosts = ref([])
const learnedAssets = ref([])
let learnPollTimer = null

function formatSize(bytes) {
  if (!bytes) return '0 B'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1048576).toFixed(1) + ' MB'
}

async function fetchLearnedData() {
  if (!shieldStore.active) return
  try {
    const [posts, assets] = await Promise.all([
      api.get('/shield/learned-posts'),
      api.get('/shield/learned-assets'),
    ])
    learnedPosts.value = posts.data
    learnedAssets.value = assets.data
  } catch {}
}

onMounted(async () => {
  sitesStore.fetchSites()
  await shieldStore.fetchStatus()
  if (shieldStore.learnMode) {
    fetchLearnedData()
    startLearnPoll()
  }
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
    stopLearnPoll()
    learnedPosts.value = []
    learnedAssets.value = []
  } catch (e) {
    deployError.value = e.response?.data?.detail || 'Failed to undeploy shield'
  }
}

async function handleToggleLearn() {
  const newState = !shieldStore.learnMode
  try {
    await shieldStore.toggleLearnMode(newState)
    if (newState) {
      fetchLearnedData()
      startLearnPoll()
    } else {
      stopLearnPoll()
    }
  } catch (e) {
    deployError.value = e.response?.data?.detail || 'Failed to toggle learn mode'
  }
}

function startLearnPoll() {
  if (learnPollTimer) return
  learnPollTimer = setInterval(fetchLearnedData, 3000)
}

function stopLearnPoll() {
  if (learnPollTimer) {
    clearInterval(learnPollTimer)
    learnPollTimer = null
  }
}
</script>
