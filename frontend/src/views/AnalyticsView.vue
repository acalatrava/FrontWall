<template>
  <div>
    <h1 class="text-2xl font-bold text-white mb-6">Security Analytics</h1>

    <div v-if="sites.length === 0" class="bg-gray-900 border border-gray-800 rounded-xl p-12 text-center">
      <p class="text-gray-400">No sites configured. <router-link to="/sites" class="text-blue-400 hover:underline">Add a site first.</router-link></p>
    </div>

    <template v-else>
      <div class="flex items-center gap-4 mb-6">
        <div class="flex-1 max-w-md">
          <label class="block text-sm font-medium text-gray-300 mb-2">Select Site</label>
          <select
            v-model="selectedSiteId"
            class="w-full px-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option v-for="site in sites" :key="site.id" :value="site.id">{{ site.name }}</option>
          </select>
        </div>
        <div class="flex gap-2 mt-7">
          <button
            v-for="opt in timeRangeOptions"
            :key="opt.value"
            @click="timeRange = opt.value"
            class="px-3 py-1.5 text-xs font-medium rounded-lg transition-colors"
            :class="timeRange === opt.value ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'"
          >{{ opt.label }}</button>
        </div>
      </div>

      <div v-if="selectedSiteId" class="space-y-6">
        <!-- Summary Cards -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div class="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <div class="flex items-center gap-3 mb-3">
              <div class="w-10 h-10 rounded-lg bg-red-500/10 flex items-center justify-center">
                <svg class="w-5 h-5 text-red-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
              </div>
              <span class="text-sm text-gray-400">Threats Blocked</span>
            </div>
            <div class="text-3xl font-bold text-white">{{ summary.total_events || 0 }}</div>
            <div class="mt-1 text-xs" :class="delta > 0 ? 'text-red-400' : delta < 0 ? 'text-green-400' : 'text-gray-500'">
              <span v-if="delta > 0">+{{ delta }}% vs prev</span>
              <span v-else-if="delta < 0">{{ delta }}% vs prev</span>
              <span v-else>No change</span>
            </div>
          </div>

          <div class="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <div class="flex items-center gap-3 mb-3">
              <div class="w-10 h-10 rounded-lg bg-orange-500/10 flex items-center justify-center">
                <svg class="w-5 h-5 text-orange-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
              </div>
              <span class="text-sm text-gray-400">Unique Attacker IPs</span>
            </div>
            <div class="text-3xl font-bold text-white">{{ summary.unique_ips || 0 }}</div>
            <div class="mt-1 text-xs text-gray-500">Last {{ timeRange }}h</div>
          </div>

          <div class="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <div class="flex items-center gap-3 mb-3">
              <div class="w-10 h-10 rounded-lg bg-yellow-500/10 flex items-center justify-center">
                <svg class="w-5 h-5 text-yellow-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
              </div>
              <span class="text-sm text-gray-400">Top Attack Type</span>
            </div>
            <div class="text-lg font-bold text-white truncate">{{ formatEventType(summary.top_event_type) || 'None' }}</div>
            <div class="mt-1 text-xs text-gray-500">Most frequent</div>
          </div>

          <div class="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <div class="flex items-center gap-3 mb-3">
              <div class="w-10 h-10 rounded-lg flex items-center justify-center" :class="threatLevelBg">
                <svg class="w-5 h-5" :class="threatLevelColor" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
              </div>
              <span class="text-sm text-gray-400">Threat Level</span>
            </div>
            <div class="text-lg font-bold capitalize" :class="threatLevelColor">{{ summary.threat_level || 'None' }}</div>
            <div class="mt-2 w-full bg-gray-800 rounded-full h-2">
              <div class="h-2 rounded-full transition-all duration-500" :class="threatLevelBarColor" :style="{ width: threatLevelWidth }"></div>
            </div>
          </div>
        </div>

        <!-- Timeline Chart -->
        <div class="bg-gray-900 border border-gray-800 rounded-xl p-6">
          <h2 class="text-lg font-semibold text-white mb-4">Threat Timeline</h2>
          <div class="h-64">
            <Bar v-if="timelineData.labels.length > 0" :data="timelineData" :options="timelineOptions" />
            <div v-else class="h-full flex items-center justify-center text-gray-500">No events in this period</div>
          </div>
        </div>

        <!-- Two-column: Event Types + Severity -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div class="bg-gray-900 border border-gray-800 rounded-xl p-6">
            <h2 class="text-lg font-semibold text-white mb-4">Event Type Breakdown</h2>
            <div class="h-64 flex items-center justify-center">
              <Doughnut v-if="eventTypesData.labels.length > 0" :data="eventTypesData" :options="doughnutOptions" />
              <div v-else class="text-gray-500">No data</div>
            </div>
          </div>

          <div class="bg-gray-900 border border-gray-800 rounded-xl p-6">
            <h2 class="text-lg font-semibold text-white mb-4">Severity Distribution</h2>
            <div class="space-y-4 mt-6">
              <div v-for="sev in severityBars" :key="sev.label" class="flex items-center gap-3">
                <span class="w-16 text-xs font-medium capitalize" :class="sev.textColor">{{ sev.label }}</span>
                <div class="flex-1 bg-gray-800 rounded-full h-4">
                  <div class="h-4 rounded-full transition-all duration-500" :class="sev.barColor" :style="{ width: sev.width }"></div>
                </div>
                <span class="w-10 text-right text-xs text-gray-400">{{ sev.count }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Top Attackers Table -->
        <div class="bg-gray-900 border border-gray-800 rounded-xl p-6">
          <h2 class="text-lg font-semibold text-white mb-4">Top Attackers</h2>
          <div class="overflow-x-auto">
            <table v-if="attackers.length > 0" class="w-full text-sm">
              <thead>
                <tr class="border-b border-gray-800">
                  <th class="text-left py-3 px-4 text-gray-400 font-medium">IP Address</th>
                  <th class="text-left py-3 px-4 text-gray-400 font-medium">Events</th>
                  <th class="text-left py-3 px-4 text-gray-400 font-medium">Last Seen</th>
                  <th class="text-left py-3 px-4 text-gray-400 font-medium">Top Attack</th>
                  <th class="text-left py-3 px-4 text-gray-400 font-medium">Severity</th>
                  <th class="text-right py-3 px-4 text-gray-400 font-medium">Action</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="attacker in attackers" :key="attacker.ip" class="border-b border-gray-800/50 hover:bg-gray-800/30">
                  <td class="py-3 px-4 font-mono text-white">{{ attacker.ip }}</td>
                  <td class="py-3 px-4 text-white font-semibold">{{ attacker.count }}</td>
                  <td class="py-3 px-4 text-gray-400">{{ formatTime(attacker.last_seen) }}</td>
                  <td class="py-3 px-4 text-gray-300">{{ formatEventType(attacker.top_event_type) }}</td>
                  <td class="py-3 px-4">
                    <span class="px-2 py-0.5 rounded-full text-xs font-medium" :class="severityBadge(attacker.severity)">{{ attacker.severity }}</span>
                  </td>
                  <td class="py-3 px-4 text-right">
                    <button
                      @click="blockIP(attacker.ip)"
                      class="px-3 py-1 text-xs font-medium text-red-400 bg-red-500/10 rounded-lg hover:bg-red-500/20 transition-colors"
                      :disabled="blockingIp === attacker.ip"
                    >
                      {{ blockingIp === attacker.ip ? 'Blocking...' : 'Block IP' }}
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
            <div v-else class="py-8 text-center text-gray-500">No attackers detected</div>
          </div>
        </div>

        <!-- Live Threat Feed -->
        <div class="bg-gray-900 border border-gray-800 rounded-xl p-6">
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-lg font-semibold text-white">Live Threat Feed</h2>
            <div class="flex items-center gap-2">
              <span class="w-2 h-2 rounded-full bg-green-400 animate-pulse"></span>
              <span class="text-xs text-gray-400">Auto-refresh 3s</span>
            </div>
          </div>
          <div class="space-y-2 max-h-96 overflow-y-auto">
            <div
              v-for="(event, idx) in recentEvents"
              :key="idx"
              class="flex items-center gap-3 px-4 py-3 bg-gray-800/40 rounded-lg hover:bg-gray-800/60 transition-colors"
            >
              <span class="w-2 h-2 rounded-full flex-shrink-0" :class="severityDot(event.severity)"></span>
              <span class="text-xs text-gray-500 font-mono w-16 flex-shrink-0">{{ formatShortTime(event.timestamp) }}</span>
              <span class="px-2 py-0.5 rounded text-[10px] font-bold uppercase flex-shrink-0" :class="methodBadge(event.method)">{{ event.method }}</span>
              <span class="text-xs text-gray-300 flex-shrink-0 w-28 truncate">{{ formatEventType(event.event_type) }}</span>
              <span class="text-xs font-mono text-gray-400 flex-shrink-0 w-28 truncate">{{ event.client_ip }}</span>
              <span class="text-xs text-gray-500 truncate flex-1">{{ event.path }}</span>
              <span class="text-xs text-gray-600 truncate max-w-[200px] hidden xl:inline">{{ event.user_agent }}</span>
            </div>
            <div v-if="recentEvents.length === 0" class="py-8 text-center text-gray-500">No events yet</div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useSitesStore } from '../stores/sites'
