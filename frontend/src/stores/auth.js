import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('ws_token') || '')
  const user = ref(null)

  async function checkSetup() {
    const { data } = await api.get('/auth/setup-required')
    return data.setup_required
  }

  async function setup(username, password) {
    const { data } = await api.post('/auth/setup', { username, password })
    token.value = data.access_token
    localStorage.setItem('ws_token', data.access_token)
  }

  async function login(username, password) {
    const { data } = await api.post('/auth/login', { username, password })
    token.value = data.access_token
    localStorage.setItem('ws_token', data.access_token)
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('ws_token')
  }

  async function fetchUser() {
    try {
      const { data } = await api.get('/auth/me')
      user.value = data
    } catch {
      logout()
    }
  }

  return { token, user, checkSetup, setup, login, logout, fetchUser }
})
