<template>
  <div>
    <h1 class="text-2xl font-bold text-white mb-6">Security Settings</h1>

    <div v-if="sites.length === 0" class="bg-gray-900 border border-gray-800 rounded-xl p-12 text-center">
      <p class="text-gray-400">No sites configured. <router-link to="/sites" class="text-blue-400 hover:underline">Add a site first.</router-link></p>
    </div>

    <template v-else>
      <div class="mb-6">
        <label class="block text-sm font-medium text-gray-300 mb-2">Select Site</label>
        <select
          v-model="selectedSiteId"
          class="w-full max-w-md px-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option v-for="site in sites" :key="site.id" :value="site.id">{{ site.name }}</option>
        </select>
      </div>

      <div v-if="selectedSite" class="space-y-6">
        <div class="bg-gray-900 border border-gray-800 rounded-xl p-6">
          <h2 class="text-lg font-semibold text-white mb-4">Shield Configuration</h2>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div class="flex items-center justify-between bg-gray-800/50 rounded-lg p-4">
              <span class="text-gray-300">Shield Port</span>
              <span class="font-mono" :class="selectedSite.shield_port ? 'text-blue-400' : 'text-gray-500'">
                {{ selectedSite.shield_port || 'Not set' }}
              </span>
            </div>
            <div class="flex items-center justify-between bg-gray-800/50 rounded-lg p-4">
              <span class="text-gray-300">Status</span>
              <span :class="selectedSite.shield_active ? 'text-green-400' : 'text-gray-500'">
                {{ selectedSite.shield_active ? 'Deployed' : 'Inactive' }}
              </span>
            </div>
          </div>
        </div>

        <div class="bg-gray-900 border border-gray-800 rounded-xl p-6">
          <h2 class="text-lg font-semibold text-white mb-4">WAF (Web Application Firewall)</h2>
          <div class="flex items-center gap-3 mb-4">
            <span class="px-3 py-1 rounded-full text-xs font-medium" :class="selectedSite.waf_enabled ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'">
              {{ selectedSite.waf_enabled ? 'Enabled' : 'Disabled' }}
            </span>
          </div>
          <div v-if="selectedSite.waf_enabled" class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div v-for="feature in wafFeatures" :key="feature.name" class="flex items-start gap-3 bg-gray-800/50 rounded-lg p-4">
              <span
                class="mt-0.5 w-5 h-5 rounded-full flex items-center justify-center text-xs"
                :class="feature.enabled ? 'bg-green-500/20 text-green-400' : 'bg-gray-700 text-gray-500'"
              >
                {{ feature.enabled ? '&#10003;' : '&#10005;' }}
              </span>
              <div>
                <div class="text-sm font-medium text-white">{{ feature.name }}</div>
                <div class="text-xs text-gray-400 mt-0.5">{{ feature.description }}</div>
              </div>
            </div>
          </div>
        </div>

        <div class="bg-gray-900 border border-gray-800 rounded-xl p-6">
          <h2 class="text-lg font-semibold text-white mb-4">Rate Limiting</h2>
          <div class="flex items-center gap-3 mb-4">
            <span class="px-3 py-1 rounded-full text-xs font-medium" :class="selectedSite.rate_limit_enabled ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'">
              {{ selectedSite.rate_limit_enabled ? 'Enabled' : 'Disabled' }}
            </span>
          </div>
          <div v-if="selectedSite.rate_limit_enabled" class="grid grid-cols-2 gap-4 text-sm">
            <div class="bg-gray-800/50 rounded-lg p-4">
              <div class="text-gray-400">Requests per window</div>
              <div class="text-white font-mono text-lg mt-1">{{ selectedSite.rate_limit_requests }}</div>
            </div>
            <div class="bg-gray-800/50 rounded-lg p-4">
              <div class="text-gray-400">Window duration</div>
              <div class="text-white font-mono text-lg mt-1">{{ selectedSite.rate_limit_window }}s</div>
            </div>
          </div>
        </div>

        <div class="bg-gray-900 border border-gray-800 rounded-xl p-6">
          <h2 class="text-lg font-semibold text-white mb-4">Security Headers</h2>
          <div class="flex items-center gap-3 mb-4">
            <span class="px-3 py-1 rounded-full text-xs font-medium" :class="selectedSite.security_headers_enabled ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'">
              {{ selectedSite.security_headers_enabled ? 'Enabled' : 'Disabled' }}
            </span>
          </div>
          <div v-if="selectedSite.security_headers_enabled" class="space-y-2">
            <div v-for="header in securityHeaders" :key="header.name" class="bg-gray-800/50 rounded-lg px-4 py-3">
              <div class="text-sm font-mono text-blue-400">{{ header.name }}</div>
              <div class="text-xs text-gray-500 font-mono mt-1 break-all">{{ header.value }}</div>
            </div>
          </div>
        </div>

        <div class="bg-gray-900 border border-gray-800 rounded-xl p-6">
          <h2 class="text-lg font-semibold text-white mb-4">IP Access Control</h2>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="bg-gray-800/50 rounded-lg p-4">
              <h3 class="text-sm font-medium text-gray-300 mb-2">Whitelist</h3>
              <p v-if="!selectedSite.ip_whitelist" class="text-xs text-gray-500">Not configured (all IPs allowed)</p>
              <div v-else class="flex flex-wrap gap-1">
                <span v-for="ip in selectedSite.ip_whitelist.split(',').filter(Boolean)" :key="ip" class="px-2 py-0.5 bg-green-500/10 text-green-400 rounded text-xs font-mono">{{ ip.trim() }}</span>
              </div>
            </div>
            <div class="bg-gray-800/50 rounded-lg p-4">
              <h3 class="text-sm font-medium text-gray-300 mb-2">Blacklist</h3>
              <p v-if="!selectedSite.ip_blacklist" class="text-xs text-gray-500">Not configured</p>
              <div v-else class="flex flex-wrap gap-1">
                <span v-for="ip in selectedSite.ip_blacklist.split(',').filter(Boolean)" :key="ip" class="px-2 py-0.5 bg-red-500/10 text-red-400 rounded text-xs font-mono">{{ ip.trim() }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="bg-gray-900 border border-gray-800 rounded-xl p-6">
          <h2 class="text-lg font-semibold text-white mb-4">Request Size Limit</h2>
          <div class="bg-gray-800/50 rounded-lg p-4 text-sm">
            <span class="text-gray-400">Maximum body size:</span>
            <span class="ml-2 text-white font-mono">{{ formatSize(selectedSite.max_body_size) }}</span>
          </div>
        </div>

        <div class="bg-gray-900 border border-gray-800 rounded-xl p-6">
          <h2 class="text-lg font-semibold text-white mb-4">Blocked Patterns</h2>
          <p class="text-sm text-gray-400 mb-4">
            Requests matching these patterns in the path or query string are automatically blocked.
          </p>
          <div class="flex flex-wrap gap-2">
            <span v-for="pattern in blockedPatterns" :key="pattern" class="px-3 py-1.5 bg-red-500/10 text-red-400 rounded-lg text-xs font-mono">
              {{ pattern }}
            </span>
          </div>
        </div>

        <div class="bg-gray-900 border border-gray-800 rounded-xl p-6">
          <h2 class="text-lg font-semibold text-white mb-4">Input Sanitization</h2>
          <p class="text-sm text-gray-400 mb-4">
            All POST form data is processed through multiple sanitization layers before forwarding.
          </p>
          <div class="space-y-3">
            <div v-for="step in sanitizationSteps" :key="step.name" class="flex items-start gap-3">
              <span class="mt-1 w-6 h-6 rounded-full bg-blue-500/20 text-blue-400 flex items-center justify-center text-xs font-bold">{{ step.order }}</span>
              <div>
                <div class="text-sm font-medium text-white">{{ step.name }}</div>
                <div class="text-xs text-gray-400 mt-0.5">{{ step.description }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useSitesStore } from '../stores/sites'

const store = useSitesStore()
const { sites } = storeToRefs(store)
const selectedSiteId = ref(null)

const selectedSite = computed(() => sites.value.find(s => s.id === selectedSiteId.value) || null)

watch(sites, (val) => {
  if (val.length && !selectedSiteId.value) {
    selectedSiteId.value = val[0].id
  }
})

onMounted(async () => {
  await store.fetchSites()
  if (sites.value.length) {
    selectedSiteId.value = sites.value[0].id
  }
})

function formatSize(bytes) {
  if (!bytes) return '0 B'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1048576) return (bytes / 1024).toFixed(0) + ' KB'
  return (bytes / 1048576).toFixed(1) + ' MB'
}