import { Bar, Doughnut } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js'
import api from '../api'

ChartJS.register(CategoryScale, LinearScale, BarElement, ArcElement, Title, Tooltip, Legend)

const sitesStore = useSitesStore()
const { sites } = storeToRefs(sitesStore)

const selectedSiteId = ref(null)
const timeRange = ref(24)
const summary = ref({})
const timeline = ref([])
const eventTypes = ref([])
const severityData = ref([])
const attackers = ref([])
const recentEvents = ref([])
const blockingIp = ref(null)
let pollInterval = null

const timeRangeOptions = [
  { label: '24h', value: 24 },
  { label: '7d', value: 168 },
  { label: '30d', value: 720 },
]

const eventTypeColors = {
  bot_blocked: '#f97316',
  rate_limited: '#eab308',
  suspicious_path: '#ef4444',
  suspicious_query: '#dc2626',
  ip_blacklisted: '#7c3aed',
  payload_too_large: '#06b6d4',
  honeypot_triggered: '#ec4899',
  post_unregistered: '#6b7280',
  post_rate_limited: '#f59e0b',
  login_failed: '#f43f5e',
  token_reuse: '#a855f7',
}

const delta = computed(() => {
  const cur = summary.value.total_events || 0
  const prev = summary.value.total_prev_period || 0
  if (prev === 0) return cur > 0 ? 100 : 0
  return Math.round(((cur - prev) / prev) * 100)
})

