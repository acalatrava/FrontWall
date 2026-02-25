<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-950 px-4">
    <div class="w-full max-w-md">
      <div class="text-center mb-8">
        <svg class="w-16 h-16 mx-auto text-blue-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
          <path d="m9 12 2 2 4-4" stroke="#22c55e"/>
        </svg>
        <h1 class="mt-4 text-2xl font-bold text-white">{{ t('auth.signInTitle') }}</h1>
        <p class="mt-1 text-gray-400">{{ t('auth.signInSubtitle') }}</p>
      </div>

      <form @submit.prevent="handleLogin" class="bg-gray-900 rounded-xl border border-gray-800 p-5 sm:p-8 space-y-5">
        <div v-if="error" class="bg-red-500/10 border border-red-500/30 rounded-lg px-4 py-3 text-sm text-red-400">
          {{ error }}
        </div>
        <div v-if="success" class="bg-emerald-500/10 border border-emerald-500/30 rounded-lg px-4 py-3 text-sm text-emerald-400">
          {{ success }}
        </div>

        <template v-if="!requiringPasskey">
          <div>
          <label class="block text-sm font-medium text-gray-300 mb-1.5">{{ t('auth.email') }}</label>
            <input
              v-model="email"
              type="email"
              required
              autocomplete="email"
              class="w-full px-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="admin@example.com"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-300 mb-1.5">{{ t('auth.password') }}</label>
            <input
              v-model="password"
              type="password"
              required
              autocomplete="current-password"
              class="w-full px-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <button
            type="submit"
            :disabled="loading"
            class="w-full py-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium rounded-lg transition-colors"
          >
            {{ loading ? t('auth.signingIn') : t('auth.signIn') }}
          </button>

          <div v-if="passkeyAvailable" class="relative">
            <div class="absolute inset-0 flex items-center"><div class="w-full border-t border-gray-800"></div></div>
            <div class="relative flex justify-center text-xs"><span class="bg-gray-900 px-3 text-gray-500">{{ t('auth.orDivider') }}</span></div>
          </div>

          <button
            v-if="passkeyAvailable"
            type="button"
            @click="handlePasskeyLogin"
            :disabled="passkeyLoading"
            class="w-full py-2.5 bg-gray-800 hover:bg-gray-700 disabled:opacity-50 text-white font-medium rounded-lg transition-colors flex items-center justify-center gap-2 border border-gray-700"
          >
            <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0110 0v4"/></svg>
            {{ passkeyLoading ? t('auth.passkeyVerifying') : t('auth.passkeySignIn') }}
          </button>

          <div class="text-center pt-1">
            <router-link to="/forgot-password" class="text-xs text-gray-500 hover:text-gray-300 transition-colors">{{ t('auth.forgotPassword') }}</router-link>
          </div>
        </template>

        <template v-else>
          <div class="text-center py-2 space-y-4">
            <div class="mx-auto w-12 h-12 bg-blue-500/10 rounded-full flex items-center justify-center text-blue-400">
              <svg class="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0110 0v4"/></svg>
            </div>
            <div>
              <p class="text-white font-medium">{{ t('auth.twoFactorRequired', 'Two-Factor Required') }}</p>
              <p class="text-sm text-gray-400 mt-1">Please verify with your passkey</p>
            </div>
            <button
              type="button"
              @click="handlePasskeyLogin"
              :disabled="passkeyLoading"
              class="w-full py-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium rounded-lg transition-colors flex items-center justify-center gap-2"
            >
              {{ passkeyLoading ? t('auth.passkeyVerifying') : 'Verify Passkey' }}
            </button>
            <button 
              type="button" 
              @click="requiringPasskey = false"
              class="text-xs text-gray-500 hover:text-white transition-colors"
            >
              Cancel
            </button>
          </div>
        </template>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '../stores/auth'

const { t } = useI18n()
const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const email = ref('')
const password = ref('')
const error = ref('')
const success = ref('')
const loading = ref(false)
const passkeyLoading = ref(false)
const passkeyAvailable = ref(false)
const requiringPasskey = ref(false)

onMounted(async () => {
  passkeyAvailable.value = !!(window.PublicKeyCredential && typeof window.PublicKeyCredential === 'function')

  if (route.query.reset === 'ok') {
    success.value = 'Password reset successfully. Please sign in.'
  }

  try {
    const needsSetup = await auth.checkSetup()
    if (needsSetup) {
      router.replace('/setup')
    }
  } catch {}
})

async function handleLogin() {
  error.value = ''
  success.value = ''
  loading.value = true
  try {
    const result = await auth.login(email.value, password.value)
    if (result && result.require_passkey) {
      requiringPasskey.value = true
      return
    }
    router.push('/dashboard')
  } catch (e) {
    const detail = e.response?.data?.detail
    if (Array.isArray(detail)) {
      error.value = detail.map(d => d.msg?.replace('Value error, ', '') || d.msg).join('. ')
    } else {
      error.value = detail || 'Login failed'
    }
  } finally {
    loading.value = false
  }
}

async function handlePasskeyLogin() {
  error.value = ''
  success.value = ''
  passkeyLoading.value = true
  try {
    await auth.loginWithPasskey()
    router.push('/dashboard')
  } catch (e) {
    if (e.name === 'NotAllowedError') {
      error.value = 'Passkey authentication was cancelled.'
    } else {
      error.value = e.response?.data?.detail || 'Passkey authentication failed'
    }
  } finally {
    passkeyLoading.value = false
  }
}
</script>