const wafFeatures = computed(() => {
  const s = selectedSite.value
  if (!s) return []
  return [
    { name: 'Rate Limiting', description: 'Token bucket per-IP rate limiting', enabled: s.rate_limit_enabled },
    { name: 'Bot Detection', description: 'Blocks known malicious scanners (SQLMap, Nikto, etc.)', enabled: s.block_bots },
    { name: 'Suspicious Path Blocking', description: 'Blocks wp-admin, path traversal, .env, .git, etc.', enabled: s.block_suspicious_paths },
    { name: 'Request Size Limits', description: `Max body: ${formatSize(s.max_body_size)}`, enabled: true },
    { name: 'IP Access Control', description: 'Whitelist / blacklist specific IPs', enabled: !!(s.ip_whitelist || s.ip_blacklist) },
    { name: 'POST Sanitization', description: 'Multi-layer input validation for form submissions', enabled: true },
  ]
})

const securityHeaders = [
  { name: 'Content-Security-Policy', value: 'Dynamically generated from cached assets' },
  { name: 'X-Content-Type-Options', value: 'nosniff' },
  { name: 'X-Frame-Options', value: 'DENY' },
  { name: 'X-XSS-Protection', value: '1; mode=block' },
  { name: 'Strict-Transport-Security', value: 'max-age=63072000; includeSubDomains; preload' },
  { name: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
  { name: 'Permissions-Policy', value: 'camera=(), microphone=(), geolocation=(), payment=()' },
  { name: 'Cross-Origin-Opener-Policy', value: 'same-origin' },
]

const blockedPatterns = [
  'wp-admin', 'wp-login.php', 'xmlrpc.php', 'wp-config',
  '.env', '.git/', 'phpmyadmin', 'wp-includes/',
  '../', '%2e%2e', '/etc/passwd', '/proc/self',
]

const sanitizationSteps = [
  { order: 1, name: 'Field Whitelist', description: 'Only explicitly declared fields are allowed through; unknown fields are stripped' },
  { order: 2, name: 'Unicode Normalization', description: 'All input is normalized to NFC form and null bytes are removed' },
  { order: 3, name: 'HTML Stripping', description: 'All HTML tags are removed using bleach with double-pass cleaning' },
  { order: 4, name: 'SQL Injection Detection', description: 'Patterns like UNION SELECT, OR 1=1, comment sequences are blocked' },
  { order: 5, name: 'XSS Detection', description: 'Script tags, event handlers, javascript: URIs, and other XSS vectors are blocked' },
  { order: 6, name: 'Type Validation', description: 'Fields are validated against their declared type (email, phone, url, etc.)' },
  { order: 7, name: 'Length Enforcement', description: 'Per-field max length limits are enforced' },
  { order: 8, name: 'Custom Regex', description: 'Optional per-field regex validation for custom patterns' },
]
</script>
