import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../api'

export const useShieldStore = defineStore('shield', () => {
  const active = ref(false)
  const port = ref(8080)
  const loading = ref(false)
  const learnMode = ref(false)

  async function fetchStatus() {
    const { data } = await api.get('/shield/status')
    active.value = data.active
    port.value = data.port
    learnMode.value = data.learn_mode || false
  }

  async function toggleLearnMode(enabled) {
    const { data } = await api.post('/shield/learn-mode', null, { params: { enabled } })
    learnMode.value = data.learn_mode
  }

  async function deploy(siteId) {
    loading.value = true
    try {
      const { data } = await api.post(`/shield/deploy/${siteId}`)
      active.value = true
      port.value = data.port
      return data
    } finally {
      loading.value = false
    }
  }

  async function undeploy() {
    loading.value = true
    try {
      await api.post('/shield/undeploy')
      active.value = false
    } finally {
      loading.value = false
    }
  }

  return { active, port, loading, learnMode, fetchStatus, deploy, undeploy, toggleLearnMode }
})
