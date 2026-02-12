<template>
  <div>
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-6">
      <h1 class="text-xl sm:text-2xl font-bold text-white">{{ t('security.title') }}</h1>
      <div v-if="saving" class="flex items-center gap-2 text-xs text-blue-400">
        <svg class="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg>
        {{ t('security.saving') }}
      </div>
      <div v-else-if="saved" class="flex items-center gap-1.5 text-xs text-emerald-400">
        <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
        {{ t('security.saved') }}
      </div>
    </div>

    <div v-if="sites.length === 0" class="bg-gray-900 border border-gray-800 rounded-xl p-12 text-center">
      <p class="text-gray-400">{{ t('common.noSites') }} <router-link to="/sites" class="text-blue-400 hover:underline">{{ t('common.addSiteFirst') }}</router-link></p>
    </div>

    <template v-else>
      <div class="mb-6">
        <label class="block text-sm font-medium text-gray-300 mb-2">{{ t('common.selectSite') }}</label>
        <select
          v-model="selectedSiteId"
          class="w-full max-w-md px-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option v-for="site in sites" :key="site.id" :value="site.id">{{ site.name }}</option>
        </select>
      </div>

      <div v-if="selectedSite" class="space-y-6">

        <!-- Shield Configuration (read-only) -->
        <div class="bg-gray-900 border border-gray-800 rounded-xl p-4 sm:p-6">
          <h2 class="text-lg font-semibold text-white mb-4">{{ t('security.shield.title') }}</h2>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div class="flex items-center justify-between bg-gray-800/50 rounded-lg p-4">
              <span class="text-gray-300">{{ t('security.shield.port') }}</span>
              <span class="font-mono" :class="selectedSite.shield_port ? 'text-blue-400' : 'text-gray-500'">
                {{ selectedSite.shield_port || t('security.shield.notSet') }}
              </span>
            </div>
            <div class="flex items-center justify-between bg-gray-800/50 rounded-lg p-4">
              <span class="text-gray-300">{{ t('security.shield.status') }}</span>
              <span :class="selectedSite.shield_active ? 'text-green-400' : 'text-gray-500'">
                {{ selectedSite.shield_active ? t('security.shield.deployed') : t('security.shield.inactive') }}
              </span>
            </div>
          </div>
        </div>

        <!-- WAF -->
        <div class="bg-gray-900 border border-gray-800 rounded-xl p-4 sm:p-6">
          <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
            <h2 class="text-lg font-semibold text-white">{{ t('security.waf.title') }}</h2>
            <ToggleSwitch :checked="selectedSite.waf_enabled" @update="v => saveSetting('waf_enabled', v)" color="green" />
          </div>
          <div v-if="selectedSite.waf_enabled" class="space-y-4">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div class="flex items-center justify-between bg-gray-800/50 rounded-lg p-4">
                <div>
                  <div class="text-sm font-medium text-white">{{ t('security.waf.botDetection') }}</div>
                  <div class="text-xs text-gray-400 mt-0.5">{{ t('security.waf.botDetectionDesc') }}</div>
                </div>
                <ToggleSwitch :checked="selectedSite.block_bots" @update="v => saveSetting('block_bots', v)" />
              </div>
              <div class="flex items-center justify-between bg-gray-800/50 rounded-lg p-4">
                <div>
                  <div class="text-sm font-medium text-white">{{ t('security.waf.suspiciousPath') }}</div>
                  <div class="text-xs text-gray-400 mt-0.5">{{ t('security.waf.suspiciousPathDesc') }}</div>
                </div>
                <ToggleSwitch :checked="selectedSite.block_suspicious_paths" @update="v => saveSetting('block_suspicious_paths', v)" />
              </div>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div v-for="feature in readOnlyWafFeatures" :key="feature.name" class="flex items-center justify-between bg-gray-800/50 rounded-lg p-4">
                <div>
                  <div class="text-sm font-medium text-white">{{ feature.name }}</div>
                  <div class="text-xs text-gray-400 mt-0.5">{{ feature.description }}</div>
                </div>
                <DisabledToggle />
              </div>
            </div>
          </div>
        </div>

        <!-- Rate Limiting -->
        <div class="bg-gray-900 border border-gray-800 rounded-xl p-4 sm:p-6">
          <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
            <h2 class="text-lg font-semibold text-white">{{ t('security.rateLimit.title') }}</h2>
            <ToggleSwitch :checked="selectedSite.rate_limit_enabled" @update="v => saveSetting('rate_limit_enabled', v)" color="green" />
          </div>
          <div v-if="selectedSite.rate_limit_enabled" class="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
            <div class="bg-gray-800/50 rounded-lg p-4">
              <label class="text-gray-400 text-xs block mb-2">{{ t('security.rateLimit.requestsPerWindow') }}</label>
              <input
                type="number" min="1" :value="selectedSite.rate_limit_requests"
                @change="e => saveSetting('rate_limit_requests', parseInt(e.target.value))"
                class="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div class="bg-gray-800/50 rounded-lg p-4">
              <label class="text-gray-400 text-xs block mb-2">{{ t('security.rateLimit.windowDuration') }}</label>
              <input
                type="number" min="1" :value="selectedSite.rate_limit_window"
                @change="e => saveSetting('rate_limit_window', parseInt(e.target.value))"
                class="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        </div>

        <!-- Security Headers -->
        <div class="bg-gray-900 border border-gray-800 rounded-xl p-4 sm:p-6">
          <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
            <h2 class="text-lg font-semibold text-white">{{ t('security.secHeaders.title') }}</h2>
            <ToggleSwitch :checked="selectedSite.security_headers_enabled" @update="v => saveSetting('security_headers_enabled', v)" color="green" />
          </div>
          <div v-if="selectedSite.security_headers_enabled" class="space-y-2">
            <div v-for="header in securityHeaders" :key="header.name" class="bg-gray-800/50 rounded-lg px-4 py-3">
              <div class="text-sm font-mono text-blue-400">{{ header.name }}</div>
              <div class="text-xs text-gray-500 font-mono mt-1 break-all">{{ header.value }}</div>
            </div>
          </div>
        </div>

        <!-- IP Access Control -->
        <div class="bg-gray-900 border border-gray-800 rounded-xl p-4 sm:p-6">
          <h2 class="text-lg font-semibold text-white mb-4">{{ t('security.ipAccess.title') }}</h2>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="rounded-lg p-4" :class="whitelistActive ? 'bg-emerald-900/20 border border-emerald-700/30' : 'bg-gray-800/50'">
              <div class="flex items-center gap-2 mb-2">
                <h3 class="text-sm font-medium" :class="whitelistActive ? 'text-emerald-300' : 'text-gray-300'">{{ t('security.ipAccess.whitelist') }}</h3>
                <span v-if="whitelistActive" class="px-1.5 py-0.5 bg-emerald-500/20 text-emerald-400 rounded text-[10px] font-semibold uppercase">{{ t('common.active') }}</span>
                <span v-else class="px-1.5 py-0.5 bg-gray-700/50 text-gray-500 rounded text-[10px] font-semibold uppercase">{{ t('security.ipAccess.noRestriction') }}</span>
              </div>
              <p class="text-xs mb-2" :class="whitelistActive ? 'text-emerald-400/70' : 'text-gray-500'">
                {{ whitelistActive ? t('security.ipAccess.whitelistActiveDesc', { count: whitelistCount }) : t('security.ipAccess.whitelistEmptyDesc') }}
              </p>
              <div class="flex gap-2">
                <input
                  v-model="ipWhitelistInput"
                  :placeholder="t('security.ipAccess.whitelistPlaceholder')"
                  class="flex-1 px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm font-mono placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button @click="saveSetting('ip_whitelist', ipWhitelistInput)" class="px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-medium rounded-lg transition-colors">{{ t('common.save') }}</button>
              </div>
              <p class="text-xs text-gray-500 mt-1.5">{{ t('security.ipAccess.whitelistHint') }}</p>
            </div>
            <div class="rounded-lg p-4" :class="blacklistActive ? 'bg-red-900/20 border border-red-700/30' : 'bg-gray-800/50'">
              <div class="flex items-center gap-2 mb-2">
                <h3 class="text-sm font-medium" :class="blacklistActive ? 'text-red-300' : 'text-gray-300'">{{ t('security.ipAccess.blacklist') }}</h3>
                <span v-if="blacklistActive" class="px-1.5 py-0.5 bg-red-500/20 text-red-400 rounded text-[10px] font-semibold uppercase">{{ t('security.ipAccess.blocking', { count: blacklistCount }) }}</span>
                <span v-else class="px-1.5 py-0.5 bg-gray-700/50 text-gray-500 rounded text-[10px] font-semibold uppercase">{{ t('security.ipAccess.noneBlocked') }}</span>
              </div>
              <p class="text-xs mb-2" :class="blacklistActive ? 'text-red-400/70' : 'text-gray-500'">
                {{ blacklistActive ? t('security.ipAccess.blacklistActiveDesc', { count: blacklistCount }) : t('security.ipAccess.blacklistEmptyDesc') }}
              </p>
              <div class="flex gap-2">
                <input
                  v-model="ipBlacklistInput"
                  :placeholder="t('security.ipAccess.blacklistPlaceholder')"
                  class="flex-1 px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm font-mono placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button @click="saveSetting('ip_blacklist', ipBlacklistInput)" class="px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-medium rounded-lg transition-colors">{{ t('common.save') }}</button>
              </div>
              <p class="text-xs text-gray-500 mt-1.5">{{ t('security.ipAccess.blacklistHint') }}</p>
            </div>
          </div>
        </div>

        <!-- Country Blocking -->
        <div class="bg-gray-900 border border-gray-800 rounded-xl p-4 sm:p-6">
          <h2 class="text-lg font-semibold text-white mb-4">Country Blocking</h2>
          <p class="text-xs text-gray-500 mb-3">Traffic from selected countries is blocked at the WAF level.</p>

          <div class="flex flex-wrap gap-1.5 mb-4" v-if="selectedCountries.length">
            <span
              v-for="code in selectedCountries"
              :key="code"
              class="inline-flex items-center gap-1 px-2.5 py-1 bg-red-900/40 border border-red-700/40 text-red-300 rounded-full text-xs font-medium cursor-pointer hover:bg-red-800/40 transition-colors"
              @click="removeCountry(code)"
            >
              {{ countryLabel(code) }}
              <svg class="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6 6 18M6 6l12 12"/></svg>
            </span>
          </div>
          <p v-else class="text-sm text-gray-500 mb-4">No countries blocked.</p>

          <div class="flex flex-col sm:flex-row gap-2">
            <div class="relative flex-1 sm:max-w-sm">
              <input
                v-model="countrySearch"
                placeholder="Search country..."
                class="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <div v-if="countrySearch && filteredCountries.length" class="absolute top-full left-0 right-0 z-20 mt-1 bg-gray-800 border border-gray-700 rounded-lg max-h-48 overflow-y-auto shadow-xl">
                <button
                  v-for="c in filteredCountries.slice(0, 20)"
                  :key="c.code"
                  @click="addCountry(c.code)"
                  class="w-full text-left px-3 py-2 text-sm text-gray-300 hover:bg-gray-700 transition-colors"
                >{{ c.code }} — {{ c.name }}</button>
              </div>
            </div>
            <button @click="loadHighRisk" class="px-3 py-2 bg-red-600/20 border border-red-700/40 text-red-400 text-xs font-medium rounded-lg hover:bg-red-600/30 transition-colors whitespace-nowrap">{{ t('security.country.highRisk') }}</button>
          </div>
        </div>

        <!-- Max Body Size -->
        <div class="bg-gray-900 border border-gray-800 rounded-xl p-4 sm:p-6">
          <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
            <h2 class="text-lg font-semibold text-white">{{ t('security.bodySize.title') }}</h2>
            <ToggleSwitch :checked="selectedSite.request_size_limit_enabled" @update="v => saveSetting('request_size_limit_enabled', v)" color="green" />
          </div>
          <div v-if="selectedSite.request_size_limit_enabled" class="bg-gray-800/50 rounded-lg p-4">
            <label class="text-gray-400 text-xs block mb-2">{{ t('security.bodySize.label') }}</label>
            <div class="flex gap-2 items-center">
              <input
                type="number" min="1024" :value="selectedSite.max_body_size"
                @change="e => saveSetting('max_body_size', parseInt(e.target.value))"
                class="w-48 px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <span class="text-sm text-gray-400">{{ formatSize(selectedSite.max_body_size) }}</span>
            </div>
          </div>
        </div>

        <!-- Blocked Patterns -->
        <div class="bg-gray-900 border border-gray-800 rounded-xl p-4 sm:p-6">
          <h2 class="text-lg font-semibold text-white mb-4">{{ t('security.blockedPatterns.title') }}</h2>
          <p class="text-sm text-gray-400 mb-4">
            {{ t('security.blockedPatterns.description') }}
          </p>
          <div class="mb-4">
            <h3 class="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">{{ t('security.blockedPatterns.builtIn') }}</h3>
            <div class="flex flex-wrap gap-2">
              <span v-for="pattern in builtInBlockedPatterns" :key="pattern" class="px-3 py-1.5 bg-red-500/10 text-red-400 rounded-lg text-xs font-mono">
                {{ pattern }}
              </span>
            </div>
          </div>
          <div>
            <h3 class="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">{{ t('security.blockedPatterns.custom') }}</h3>
            <div v-if="customPatterns.length" class="flex flex-wrap gap-2 mb-3">
              <span
                v-for="(pattern, idx) in customPatterns"
                :key="idx"
                class="inline-flex items-center gap-1 px-3 py-1.5 bg-orange-500/10 text-orange-400 rounded-lg text-xs font-mono cursor-pointer hover:bg-orange-500/20 transition-colors"
                @click="removeCustomPattern(idx)"
              >
                {{ pattern }}
                <svg class="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6 6 18M6 6l12 12"/></svg>
              </span>
            </div>
            <p v-else class="text-xs text-gray-500 mb-3">{{ t('security.blockedPatterns.noCustom') }}</p>
            <div class="flex gap-2">
              <input
                v-model="newPatternInput"
                @keydown.enter="addCustomPattern"
                :placeholder="t('security.blockedPatterns.addPlaceholder')"
                class="flex-1 max-w-sm px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm font-mono placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button @click="addCustomPattern" :disabled="!newPatternInput.trim()" class="px-3 py-2 bg-orange-600 hover:bg-orange-700 disabled:opacity-40 text-white text-xs font-medium rounded-lg transition-colors">{{ t('common.add') }}</button>
            </div>
          </div>
        </div>

        <!-- Input Sanitization -->
        <div class="bg-gray-900 border border-gray-800 rounded-xl p-4 sm:p-6">
          <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
            <div>
              <h2 class="text-lg font-semibold text-white">{{ t('security.sanitization.title') }}</h2>
              <p class="text-sm text-gray-400 mt-1">{{ t('security.sanitization.description') }}</p>
            </div>
            <ToggleSwitch :checked="selectedSite.sanitization_enabled" @update="v => saveSetting('sanitization_enabled', v)" color="green" />
          </div>
          <div v-if="selectedSite.sanitization_enabled" class="space-y-3">
            <div v-for="step in sanitizationSteps" :key="step.order" class="flex items-start gap-3">
              <span class="mt-1 w-6 h-6 rounded-full bg-blue-500/20 text-blue-400 flex items-center justify-center text-xs font-bold">{{ step.order }}</span>
              <div>
                <div class="text-sm font-medium text-white">{{ step.name }}</div>
                <div class="text-xs text-gray-400 mt-0.5">{{ step.description }}</div>
              </div>
            </div>
          </div>
          <div v-else class="bg-amber-500/10 border border-amber-500/20 rounded-lg p-3 mt-2">
            <p class="text-xs text-amber-300">{{ t('security.sanitization.disabledWarning') }}</p>
          </div>
        </div>

      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, h } from 'vue'
