<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-white">Sites</h1>
      <button
        @click="openCreateModal"
        class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors"
      >
        + Add Site
      </button>
    </div>

    <div v-if="loading" class="text-center text-gray-400 py-12">Loading...</div>

    <div v-else-if="sites.length === 0" class="bg-gray-900 border border-gray-800 rounded-xl p-12 text-center">
      <p class="text-gray-400 mb-4">No sites configured. Add your first WordPress site to protect.</p>
      <button
        @click="openCreateModal"
        class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors"
      >
        Add Site
      </button>
    </div>

    <div v-else class="space-y-4">
      <div
        v-for="site in sites"
        :key="site.id"
        class="bg-gray-900 border border-gray-800 rounded-xl p-6"
      >
        <div class="flex items-start justify-between">
          <div>
            <h3 class="text-lg font-semibold text-white">{{ site.name }}</h3>
            <p class="text-sm text-gray-400 mt-1">{{ site.target_url }}</p>
            <p v-if="site.internal_url" class="text-xs text-amber-400/70 mt-1">
              Internal: {{ site.internal_url }}
              <span v-if="site.override_host" class="text-gray-500 ml-1">(Host: {{ site.override_host }})</span>
            </p>
            <div class="flex gap-4 mt-3 text-xs text-gray-500">
              <span>Concurrency: {{ site.crawl_concurrency }}</span>
              <span>Max pages: {{ site.crawl_max_pages }}</span>
              <span>Delay: {{ site.crawl_delay }}s</span>
              <span v-if="site.shield_port" class="text-blue-400">Port: {{ site.shield_port }}</span>
            </div>
            <div class="flex gap-3 mt-2">
              <span class="text-xs px-2 py-0.5 rounded" :class="site.waf_enabled ? 'bg-green-500/10 text-green-400' : 'bg-gray-800 text-gray-500'">WAF</span>
              <span class="text-xs px-2 py-0.5 rounded" :class="site.rate_limit_enabled ? 'bg-green-500/10 text-green-400' : 'bg-gray-800 text-gray-500'">Rate Limit</span>
              <span class="text-xs px-2 py-0.5 rounded" :class="site.security_headers_enabled ? 'bg-green-500/10 text-green-400' : 'bg-gray-800 text-gray-500'">Headers</span>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <button
              @click="openEditModal(site)"
              class="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-sm text-gray-300 rounded-lg transition-colors"
            >
              Edit
            </button>
            <router-link
              :to="`/crawler/${site.id}`"
              class="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-sm text-gray-300 rounded-lg transition-colors"
            >
              Crawler
            </router-link>
            <router-link
              :to="`/pages/${site.id}`"
              class="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-sm text-gray-300 rounded-lg transition-colors"
            >
              Pages
            </router-link>
            <router-link
              :to="`/rules/${site.id}`"
              class="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-sm text-gray-300 rounded-lg transition-colors"
            >
              POST Rules
            </router-link>
            <button
              @click="handleDelete(site.id)"
              class="px-3 py-1.5 bg-red-500/10 hover:bg-red-500/20 text-sm text-red-400 rounded-lg transition-colors"
            >
              Delete
            </button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div class="bg-gray-900 border border-gray-800 rounded-xl w-full max-w-2xl p-6 mx-4 max-h-[90vh] overflow-y-auto">
        <h2 class="text-xl font-bold text-white mb-4">{{ editingSiteId ? 'Edit Site' : 'Add New Site' }}</h2>
        <form @submit.prevent="handleSubmit" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-300 mb-1">Site Name</label>
            <input v-model="form.name" required class="w-full px-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="My WordPress Site" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-300 mb-1">Target URL</label>
            <input v-model="form.target_url" required type="url" class="w-full px-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="https://mysite.com" />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-300 mb-1">Shield Port</label>
            <input v-model.number="form.shield_port" type="number" min="1024" max="65535" class="w-full px-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="8080" />
            <p class="text-xs text-gray-500 mt-1">Port where this site's shield will listen (1024-65535, unique per site)</p>
          </div>

          <div class="grid grid-cols-3 gap-3">
            <div>
              <label class="block text-sm font-medium text-gray-300 mb-1">Concurrency</label>
              <input v-model.number="form.crawl_concurrency" type="number" min="1" max="20" class="w-full px-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-300 mb-1">Delay (s)</label>
              <input v-model.number="form.crawl_delay" type="number" step="0.1" min="0" class="w-full px-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-300 mb-1">Max Pages</label>
              <input v-model.number="form.crawl_max_pages" type="number" min="1" class="w-full px-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
          </div>
          <div class="flex items-center gap-2">
            <input v-model="form.respect_robots_txt" type="checkbox" id="robots" class="rounded bg-gray-800 border-gray-700" />
            <label for="robots" class="text-sm text-gray-300">Respect robots.txt</label>
          </div>

          <div>
            <button
              type="button"
              @click="showAdvanced = !showAdvanced"
              class="text-sm text-blue-400 hover:text-blue-300 transition-colors flex items-center gap-1"
            >
              <svg class="w-4 h-4 transition-transform" :class="showAdvanced ? 'rotate-90' : ''" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m9 18 6-6-6-6"/></svg>
              Advanced Options
            </button>
            <div v-if="showAdvanced" class="mt-3 space-y-3 bg-gray-800/50 rounded-lg p-4 border border-gray-700/50">
              <p class="text-xs text-gray-400 mb-2">
                Use these when the site isn't publicly accessible and the crawler needs to reach it through an internal address.
              </p>
              <div>
                <label class="block text-sm font-medium text-gray-300 mb-1">Internal URL</label>
                <input v-model="form.internal_url" type="url" class="w-full px-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="http://mysite.int:8000" />
                <p class="text-xs text-gray-500 mt-1">The actual address where the server is reachable (e.g. internal IP, Docker hostname)</p>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-300 mb-1">Host Override</label>
                <input v-model="form.override_host" type="text" class="w-full px-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="mysite.com" />
                <p class="text-xs text-gray-500 mt-1">The hostname to send in the Host header (defaults to Target URL hostname)</p>
              </div>
            </div>
          </div>

          <div>
            <button
              type="button"
              @click="showSecurity = !showSecurity"
              class="text-sm text-blue-400 hover:text-blue-300 transition-colors flex items-center gap-1"
            >
              <svg class="w-4 h-4 transition-transform" :class="showSecurity ? 'rotate-90' : ''" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m9 18 6-6-6-6"/></svg>
              Security Settings
            </button>
            <div v-if="showSecurity" class="mt-3 space-y-4 bg-gray-800/50 rounded-lg p-4 border border-gray-700/50">
              <div class="grid grid-cols-2 gap-4">
                <label class="flex items-center gap-2 cursor-pointer">
                  <input v-model="form.waf_enabled" type="checkbox" class="rounded bg-gray-800 border-gray-700" />
                  <span class="text-sm text-gray-300">WAF Enabled</span>
                </label>
                <label class="flex items-center gap-2 cursor-pointer">
                  <input v-model="form.security_headers_enabled" type="checkbox" class="rounded bg-gray-800 border-gray-700" />
                  <span class="text-sm text-gray-300">Security Headers</span>
                </label>
                <label class="flex items-center gap-2 cursor-pointer">
                  <input v-model="form.block_bots" type="checkbox" class="rounded bg-gray-800 border-gray-700" />
                  <span class="text-sm text-gray-300">Block Malicious Bots</span>
                </label>
                <label class="flex items-center gap-2 cursor-pointer">
                  <input v-model="form.block_suspicious_paths" type="checkbox" class="rounded bg-gray-800 border-gray-700" />
                  <span class="text-sm text-gray-300">Block Suspicious Paths</span>
                </label>
              </div>

              <div>
                <label class="flex items-center gap-2 cursor-pointer mb-2">
                  <input v-model="form.rate_limit_enabled" type="checkbox" class="rounded bg-gray-800 border-gray-700" />
                  <span class="text-sm text-gray-300">Rate Limiting</span>
                </label>
                <div v-if="form.rate_limit_enabled" class="grid grid-cols-2 gap-3 ml-6">
                  <div>
                    <label class="block text-xs text-gray-400 mb-1">Requests</label>
                    <input v-model.number="form.rate_limit_requests" type="number" min="1" max="10000" class="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
                  </div>
                  <div>
                    <label class="block text-xs text-gray-400 mb-1">Window (seconds)</label>
                    <input v-model.number="form.rate_limit_window" type="number" min="1" max="3600" class="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
                  </div>
                </div>
              </div>

              <div>
                <label class="block text-sm font-medium text-gray-300 mb-1">Max Request Body Size</label>
                <div class="flex items-center gap-2">
                  <input v-model.number="bodySizeKB" type="number" min="1" class="w-32 px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
                  <span class="text-sm text-gray-400">KB</span>
                </div>
              </div>

              <div>
                <label class="block text-sm font-medium text-gray-300 mb-1">IP Whitelist</label>
                <input v-model="form.ip_whitelist" type="text" class="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="1.2.3.4, 5.6.7.8" />
                <p class="text-xs text-gray-500 mt-1">Comma-separated IPs. Leave empty to allow all.</p>
              </div>

              <div>
                <label class="block text-sm font-medium text-gray-300 mb-1">IP Blacklist</label>
                <input v-model="form.ip_blacklist" type="text" class="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="10.0.0.1, 10.0.0.2" />
                <p class="text-xs text-gray-500 mt-1">Comma-separated IPs to block.</p>
              </div>

              <div>
                <label class="block text-sm font-medium text-gray-300 mb-2">Country Blocking</label>
                <p class="text-xs text-gray-500 mb-2">Block traffic from specific countries. Uses Cloudflare CF-IPCountry header.</p>

                <div v-if="selectedCountries.length" class="flex flex-wrap gap-1.5 mb-3">
                  <span
                    v-for="code in selectedCountries"
                    :key="code"
                    class="inline-flex items-center gap-1 px-2 py-0.5 bg-red-900/50 border border-red-700/50 text-red-300 text-xs rounded-full"
                  >
                    {{ code }} - {{ countryName(code) }}
                    <button type="button" @click="toggleCountry(code)" class="hover:text-red-100 ml-0.5">&times;</button>
                  </span>
                </div>

                <div class="flex gap-2 mb-2">
                  <button
                    type="button"
                    @click="showCountryPicker = !showCountryPicker"
                    class="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-gray-200 text-xs rounded-lg transition-colors"
                  >
                    {{ showCountryPicker ? 'Hide Picker' : 'Select Countries' }}
                  </button>
                  <button
                    type="button"
                    @click="addHighRiskPreset"
                    class="px-3 py-1.5 bg-amber-900/50 hover:bg-amber-800/50 text-amber-300 text-xs rounded-lg border border-amber-700/50 transition-colors"
                  >
                    + High-Risk Preset
                  </button>
                  <button
                    v-if="selectedCountries.length"
                    type="button"
                    @click="clearBlockedCountries"
                    class="px-3 py-1.5 text-gray-400 hover:text-gray-200 text-xs transition-colors"
                  >
                    Clear All
                  </button>
                </div>

                <div v-if="showCountryPicker" class="bg-gray-800 border border-gray-700 rounded-lg p-3 max-h-52 overflow-hidden flex flex-col">
                  <input
                    v-model="countrySearch"
                    type="text"
                    placeholder="Search countries..."
                    class="w-full px-3 py-1.5 bg-gray-900 border border-gray-600 rounded-lg text-white text-xs mb-2 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                  <div class="overflow-y-auto flex-1 space-y-0.5">
                    <label
                      v-for="c in filteredCountries"
                      :key="c.code"
                      class="flex items-center gap-2 cursor-pointer px-2 py-1 rounded hover:bg-gray-700/50 text-xs"
                    >
                      <input
                        type="checkbox"
                        :checked="selectedCountries.includes(c.code)"
                        @change="toggleCountry(c.code)"
                        class="rounded bg-gray-800 border-gray-600"
                      />
                      <span class="text-gray-300">{{ c.code }}</span>
                      <span class="text-gray-400">{{ c.name }}</span>
                      <span
                        v-if="highRiskCountries.includes(c.code)"
                        class="ml-auto text-amber-400 text-[10px] font-medium"
                      >HIGH RISK</span>
                    </label>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div v-if="formError" class="text-sm text-red-400">{{ formError }}</div>
          <div class="flex justify-end gap-3 pt-2">
            <button type="button" @click="closeModal" class="px-4 py-2 text-sm text-gray-400 hover:text-gray-200">Cancel</button>
            <button type="submit" :disabled="submitting" class="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-medium rounded-lg transition-colors">
              {{ submitting ? (editingSiteId ? 'Saving...' : 'Creating...') : (editingSiteId ? 'Save Changes' : 'Create Site') }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useSitesStore } from '../stores/sites'
