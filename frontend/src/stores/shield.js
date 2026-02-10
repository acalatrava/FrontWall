import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../api'

export const useShieldStore = defineStore('shield', () => {
  const active = ref(false)
  const port = ref(8080)
  const loading = ref(false)

  async function fetchStatus() {
    const { data } = await api.get('/shield/status')
    active.value = data.active
    port.value = data.port
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

  return { active, port, loading, fetchStatus, deploy, undeploy }
})