import { storeToRefs } from 'pinia'
import { useI18n } from 'vue-i18n'
import { useSitesStore } from '../stores/sites'
import api from '../api'

const { t } = useI18n()
const store = useSitesStore()
const { sites } = storeToRefs(store)
const selectedSiteId = ref(null)
const saving = ref(false)
const saved = ref(false)
let savedTimer = null

const selectedSite = computed(() => sites.value.find(s => s.id === selectedSiteId.value) || null)

const ipWhitelistInput = ref('')
const ipBlacklistInput = ref('')
const countrySearch = ref('')
const countries = ref([])
const highRiskCountries = ref([])
const newPatternInput = ref('')

const ToggleSwitch = {
  props: { checked: Boolean, color: { type: String, default: 'blue' } },
  emits: ['update'],
  setup(props, { emit }) {
    const colors = { green: 'peer-checked:bg-green-500', blue: 'peer-checked:bg-blue-500' }
    return () =>
      h('label', { class: 'flex items-center cursor-pointer flex-shrink-0' }, [
        h('div', { class: 'relative' }, [
          h('input', {
            type: 'checkbox',
            checked: props.checked,
            onChange: () => emit('update', !props.checked),
            class: 'sr-only peer',
          }),
          h('div', { class: `w-11 h-6 bg-gray-700 rounded-full ${colors[props.color] || colors.blue} transition-colors` }),
          h('div', { class: 'absolute left-0.5 top-0.5 w-5 h-5 bg-white rounded-full transition-transform peer-checked:translate-x-5' }),
        ]),
      ])
  },
}

