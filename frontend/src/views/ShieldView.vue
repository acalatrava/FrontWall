<template>
  <div>
    <h1 class="text-xl sm:text-2xl font-bold text-white mb-6">Shield Deployment</h1>

    <div v-if="sites.length === 0" class="bg-gray-900 border border-gray-800 rounded-xl p-12 text-center">
      <p class="text-gray-400 mb-4">No sites configured.</p>
      <router-link to="/sites" class="text-blue-400 hover:underline">Add a site first.</router-link>
    </div>

    <div v-else class="space-y-6">
      <div
        v-for="site in sites"
        :key="site.id"
        class="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden"
      >
        <div class="px-4 sm:px-6 py-5 flex flex-col sm:flex-row sm:items-center gap-4 sm:justify-between">
          <div class="flex items-center gap-4">
            <div
              class="w-10 h-10 sm:w-12 sm:h-12 rounded-full flex items-center justify-center flex-shrink-0"
              :class="isActive(site.id) ? 'bg-green-500/20' : 'bg-gray-800'"
            >
              <svg class="w-5 h-5 sm:w-6 sm:h-6" :class="isActive(site.id) ? 'text-green-400' : 'text-gray-600'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                <path v-if="isActive(site.id)" d="m9 12 2 2 4-4" stroke="currentColor"/>
              </svg>
            </div>
            <div class="min-w-0">
              <h2 class="text-base sm:text-lg font-semibold text-white truncate">{{ site.name }}</h2>
              <p class="text-sm text-gray-400 truncate">{{ site.target_url }}</p>
              <p v-if="isActive(site.id)" class="text-xs text-green-400 mt-1">
                Serving on port {{ getShieldPort(site.id) || site.shield_port }}
              </p>
              <p v-else-if="!site.shield_port" class="text-xs text-amber-400 mt-1">
                No shield port configured — set one in site settings to deploy
              </p>
            </div>
          </div>
          <div class="flex items-center gap-3 self-end sm:self-auto flex-shrink-0">
            <button
              v-if="isActive(site.id)"
              @click="handleUndeploy(site.id)"
              :disabled="shieldStore.loading"
              class="px-5 py-2.5 bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white text-sm font-medium rounded-lg transition-colors"
            >
              Undeploy
            </button>
            <button
              v-else
              @click="handleDeploy(site.id)"
              :disabled="shieldStore.loading || !site.shield_port"
              class="px-5 py-2.5 bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white text-sm font-medium rounded-lg transition-colors"
            >
              Deploy
            </button>
          </div>
        </div>

        <div v-if="isActive(site.id)" class="border-t border-gray-800">
          <div class="px-4 sm:px-6 py-4 grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
              <span class="text-gray-400">Shield Port:</span>
              <code class="ml-2 bg-gray-800 px-2 py-0.5 rounded text-blue-400">{{ getShieldPort(site.id) || site.shield_port }}</code>
            </div>
            <div>
              <span class="text-gray-400">Proxy Config:</span>
              <code class="ml-2 bg-gray-800 px-2 py-0.5 rounded text-green-400 text-xs">
                proxy_pass http://frontwall:{{ getShieldPort(site.id) || site.shield_port }};
              </code>
            </div>
          </div>

          <div class="px-4 sm:px-6 py-4 border-t border-gray-800">
            <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-3">
              <div>
                <h3 class="text-sm font-semibold text-white">Learn Mode</h3>
                <p class="text-xs text-gray-500 mt-0.5">Auto-captures POST rules, 404 assets, and CSP-blocked domains from the browser</p>
              </div>
              <label class="flex items-center cursor-pointer">
                <div class="relative">
                  <input
                    type="checkbox"
                    :checked="getLearnMode(site.id)"
                    @change="handleToggleLearn(site.id)"
                    class="sr-only peer"
                  />
                  <div class="w-11 h-6 bg-gray-700 rounded-full peer-checked:bg-amber-500 transition-colors"></div>
                  <div class="absolute left-0.5 top-0.5 w-5 h-5 bg-white rounded-full transition-transform peer-checked:translate-x-5"></div>
                </div>
                <span class="ml-3 text-sm font-medium" :class="getLearnMode(site.id) ? 'text-amber-400' : 'text-gray-400'">
                  {{ getLearnMode(site.id) ? 'Active' : 'Off' }}
                </span>
              </label>
            </div>

            <div v-if="(siteLearnedPosts[site.id] || []).length > 0" class="mb-3">
              <h4 class="text-xs font-medium text-gray-300 mb-1.5">Learned POST Rules ({{ siteLearnedPosts[site.id].length }})</h4>
              <div class="divide-y divide-gray-800 bg-gray-800/50 rounded-lg overflow-hidden">
                <div v-for="(post, idx) in siteLearnedPosts[site.id]" :key="idx" class="px-3 py-2">
                  <div class="flex items-center justify-between">
                    <code class="text-xs text-amber-400">{{ post.path }}</code>
                    <span class="text-xs text-gray-500">{{ post.fields.length }} fields</span>
                  </div>
                </div>
              </div>
            </div>

            <div v-if="(siteLearnedAssets[site.id] || []).length > 0" class="mb-3">
              <h4 class="text-xs font-medium text-gray-300 mb-1.5">Learned Assets ({{ siteLearnedAssets[site.id].length }})</h4>
              <div class="divide-y divide-gray-800 bg-gray-800/50 rounded-lg overflow-hidden max-h-48 overflow-y-auto">
                <div v-for="(asset, idx) in siteLearnedAssets[site.id]" :key="idx" class="px-3 py-1.5">
                  <div class="flex items-center justify-between">
                    <code class="text-xs text-cyan-400 truncate mr-4">{{ asset.path }}</code>
                    <div class="flex items-center gap-2 shrink-0">
                      <span class="text-xs text-gray-500">{{ asset.content_type }}</span>
                      <span class="text-xs text-gray-600">{{ formatSize(asset.size) }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div v-if="(siteLearnedCsp[site.id] || []).length > 0" class="mb-3">
              <h4 class="text-xs font-medium text-gray-300 mb-1.5">
                Learned CSP Origins ({{ siteLearnedCsp[site.id].length }})
                <span class="text-gray-500 font-normal ml-1">— will be included in CSP on next deploy</span>
              </h4>
              <div class="flex flex-wrap gap-1.5 bg-gray-800/50 rounded-lg p-3">
                <span
                  v-for="(origin, idx) in siteLearnedCsp[site.id]"
                  :key="idx"
                  class="px-2 py-0.5 bg-purple-500/10 text-purple-400 rounded text-xs font-mono"
                >{{ origin }}</span>
              </div>
            </div>

            <div
              v-if="getLearnMode(site.id) && !(siteLearnedPosts[site.id] || []).length && !(siteLearnedAssets[site.id] || []).length && !(siteLearnedCsp[site.id] || []).length"
              class="text-xs text-gray-500 bg-gray-800/50 rounded-lg p-3 text-center"
            >
              Waiting for traffic...
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="deployError" class="mt-4 bg-red-500/10 border border-red-500/30 rounded-xl px-6 py-4 text-sm text-red-400">
      {{ deployError }}
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useSitesStore } from '../stores/sites'
import { useShieldStore } from '../stores/shield'
import api from '../api'

