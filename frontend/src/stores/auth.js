import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const authenticated = ref(false)

  const isAdmin = computed(() => user.value?.role === 'admin')

  async function checkSetup() {
    const { data } = await api.get('/auth/setup-required')
    return data.setup_required
  }

  async function setup(username, password, email) {
    const { data } = await api.post('/auth/setup', { username, password, email: email || null })
    user.value = { user_id: data.user_id, username: data.username, role: data.role }
    authenticated.value = true
  }

  async function login(username, password) {
    const { data } = await api.post('/auth/login', { username, password })
    user.value = { user_id: data.user_id, username: data.username, role: data.role }
    authenticated.value = true
  }

  async function loginWithPasskey() {
    const { data: optData } = await api.post('/auth/passkey/auth-options')
    const options = JSON.parse(optData.options)
    const sessionId = optData.session_id

    options.challenge = _base64urlToBuffer(options.challenge)
    if (options.allowCredentials) {
      options.allowCredentials = options.allowCredentials.map(c => ({
        ...c,
        id: _base64urlToBuffer(c.id),
      }))
    }

    const assertion = await navigator.credentials.get({ publicKey: options })

    const credential = {
      id: assertion.id,
      rawId: _bufferToBase64url(assertion.rawId),
      type: assertion.type,
      response: {
        clientDataJSON: _bufferToBase64url(assertion.response.clientDataJSON),
        authenticatorData: _bufferToBase64url(assertion.response.authenticatorData),
        signature: _bufferToBase64url(assertion.response.signature),
        userHandle: assertion.response.userHandle ? _bufferToBase64url(assertion.response.userHandle) : null,
      },
    }

    const { data } = await api.post('/auth/passkey/auth-verify', {
      credential,
      session_id: sessionId,
    })
    user.value = { user_id: data.user_id, username: data.username, role: data.role }
    authenticated.value = true
  }

  async function logout() {
    try {
      await api.post('/auth/logout')
    } catch {
      // Ignore
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

  return { user, authenticated, isAdmin, checkSetup, setup, login, loginWithPasskey, logout, fetchUser, checkAuth }
})


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