const DisabledToggle = {
  setup() {
    return () =>
      h('div', { class: 'flex items-center flex-shrink-0 opacity-60', title: 'Always enabled' }, [
        h('div', { class: 'relative' }, [
          h('div', { class: 'w-11 h-6 bg-green-500/70 rounded-full' }),
          h('div', { class: 'absolute left-[22px] top-0.5 w-5 h-5 bg-white/80 rounded-full' }),
        ]),
      ])
  },
}

const selectedCountries = computed(() => {
  const s = selectedSite.value
  if (!s || !s.blocked_countries) return []
  return s.blocked_countries.split(',').map(c => c.trim()).filter(Boolean)
})

const filteredCountries = computed(() => {
  const q = countrySearch.value.toLowerCase()
  return countries.value.filter(c =>
    !selectedCountries.value.includes(c.code) &&
    (c.code.toLowerCase().includes(q) || c.name.toLowerCase().includes(q))
  )
})

function countryLabel(code) {
  const found = countries.value.find(c => c.code === code)
  return found ? `${code} — ${found.name}` : code
}

function addCountry(code) {
  const updated = [...selectedCountries.value, code]
  countrySearch.value = ''
  saveSetting('blocked_countries', updated.join(','))
}

function removeCountry(code) {
  const updated = selectedCountries.value.filter(c => c !== code)
  saveSetting('blocked_countries', updated.join(','))
}

