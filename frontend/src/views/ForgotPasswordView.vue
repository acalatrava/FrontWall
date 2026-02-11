<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-950 px-4">
    <div class="w-full max-w-md">
      <div class="text-center mb-8">
        <svg class="w-16 h-16 mx-auto text-blue-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
        </svg>
        <h1 class="mt-4 text-2xl font-bold text-white">Reset Password</h1>
        <p class="mt-1 text-gray-400">Enter your email to receive a reset link</p>
      </div>

      <div v-if="sent" class="bg-gray-900 rounded-xl border border-gray-800 p-5 sm:p-8 text-center">
        <div class="w-12 h-12 mx-auto mb-4 bg-emerald-500/10 rounded-full flex items-center justify-center">
          <svg class="w-6 h-6 text-emerald-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
        </div>
        <p class="text-gray-300 mb-2">Check your email</p>
        <p class="text-sm text-gray-500 mb-6">If an account exists with that email, we've sent a reset link.</p>
        <router-link to="/login" class="text-sm text-blue-400 hover:text-blue-300">Back to Sign In</router-link>
      </div>

      <form v-else @submit.prevent="handleSubmit" class="bg-gray-900 rounded-xl border border-gray-800 p-5 sm:p-8 space-y-5">
        <div v-if="error" class="bg-red-500/10 border border-red-500/30 rounded-lg px-4 py-3 text-sm text-red-400">{{ error }}</div>

        <div>
          <label class="block text-sm font-medium text-gray-300 mb-1.5">Email</label>
          <input v-model="email" type="email" required class="w-full px-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="you@example.com" />
        </div>

        <button type="submit" :disabled="loading" class="w-full py-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium rounded-lg transition-colors">
          {{ loading ? 'Sending...' : 'Send Reset Link' }}
        </button>

        <div class="text-center">
          <router-link to="/login" class="text-xs text-gray-500 hover:text-gray-300">Back to Sign In</router-link>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import api from '../api'

const email = ref('')
const error = ref('')
const loading = ref(false)
const sent = ref(false)

async function handleSubmit() {
  error.value = ''
  loading.value = true
  try {
    await api.post('/auth/forgot-password', { email: email.value })
    sent.value = true
  } catch (e) {
    error.value = e.response?.data?.detail || 'Failed to send reset link'
  } finally {
    loading.value = false
  }
}
</script>
