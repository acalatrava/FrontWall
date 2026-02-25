<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-xl sm:text-2xl font-bold text-white">{{ t('users.title') }}</h1>
      <button @click="showInvite = true" class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors">{{ t('users.inviteUser') }}</button>
    </div>

    <div v-if="loading" class="text-center text-gray-400 py-12">Loading...</div>

    <div v-else class="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
      <!-- Desktop table -->
      <div class="hidden md:block overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b border-gray-800 text-xs text-gray-500 uppercase">
              <th class="text-left py-3 px-5">{{ t('users.user') }}</th>
              <th class="text-left py-3 px-5">{{ t('users.role') }}</th>
              <th class="text-left py-3 px-5">{{ t('users.status') }}</th>
              <th class="text-left py-3 px-5">{{ t('users.lastLogin') }}</th>
              <th class="text-left py-3 px-5">{{ t('users.securityCol') }}</th>
              <th class="text-right py-3 px-5">{{ t('users.actions') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="u in users" :key="u.id" class="border-b border-gray-800/50 last:border-0 hover:bg-gray-800/30 transition-colors">
              <td class="py-3 px-5">
                <div class="text-sm font-medium text-white">{{ u.email }}</div>
              </td>
              <td class="py-3 px-5">
                <span class="px-2 py-0.5 rounded-full text-xs font-semibold"
                      :class="u.role === 'admin' ? 'bg-purple-500/10 text-purple-400' : 'bg-blue-500/10 text-blue-400'">
                  {{ u.role }}
                </span>
              </td>
              <td class="py-3 px-5">
                <span v-if="u.is_active" class="text-xs text-emerald-400 flex items-center gap-1">
                  <span class="w-1.5 h-1.5 bg-emerald-400 rounded-full"></span> Active
                </span>
                <span v-else class="text-xs text-red-400 flex items-center gap-1">
                  <span class="w-1.5 h-1.5 bg-red-400 rounded-full"></span> Inactive
                </span>
              </td>
              <td class="py-3 px-5 text-xs text-gray-400">{{ u.last_login ? formatDate(u.last_login) : t('users.never') }}</td>
              <td class="py-3 px-5">
                <div class="flex items-center gap-2">
                  <span v-if="u.email_verified" class="px-1.5 py-0.5 bg-emerald-500/10 text-emerald-400 rounded text-[10px]">{{ t('users.emailVerified') }}</span>
                  <span v-if="u.has_passkey" class="px-1.5 py-0.5 bg-blue-500/10 text-blue-400 rounded text-[10px]">{{ t('users.passkey') }}</span>
                </div>
              </td>
              <td class="py-3 px-5 text-right">
                <div v-if="u.id !== currentUserId" class="flex items-center justify-end gap-1">
                  <button @click="toggleRole(u)" class="px-2 py-1 text-xs text-gray-400 hover:text-white hover:bg-gray-700 rounded transition-colors">
                    {{ u.role === 'admin' ? t('users.demote') : t('users.promote') }}
                  </button>
                  <button @click="toggleActive(u)" class="px-2 py-1 text-xs rounded transition-colors"
                          :class="u.is_active ? 'text-amber-400 hover:bg-amber-500/10' : 'text-emerald-400 hover:bg-emerald-500/10'">
                    {{ u.is_active ? t('users.deactivate') : t('users.activate') }}
                  </button>
                  <button @click="handleDelete(u)" class="px-2 py-1 text-xs text-red-400 hover:bg-red-500/10 rounded transition-colors">{{ t('common.delete') }}</button>
                </div>
                <span v-else class="text-xs text-gray-600">{{ t('users.you') }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Mobile cards -->
      <div class="md:hidden divide-y divide-gray-800/50">
        <div v-for="u in users" :key="'m'+u.id" class="p-4 space-y-2">
          <div class="flex items-center justify-between">
            <div>
              <div class="text-sm font-medium text-white">{{ u.email }}</div>
            </div>
            <span class="px-2 py-0.5 rounded-full text-xs font-semibold"
                  :class="u.role === 'admin' ? 'bg-purple-500/10 text-purple-400' : 'bg-blue-500/10 text-blue-400'">
              {{ u.role }}
            </span>
          </div>
          <div class="flex flex-wrap items-center gap-2 text-xs">
            <span v-if="u.is_active" class="text-emerald-400 flex items-center gap-1">
              <span class="w-1.5 h-1.5 bg-emerald-400 rounded-full"></span> Active
            </span>
            <span v-else class="text-red-400 flex items-center gap-1">
              <span class="w-1.5 h-1.5 bg-red-400 rounded-full"></span> Inactive
            </span>
            <span v-if="u.email_verified" class="px-1.5 py-0.5 bg-emerald-500/10 text-emerald-400 rounded text-[10px]">{{ t('users.emailVerified') }}</span>
            <span v-if="u.has_passkey" class="px-1.5 py-0.5 bg-blue-500/10 text-blue-400 rounded text-[10px]">{{ t('users.passkey') }}</span>
            <span class="text-gray-500">{{ u.last_login ? formatDate(u.last_login) : t('users.neverLoggedIn') }}</span>
          </div>
          <div v-if="u.id !== currentUserId" class="flex flex-wrap gap-2 pt-1">
            <button @click="toggleRole(u)" class="px-2.5 py-1 text-xs text-gray-400 hover:text-white bg-gray-800 hover:bg-gray-700 rounded transition-colors">
              {{ u.role === 'admin' ? t('users.demote') : t('users.promote') }}
            </button>
            <button @click="toggleActive(u)" class="px-2.5 py-1 text-xs rounded transition-colors"
                    :class="u.is_active ? 'text-amber-400 bg-amber-500/10' : 'text-emerald-400 bg-emerald-500/10'">
              {{ u.is_active ? t('users.deactivate') : t('users.activate') }}
            </button>
            <button @click="handleDelete(u)" class="px-2.5 py-1 text-xs text-red-400 bg-red-500/10 rounded transition-colors">{{ t('common.delete') }}</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Passkey management for current user -->
    <div class="mt-8">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-base sm:text-lg font-bold text-white">{{ t('users.yourPasskeys') }}</h2>
        <button @click="registerPasskey" :disabled="passkeyRegistering" class="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-white text-xs font-medium rounded-lg border border-gray-700 transition-colors flex items-center gap-1.5">
          <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0110 0v4"/></svg>
          {{ passkeyRegistering ? t('users.registering') : t('users.addPasskey') }}
        </button>
      </div>
      <div v-if="passkeys.length === 0" class="bg-gray-900 border border-gray-800 rounded-xl p-6 text-center">
        <p class="text-sm text-gray-500">{{ t('users.noPasskeys') }}</p>
      </div>
      <div v-else class="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden divide-y divide-gray-800/50">
        <div v-for="pk in passkeys" :key="pk.id" class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 px-4 sm:px-5 py-3">
          <div class="min-w-0">
            <div class="text-sm text-white font-medium truncate">{{ pk.name }}</div>
            <div class="text-xs text-gray-500 truncate">{{ t('users.registered') }} {{ formatDate(pk.created_at) }} &middot; ID: {{ pk.credential_id_preview }}</div>
          </div>
          <div class="flex items-center gap-3 flex-shrink-0">
            <span v-if="pk.last_used" class="text-xs text-gray-500 hidden sm:inline">{{ t('users.lastUsed') }} {{ formatDate(pk.last_used) }}</span>
            <button @click="deletePasskey(pk)" class="text-xs text-red-400 hover:text-red-300">{{ t('common.remove') }}</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Invite modal -->
    <div v-if="showInvite" class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" @mousedown.self="showInvite = false">
      <div class="bg-gray-900 border border-gray-800 rounded-xl w-full max-w-md p-4 sm:p-6 mx-4 shadow-2xl">
        <h3 class="text-lg font-bold text-white mb-4">{{ t('users.inviteModal.title') }}</h3>
        <form @submit.prevent="handleInvite" class="space-y-4">
          <div v-if="inviteError" class="bg-red-500/10 border border-red-500/30 rounded-lg px-4 py-3 text-sm text-red-400">{{ inviteError }}</div>
          <div v-if="inviteSuccess" class="bg-emerald-500/10 border border-emerald-500/30 rounded-lg px-4 py-3 text-sm text-emerald-400">{{ inviteSuccess }}</div>

          <div>
            <label class="block text-sm font-medium text-gray-300 mb-1">{{ t('users.inviteModal.email') }}</label>
            <input v-model="inviteEmail" type="email" required class="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="user@example.com" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-300 mb-1">{{ t('users.inviteModal.role') }}</label>
            <select v-model="inviteRole" class="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
              <option value="viewer">{{ t('users.inviteModal.viewer') }}</option>
              <option value="admin">{{ t('users.inviteModal.admin') }}</option>
            </select>
            <p class="text-xs text-gray-500 mt-1">{{ t('users.inviteModal.roleHint') }}</p>
          </div>
          <div class="flex justify-end gap-3 pt-2">
            <button type="button" @click="showInvite = false" class="px-4 py-2 text-sm text-gray-400 hover:text-gray-200">{{ t('common.cancel') }}</button>
            <button type="submit" :disabled="inviting" class="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-medium rounded-lg transition-colors">
              {{ inviting ? t('users.inviteModal.sending') : t('users.inviteModal.send') }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import api from '../api'
import { useAuthStore } from '../stores/auth'

const { t } = useI18n()
const auth = useAuthStore()
const currentUserId = computed(() => auth.user?.user_id)

const users = ref([])
const passkeys = ref([])
const loading = ref(true)

const showInvite = ref(false)
const inviteEmail = ref('')
const inviteRole = ref('viewer')
const inviteError = ref('')
const inviteSuccess = ref('')
const inviting = ref(false)

const passkeyRegistering = ref(false)

async function fetchUsers() {
  loading.value = true
  try {
    const { data } = await api.get('/auth/users')
    users.value = data
  } catch { /* empty */ }
  loading.value = false
}

async function fetchPasskeys() {
  try {
    const { data } = await api.get('/auth/passkeys')
    passkeys.value = data
  } catch { /* empty */ }
}

onMounted(() => {
  fetchUsers()
  fetchPasskeys()
})

async function toggleRole(u) {
  const newRole = u.role === 'admin' ? 'viewer' : 'admin'
  if (!confirm(`Change ${u.email}'s role to ${newRole}?`)) return
  await api.put(`/auth/users/${u.id}`, { role: newRole })
  await fetchUsers()
}

async function toggleActive(u) {
  const action = u.is_active ? 'deactivate' : 'activate'
  if (!confirm(`${action.charAt(0).toUpperCase() + action.slice(1)} ${u.email}?`)) return
  await api.put(`/auth/users/${u.id}`, { is_active: !u.is_active })
  await fetchUsers()
}

async function handleDelete(u) {
  if (!confirm(`Permanently delete ${u.email}? This cannot be undone.`)) return
  await api.delete(`/auth/users/${u.id}`)
  await fetchUsers()
}

async function handleInvite() {
  inviteError.value = ''
  inviteSuccess.value = ''
  inviting.value = true
  try {
    await api.post('/auth/invite', { email: inviteEmail.value, role: inviteRole.value })
    inviteSuccess.value = `Invitation sent to ${inviteEmail.value}`
    inviteEmail.value = ''
    await fetchUsers()
    setTimeout(() => {
      showInvite.value = false
    }, 1500)
  } catch (e) {
    inviteError.value = e.response?.data?.detail || 'Failed to send invitation'
  } finally {
    inviting.value = false
  }
}

function _base64urlToBuffer(b64url) {
  const padding = '='.repeat((4 - b64url.length % 4) % 4)
  const base64 = (b64url + padding).replace(/-/g, '+').replace(/_/g, '/')
  const binary = atob(base64)
  const bytes = new Uint8Array(binary.length)
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i)
  return bytes.buffer
}

function _bufferToBase64url(buffer) {
  const bytes = new Uint8Array(buffer)
  let binary = ''
  for (const b of bytes) binary += String.fromCharCode(b)
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '')
}

async function registerPasskey() {
  passkeyRegistering.value = true
  try {
    const { data: optData } = await api.post('/auth/passkey/register-options', { name: 'My Passkey' })
    const options = JSON.parse(optData.options)

    options.challenge = _base64urlToBuffer(options.challenge)
    options.user.id = _base64urlToBuffer(options.user.id)
    if (options.excludeCredentials) {
      options.excludeCredentials = options.excludeCredentials.map(c => ({
        ...c,
        id: _base64urlToBuffer(c.id),
      }))
    }

    const credential = await navigator.credentials.create({ publicKey: options })

    const credentialJSON = {
      id: credential.id,
      rawId: _bufferToBase64url(credential.rawId),
      type: credential.type,
      response: {
        attestationObject: _bufferToBase64url(credential.response.attestationObject),
        clientDataJSON: _bufferToBase64url(credential.response.clientDataJSON),
      },
    }

    const transports = credential.response.getTransports ? credential.response.getTransports() : []

    await api.post('/auth/passkey/register-verify', {
      credential: credentialJSON,
      transports,
      name: optData.passkey_name,
    })

    await fetchPasskeys()
  } catch (e) {
    if (e.name !== 'NotAllowedError') {
      alert(e.response?.data?.detail || 'Passkey registration failed')
    }
  } finally {
    passkeyRegistering.value = false
  }
}

async function deletePasskey(pk) {
  if (!confirm(`Remove passkey "${pk.name}"?`)) return
  await api.delete(`/auth/passkeys/${pk.id}`)
  await fetchPasskeys()
}

function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}
</script>