function loadHighRisk() {
  const merged = new Set([...selectedCountries.value, ...highRiskCountries.value])
  saveSetting('blocked_countries', [...merged].join(','))
}

const whitelistActive = computed(() => {
  const s = selectedSite.value
  return s && s.ip_whitelist && s.ip_whitelist.trim().length > 0
})
const whitelistCount = computed(() => {
  const s = selectedSite.value
  if (!s || !s.ip_whitelist) return 0
  return s.ip_whitelist.split(',').filter(ip => ip.trim()).length
})
const blacklistActive = computed(() => {
  const s = selectedSite.value
  return s && s.ip_blacklist && s.ip_blacklist.trim().length > 0
})
const blacklistCount = computed(() => {
  const s = selectedSite.value
  if (!s || !s.ip_blacklist) return 0
  return s.ip_blacklist.split(',').filter(ip => ip.trim()).length
})

const customPatterns = computed(() => {
  const s = selectedSite.value
  if (!s || !s.custom_blocked_patterns) return []
  return s.custom_blocked_patterns.split('\n').filter(p => p.trim())
})

function addCustomPattern() {
  const val = newPatternInput.value.trim()
  if (!val) return
  const current = customPatterns.value
  if (current.includes(val)) {
    newPatternInput.value = ''
    return
  }
  const updated = [...current, val].join('\n')
  newPatternInput.value = ''
  saveSetting('custom_blocked_patterns', updated)
}

