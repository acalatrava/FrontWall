<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-950 px-4">
    <div class="w-full max-w-md">
      <div class="text-center mb-8">
        <svg class="w-16 h-16 mx-auto text-blue-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
          <path d="m9 12 2 2 4-4" stroke="#22c55e"/>
        </svg>
        <h1 class="mt-4 text-2xl font-bold text-white">Web Shield</h1>
        <p class="mt-1 text-gray-400">Sign in to your admin panel</p>
      </div>

      <form @submit.prevent="handleLogin" class="bg-gray-900 rounded-xl border border-gray-800 p-8 space-y-5">
        <div v-if="error" class="bg-red-500/10 border border-red-500/30 rounded-lg px-4 py-3 text-sm text-red-400">
          {{ error }}
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-300 mb-1.5">Username</label>
          <input
            v-model="username"
            type="text"
            required
            autocomplete="username"
            class="w-full px-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="admin"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-300 mb-1.5">Password</label>
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
          {{ loading ? 'Signing in...' : 'Sign In' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()
const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

onMounted(async () => {
  try {
    const needsSetup = await auth.checkSetup()
    if (needsSetup) {
      router.replace('/setup')
    }
  } catch {}
})

async function handleLogin() {
  error.value = ''
  loading.value = true
  try {
    await auth.login(username.value, password.value)
    router.push('/')
  } catch (e) {
    error.value = e.response?.data?.detail || 'Login failed'
  } finally {
    loading.value = false
  }
}
</script>
