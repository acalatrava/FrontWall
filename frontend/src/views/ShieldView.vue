<template>
  <div>
    <h1 class="text-xl sm:text-2xl font-bold text-white mb-6">{{ t('shieldPage.title') }}</h1>

    <div v-if="sites.length === 0" class="bg-gray-900 border border-gray-800 rounded-xl p-12 text-center">
      <p class="text-gray-400 mb-4">{{ t('shieldPage.noSites') }}</p>
      <router-link to="/sites" class="text-blue-400 hover:underline">{{ t('common.addSiteFirst') }}</router-link>
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
                {{ t('shieldPage.servingOnPort', { port: getShieldPort(site.id) || site.shield_port }) }}
              </p>
              <p v-else-if="!site.shield_port" class="text-xs text-amber-400 mt-1">
                {{ t('shieldPage.noPortConfigured') }}
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
              {{ t('shieldPage.undeploy') }}
            </button>
            <button
              v-else
              @click="handleDeploy(site.id)"
              :disabled="shieldStore.loading || !site.shield_port"
              class="px-5 py-2.5 bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white text-sm font-medium rounded-lg transition-colors"
            >
              {{ t('shieldPage.deploy') }}
            </button>
          </div>
        </div>

        <div v-if="isActive(site.id)" class="border-t border-gray-800">
          <div class="px-4 sm:px-6 py-4 grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
              <span class="text-gray-400">{{ t('shieldPage.shieldPort') }}</span>
              <code class="ml-2 bg-gray-800 px-2 py-0.5 rounded text-blue-400">{{ getShieldPort(site.id) || site.shield_port }}</code>
            </div>
            <div>
              <span class="text-gray-400">{{ t('shieldPage.proxyConfig') }}</span>
              <code class="ml-2 bg-gray-800 px-2 py-0.5 rounded text-green-400 text-xs">
                proxy_pass http://frontwall:{{ getShieldPort(site.id) || site.shield_port }};
              </code>
            </div>
          </div>

          <div class="px-4 sm:px-6 py-4 border-t border-gray-800">
            <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
              <div>
                <h3 class="text-sm font-semibold text-white flex items-center gap-2">
                  <svg class="w-4 h-4 text-orange-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M13 10V3L4 14h7v7l9-11h-7z"/>
                  </svg>
                  {{ t('shieldPage.bypassMode') }}
                </h3>
                <p class="text-xs text-gray-500 mt-0.5">{{ t('shieldPage.bypassModeDesc') }}</p>
              </div>
              <label class="flex items-center cursor-pointer">
                <div class="relative">
                  <input
                    type="checkbox"
                    :checked="getBypassMode(site.id)"
                    @change="handleToggleBypass(site.id)"
                    class="sr-only peer"
                  />
                  <div class="w-11 h-6 bg-gray-700 rounded-full peer-checked:bg-orange-500 transition-colors"></div>
                  <div class="absolute left-0.5 top-0.5 w-5 h-5 bg-white rounded-full transition-transform peer-checked:translate-x-5"></div>
                </div>
                <span class="ml-3 text-sm font-medium" :class="getBypassMode(site.id) ? 'text-orange-400' : 'text-gray-400'">
                  {{ getBypassMode(site.id) ? t('shieldPage.bypassActive') : t('shieldPage.bypassOff') }}
                </span>
              </label>
            </div>

            <div v-if="getBypassMode(site.id)" class="mb-4 bg-orange-500/10 border border-orange-500/30 rounded-lg p-3">
              <div class="flex items-start gap-2">
                <svg class="w-4 h-4 text-orange-400 mt-0.5 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                  <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
                </svg>
                <p class="text-xs text-orange-300">{{ t('shieldPage.bypassWarning') }}</p>
              </div>
            </div>
          </div>

          <div class="px-4 sm:px-6 py-4 border-t border-gray-800">
            <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-3">
              <div>
                <h3 class="text-sm font-semibold text-white">{{ t('shieldPage.learnMode') }}</h3>
                <p class="text-xs text-gray-500 mt-0.5">{{ t('shieldPage.learnModeDesc') }}</p>
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
                  {{ getLearnMode(site.id) ? t('shieldPage.learnActive') : t('shieldPage.learnOff') }}
                </span>
              </label>
            </div>

            <div v-if="(siteLearnedPosts[site.id] || []).length > 0" class="mb-3">
              <h4 class="text-xs font-medium text-gray-300 mb-1.5">{{ t('shieldPage.learnedPostRules') }} ({{ siteLearnedPosts[site.id].length }})</h4>
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
              <h4 class="text-xs font-medium text-gray-300 mb-1.5">{{ t('shieldPage.learnedAssets') }} ({{ siteLearnedAssets[site.id].length }})</h4>
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
                {{ t('shieldPage.learnedCspOrigins') }} ({{ siteLearnedCsp[site.id].length }})
                <span class="text-gray-500 font-normal ml-1">{{ t('shieldPage.cspHint') }}</span>
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
              {{ t('shieldPage.waitingTraffic') }}
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
import { useI18n } from 'vue-i18n'
import { useSitesStore } from '../stores/sites'
import { useShieldStore } from '../stores/shield'
import api from '../api'

const { t } = useI18n()
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

function getBypassMode(siteId) {
  const s = shieldStore.getShield(siteId)
  return s ? s.bypass_mode : false
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
    deployError.value = Array.isArray(detail) ? detail.map(d => d.msg || d).join('. ') : (detail || t('shieldPage.deployFailed'))
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
    deployError.value = e.response?.data?.detail || t('shieldPage.undeployFailed')
  }
}

async function handleToggleBypass(siteId) {
  const current = getBypassMode(siteId)
  try {
    await shieldStore.toggleBypassMode(siteId, !current)
  } catch (e) {
    deployError.value = e.response?.data?.detail || t('shieldPage.bypassToggleFailed')
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
    deployError.value = e.response?.data?.detail || t('shieldPage.learnToggleFailed')
  }
}
</script>