import api from '../api'

const store = useSitesStore()
const { sites, loading } = storeToRefs(store)
const showModal = ref(false)
const showAdvanced = ref(false)
const showSecurity = ref(false)
const submitting = ref(false)
const formError = ref('')
const editingSiteId = ref(null)

const allCountries = ref([])
const highRiskCountries = ref([])
const countrySearch = ref('')
const showCountryPicker = ref(false)

async function loadCountries() {
  try {
    const { data } = await api.get('/shield/countries')
    allCountries.value = data.countries
    highRiskCountries.value = data.high_risk
  } catch { /* countries will stay empty */ }
}

const selectedCountries = computed({
  get: () => form.blocked_countries ? form.blocked_countries.split(',').filter(Boolean) : [],
  set: (codes) => { form.blocked_countries = codes.join(',') },
})

const filteredCountries = computed(() => {
  const q = countrySearch.value.toLowerCase()
  if (!q) return allCountries.value
  return allCountries.value.filter(c =>
    c.name.toLowerCase().includes(q) || c.code.toLowerCase().includes(q)
  )
})

function toggleCountry(code) {
  const current = new Set(selectedCountries.value)
  if (current.has(code)) {
    current.delete(code)
  } else {
    current.add(code)
  }
  selectedCountries.value = [...current].sort()
}

