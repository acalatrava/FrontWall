<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-white">Cached Pages</h1>
        <p class="text-sm text-gray-400 mt-1">Site: {{ site?.name || siteId }}</p>
      </div>
      <button
        @click="showAddModal = true"
        class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors"
      >
        + Add URL
      </button>
    </div>

    <div v-if="stats" class="grid grid-cols-3 gap-4 mb-6">
      <div class="bg-gray-900 border border-gray-800 rounded-xl p-4 text-center">
        <div class="text-2xl font-bold text-white">{{ stats.total_pages }}</div>
        <div class="text-xs text-gray-400">Total Pages</div>
      </div>
      <div class="bg-gray-900 border border-gray-800 rounded-xl p-4 text-center">
        <div class="text-2xl font-bold text-blue-400">{{ formatSize(stats.total_size_bytes) }}</div>
        <div class="text-xs text-gray-400">Cache Size</div>
      </div>
      <div class="bg-gray-900 border border-gray-800 rounded-xl p-4 text-center">
        <div class="text-2xl font-bold text-purple-400">{{ stats.pages_with_forms }}</div>
        <div class="text-xs text-gray-400">Pages with Forms</div>
      </div>
    </div>

    <div class="bg-gray-900 border border-gray-800 rounded-xl">
      <div class="px-6 py-4 border-b border-gray-800 flex items-center gap-3">
        <input
          v-model="search"
          placeholder="Filter pages..."
          class="flex-1 px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>
      <div v-if="filteredPages.length === 0" class="p-6 text-center text-gray-500">
        No pages found.
      </div>
      <div v-else class="divide-y divide-gray-800 max-h-[600px] overflow-y-auto">
        <div v-for="page in filteredPages" :key="page.id" class="px-6 py-3 flex items-center justify-between group hover:bg-gray-800/50">
          <div class="flex-1 min-w-0">
            <div class="text-sm text-white truncate">{{ page.path }}</div>
            <div class="text-xs text-gray-500 flex gap-3 mt-0.5">
              <span>{{ page.content_type }}</span>
              <span>{{ formatSize(page.size_bytes) }}</span>
              <span v-if="page.is_manual" class="text-yellow-400">manual</span>
              <span v-if="page.detected_forms" class="text-purple-400">has forms</span>
            </div>
          </div>
          <button
            @click="deletePage(page.id)"
            class="opacity-0 group-hover:opacity-100 px-2 py-1 text-xs text-red-400 hover:bg-red-500/10 rounded transition-all"
          >
            Remove
          </button>
        </div>
      </div>
    </div>

    <div v-if="showAddModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div class="bg-gray-900 border border-gray-800 rounded-xl w-full max-w-lg p-6 mx-4">
        <h2 class="text-xl font-bold text-white mb-4">Add URL to Cache</h2>
        <form @submit.prevent="handleAdd" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-300 mb-1">URL</label>
            <input v-model="addUrl" required type="url" class="w-full px-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="https://mysite.com/some-page" />
          </div>
          <div v-if="addError" class="text-sm text-red-400">{{ addError }}</div>
          <div class="flex justify-end gap-3">
            <button type="button" @click="showAddModal = false" class="px-4 py-2 text-sm text-gray-400">Cancel</button>
            <button type="submit" :disabled="adding" class="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-medium rounded-lg transition-colors">
              {{ adding ? 'Adding...' : 'Add' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../api'

const props = defineProps({ siteId: String })

const site = ref(null)
const pages = ref([])
const stats = ref(null)
const search = ref('')
const showAddModal = ref(false)
const addUrl = ref('')
const addError = ref('')
const adding = ref(false)

const filteredPages = computed(() => {
  if (!search.value) return pages.value
  const q = search.value.toLowerCase()
  return pages.value.filter(p => p.path.toLowerCase().includes(q) || p.url.toLowerCase().includes(q))
})

function formatSize(bytes) {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let i = 0
  let size = bytes
  while (size >= 1024 && i < units.length - 1) { size /= 1024; i++ }
  return `${size.toFixed(i > 0 ? 1 : 0)} ${units[i]}`
}

async function loadData() {
  try {
    const [siteResp, pagesResp, statsResp] = await Promise.all([
      api.get(`/sites/${props.siteId}`),
      api.get(`/pages/${props.siteId}`),
      api.get(`/pages/${props.siteId}/stats`),
    ])
    site.value = siteResp.data
    pages.value = pagesResp.data
    stats.value = statsResp.data
  } catch {}
}

async function handleAdd() {
  addError.value = ''
  adding.value = true
  try {
    await api.post('/pages/add', { url: addUrl.value, site_id: props.siteId })
    showAddModal.value = false
    addUrl.value = ''
    await loadData()
  } catch (e) {
    addError.value = e.response?.data?.detail || 'Failed to add URL'
  } finally {
    adding.value = false
  }
}

async function deletePage(pageId) {
  if (!confirm('Remove this page from cache?')) return
  try {
    await api.delete(`/pages/${pageId}`)
    pages.value = pages.value.filter(p => p.id !== pageId)
  } catch {}
}

onMounted(loadData)
</script>
