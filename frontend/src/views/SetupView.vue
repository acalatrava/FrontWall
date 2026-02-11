<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-950 px-4">
    <div class="w-full max-w-md">
      <div class="text-center mb-8">
        <svg class="w-16 h-16 mx-auto text-blue-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
          <path d="m9 12 2 2 4-4" stroke="#22c55e"/>
        </svg>
        <h1 class="mt-4 text-2xl font-bold text-white">Welcome to FrontWall</h1>
        <p class="mt-1 text-gray-400">Create your admin account to get started</p>
      </div>

      <form @submit.prevent="handleSetup" class="bg-gray-900 rounded-xl border border-gray-800 p-5 sm:p-8 space-y-5">
        <div v-if="error" class="bg-red-500/10 border border-red-500/30 rounded-lg px-4 py-3 text-sm text-red-400">
          {{ error }}
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-300 mb-1.5">Username</label>
          <input
            v-model="username"
            type="text"
            required
            class="w-full px-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="admin"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-300 mb-1.5">Email <span class="text-gray-500 font-normal">(optional)</span></label>
          <input
            v-model="email"
            type="email"
            class="w-full px-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="admin@example.com"
          />
          <p class="mt-1 text-xs text-gray-500">Used for password reset and notifications</p>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-300 mb-1.5">Password</label>
          <input
            v-model="password"
            type="password"
            required
            minlength="10"
            class="w-full px-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <p class="mt-1 text-xs text-gray-500">Min 10 chars, at least 1 uppercase, 1 lowercase, 1 digit</p>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-300 mb-1.5">Confirm Password</label>
          <input
            v-model="confirmPassword"
            type="password"
            required
            class="w-full px-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        <button
          type="submit"
          :disabled="loading"
          class="w-full py-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium rounded-lg transition-colors"
        >
          {{ loading ? 'Creating account...' : 'Create Admin Account' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()
const username = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const error = ref('')
const loading = ref(false)

async function handleSetup() {
  error.value = ''
  if (password.value !== confirmPassword.value) {
    error.value = 'Passwords do not match'
    return
  }
  loading.value = true
  try {
    await auth.setup(username.value, password.value, email.value)
    router.push('/dashboard')
  } catch (e) {
    const detail = e.response?.data?.detail
    if (Array.isArray(detail)) {
      error.value = detail.map(d => d.msg?.replace('Value error, ', '') || d.msg).join('. ')
    } else {
      error.value = detail || 'Setup failed'
    }
  } finally {
    loading.value = false
  }
}
</script>
