import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const authenticated = ref(false)

  async function checkSetup() {
    const { data } = await api.get('/auth/setup-required')
    return data.setup_required
  }

  async function setup(username, password) {
    const { data } = await api.post('/auth/setup', { username, password })
    user.value = { user_id: data.user_id, username: data.username }
    authenticated.value = true
  }

  async function login(username, password) {
    const { data } = await api.post('/auth/login', { username, password })
    user.value = { user_id: data.user_id, username: data.username }
    authenticated.value = true
  }

  async function logout() {
    try {
      await api.post('/auth/logout')
    } catch {
      // Ignore logout errors
    }
    user.value = null
    authenticated.value = false
  }

  async function fetchUser() {
    try {
      const { data } = await api.get('/auth/me')
      user.value = data
      authenticated.value = true
    } catch {
      user.value = null
      authenticated.value = false
    }
  }

  async function checkAuth() {
    try {
      const { data } = await api.get('/auth/me')
      user.value = data
      authenticated.value = true
      return true
    } catch {
      user.value = null
      authenticated.value = false
      return false
    }
  }

  return { user, authenticated, checkSetup, setup, login, logout, fetchUser, checkAuth }
})