const threatLevelColor = computed(() => {
  const m = { critical: 'text-red-400', high: 'text-orange-400', medium: 'text-yellow-400', low: 'text-blue-400', none: 'text-gray-500' }
  return m[summary.value.threat_level] || 'text-gray-500'
})

const threatLevelBg = computed(() => {
  const m = { critical: 'bg-red-500/10', high: 'bg-orange-500/10', medium: 'bg-yellow-500/10', low: 'bg-blue-500/10', none: 'bg-gray-500/10' }
  return m[summary.value.threat_level] || 'bg-gray-500/10'
})

const threatLevelBarColor = computed(() => {
  const m = { critical: 'bg-red-500', high: 'bg-orange-500', medium: 'bg-yellow-500', low: 'bg-blue-500', none: 'bg-gray-700' }
  return m[summary.value.threat_level] || 'bg-gray-700'
})

const threatLevelWidth = computed(() => {
  const m = { critical: '100%', high: '75%', medium: '50%', low: '25%', none: '5%' }
  return m[summary.value.threat_level] || '5%'
})

const timelineData = computed(() => {
  const labels = timeline.value.map(b => b.bucket)
  return {
    labels,
    datasets: [
      { label: 'Critical', data: timeline.value.map(b => b.critical || 0), backgroundColor: '#ef4444', borderRadius: 3 },
      { label: 'High', data: timeline.value.map(b => b.high || 0), backgroundColor: '#f97316', borderRadius: 3 },
      { label: 'Medium', data: timeline.value.map(b => b.medium || 0), backgroundColor: '#eab308', borderRadius: 3 },
      { label: 'Low', data: timeline.value.map(b => b.low || 0), backgroundColor: '#3b82f6', borderRadius: 3 },
    ],
  }
})

const timelineOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { position: 'top', labels: { color: '#9ca3af', boxWidth: 12, padding: 16 } },
    tooltip: { mode: 'index', intersect: false },
  },
  scales: {
    x: {
      stacked: true,
      ticks: { color: '#6b7280', maxRotation: 45 },
      grid: { color: '#1f2937' },
    },
    y: {
      stacked: true,
      ticks: { color: '#6b7280', precision: 0 },
      grid: { color: '#1f2937' },
    },
  },
}

const eventTypesData = computed(() => {
  return {
    labels: eventTypes.value.map(e => formatEventType(e.event_type)),
    datasets: [{
      data: eventTypes.value.map(e => e.count),
      backgroundColor: eventTypes.value.map(e => eventTypeColors[e.event_type] || '#6b7280'),
      borderWidth: 0,
    }],
  }
})

const doughnutOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { position: 'right', labels: { color: '#9ca3af', boxWidth: 12, padding: 10, font: { size: 11 } } },
  },
}