const sitesStore = useSitesStore()
const shieldStore = useShieldStore()
const { sites } = storeToRefs(sitesStore)
const deployError = ref('')
const siteLearnedPosts = reactive({})
const siteLearnedAssets = reactive({})
const siteLearnedCsp = reactive({})
let learnPollTimer = null

function formatSize(bytes) {
  if (!bytes) return '0 B'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1048576).toFixed(1) + ' MB'
}

function isActive(siteId) {
  return shieldStore.isActive(siteId)
}

function getShieldPort(siteId) {
  const s = shieldStore.getShield(siteId)
  return s ? s.port : null
}

function getLearnMode(siteId) {
  const s = shieldStore.getShield(siteId)
  return s ? s.learn_mode : false
}

async function fetchAllLearnedData() {
  for (const shield of shieldStore.shields) {
    if (!shield.learn_mode) continue
    try {
      const [posts, assets, csp] = await Promise.all([
        api.get(`/shield/learned-posts/${shield.site_id}`),
        api.get(`/shield/learned-assets/${shield.site_id}`),
        api.get(`/shield/learned-csp/${shield.site_id}`),
      ])
      siteLearnedPosts[shield.site_id] = posts.data
      siteLearnedAssets[shield.site_id] = assets.data
      siteLearnedCsp[shield.site_id] = csp.data
    } catch {}
  }
}

function startLearnPoll() {
  if (learnPollTimer) return
  learnPollTimer = setInterval(fetchAllLearnedData, 3000)
}

function stopLearnPoll() {
  if (learnPollTimer) {
    clearInterval(learnPollTimer)
    learnPollTimer = null
  }
}

onMounted(async () => {
  await sitesStore.fetchSites()
  await shieldStore.fetchStatus()
  const hasLearn = shieldStore.shields.some(s => s.learn_mode)
  if (hasLearn) {
    fetchAllLearnedData()
    startLearnPoll()
  }
})

onUnmounted(() => stopLearnPoll())

async function handleDeploy(siteId) {
  deployError.value = ''
  try {
    await shieldStore.deploy(siteId)
  } catch (e) {
    const detail = e.response?.data?.detail
    deployError.value = Array.isArray(detail) ? detail.map(d => d.msg || d).join('. ') : (detail || 'Failed to deploy shield')
  }
}

async function handleUndeploy(siteId) {
  deployError.value = ''
  try {
    await shieldStore.undeploy(siteId)
    delete siteLearnedPosts[siteId]
    delete siteLearnedAssets[siteId]
    delete siteLearnedCsp[siteId]
  } catch (e) {
    deployError.value = e.response?.data?.detail || 'Failed to undeploy shield'
  }
}

async function handleToggleLearn(siteId) {
  const current = getLearnMode(siteId)
  try {
    await shieldStore.toggleLearnMode(siteId, !current)
    if (!current) {
      fetchAllLearnedData()
      startLearnPoll()
    }
  } catch (e) {
    deployError.value = e.response?.data?.detail || 'Failed to toggle learn mode'
  }
}
</script>
