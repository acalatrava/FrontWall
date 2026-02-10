<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-white">POST Exception Rules</h1>
        <p class="text-sm text-gray-400 mt-1">Site: {{ site?.name || siteId }}</p>
      </div>
      <button
        @click="openCreateModal"
        class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors"
      >
        + Add Rule
      </button>
    </div>

    <div v-if="detectedForms.length > 0" class="bg-purple-500/10 border border-purple-500/30 rounded-xl p-4 mb-6">
      <h3 class="text-sm font-semibold text-purple-400 mb-2">Detected Forms</h3>
      <p class="text-xs text-gray-400 mb-3">These forms were detected during crawling. Click to create a rule from a form.</p>
      <div class="space-y-2">
        <div v-for="(form, idx) in detectedForms" :key="idx" class="flex items-center justify-between bg-gray-900/50 rounded-lg px-4 py-2">
          <div>
            <span class="text-sm text-white">{{ form.method }} {{ form.action || '(same page)' }}</span>
            <span class="text-xs text-gray-500 ml-2">{{ form.fields.length }} fields</span>
          </div>
          <button @click="createFromForm(form)" class="text-xs text-purple-400 hover:text-purple-300">
            Create Rule
          </button>
        </div>
      </div>
    </div>

    <div v-if="rules.length === 0" class="bg-gray-900 border border-gray-800 rounded-xl p-12 text-center">
      <p class="text-gray-400">No POST rules configured. POST requests will be blocked by the shield.</p>
    </div>

    <div v-else class="space-y-4">
      <div v-for="rule in rules" :key="rule.id" class="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <div class="flex items-start justify-between">
          <div>
            <div class="flex items-center gap-2">
              <h3 class="text-lg font-semibold text-white">{{ rule.name }}</h3>
              <span
                class="px-2 py-0.5 rounded-full text-xs"
                :class="rule.is_active ? 'bg-green-500/10 text-green-400' : 'bg-gray-700 text-gray-400'"
              >
                {{ rule.is_active ? 'Active' : 'Inactive' }}
              </span>
            </div>
            <p class="text-sm text-gray-400 mt-1">
              Pattern: <code class="bg-gray-800 px-1.5 py-0.5 rounded text-blue-400">{{ rule.url_pattern }}</code>
              &rarr; <code class="bg-gray-800 px-1.5 py-0.5 rounded text-green-400">{{ rule.forward_to }}</code>
            </p>
            <div class="flex gap-4 mt-2 text-xs text-gray-500">
              <span>Rate: {{ rule.rate_limit_requests }}/{{ rule.rate_limit_window }}s</span>
              <span>Fields: {{ rule.fields.length }}</span>
              <span v-if="rule.honeypot_field">Honeypot: {{ rule.honeypot_field }}</span>
            </div>
            <div v-if="rule.fields.length > 0" class="mt-3 flex flex-wrap gap-2">
              <span
                v-for="field in rule.fields"
                :key="field.id"
                class="px-2 py-1 bg-gray-800 rounded text-xs text-gray-300"
              >
                {{ field.field_name }}
                <span class="text-gray-500">({{ field.field_type }}{{ field.required ? ', required' : '' }})</span>
              </span>
            </div>
          </div>
          <button
            @click="deleteRule(rule.id)"
            class="px-3 py-1.5 bg-red-500/10 hover:bg-red-500/20 text-sm text-red-400 rounded-lg transition-colors"
          >
            Delete
          </button>
        </div>
      </div>
    </div>

    <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 overflow-y-auto py-8">
      <div class="bg-gray-900 border border-gray-800 rounded-xl w-full max-w-2xl p-6 mx-4">
        <h2 class="text-xl font-bold text-white mb-4">{{ editingRule ? 'Edit Rule' : 'Create POST Rule' }}</h2>
        <form @submit.prevent="handleSave" class="space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-300 mb-1">Rule Name</label>
              <input v-model="form.name" required class="w-full px-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Contact Form" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-300 mb-1">URL Pattern</label>
              <input v-model="form.url_pattern" required class="w-full px-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="/contact" />
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-300 mb-1">Forward To (WordPress URL)</label>
            <input v-model="form.forward_to" required type="url" class="w-full px-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="https://mysite.com/wp-admin/admin-post.php" />
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-300 mb-1">Success Redirect</label>
              <input v-model="form.success_redirect" class="w-full px-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="/thank-you" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-300 mb-1">Honeypot Field</label>
              <input v-model="form.honeypot_field" class="w-full px-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="website_url" />
            </div>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-300 mb-1">Rate Limit (requests)</label>
              <input v-model.number="form.rate_limit_requests" type="number" min="1" class="w-full px-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-300 mb-1">Rate Window (seconds)</label>
              <input v-model.number="form.rate_limit_window" type="number" min="1" class="w-full px-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
          </div>

          <div>
            <div class="flex items-center justify-between mb-2">
              <label class="text-sm font-medium text-gray-300">Allowed Fields</label>
              <button type="button" @click="addField" class="text-xs text-blue-400 hover:text-blue-300">+ Add Field</button>
            </div>
            <div class="space-y-2">
              <div v-for="(field, idx) in form.fields" :key="idx" class="flex gap-2 items-start">
                <input v-model="field.field_name" placeholder="Field name" class="flex-1 px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
                <select v-model="field.field_type" class="px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                  <option value="text">text</option>
                  <option value="email">email</option>
                  <option value="phone">phone</option>
                  <option value="number">number</option>
                  <option value="url">url</option>
                </select>
                <input v-model.number="field.max_length" type="number" placeholder="Max len" class="w-24 px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
                <label class="flex items-center gap-1 text-xs text-gray-400 py-2">
                  <input v-model="field.required" type="checkbox" class="rounded bg-gray-800 border-gray-700" />
                  Req
                </label>
                <button type="button" @click="form.fields.splice(idx, 1)" class="p-2 text-red-400 hover:bg-red-500/10 rounded">
                  &times;
                </button>
              </div>
            </div>
          </div>

          <div v-if="formError" class="text-sm text-red-400">{{ formError }}</div>
          <div class="flex justify-end gap-3 pt-2">
            <button type="button" @click="showModal = false" class="px-4 py-2 text-sm text-gray-400">Cancel</button>
            <button type="submit" :disabled="saving" class="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-medium rounded-lg transition-colors">
              {{ saving ? 'Saving...' : 'Save Rule' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import api from '../api'

const props = defineProps({ siteId: String })

const site = ref(null)
const rules = ref([])
const pages = ref([])
const showModal = ref(false)
const editingRule = ref(null)
const saving = ref(false)
const formError = ref('')

const defaultForm = () => ({
  name: '',
  url_pattern: '',
  forward_to: '',
  success_redirect: '',
  honeypot_field: '',
  rate_limit_requests: 10,
  rate_limit_window: 60,
  fields: [],
})
const form = reactive(defaultForm())

const detectedForms = computed(() => {
  const forms = []
  for (const page of pages.value) {
    if (page.detected_forms) {
      try {
        const parsed = JSON.parse(page.detected_forms)
        forms.push(...parsed.filter(f => f.method === 'POST'))
      } catch {}
    }
  }
  return forms
})

function openCreateModal() {
  Object.assign(form, defaultForm())
  editingRule.value = null
  showModal.value = true
}

function createFromForm(detected) {
  Object.assign(form, defaultForm())
  form.name = `Form: ${detected.action || detected.page_url}`
  form.url_pattern = detected.action || '/'
  form.forward_to = site.value ? `${site.value.target_url}${detected.action || '/'}` : detected.action
  form.fields = detected.fields.map(f => ({
    field_name: f.name,
    field_type: f.type === 'textarea' ? 'text' : (f.type || 'text'),
    required: f.required || false,
    max_length: f.maxlength || 1000,
    validation_regex: f.pattern || null,
  }))
  editingRule.value = null
  showModal.value = true
}

function addField() {
  form.fields.push({ field_name: '', field_type: 'text', required: false, max_length: 1000, validation_regex: null })
}

async function handleSave() {
  formError.value = ''
  saving.value = true
  try {
    const payload = {
      site_id: props.siteId,
      name: form.name,
      url_pattern: form.url_pattern,
      forward_to: form.forward_to,
      success_redirect: form.success_redirect || null,
      honeypot_field: form.honeypot_field || null,
      rate_limit_requests: form.rate_limit_requests,
      rate_limit_window: form.rate_limit_window,
      fields: form.fields.filter(f => f.field_name),
    }
    await api.post('/rules/', payload)
    showModal.value = false
    await loadData()
  } catch (e) {
    formError.value = e.response?.data?.detail || 'Failed to save rule'
  } finally {
    saving.value = false
  }
}

async function deleteRule(ruleId) {
  if (!confirm('Delete this rule?')) return
  try {
    await api.delete(`/rules/${ruleId}`)
    rules.value = rules.value.filter(r => r.id !== ruleId)
  } catch {}
}

async function loadData() {
  try {
    const [siteResp, rulesResp, pagesResp] = await Promise.all([
      api.get(`/sites/${props.siteId}`),
      api.get(`/rules/${props.siteId}`),
      api.get(`/pages/${props.siteId}`),
    ])
    site.value = siteResp.data
    rules.value = rulesResp.data
    pages.value = pagesResp.data
  } catch {}
}

onMounted(loadData)
</script>
