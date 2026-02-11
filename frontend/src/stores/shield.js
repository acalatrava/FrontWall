import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../api'

export const useShieldStore = defineStore('shield', () => {
  const shields = ref([])
  const loading = ref(false)

  async function fetchStatus() {
    const { data } = await api.get('/shield/status')
    shields.value = data.shields || []
  }

  async function fetchSiteStatus(siteId) {
    const { data } = await api.get(`/shield/status/${siteId}`)
    return data
  }

  async function deploy(siteId) {
    loading.value = true
    try {
      const { data } = await api.post(`/shield/deploy/${siteId}`)
      await fetchStatus()
      return data
    } finally {
      loading.value = false
    }
  }

  async function undeploy(siteId) {
    loading.value = true
    try {
      await api.post(`/shield/undeploy/${siteId}`)
      await fetchStatus()
    } finally {
      loading.value = false
    }
  }

  async function toggleLearnMode(siteId, enabled) {
    const { data } = await api.post(`/shield/learn-mode/${siteId}`, null, { params: { enabled } })
    await fetchStatus()
    return data
  }

  async function toggleBypassMode(siteId, enabled) {
    const { data } = await api.post(`/shield/bypass-mode/${siteId}`, null, { params: { enabled } })
    await fetchStatus()
    return data
  }

  function isActive(siteId) {
    return shields.value.some(s => s.site_id === siteId && s.active)
  }

  function getShield(siteId) {
    return shields.value.find(s => s.site_id === siteId)
  }

  return { shields, loading, fetchStatus, fetchSiteStatus, deploy, undeploy, toggleLearnMode, toggleBypassMode, isActive, getShield }
})