function addHighRiskPreset() {
  const current = new Set(selectedCountries.value)
  highRiskCountries.value.forEach(c => current.add(c))
  selectedCountries.value = [...current].sort()
}

function clearBlockedCountries() {
  selectedCountries.value = []
}

function countryName(code) {
  const c = allCountries.value.find(x => x.code === code)
  return c ? c.name : code
}

const defaultForm = {
  name: '',
  target_url: '',
  crawl_concurrency: 5,
  crawl_delay: 0.5,
  crawl_max_pages: 10000,
  respect_robots_txt: true,
  internal_url: '',
  override_host: '',
  shield_port: null,
  waf_enabled: true,
  rate_limit_enabled: true,
  rate_limit_requests: 60,
  rate_limit_window: 60,
  security_headers_enabled: true,
  block_bots: true,
  block_suspicious_paths: true,
  max_body_size: 1048576,
  ip_whitelist: '',
  ip_blacklist: '',
  blocked_countries: '',
}

const form = reactive({ ...defaultForm })

const bodySizeKB = computed({
  get: () => Math.round(form.max_body_size / 1024),
  set: (v) => { form.max_body_size = v * 1024 },
})

onMounted(() => {
  store.fetchSites()
  loadCountries()
})

function openCreateModal() {
  editingSiteId.value = null
  Object.assign(form, { ...defaultForm })
  showAdvanced.value = false
  showSecurity.value = false
  showCountryPicker.value = false
  countrySearch.value = ''
  formError.value = ''
  showModal.value = true
}

