<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-950 px-4">
    <div class="w-full max-w-md">
      <div class="text-center mb-8">
        <svg class="w-16 h-16 mx-auto text-blue-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
        </svg>
        <h1 class="mt-4 text-2xl font-bold text-white">{{ t('auth.resetPw.title') }}</h1>
      </div>

      <form @submit.prevent="handleReset" class="bg-gray-900 rounded-xl border border-gray-800 p-5 sm:p-8 space-y-5">
        <div v-if="error" class="bg-red-500/10 border border-red-500/30 rounded-lg px-4 py-3 text-sm text-red-400">{{ error }}</div>

        <div>
          <label class="block text-sm font-medium text-gray-300 mb-1.5">{{ t('auth.resetPw.newPassword') }}</label>
          <input v-model="password" type="password" required minlength="10" class="w-full px-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500" />
          <p class="mt-1 text-xs text-gray-500">{{ t('auth.setup.passwordHint') }}</p>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-300 mb-1.5">{{ t('auth.confirmPassword') }}</label>
          <input v-model="confirm" type="password" required class="w-full px-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>

        <button type="submit" :disabled="loading" class="w-full py-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium rounded-lg transition-colors">
          {{ loading ? t('auth.resetPw.resetting') : t('auth.resetPw.reset') }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import api from '../api'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const password = ref('')
const confirm = ref('')
const error = ref('')
const loading = ref(false)

async function handleReset() {
  error.value = ''
  if (password.value !== confirm.value) {
    error.value = t('auth.setup.passwordsNoMatch')
    return
  }
  loading.value = true
  try {
    await api.post('/auth/reset-password', {
      token: route.query.token,
      password: password.value,
    })
    router.push('/login?reset=ok')
  } catch (e) {
    const detail = e.response?.data?.detail
    if (Array.isArray(detail)) {
      error.value = detail.map(d => d.msg?.replace('Value error, ', '') || d.msg).join('. ')
    } else {
      error.value = detail || t('auth.resetPw.resetFailed')
    }
  } finally {
    loading.value = false
  }
}
</script>