const severityBars = computed(() => {
  const total = severityData.value.reduce((a, b) => a + b.count, 0) || 1
  const map = {}
  severityData.value.forEach(s => { map[s.severity] = s.count })
  return [
    { label: 'critical', count: map.critical || 0, width: ((map.critical || 0) / total * 100) + '%', barColor: 'bg-red-500', textColor: 'text-red-400' },
    { label: 'high', count: map.high || 0, width: ((map.high || 0) / total * 100) + '%', barColor: 'bg-orange-500', textColor: 'text-orange-400' },
    { label: 'medium', count: map.medium || 0, width: ((map.medium || 0) / total * 100) + '%', barColor: 'bg-yellow-500', textColor: 'text-yellow-400' },
    { label: 'low', count: map.low || 0, width: ((map.low || 0) / total * 100) + '%', barColor: 'bg-blue-500', textColor: 'text-blue-400' },
  ]
})

function formatEventType(t) {
  if (!t) return ''
  return t.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

function formatTime(iso) {
  if (!iso) return '-'
  const d = new Date(iso)
  return d.toLocaleString()
}

function formatShortTime(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

function severityBadge(sev) {
  const m = {
    critical: 'bg-red-500/20 text-red-400',
    high: 'bg-orange-500/20 text-orange-400',
    medium: 'bg-yellow-500/20 text-yellow-400',
    low: 'bg-blue-500/20 text-blue-400',
  }
  return m[sev] || 'bg-gray-500/20 text-gray-400'
}

function severityDot(sev) {
  const m = { critical: 'bg-red-400', high: 'bg-orange-400', medium: 'bg-yellow-400', low: 'bg-blue-400' }
  return m[sev] || 'bg-gray-400'
}

function methodBadge(method) {
  return method === 'POST' ? 'bg-purple-500/20 text-purple-400' : 'bg-cyan-500/20 text-cyan-400'
}

async function fetchAll() {
  if (!selectedSiteId.value) return
  const siteId = selectedSiteId.value
  const hours = timeRange.value
  const bucket = hours <= 24 ? 'hour' : hours <= 168 ? 'hour' : 'day'

  const [sumRes, tlRes, etRes, sevRes, atkRes, recRes] = await Promise.allSettled([
    api.get(`/analytics/${siteId}/summary?hours=${hours}`),
    api.get(`/analytics/${siteId}/timeline?hours=${hours}&bucket=${bucket}`),
    api.get(`/analytics/${siteId}/event-types?hours=${hours}`),
    api.get(`/analytics/${siteId}/severity?hours=${hours}`),
    api.get(`/analytics/${siteId}/top-attackers?hours=${hours}&limit=10`),
    api.get(`/analytics/${siteId}/recent?limit=50`),
  ])

  if (sumRes.status === 'fulfilled') summary.value = sumRes.value.data
  if (tlRes.status === 'fulfilled') timeline.value = tlRes.value.data
  if (etRes.status === 'fulfilled') eventTypes.value = etRes.value.data
  if (sevRes.status === 'fulfilled') severityData.value = sevRes.value.data
  if (atkRes.status === 'fulfilled') attackers.value = atkRes.value.data
  if (recRes.status === 'fulfilled') recentEvents.value = recRes.value.data
}

async function fetchRecent() {
  if (!selectedSiteId.value) return
  try {
    const { data } = await api.get(`/analytics/${selectedSiteId.value}/recent?limit=50`)
    recentEvents.value = data
  } catch { /* ignore */ }
}

async function blockIP(ip) {
  if (!selectedSiteId.value) return
  blockingIp.value = ip
  try {
    const site = sites.value.find(s => s.id === selectedSiteId.value)
    if (!site) return
    const currentList = site.ip_blacklist || ''
    const ips = currentList.split(',').map(s => s.trim()).filter(Boolean)
    if (!ips.includes(ip)) {
      ips.push(ip)
    }
    await sitesStore.updateSite(selectedSiteId.value, { ip_blacklist: ips.join(', ') })
  } finally {
    blockingIp.value = null
  }
}

watch(sites, (val) => {
  if (val.length && !selectedSiteId.value) {
    selectedSiteId.value = val[0].id
  }
})

watch([selectedSiteId, timeRange], () => {
  fetchAll()
})

onMounted(async () => {
  await sitesStore.fetchSites()
  if (sites.value.length) {
    selectedSiteId.value = sites.value[0].id
  }
  pollInterval = setInterval(fetchRecent, 3000)
})

onUnmounted(() => {
  if (pollInterval) clearInterval(pollInterval)
})
</script>
