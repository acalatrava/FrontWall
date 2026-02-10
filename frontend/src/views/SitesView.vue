<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-white">Sites</h1>
      <button
        @click="showModal = true"
        class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors"
      >
        + Add Site
      </button>
    </div>

    <div v-if="loading" class="text-center text-gray-400 py-12">Loading...</div>

    <div v-else-if="sites.length === 0" class="bg-gray-900 border border-gray-800 rounded-xl p-12 text-center">
      <p class="text-gray-400 mb-4">No sites configured. Add your first WordPress site to protect.</p>
      <button
        @click="showModal = true"
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
            <div class="flex gap-4 mt-3 text-xs text-gray-500">
              <span>Concurrency: {{ site.crawl_concurrency }}</span>
              <span>Max pages: {{ site.crawl_max_pages }}</span>
              <span>Delay: {{ site.crawl_delay }}s</span>
            </div>
          </div>
          <div class="flex items-center gap-2">
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
      <div class="bg-gray-900 border border-gray-800 rounded-xl w-full max-w-lg p-6 mx-4">
        <h2 class="text-xl font-bold text-white mb-4">Add New Site</h2>
        <form @submit.prevent="handleCreate" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-300 mb-1">Site Name</label>
            <input v-model="form.name" required class="w-full px-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="My WordPress Site" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-300 mb-1">Target URL</label>
            <input v-model="form.target_url" required type="url" class="w-full px-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="https://mysite.com" />
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
          <div v-if="formError" class="text-sm text-red-400">{{ formError }}</div>
          <div class="flex justify-end gap-3 pt-2">
            <button type="button" @click="showModal = false" class="px-4 py-2 text-sm text-gray-400 hover:text-gray-200">Cancel</button>
            <button type="submit" :disabled="creating" class="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-medium rounded-lg transition-colors">
              {{ creating ? 'Creating...' : 'Create Site' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useSitesStore } from '../stores/sites'

const store = useSitesStore()
const { sites, loading } = storeToRefs(store)
const showModal = ref(false)
const creating = ref(false)
const formError = ref('')

const form = reactive({
  name: '',
  target_url: '',
  crawl_concurrency: 5,
  crawl_delay: 0.5,
  crawl_max_pages: 10000,
  respect_robots_txt: true,
})

onMounted(() => store.fetchSites())

async function handleCreate() {
  formError.value = ''
  creating.value = true
  try {
    await store.createSite({ ...form })
    showModal.value = false
    Object.assign(form, { name: '', target_url: '', crawl_concurrency: 5, crawl_delay: 0.5, crawl_max_pages: 10000, respect_robots_txt: true })
  } catch (e) {
    formError.value = e.response?.data?.detail || 'Failed to create site'
  } finally {
    creating.value = false
  }
}

async function handleDelete(siteId) {
  if (confirm('Are you sure? This will delete all cached data for this site.')) {
    await store.deleteSite(siteId)
  }
}
</script>
