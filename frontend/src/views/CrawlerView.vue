<template>
  <div>
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-6">
      <div>
        <h1 class="text-xl sm:text-2xl font-bold text-white">Crawler</h1>
        <p class="text-sm text-gray-400 mt-1">Site: {{ site?.name || siteId }}</p>
      </div>
      <div class="flex gap-2 sm:gap-3">
        <button
          v-if="!isCrawling"
          @click="startCrawl"
          :disabled="starting"
          class="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white text-sm font-medium rounded-lg transition-colors"
        >
          {{ starting ? 'Starting...' : 'Start Crawl' }}
        </button>
        <button
          v-else
          @click="stopCrawl"
          class="px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm font-medium rounded-lg transition-colors"
        >
          Stop Crawl
        </button>
      </div>
    </div>

    <div v-if="progress" class="bg-gray-900 border border-gray-800 rounded-xl p-4 sm:p-6 mb-6">
      <h2 class="text-lg font-semibold text-white mb-4">Crawl Progress</h2>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
        <div class="text-center">
          <div class="text-2xl font-bold text-blue-400">{{ progress.pages_crawled }}</div>
          <div class="text-xs text-gray-400">Pages Crawled</div>
        </div>
        <div class="text-center">
          <div class="text-2xl font-bold text-purple-400">{{ progress.pages_found }}</div>
          <div class="text-xs text-gray-400">Pages Found</div>
        </div>
        <div class="text-center">
          <div class="text-2xl font-bold text-green-400">{{ progress.assets_downloaded }}</div>
          <div class="text-xs text-gray-400">Assets Downloaded</div>
        </div>
        <div class="text-center">
          <div class="text-2xl font-bold text-red-400">{{ progress.errors }}</div>
          <div class="text-xs text-gray-400">Errors</div>
        </div>
      </div>
      <div class="w-full bg-gray-800 rounded-full h-2">
        <div
          class="bg-blue-500 h-2 rounded-full transition-all duration-300"
          :style="{ width: progressPercent + '%' }"
        ></div>
      </div>
    </div>

    <div class="bg-gray-900 border border-gray-800 rounded-xl">
      <div class="px-4 sm:px-6 py-4 border-b border-gray-800">
        <h2 class="text-lg font-semibold text-white">Crawl History</h2>
      </div>
      <div v-if="jobs.length === 0" class="p-4 sm:p-6 text-center text-gray-500">
        No crawl jobs yet. Start a crawl to begin caching the site.
      </div>
      <div v-else class="divide-y divide-gray-800">
        <div v-for="job in jobs" :key="job.id" class="px-4 sm:px-6 py-4">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-3">
              <span
                class="px-2.5 py-1 rounded-full text-xs font-medium"
                :class="statusClass(job.status)"
              >
                {{ job.status }}
              </span>
              <span class="text-sm text-gray-400">{{ formatDate(job.created_at) }}</span>
            </div>
            <div class="text-sm text-gray-400">
              {{ job.pages_crawled }} pages / {{ job.assets_downloaded }} assets
              <span v-if="job.errors > 0" class="text-red-400 ml-2">{{ job.errors }} errors</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import api from '../api'

const props = defineProps({ siteId: String })

const site = ref(null)
const jobs = ref([])
const isCrawling = ref(false)
const starting = ref(false)
const progress = ref(null)
let pollTimer = null
let ws = null

const progressPercent = computed(() => {
  if (!progress.value || !progress.value.pages_found) return 0
  return Math.min(100, Math.round((progress.value.pages_crawled / progress.value.pages_found) * 100))
})

function statusClass(status) {
  const map = {
    completed: 'bg-green-500/10 text-green-400',
    running: 'bg-blue-500/10 text-blue-400',
    failed: 'bg-red-500/10 text-red-400',
    stopped: 'bg-yellow-500/10 text-yellow-400',
    pending: 'bg-gray-700/50 text-gray-400',
  }
  return map[status] || map.pending
}

function formatDate(d) {
  return new Date(d).toLocaleString()
}

async function loadData() {
  try {
    const [siteResp, jobsResp, statusResp] = await Promise.all([
      api.get(`/sites/${props.siteId}`),
      api.get(`/crawler/jobs/${props.siteId}`),
      api.get(`/crawler/status/${props.siteId}`),
    ])
    site.value = siteResp.data
    jobs.value = jobsResp.data
    isCrawling.value = statusResp.data.is_crawling
    if (isCrawling.value) {
      startPolling()
      connectWebSocket()
    }
  } catch {}
}

async function pollProgress() {
  try {
    const resp = await api.get(`/crawler/progress/${props.siteId}`)
    if (resp.data.is_crawling && resp.data.progress) {
      progress.value = resp.data.progress
    } else if (!resp.data.is_crawling) {
      stopPolling()
      isCrawling.value = false
      progress.value = null
      await loadData()
    }
  } catch {}
}

function startPolling() {
  if (pollTimer) return
  pollProgress()
  pollTimer = setInterval(pollProgress, 1500)
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

function connectWebSocket() {
  if (ws && ws.readyState <= 1) return
  const proto = location.protocol === 'https:' ? 'wss' : 'ws'
  ws = new WebSocket(`${proto}://${location.host}/api/crawler/ws/${props.siteId}`)
  ws.onmessage = (e) => {
    const data = JSON.parse(e.data)
    progress.value = data
    if (data.finished) {
      isCrawling.value = false
      stopPolling()
      loadData()
    }
  }
  ws.onclose = () => {
    ws = null
  }
  ws.onerror = () => {
    ws = null
  }
}

async function startCrawl() {
  starting.value = true
  try {
    await api.post(`/crawler/start/${props.siteId}`)
    isCrawling.value = true
    progress.value = { pages_found: 0, pages_crawled: 0, assets_downloaded: 0, errors: 0 }
    startPolling()
    connectWebSocket()
  } catch (e) {
    alert(e.response?.data?.detail || 'Failed to start crawl')
  } finally {
    starting.value = false
  }
}

async function stopCrawl() {
  try {
    await api.post(`/crawler/stop/${props.siteId}`)
    isCrawling.value = false
    stopPolling()
    await loadData()
  } catch {}
}

onMounted(() => {
  loadData()
})

onUnmounted(() => {
  stopPolling()
  if (ws) ws.close()
})
</script>