function openEditModal(site) {
  editingSiteId.value = site.id
  Object.assign(form, {
    name: site.name,
    target_url: site.target_url,
    crawl_concurrency: site.crawl_concurrency,
    crawl_delay: site.crawl_delay,
    crawl_max_pages: site.crawl_max_pages,
    respect_robots_txt: site.respect_robots_txt,
    internal_url: site.internal_url || '',
    override_host: site.override_host || '',
    shield_port: site.shield_port,
    waf_enabled: site.waf_enabled,
    rate_limit_enabled: site.rate_limit_enabled,
    rate_limit_requests: site.rate_limit_requests,
    rate_limit_window: site.rate_limit_window,
    security_headers_enabled: site.security_headers_enabled,
    block_bots: site.block_bots,
    block_suspicious_paths: site.block_suspicious_paths,
    max_body_size: site.max_body_size,
    ip_whitelist: site.ip_whitelist || '',
    ip_blacklist: site.ip_blacklist || '',
    blocked_countries: site.blocked_countries || '',
  })
  showAdvanced.value = !!(site.internal_url || site.override_host)
  showSecurity.value = false
  showCountryPicker.value = false
  countrySearch.value = ''
  formError.value = ''
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  editingSiteId.value = null
}

function buildPayload() {
  const payload = { ...form }
  if (!payload.internal_url) payload.internal_url = null
  if (!payload.override_host) payload.override_host = null
  if (!payload.shield_port) payload.shield_port = null
  return payload
}

async function handleSubmit() {
  formError.value = ''
  submitting.value = true
  try {
    const payload = buildPayload()
    if (editingSiteId.value) {
      await store.updateSite(editingSiteId.value, payload)
    } else {
      await store.createSite(payload)
    }
    closeModal()
  } catch (e) {
    const detail = e.response?.data?.detail
    if (Array.isArray(detail)) {
      formError.value = detail.map(d => d.msg?.replace('Value error, ', '') || d.msg).join('. ')
    } else {
      formError.value = detail || 'Operation failed'
    }
  } finally {
    submitting.value = false
  }
}

async function handleDelete(siteId) {
  if (confirm('Are you sure? This will delete all cached data for this site.')) {
    await store.deleteSite(siteId)
  }
}
</script>
