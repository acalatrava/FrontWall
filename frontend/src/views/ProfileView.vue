<template>
  <div class="max-w-2xl mx-auto">
    <h1 class="text-xl sm:text-2xl font-bold text-white mb-6">{{ t('profile.title') }}</h1>

    <!-- Account Info -->
    <div class="bg-gray-900 border border-gray-800 rounded-xl p-5 sm:p-6 mb-6">
      <h2 class="text-base font-semibold text-white mb-4">{{ t('profile.accountInfo') }}</h2>
      <div class="space-y-3">
        <div class="flex items-center justify-between">
          <span class="text-sm text-gray-400">{{ t('profile.emailLabel') }}</span>
          <span class="text-sm text-white font-medium">{{ auth.user?.email }}</span>
        </div>
        <div class="flex items-center justify-between">
          <span class="text-sm text-gray-400">{{ t('profile.roleLabel') }}</span>
          <span class="text-xs px-2 py-0.5 rounded-full font-semibold"
                :class="auth.user?.role === 'admin' ? 'bg-purple-500/10 text-purple-400' : 'bg-blue-500/10 text-blue-400'">
            {{ auth.user?.role }}
          </span>
        </div>
      </div>
    </div>

    <!-- Change Password -->
    <div class="bg-gray-900 border border-gray-800 rounded-xl p-5 sm:p-6 mb-6">
      <h2 class="text-base font-semibold text-white mb-4">{{ t('profile.changePassword') }}</h2>
      <form @submit.prevent="handleChangePassword" class="space-y-4">
        <div v-if="pwError" class="bg-red-500/10 border border-red-500/30 rounded-lg px-4 py-3 text-sm text-red-400">{{ pwError }}</div>
        <div v-if="pwSuccess" class="bg-emerald-500/10 border border-emerald-500/30 rounded-lg px-4 py-3 text-sm text-emerald-400">{{ pwSuccess }}</div>

        <div>
          <label class="block text-sm font-medium text-gray-300 mb-1.5">{{ t('profile.currentPassword') }}</label>
          <input v-model="currentPassword" type="password" required autocomplete="current-password"
                 class="w-full px-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-300 mb-1.5">{{ t('profile.newPassword') }}</label>
          <input v-model="newPassword" type="password" required autocomplete="new-password"
                 class="w-full px-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
          <p class="mt-1 text-xs text-gray-500">{{ t('profile.passwordHint') }}</p>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-300 mb-1.5">{{ t('profile.confirmNewPassword') }}</label>
          <input v-model="confirmNewPassword" type="password" required autocomplete="new-password"
                 class="w-full px-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
        </div>
        <button type="submit" :disabled="pwLoading"
                class="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-medium rounded-lg transition-colors">
          {{ pwLoading ? t('profile.saving') : t('profile.savePassword') }}
        </button>
      </form>
    </div>

    <!-- Passkey Management -->
    <div class="bg-gray-900 border border-gray-800 rounded-xl p-5 sm:p-6">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-base font-semibold text-white">{{ t('profile.yourPasskeys') }}</h2>
        <button @click="registerPasskey" :disabled="passkeyRegistering"
                class="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-white text-xs font-medium rounded-lg border border-gray-700 transition-colors flex items-center gap-1.5">
          <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0110 0v4"/></svg>
          {{ passkeyRegistering ? t('profile.registering') : t('profile.addPasskey') }}
        </button>
      </div>

      <div v-if="passkeys.length === 0" class="text-center py-6">
        <p class="text-sm text-gray-500">{{ t('profile.noPasskeys') }}</p>
      </div>
      <div v-else class="divide-y divide-gray-800/50">
        <div v-for="pk in passkeys" :key="pk.id" class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 py-3">
          <div class="min-w-0">
            <div class="text-sm text-white font-medium truncate">{{ pk.name }}</div>
            <div class="text-xs text-gray-500 truncate">{{ t('profile.registered') }} {{ formatDate(pk.created_at) }} &middot; ID: {{ pk.credential_id_preview }}</div>
          </div>
          <div class="flex items-center gap-3 flex-shrink-0">
            <span v-if="pk.last_used" class="text-xs text-gray-500 hidden sm:inline">{{ t('profile.lastUsed') }} {{ formatDate(pk.last_used) }}</span>
            <button @click="deletePasskey(pk)" class="text-xs text-red-400 hover:text-red-300">{{ t('common.remove') }}</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import api from '../api'
import { useAuthStore } from '../stores/auth'

const { t } = useI18n()
const auth = useAuthStore()

// Password change
const currentPassword = ref('')
const newPassword = ref('')
const confirmNewPassword = ref('')
const pwError = ref('')
const pwSuccess = ref('')
const pwLoading = ref(false)

// Passkeys
const passkeys = ref([])
const passkeyRegistering = ref(false)

async function fetchPasskeys() {
  try {
    const { data } = await api.get('/auth/passkeys')
    passkeys.value = data
  } catch { /* empty */ }
}

onMounted(() => {
  fetchPasskeys()
})

async function handleChangePassword() {
  pwError.value = ''
  pwSuccess.value = ''
  if (newPassword.value !== confirmNewPassword.value) {
    pwError.value = t('profile.passwordsNoMatch')
    return
  }
  pwLoading.value = true
  try {
    await api.post('/auth/change-password', {
      current_password: currentPassword.value,
      new_password: newPassword.value,
    })
    pwSuccess.value = t('profile.passwordChanged')
    currentPassword.value = ''
    newPassword.value = ''
    confirmNewPassword.value = ''
  } catch (e) {
    const detail = e.response?.data?.detail
    if (Array.isArray(detail)) {
      pwError.value = detail.map(d => d.msg?.replace('Value error, ', '') || d.msg).join('. ')
    } else {
      pwError.value = detail || t('profile.changeFailed')
    }
  } finally {
    pwLoading.value = false
  }
}

// Passkey helpers
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