function removeCustomPattern(idx) {
  const updated = customPatterns.value.filter((_, i) => i !== idx).join('\n')
  saveSetting('custom_blocked_patterns', updated)
}

watch(sites, (val) => {
  if (val.length && !selectedSiteId.value) {
    selectedSiteId.value = val[0].id
  }
})

watch(selectedSite, (s) => {
  if (s) {
    ipWhitelistInput.value = s.ip_whitelist || ''
    ipBlacklistInput.value = s.ip_blacklist || ''
  }
})

async function saveSetting(field, value) {
  if (!selectedSiteId.value) return
  saving.value = true
  saved.value = false
  clearTimeout(savedTimer)
  try {
    await store.updateSite(selectedSiteId.value, { [field]: value })
    saving.value = false
    saved.value = true
    savedTimer = setTimeout(() => { saved.value = false }, 2000)
  } catch {
    saving.value = false
  }
}

onMounted(async () => {
  await store.fetchSites()
  if (sites.value.length) {
    selectedSiteId.value = sites.value[0].id
  }
  try {
    const { data } = await api.get('/shield/countries')
    countries.value = data.countries || []
    highRiskCountries.value = data.high_risk || []
  } catch {}
})

function formatSize(bytes) {
  if (!bytes) return '0 B'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1048576) return (bytes / 1024).toFixed(0) + ' KB'
  return (bytes / 1048576).toFixed(1) + ' MB'
}

const readOnlyWafFeatures = computed(() => {
  const s = selectedSite.value
  if (!s) return []
  return [
    { name: t('security.waf.requestSizeLimits'), description: t('security.waf.requestSizeLimitsDesc', { size: formatSize(s.max_body_size) }) },
    { name: t('security.waf.postSanitization'), description: t('security.waf.postSanitizationDesc') },
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

const builtInBlockedPatterns = [
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
